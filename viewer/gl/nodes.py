from ctypes import c_void_p
from contextlib import contextmanager

# Third-party
from OpenGL.GL import *
from OpenGL.GL import shaders as GLShaders
from OpenGL.arrays import vbo

import numpy as np
import glm
from viewer.gl.primitives import BasePrimitive

class baseNode(object):
    vertex_shader = """
        #version 330 core
        in layout(location = 0) vec3 vertexPosition;
        in layout(location = 1) vec2 vertexUV;

        uniform mat4 MVP;
        uniform float scale;

        out vec2 fVertexUV;
        out vec3 fVertexPosition;
        void main()
        {
            gl_Position = MVP * vec4((vertexPosition + vec3(0, 0, -scale)) + (vertexPosition*vec3(scale))-vertexPosition, 1);
            fVertexUV = vertexUV;
            fVertexPosition = vertexPosition;
        }
    """

    fragment_shader = """
        #version 330 core
        in vec2 fVertexUV;

        uniform vec3 selected;
        uniform sampler2D tex2D;

        out vec4 rgba;

        void main()
        {
            vec4 img = texture2D(tex2D, fVertexUV);
            rgba = vec4(selected, (img.a * -0.2)) + img;
        }
    """
    def __init__(self, image=None):
        self.shader = GLShaders.compileProgram(
            GLShaders.compileShader(self.vertex_shader, GL_VERTEX_SHADER),
            GLShaders.compileShader(self.fragment_shader, GL_FRAGMENT_SHADER),
        )
        self.MVP_location = glGetUniformLocation(self.shader, "MVP")
        self.TEX_location = glGetUniformLocation(self.shader, "tex2D")
        self.selected_location = glGetUniformLocation(self.shader, "selected")
        self.scale_location = glGetUniformLocation(self.shader, "scale")

        self.shape = glm.vec3(1, 1, 0)
        self.selected = glm.vec3(0.0, 0.0, 0.0)
        self.scale = 1
        self.setTexture(image)
        self.setGeometry(self.shape)
        self.MVP_world = glm.mat4(0.0)

    def __enter__(self):
        glUseProgram(self.shader)
        glUniformMatrix4fv(self.MVP_location, 1, GL_FALSE, glm.value_ptr(self.MVP_world))
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glUniform1i(self.TEX_location, 1)
        glUniform1f(self.scale_location, 1.0)
        glUniform3fv(self.selected_location, 1, [0.04, 0.04, 0.04])

        return self

    def __exit__(self, *exc):
        glBindTexture(GL_TEXTURE_2D, 0)
        glUseProgram(0)

        return False

    def select(self, selection=True):
        if selection:
            self.selected = glm.vec3(0.0, 0.6, 0.0)
            self.scale = 1.03
        else:
            self.selected = glm.vec3(0.0, 0.0, 0.0)
            self.scale = 1

    def setTexture(self, img_data):
        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA8,
            img_data.shape[0],
            img_data.shape[1],
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            img_data,
        )
        glGenerateMipmap(GL_TEXTURE_2D)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glBindTexture(GL_TEXTURE_2D, 0)

    def setGeometry(self, shape):
        x, y, z = shape
        self.elements = np.array(
            [
                -x, y, z, 0.0, 0.0,
                x, y, z, 1.0, 0.0,
                x, -y, z, 1.0, -1.0,
                -x, -y, z, 0.0, -1.0,
            ],
            dtype=np.float32,
        )
        self.indices = vbo.VBO(
            np.array([0, 1, 2, 2, 3, 0], dtype=np.int16),
            target=GL_ELEMENT_ARRAY_BUFFER,
        )
        self.vertices = vbo.VBO(self.elements)
