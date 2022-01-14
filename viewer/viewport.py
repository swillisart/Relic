import os
import sys
import copy
from ctypes import c_void_p
from collections import deque
import string
from sequencePath import sequencePath as Path
# -- Third-party -- 

import glm
import numpy as np
import ocio.PyOpenColorIO as ocio

from OpenGL.arrays import vbo
from OpenGL.GL import *
from OpenGL.GL import shaders as GLShaders
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtOpenGL import *
from PySide6.QtWidgets import *
from shiboken6 import VoidPtr

# -- Module --
from viewer.gl.widgets import InteractiveGLView
from viewer.gl.shading import BaseProgram
from viewer.gl.primitives import Circle, ColorWheel, Line, LineRect, Ellipse
from viewer.gl.text import glyphContainer, TextShader, createFontAtlas
from viewer.ui.widgets import colorSampler, AnnotationDock
# -- Globals --
NOPE = 0
OVERSCAN = 1

SHADER_DESCRIPTION = {
    "language": ocio.Constants.GPU_LANGUAGE_GLSL_1_3,
    "functionName": "OCIODisplay",
    "lut3DEdgeLen": 32,
}
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


class BrushStroke(QObject):

    updatedBrushCursor = Signal(QImage)

    def __init__(self, radius, color=QColor(250, 250, 250), focal=1, img=None):
        self.setBrushRadius(radius)
        self.tip = color
        self.color = color
        self.eraser = QColor(255, 255, 255, 255)
        self.erase = False

    @property
    def doubleSize(self):
        return int(self.radius * 2)

    @property
    def halfSize(self):
        return self.radius / 2

    @Slot()
    def setColor(self, color):
        if self.tip != self.eraser:
            self.tip = color
        self.color = color

    def setBrushRadius(self, radius):
        if radius <= 2:
            radius = 2
        self.radius = int(radius)
        self.spacing = int(radius / 4.0) or 1

    def scaleBrush(self, amount):
        new_size = (self.radius + amount + 0.5)
        self.setBrushRadius(new_size)

    def toggleEraser(self):
        if self.tip == self.eraser:
            self.tip = self.color
            self.erase = False
        else:
            self.tip = self.eraser
            self.erase = True


class ShapeFactory(object):
    RECTANGLE = 0 
    LINE = 1
    ELLIPSE = 2
    CIRCLE = 3
    NOTE = 4

    def __init__(self, *args, **kwargs):
        super(ShapeFactory, self).__init__(*args, **kwargs)
        self.primitives = deque()
        self._type = 0
        self.active = None
        self.undone = deque()
        self.text_shader = None
        self.glyphs = None
        self.text = ''

    def undo(self):
        self.undone.append(self.primitives.pop())

    def redo(self):
        self.primitives.append(self.undone.pop())

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, index):
        self._type = index
        self.newActiveShape()

    def create(self):
        self.undone.clear()
        if self._type == self.NOTE:
            self.active.newText(self.text.strip(), self.text_pos, self.text_scale)
        self.primitives.append(copy.copy(self.active))
        self.newActiveShape()

    def newActiveShape(self):
        if self._type == self.RECTANGLE:
            self.active = LineRect()
        elif self._type == self.LINE:
            self.active = Line()
        elif self._type == self.ELLIPSE:
            self.active = Ellipse()
        elif self._type == self.CIRCLE:
            self.active = Ellipse()
        elif self._type == self.NOTE:
            self.active = self.glyphs

    def updateActiveShape(self, a, b, color):
        left, right, bot, top = self.getRect(a, b)
        dist = glm.distance(b, a)
        size = a - b
        
        move = glm.vec3(a - (size / 2), 0.0)
        t = glm.translate(glm.mat4(1.0), move)
        primitive = self.active
        primitive.color = glm.vec4(*color)
        if self._type == self.CIRCLE:
            primitive.transform = glm.scale(t, glm.vec3(dist))
        
        elif self._type == self.ELLIPSE:
            s = glm.vec3(size.x, size.y, 0)
            primitive.transform = glm.scale(t, s)

        elif self._type == self.LINE:
            primitive.resize(a, b)

        elif self._type == self.RECTANGLE:
            primitive.resize(left, right, bot, top)

        elif self._type == self.NOTE:
            self.text = '\n'
            self.text_pos = a
            self.text_scale = dist * 0.005
            primitive.newText(self.text, a, self.text_scale)

    @staticmethod
    def getRect(a, b):
        left = min(a.x, b.x)
        right = max(a.x, b.x)
        bot = min(a.y, b.y)
        top = max(a.y, b.y)
        return left, right, bot, top

