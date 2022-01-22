# -- Third-party --
from OpenGL.GL import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtOpenGL import *
from shiboken6 import VoidPtr
import numpy as np

# -- First-Party -- 
from viewer.gl.shading import BaseProgram

# -- Globals --
NP_TEXTURE_FORMAT = {
    'uint8': GL_UNSIGNED_BYTE,
    'float16': GL_HALF_FLOAT,
    'float32': GL_FLOAT,
}
RGB_CHANNELS = {
    GL_UNSIGNED_BYTE: GL_RGB8,
    GL_HALF_FLOAT: GL_RGB16F,
    GL_FLOAT: GL_RGB32F
}
RGBA_CHANNELS = {
    GL_UNSIGNED_BYTE: GL_RGBA8,
    GL_HALF_FLOAT: GL_RGBA16F,
    GL_FLOAT: GL_RGBA32F
}
R_CHANNEL = {
    GL_UNSIGNED_BYTE: GL_R8,
    GL_HALF_FLOAT: GL_R16F,
    GL_FLOAT: GL_R32F
}


class BaseWrapper(object):

    def __enter__(self):
        self.bind()
        return self

    def __exit__(self, *args):
        self.release()


class Buffer(QOpenGLBuffer, BaseWrapper):
    def __init__(self, *args, **kwargs):
        super(Buffer, self).__init__(*args, **kwargs)
        self.create()

    def allocate(self, allocation):
        if isinstance(allocation, np.ndarray):
            return super(Buffer, self).allocate(allocation, allocation.nbytes)
        return super(Buffer, self).allocate(allocation)


class ImageShader(BaseProgram):

    vertex = """
    #version 400
    in layout(location = 0) vec3 vertexPosition;
    in layout(location = 1) vec2 vertexUV;

    uniform mat4 MVP;

    out vertex {
        vec2 UV;
        vec3 Position;
    } verts;

    void main()
    {
        gl_Position = MVP * vec4(vertexPosition, 1);
        verts.UV = vertexUV;
        verts.Position = vertexPosition;
    }
    """

    fragment = """
    #version 400
    in vertex {
        vec2 UV;
        vec3 Position;
    } verts;

    uniform sampler2D tex2D;

    out vec4 rgba;

    void main()
    {
        rgba = texture2D(tex2D, verts.UV);
    }
    """

    @classmethod
    def create(cls):
        obj = super(ImageShader, cls).fromGlsl(
            ImageShader.vertex, ImageShader.fragment
        )
        obj.setUniforms('MVP', 'tex2D')
        return obj


class TextureFactory(object):


    def __init__(self, *args, **kwargs):
        self.textures = {}
        self.shader = ImageShader.create()
        self.glf = QOpenGLFunctions(QOpenGLContext.currentContext())

    @staticmethod
    def _keyFromPixels(pixels, sequence=0):
        return '{}{}{}{}{}'.format(sequence, *pixels.shape, pixels.itemsize)

    def addNewFormat(self, pixels, order, sequence=0):
        key = self._keyFromPixels(pixels, sequence)
        if not key in self.textures.keys():
            self.textures[key] = BufferedTexture(pixels, order, self.glf)
        return self.textures[key]

    def clear(self):
        values = self.textures.values()
        glDeleteTextures(len(values), values)


class BufferedTexture(object):
    __slots__ = [
        'id',
        'pbo',
        'order',
        'texture_format',
        'pixel_format',
        'height',
        'width',
        'glf',
        'pixels',
    ]

    def __init__(self, pixels, order, glf):
        self.glf = glf
        self.id = glGenTextures(1)
        self.pbo = Buffer(QOpenGLBuffer.PixelUnpackBuffer)
        with self.pbo as pbo:
            pbo.setUsagePattern(QOpenGLBuffer.StreamDraw)
            pbo.allocate(pixels.nbytes)

        glBindTexture(GL_TEXTURE_2D, self.id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        # need to use QOpenGLFunctions for GL_HALF_FLOAT type missing in python ctypes.
        texture_format = NP_TEXTURE_FORMAT.get(str(pixels.dtype))
        height, width, channels = pixels.shape
        if channels == 3:
            pixel_format = RGB_CHANNELS.get(texture_format)
            self.order = GL_RGB if order == 'rgb' else GL_BGR
        elif channels == 4:
            pixel_format = RGBA_CHANNELS.get(texture_format)
            self.order = GL_RGBA if order == 'rgb' else GL_BGRA
        elif channels == 1:
            pixel_format = R_CHANNEL.get(texture_format)
            self.order = GL_RED
        self.glf.glTexImage2D(
            GL_TEXTURE_2D,
            0,
            pixel_format,
            width,
            height,
            0,
            self.order,
            texture_format,
            VoidPtr(0),
        )
        glBindTexture(GL_TEXTURE_2D, 0)
        self.texture_format = texture_format
        self.pixel_format = pixel_format
        self.height = height; self.width = width
        self.pixels = pixels

    def push(self, pixels):
        with self.pbo as pbo:
            glBindTexture(GL_TEXTURE_2D, self.id)
            self.glf.glTexSubImage2D(
                GL_TEXTURE_2D, 0, 0, 0, self.width, self.height, self.order, self.texture_format, VoidPtr(0))
            pbo.write(0, pixels, pixels.nbytes)
            #glBindTexture(GL_TEXTURE_2D, 0)
        self.pixels = pixels

    def pull(self):
        with self.pbo as pbo:
            glBindTexture(GL_TEXTURE_2D, self.id)
            self.glf.glTexSubImage2D(
                GL_TEXTURE_2D, 0, 0, 0, self.width, self.height, self.order, self.texture_format, VoidPtr(0))
            #glBindTexture(GL_TEXTURE_2D, 0)