class PaintEngine(QObject):
    
    LINES = 10# * 3
    STEP = 0.1# / 3
    #LINES = 32
    #STEP = 1.0 / float(LINES)

    def __init__(self, *args, **kwargs):
        super(PaintEngine, self).__init__(*args, **kwargs)
        self.strokes = deque()
        self.brush = BrushStroke(12, QColor(0, 255, 0, 255))
        self.shapes = ShapeFactory()
        self.enabled = False

    def clear(self):
        self.shapes.glyphs.reset()
        self.shapes.glyphs.rebuild()
        self.shapes.primitives.clear()
        self.strokes.clear()

    def drawOnCanvas(self, x, y, canvas, result=True):
        qpainter = QPainter()
        qpainter.begin(canvas)
        if self.brush.erase:
            qpainter.setCompositionMode(QPainter.CompositionMode_DestinationOut)
        radGrad = QRadialGradient(x, y, self.brush.halfSize)
        #radGrad.setFocalRadius(2)
        radGrad.setColorAt(0, self.brush.tip)
        radGrad.setColorAt(1, QColor(0,0,0,0))
        brsh_double = self.brush.doubleSize
        brush_rect = QRect(
                int(x) - self.brush.radius,
                int(y) - self.brush.radius,
                brsh_double,
                brsh_double,
            )
        qpainter.setBrush(radGrad)
        qpainter.fillRect(brush_rect, radGrad)
        qpainter.end()
        #roi = canvas.copy(brush_rect)
        if result:
            array = np.ndarray(
                #shape = (self.brush.radius, self.brush.radius, 3),
                shape = (canvas.height(), canvas.width(), 3),
                buffer = canvas.constBits(),
                dtype = np.uint8
            )
        else:
            array = False

        return array

    @staticmethod
    def iterativeSpline(points, spline, diameter):
        if len(points) < 4:
            return

        speed = glm.distance(points[0], points[-1])
        if speed >= 5:
            speed = int(speed) / diameter
            for index in range(int(PaintEngine.LINES * speed)):
                b = PaintEngine.splineInterpolation(points, (PaintEngine.STEP / speed) * float(index))
                spline.append(b)
        else:
            spline.append(points.pop())
            return
        # exetend our last to a (made up vector)

        points.popleft()

    @staticmethod
    def splineInterpolation(four_points, t=1.0):
        """
        Interpolation of 4 points using catmull-rom 
        see: https://en.wikipedia.org/wiki/Centripetal_Catmull–Rom_spline

        Parameters
        ----------
        four_points : collections.deque or list
            [vec2(x, y), ..] coordinates for interpolating between
        t : float, optional
            tension?, by default 1.0

        Returns
        -------
        vec2(x, y)
            interpolated point position
        """
        alpha = 1.0
        tension = 0.0
        p0, p1, p2, p3 = four_points
        
        t01 = pow(glm.distance(p0, p1), alpha)
        t12 = pow(glm.distance(p1, p2), alpha)
        t23 = pow(glm.distance(p2, p3), alpha)

        m1 = (1.0 - tension) * (p2 - p1 + t12 * ((p1 - p0) / t01 - (p2 - p0) / (t01 + t12)))
        m2 = (1.0 - tension) * (p2 - p1 + t12 * ((p3 - p2) / t23 - (p3 - p1) / (t12 + t23)))
        
        a = 2.0 * (p1 - p2) + m1 + m2
        b = -3.0 * (p1 - p2) - m1 - m1 - m2
        c = m1
        d = p1

        return a * t * t * t + b * t * t + c * t + d

    @staticmethod
    def iterativeSplineYielder(points):
        """
        curve fitting / smoothing.

        Parameters
        ----------
        points : collections.deque
            queue of 2d points for a brush stroke (glm.vec2)

        Yields
        -------
        glm.vec2(x, y)
            interpolated coordinate.
        """
        #if len(points) == 2:
        #    initial = ((points[0] - points[1]) * 2) + points[0]
        #    points.appendleft(initial)
        #    return
        if len(points) <= 3:
            return

        # TODO: scale the distance 
        #speed = glm.distance(p0, p3)
        # if (speed % 10) == 1 # check the divisibility first
        for l_index in range(PaintEngine.LINES):
            b = PaintEngine.splineInterpolation(points, PaintEngine.STEP * float(l_index))
            yield b
            #spline.append(b.x, b.y)
        points.popleft()


class colorFramebuffer(object):
    
    vertex_shader = """
        #version 330 core
        in layout(location = 0) vec3 vertexPosition;
        in layout(location = 1) vec2 vertexUV;

        out vec2 fVertexUV;

        void main()
        {
            gl_Position = vec4(vertexPosition, 1.0);
            fVertexUV = vertexUV;
        }
    """

    fragment_shader = """
        #version 330 core
        {}
        in vec2 fVertexUV;

        uniform sampler2D framebufferTexture;
        uniform sampler3D lut3DTexture;

        uniform float exposure;
        uniform float gamma;

        out vec4 out_rgba;

        void main()
        {{
            vec4 rgba = texture(framebufferTexture, fVertexUV);
            vec4 gain = vec4(rgba.rgb * pow(2.0, exposure), rgba.a);
            vec4 knee = vec4(pow(gain.rgb, vec3(1.0/gamma)), rgba.a);
            vec4 color = OCIODisplay(knee, lut3DTexture);
            out_rgba = {};
        }}
    """
    base_shader = """
        #version 330 core
        in vec2 fVertexUV;

        uniform sampler2D framebufferTexture;

        uniform float exposure;
        uniform float gamma;

        out vec4 out_rgba;

        void main()
        {{
            vec4 rgba = texture(framebufferTexture, fVertexUV);
            vec4 gain = vec4(rgba.rgb * pow(2.0, exposure), rgba.a);
            vec4 knee = vec4(pow(gain.rgb, vec3(1.0/gamma)), rgba.a);
            vec4 color = knee;
            out_rgba = {};
        }}
    """
    exposure = 0.0
    gamma = 1.0

    def __init__(self, width, height):
        # OpenGL targets
        self.FBO = glGenFramebuffers(1)
        self.color_target_texture = glGenTextures(1)
        self.depth_target_texture = glGenTextures(1)
        self.lut3d_target_texture = glGenTextures(1)
        self.bgc = 0.18
        self.active_channel = 'color'
        # Sets the intial view and creates our shader for uniform assignment
 
        # Geometry buffers
        self.quad_elements = np.array(
            [#  (X - Y - Z)  (U -  V)
                -1, -1, 0.0, 0.0, 0.0,
                 1, -1, 0.0, 1.0, 0.0,
                 1,  1, 0.0, 1.0, 1.0,
                -1,  1, 0.0, 0.0, 1.0,
            ],
            dtype=np.float32,
        )
        self.quad_vbo = vbo.VBO(self.quad_elements)
        self.quad_ibo = vbo.VBO(
            np.array([0, 1, 2, 2, 3, 0], dtype=np.int16),
            target=GL_ELEMENT_ARRAY_BUFFER,
        )

    def __enter__(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.FBO)
        glDrawBuffers(1, [GL_COLOR_ATTACHMENT0])
        glClearColor(self.bgc, self.bgc, self.bgc, 0.01)
        #glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        #glDepthFunc(GL_LESS)
        #glDepthFunc(GL_LEQUAL)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        return self

    def __exit__(self, *exc):
        # Important to unbind for overpainting
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        #glDisable(GL_DEPTH_TEST)
        glClearColor(self.bgc, self.bgc, self.bgc, 0.01)
        glClear(GL_COLOR_BUFFER_BIT)
        return False

    def setColorProcessor(self, processor):
        self.color_processor = processor
        OCIODisplay = self.color_processor.getGpuShaderText(SHADER_DESCRIPTION)
        lut3d = self.color_processor.getGpuLut3D(SHADER_DESCRIPTION)
        self.buildLUT(lut3d)
        self.compileShader()

        # Shader Uniform Locations
        self.texture_location = glGetUniformLocation(self.shader, "framebufferTexture")
        self.lut_location = glGetUniformLocation(self.shader, "lut3DTexture")
        self.exposure_location = glGetUniformLocation(self.shader, "exposure")
        self.gamma_location = glGetUniformLocation(self.shader, "gamma")


    def compileShader(self, channels='color'):
        if channels == self.active_channel:
            self.active_channel = 'color'
            shader_channel = 'color'
        elif channels != 'color':
            self.active_channel = channels
            shader_channel = 'vec4(vec3(color.{c} + color.{c} + color.{c}) / 3.0, 1.0)'.format(c=channels)
        OCIODisplay = self.color_processor.getGpuShaderText(SHADER_DESCRIPTION)
        frag_shader_text = colorFramebuffer.fragment_shader.format(
            OCIODisplay.replace('texture3D', 'texture'), # "texture3D" functions are deprecated
            shader_channel
        )
        self.shader = GLShaders.compileProgram(
            GLShaders.compileShader(colorFramebuffer.vertex_shader, GL_VERTEX_SHADER),
            GLShaders.compileShader(frag_shader_text, GL_FRAGMENT_SHADER),
        )


    def buildLUT(self, lut3d):
        glBindTexture(GL_TEXTURE_3D, self.lut3d_target_texture)
        glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)

        glTexImage3D(
            GL_TEXTURE_3D, 0, GL_RGBA32F, 32, 32, 32, 0, GL_RGB, GL_FLOAT, lut3d
        )
        glTexSubImage3D(GL_TEXTURE_3D, 0, 0, 0, 0, 32, 32, 32, GL_RGB, GL_FLOAT, lut3d)

    def build(self, width, height):
        glBindFramebuffer(GL_FRAMEBUFFER, self.FBO)

        # Attach Color texture
        glBindTexture(GL_TEXTURE_2D, self.color_target_texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA32F,
            width,
            height,
            0,
            GL_RGBA,
            GL_FLOAT,
            None,
        )
        glFramebufferTexture2D(
            GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.color_target_texture, 0
        )

        # Attach depth texture
        glBindTexture(GL_TEXTURE_2D, self.depth_target_texture)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_DEPTH_COMPONENT24,
            width,
            height,
            0,
            GL_DEPTH_COMPONENT,
            GL_FLOAT,
            None,
        )
        glFramebufferTexture2D(
            GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.depth_target_texture, 0
        )

        # Unbind buffers and textures
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glBindTexture(GL_TEXTURE_2D, 0)


    def draw(self):
        glUniform1f(self.exposure_location, self.exposure)
        glUniform1f(self.gamma_location, self.gamma)

        glUniform1i(self.texture_location, 1)

        glBindTexture(GL_TEXTURE_2D, self.color_target_texture)
        glBindTexture(GL_TEXTURE_3D, self.lut3d_target_texture)


        with self.quad_ibo, self.quad_vbo:
            glVertexAttribPointer(0, 3, GL_FLOAT, False, 5 * 4, c_void_p(0))
            glEnableVertexAttribArray(0)

            glVertexAttribPointer(1, 2, GL_FLOAT, False, 5 * 4, c_void_p(3 * 4))
            glEnableVertexAttribArray(1)

            glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_SHORT, c_void_p(0))

        glBindTexture(GL_TEXTURE_2D, 0)
        glBindTexture(GL_TEXTURE_3D, 0)


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


class ImagePlane(object):

    def __init__(self, width, height, z=0, aspect=1, pixels=None, shader=None, order='rgb'):
        if shader:
            self.shader = shader
        else:
            self.shader = ImageShader.create()

        self.f = QOpenGLFunctions(QOpenGLContext.currentContext())

        self.shape = glm.vec3(width, height, z)
        self.aspect = aspect
        self.tile = 1
        if order == 'rgb':
            if pixels.shape[2] == 4:
                self.order = GL_RGBA
            else:    
                self.order = GL_RGB
        else:
            if pixels.shape[2] == 4:
                self.order = GL_BGRA
            else:    
                self.order = GL_BGR
        self.build(pixels)
        self.no_annotation = True

    def build(self, pixels):
        self.pixels = pixels
        x, y, z = self.shape
        self.elements = np.array(
            [
                (-x / 2) * self.aspect,  y / 2, z, 0.0, 0.0,
                ( x / 2) * self.aspect,  y / 2, z, 1.0 * self.tile, 0.0,
                ( x / 2) * self.aspect, -y / 2, z, 1.0 * self.tile, 1.0 * self.tile,
                (-x / 2) * self.aspect, -y / 2, z, 0.0, 1.0 * self.tile,
            ],
            dtype=np.float32,
        )
        self.ibo = vbo.VBO(
            np.array([0, 1, 2, 2, 3, 0], dtype=np.int16),
            target=GL_ELEMENT_ARRAY_BUFFER,
        )
        self.vbo = vbo.VBO(self.elements)

        self.texture_id = glGenTextures(1)

        self.pbo = Buffer(QOpenGLBuffer.PixelUnpackBuffer)

        with self.pbo as pbo:
            pbo.setUsagePattern(QOpenGLBuffer.StreamDraw)
            pbo.allocate(pixels.nbytes)

        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        # need to use QOpenGLFunctions for GL_HALF_FLOAT type missing in python ctypes.
        self.gl_format = NP_TEXTURE_FORMAT.get(str(pixels.dtype))
        if pixels.shape[2] == 4:    
            self.gl_internal_format = RGBA_CHANNELS.get(self.gl_format)
        elif pixels.shape[2] == 3:
            self.gl_internal_format = RGB_CHANNELS.get(self.gl_format)
        elif pixels.shape[2] == 1:
            self.gl_internal_format = R_CHANNEL.get(self.gl_format)
        # need to use QOpenGLFunctions for GL_HALF_FLOAT type missing in python ctypes.

        self.f.glTexImage2D(
            GL_TEXTURE_2D,
            0,
            self.gl_internal_format,
            int(self.shape.x),
            int(self.shape.y),
            0,
            self.order,
            self.gl_format,
            pixels,
        )
        glBindTexture(GL_TEXTURE_2D, 0)
    
        self.annotation_id = glGenTextures(1)
        #glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.annotation_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA8,
            int(self.shape.x * OVERSCAN),
            int(self.shape.y * OVERSCAN),
            0,
            GL_BGRA,
            GL_UNSIGNED_BYTE,
            None,
        )
        glBindTexture(GL_TEXTURE_2D, 0)
        self.resetAnnotation()

    def clear(self):
        glDeleteTextures(2, [self.texture_id, self.annotation_id])

    def resetAnnotation(self):
        w = int(self.shape.x  * OVERSCAN)
        h = int(self.shape.y * OVERSCAN)
        self.paint_canvas = QImage(w, h, QImage.Format_ARGB32)
        self.paint_canvas.fill(QColor(0, 0, 0, 0))
        pixels = np.ndarray(shape=(h, w, 3), buffer=self.paint_canvas.constBits(), dtype=np.uint8)
        self.updateAnnotation(pixels)
        self.no_annotation = True

    def setAnnotation(self, img):
        pixels = np.ndarray(
            shape = (img.height(), img.width(), 3),
            buffer = img.bits(),
            dtype = np.uint8
        )
        h, w, c = pixels.shape
        self.paint_canvas = img
        self.updateAnnotation(pixels)

    def updateTexture(self, pixels):
        #glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        #glFlush()
        null = VoidPtr(0)
        shape = self.shape
        with self.pbo as pbo:
            glBindTexture(GL_TEXTURE_2D, self.texture_id)
            self.f.glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, shape.x, shape.y, self.order, self.gl_format, null)
            #glBufferData(GL_PIXEL_UNPACK_BUFFER, pixels.nbytes, c_void_p(0), GL_STREAM_DRAW)
            pbo.write(0, pixels, pixels.nbytes)
            glBindTexture(GL_TEXTURE_2D, 0)

        self.pixels = pixels

    def updateAnnotation(self, pixels):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glBindTexture(GL_TEXTURE_2D, self.annotation_id)
        glTexSubImage2D(
            GL_TEXTURE_2D,
            0,
            0, # x offset
            0, # y offset
            self.shape.x,
            self.shape.y,
            GL_BGRA,
            GL_UNSIGNED_BYTE,
            pixels
        )
        glBindTexture(GL_TEXTURE_2D, 0)

    def updateAnnotationRegion(self, x, y, pixels, brush):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glBindTexture(GL_TEXTURE_2D, self.annotation_id)
        brsh_double = brush.doubleSize
        glTexSubImage2D(
            GL_TEXTURE_2D,
            0,
            int(x) - brush.radius, # x offset
            int(y) - brush.radius, # y offset
            brsh_double,
            brsh_double,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            pixels
        )
        glBindTexture(GL_TEXTURE_2D, 0)

    def draw(self, transpose_mvp):
        # Handle Texturing
        glUniform1i(self.shader.tex2D, 1)

        with self.ibo, self.vbo:
            glUniformMatrix4fv(self.shader.MVP, 1, GL_FALSE, glm.value_ptr(transpose_mvp))

            # Positions
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 3, GL_FLOAT, False, 5 * 4, c_void_p(0))

            # UV
            glEnableVertexAttribArray(1)
            glVertexAttribPointer(1, 2, GL_FLOAT, False, 5 * 4, c_void_p(3 * 4))

            glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_SHORT, c_void_p(0))

        glBindTexture(GL_TEXTURE_2D, 0)


class Viewport(InteractiveGLView):

    colorConfigChanged = Signal(list)
    zoomChanged = Signal(int)
    finishAnnotation = Signal(QImage)

    def __init__(self, *args, **kwargs):
        super(Viewport, self).__init__(*args, **kwargs)
        self.image_plane = None
        self.setColorConfig()
        self.paint_engine = PaintEngine()
        self.color_sampler = colorSampler()
        self.key_callback = None
        self.active_tool = AnnotationDock.Brush
        self.is_painting = False

    def renderShapes(self, scene=False):
        img = self.image_plane.paint_canvas
        w, h = img.width(), img.height()
        _w, _h = self.width(), self.height()
        self.resize(w, h)

        self.camera.left = -(w/2)
        self.camera.right = w/2
        self.camera.bottom = -(h/2)
        self.camera.top = h/2
        self.camera.updatePerspective()
        self.glmview = self.camera.getMVP()
        self.paintGL(scene=scene)

        glViewport(0, 0, w, h)
        glPixelStorei(GL_PACK_ALIGNMENT, 1)

        sampled = glReadPixels(0, 0, w, h, GL_RGBA, GL_UNSIGNED_BYTE)
        annotated_shapes = QImage(sampled, w, h, QImage.Format_ARGB32).rgbSwapped().mirrored()
        self.resize(_w, _h)
        self.drawViewport()
        return annotated_shapes

    def initializeGL(self):
        super(Viewport, self).initializeGL()
        self.framebuffer = colorFramebuffer(self.width(), self.height())
        self.setColorspace(0)
        self.brushCursor = Circle()
        self.brushCursor.build()
        self.paint_engine.shapes.newActiveShape()

        # Text rendering
        text_shader = TextShader.create()
        glyphs = glyphContainer(shader=text_shader)
        self.paint_engine.shapes.text_shader = text_shader
        self.paint_engine.shapes.glyphs = glyphs
    
        font_atlas, char_map = createFontAtlas(':/resources/LucidaTypewriterRegular.ttf')
        glyphContainer.atlas_texture = glyphs.createFontAtlasTexture(font_atlas)
        glyphContainer.char_map = char_map

    def paintGL(self, scene=True):
        super(Viewport, self).paintGL()
        image_plane = self.image_plane
        paint_engine = self.paint_engine
        if scene:
            # Draw our scene
            if image_plane:
                null = VoidPtr(0)
                glBindTexture(GL_TEXTURE_2D, image_plane.texture_id)
                with image_plane.pbo as pbo:
                    x = image_plane.shape.x
                    y = image_plane.shape.y
                    image_plane.f.glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, x, y, image_plane.order, image_plane.gl_format, null)
                    

                with self.framebuffer:
                    with image_plane.shader:
                        image_plane.draw(self.MVP)
            # Draw the actual screen-space framebuffer quad
            with self.framebuffer.shader:
                self.framebuffer.draw()

        # Annotation overlay
        if image_plane:
            if not image_plane.no_annotation or paint_engine.enabled:
                glBindTexture(GL_TEXTURE_2D, image_plane.annotation_id)
                with image_plane.shader:
                    annotation_transform = glm.translate(glm.mat4(1.0), glm.vec3(0, 0.0, -1.0))
                    scale = glm.scale(annotation_transform, glm.vec3(OVERSCAN))
                    annotation_mvp = self.camera.perspective * self.glmview * scale
                    image_plane.draw(annotation_mvp)

        # GL primitives and visual Gizmos
        mv = self.camera.perspective * self.glmview
        if paint_engine.enabled:
            # Draw the cursor cylinder 3 times 1 white then slightly smaller black
            # and finally cutout them by painting a transparent circle first. 
            radius = paint_engine.brush.radius
            w_scale = mv * glm.scale(self.cursorTransform, glm.vec3(radius))
            t_scale = mv * glm.scale(self.cursorTransform, glm.vec3(radius - (4 * self.zoom2d)))
            b_scale = mv * glm.scale(self.cursorTransform, glm.vec3(radius - (2 * self.zoom2d)))
            brush_rgba = paint_engine.brush.color.getRgbF()
            self.brushCursor.color = glm.vec4(*brush_rgba) # Transparent
            self.brushCursor.draw(t_scale)
            self.brushCursor.color = glm.vec4(0.0, 0.0, 0.0, 1.0) # Brush Color
            self.brushCursor.draw(b_scale)
            self.brushCursor.color = glm.vec4(1.0) # White
            self.brushCursor.draw(w_scale)
        paint_engine.shapes.active.draw(mv)
        for primitive in paint_engine.shapes.primitives:
            primitive.draw(mv)
        glBindTexture(GL_TEXTURE_2D, 0)

    def resizeGL(self, width, height):
        super(Viewport, self).resizeGL(width, height)
        self.framebuffer.build(width, height)

    def drawViewport(self, orbit=False, scale=False, pan=False):
        super(Viewport, self).drawViewport(orbit, scale, pan)
        if scale:
            percent = int(100 / self.zoom2d)
            self.zoomChanged.emit(percent)

    def zoom(self, delta):
        super(Viewport, self).zoom(delta)
        self.zoomChanged.emit(int(100 / self.zoom2d))

    def setColorConfig(self, file_path=None):
        if not file_path:
            backup_config = '{}/config.ocio'.format(os.path.dirname(__file__))
            file_path = os.getenv('ocio') or backup_config
        self.color_config = ocio.Config().CreateFromFile(str(file_path))
        try:
            self.color_views = self.color_config.getViews('default')
        except:
            self.color_views = self.color_config.getViews('ACES')
            
        self.colorConfigChanged.emit(self.color_views)

    def undo(self):
        if self.active_tool == AnnotationDock.Brush:
            pass
        elif self.active_tool == AnnotationDock.Shape:
            self.paint_engine.shapes.undo()
        elif self.active_tool == AnnotationDock.Text:
            self.paint_engine.shapes.undo()
            self.paint_engine.shapes.glyphs.reset()

    def redo(self):
        if self.active_tool == AnnotationDock.Brush:
            pass
        elif self.active_tool == AnnotationDock.Shape:
            self.paint_engine.shapes.redo()
        elif self.active_tool == AnnotationDock.Text:
            pass

    @Slot()
    def setShapeType(self, index):
        self.paint_engine.shapes.type = index

    @Slot()
    def setActiveTool(self, tool):
        sender = self.sender()
        if tool == AnnotationDock.Shape:
            self.paint_engine.shapes.create()
            self.paint_engine.shapes._type = sender.shapeTypeCombobox.currentIndex()
            self.paint_engine.shapes.newActiveShape()
            self.paint_engine.shapes.glyphs.reset()

        self.active_tool = tool

    @Slot()
    def setExposure(self, value):
        self.framebuffer.exposure = value
        self.update()

    @Slot()
    def setGamma(self, value):
        self.framebuffer.gamma = value
        self.update()

    @Slot()
    def setColorspace(self, value):
        displayColorSpace = self.color_config.getDisplayColorSpaceName(
            "default", self.color_views[value]
        )
        color_processor = self.color_config.getProcessor(
            ocio.Constants.ROLE_SCENE_LINEAR, displayColorSpace
        )
        if hasattr(self, 'framebuffer'):
            self.framebuffer.setColorProcessor(color_processor)
        self.update()

    @Slot()
    def setColorChannel(self, channel):
        self.framebuffer.compileShader(channel)
        self.update()

    def frameGeometry(self):
        if self.camera.ortho and self.image_plane:
            self.pan2d = glm.vec2(0, 0)
            self.origin_pos = glm.vec2(0, 0)
            tw = self.image_plane.shape.x / self.width()
            th = self.image_plane.shape.y / self.height()
            if th < tw:
                self.zoom2d = tw
            else:
                self.zoom2d = th
            self.zoomChanged.emit(int(100 / self.zoom2d))
        #else:
        #    if self.mesh_container:
        #        if self.mesh_container.name == 'latlong':
        #            self.glmCamera.frameMesh(
        #                self.mesh_container.min, self.mesh_container.max, position=glm.vec3(0,0,0)
        #            )
        #        else:
        #            self.glmCamera.frameMesh(
        #                self.mesh_container.min, self.mesh_container.max
        #            )
        self.drawViewport()

    def setZoom(self, value):
        self.zoom2d = 100 / value
        self.drawViewport()
        # Do not use fraction values for camera zoom level. 1:1 pixels
        self.camera.left = int(self.camera.left)
        self.camera.right = int(self.camera.right)
        self.camera.bottom = int(self.camera.bottom)
        self.camera.top = int(self.camera.top)
        self.camera.updatePerspective()

    def paintPath(self):
        path = QPainterPath()
        canvas_lastpos = self.screenToCanvas(self.m_lastpos)
        canvas_pos = self.screenToCanvas(self.m_pos)

        path.moveTo(canvas_lastpos)
        path.lineTo(canvas_pos)
        length = path.length()
        pos = 0
        step = self.paint_engine.brush.spacing
        while pos < length:
            percent = path.percentAtLength(pos)
            ppoint = path.pointAtPercent(percent)
            x = int(ppoint.x())
            y = int(ppoint.y())
        
            pos += step
            roi = self.paint_engine.drawOnCanvas(x, y, self.image_plane.paint_canvas)
        self.image_plane.updateAnnotation(roi)

    def paintSimpleStroke(self):
        canvas_lastpos = self.screenToCanvas(self.m_lastpos)
        canvas_pos = self.screenToCanvas(self.m_pos)

        val = glm.vec2(int(canvas_pos.x()), int(canvas_pos.y()))

        strokes = self.paint_engine.strokes
        strokes.append(val)
        series = deque()
        PaintEngine.iterativeSpline(strokes, series, self.paint_engine.brush.doubleSize)
        roi = None

        for point in series:
            roi = self.paint_engine.drawOnCanvas(int(point.x), int(point.y), self.image_plane.paint_canvas)

        if roi is not None:
            self.image_plane.updateAnnotation(roi)

    def createShape(self):
        b = glm.vec2(self.w_pos.x(), self.w_pos.y())
        a = self.w_firstpos
        color = self.paint_engine.brush.color.getRgbF()
        self.paint_engine.shapes.updateActiveShape(a, b, color)

    def paintStroke(self, position):
        pos = glm.vec2(position.x(), -(position.y()))

        last_pos = self.screenToCanvas(self.m_lastpos)
        canvas_pos = self.screenToCanvas(pos)
        val = glm.vec2(canvas_pos.x(), canvas_pos.y())
        strokes = self.paint_engine.strokes
        strokes.append(val)

        last = None
        for point in PaintEngine.iterativeSplineYielder(strokes):
            if not last:
                last = point
                continue

            distance = glm.distance(point, last)
            direction = glm.atan(point.x - last.x, point.y - last.y)
            step = self.paint_engine.brush.spacing
            
            for index in range(1, int(distance), step):
                x = last.x + (glm.sin(direction) * index)
                y = last.y + (glm.cos(direction) * index)
                self.paint_engine.drawOnCanvas(x, y, self.image_plane.paint_canvas, result=False)
                #self.image_plane.updateAnnotationRegion(x, y, roi, None)#self.paint_engine.brush)

            last = point
            # Always draw first point
            x = point.x
            y = point.y
            roi = self.paint_engine.drawOnCanvas(x, y, self.image_plane.paint_canvas)
        if last:
            self.image_plane.updateAnnotationRegion(x, y, roi, None)#self.paint_engine.brush)

    def screenToCanvas(self, position, overscan=OVERSCAN):
        mousex = position.x - (self.width() * 0.5)
        mousey = position.y + (self.height() * 0.5)

        w, h, z = (self.image_plane.shape * overscan)

        center = glm.vec2((w / 2), (h / 2))
        offsetx = ((
            mousex * self.lastzoom2d
        ) - self.pan2d.x) + center.x
        offsety = -1 * (((
            mousey * self.lastzoom2d
        ) - self.pan2d.y) - center.y)

        return QPointF(offsetx, offsety)

    def sampleColor(self):
        pos = self.screenToCanvas(self.m_pos, overscan=1.0)
        if not self.image_plane:
            return 
        try:
            pixel = self.image_plane.pixels[
                int(pos.y()),
                int(pos.x())
                ]
        except: return
        lut_pixel = self.framebuffer.color_processor.applyRGB(pixel)
        raw_pixel = pixel
        g_c_pos = self.mapToGlobal(self.c_pos)
        self.color_sampler.setRGB(lut_pixel, raw_pixel, g_c_pos, 'Look')

    def togglePaintContext(self, save=True):
        self.paint_engine.enabled = not self.paint_engine.enabled
        if self.paint_engine.enabled:
            if self.paint_engine.brush.radius >= 20:
                self.setCursor(Qt.CrossCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
            if self.image_plane:
                annotated_shapes = self.renderShapes()
                annotated_comp = self.compQImages(annotated_shapes, self.image_plane.paint_canvas)
                self.paint_engine.shapes.primitives.clear()
                self.paint_engine.strokes.clear()
                if save:
                    self.finishAnnotation.emit(annotated_comp)
                self.image_plane.resetAnnotation()

        return self.paint_engine.enabled

    def clipScene(self):
        scene_img = self.renderShapes(scene=True)
        scene_comp = self.compQImages(scene_img, self.image_plane.paint_canvas)
        QApplication.clipboard().setImage(
            scene_comp, QClipboard.Clipboard
        )

    @staticmethod
    def compQImages(a, b):
        qp = QPainter()
        qp.begin(a)
        qp.setCompositionMode(QPainter.CompositionMode_SourceOver)
        qp.drawImage(0, 0, b)
        return a

    def mousePressEvent(self, event):
        if self.active_tool == AnnotationDock.Text:
            if self.paint_engine.shapes.glyphs.indices_count != 0:
                self.paint_engine.shapes.create()
        super(Viewport, self).mousePressEvent(event)
        self.c_firstpos = event.pos()
        self.w_firstpos = glm.vec2(self.w_pos.x(), self.w_pos.y())

    def mouseDoubleClickEvent(self, event):
        mods = event.modifiers()
        if mods == Qt.ControlModifier:
            self.color_sampler.hide()

    def mouseReleaseEvent(self, event):
        super(Viewport, self).mouseReleaseEvent(event)
        if self.paint_engine.brush.radius >= 25 and self.paint_engine.enabled:
            self.setCursor(Qt.CrossCursor)
        if self.is_painting:
            if self.active_tool == AnnotationDock.Shape:
                self.paint_engine.shapes.create()
            self.paint_engine.strokes.clear()
            self.is_painting = False

    def keyPressEvent(self, event):
        mods = QApplication.keyboardModifiers()
        key = event.key()
        if self.active_tool == AnnotationDock.Text and mods != Qt.ControlModifier:
            self.updateText(event)
            return
        if key == Qt.Key_F:
            self.frameGeometry()
        elif key == Qt.Key_B:
            self.key_callback = self.scalePaintEngineBrush
        elif key == Qt.Key_E:
            self.paint_engine.brush.toggleEraser()
        elif key == Qt.Key_Z and mods == (Qt.ControlModifier | Qt.ShiftModifier):
            self.redo()
        elif key == Qt.Key_Z and mods == Qt.ControlModifier:
            self.undo()
        elif key == Qt.Key_C and mods == Qt.ControlModifier:
            self.clipScene()


        super(Viewport, self).keyPressEvent(event)

    def updateText(self, event):
        shaper = self.paint_engine.shapes
        keyt = event.text()
        if event.key() == Qt.Key_Backspace:
            shaper.text = shaper.text[:-1]
        elif keyt in string.printable:
            shaper.text += keyt
        else:
            return
        if shaper.text.startswith('\n'):
            shaper.text = shaper.text[1:] 
        shaper.glyphs.newText(shaper.text + '\n', shaper.text_pos, shaper.text_scale)
        self.update()

    def keyReleaseEvent(self, event):
        self.key_callback = None
        super(Viewport, self).keyPressEvent(event)

    def scalePaintEngineBrush(self):
        size = self.m_pos - self.m_lastpos
        if abs(size.x) <= abs(size.y):
            factor = size.y
        else:
            factor = size.x
        self.paint_engine.brush.scaleBrush(factor * self.zoom2d)
        self.c_pos = self.c_firstpos
        self.update()

    def mouseMoveEvent(self, event):
        super(Viewport, self).mouseMoveEvent(event)

        buttons = event.buttons()
        mods = event.modifiers()

        if buttons == Qt.LeftButton and mods == Qt.ControlModifier:
            self.sampleColor()
        elif buttons == Qt.LeftButton and self.paint_engine.enabled:
            self.setCursor(Qt.BlankCursor)

            if self.key_callback:
                self.key_callback()
                return
            else:
                self.is_painting = True
                if self.active_tool == AnnotationDock.Brush:
                    self.paintSimpleStroke()
                    #self.paintPath()
                elif self.active_tool == AnnotationDock.Shape:
                    self.createShape()
                elif self.active_tool == AnnotationDock.Text:
                    self.paint_engine.shapes._type = 4
                    self.paint_engine.shapes.newActiveShape()
                    self.createShape()
                return
        self.c_firstpos = self.c_pos
