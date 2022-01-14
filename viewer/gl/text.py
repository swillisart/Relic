import sys, string, calendar, os
from ctypes import c_void_p
import datetime as dt
from functools import partial

# Third-party
from OpenGL.GL import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtOpenGL import *
from OpenGL.arrays import vbo

import freetype
import numpy as np
import glm
from viewer.gl.shading import BaseProgram

def createFontAtlas(file_path):
    font_file = QFile(file_path)
    if font_file.open(QFile.ReadOnly):
        stream = font_file.readAll()
        # hack for getting qt resource bytes into freetype memory load.  
        stream.read = partial(bytes, stream)
        face = freetype.Face(stream)
    else:
        raise OSError('Unable to open font : {}'.format(file_path))

    face.set_pixel_sizes(0, 44)
    slot = face.glyph

    # Create indexes and calculate atlas dimensions
    offset = height = baseline = 0
    char_map = {}

    for c in string.printable:
        face.load_char(c)
        bitmap = slot.bitmap

        height = max(height, bitmap.rows + max(0, -(slot.bitmap_top - bitmap.rows)))
        baseline = max(baseline, max(0, -(slot.bitmap_top - bitmap.rows)))
        offset += (slot.advance.x >> 6)
        bearing = glm.vec2(face.glyph.bitmap_left, face.glyph.bitmap_top)

        char_map[c] = glCharacter(
            offset,
            bitmap.width,
            bearing,
        )

    width = offset
    img = np.zeros((height, width), dtype=np.ubyte)

    # Second pass for actual rendering
    x, y = 0, 0
    for c in string.printable:
        face.load_char(c)
        bitmap = slot.bitmap
        
        top = slot.bitmap_top
        left = slot.bitmap_left
        w, h = bitmap.width, bitmap.rows
        y = height - baseline - top
        img[y:y+h, x:x+w] += np.array(bitmap.buffer, dtype='ubyte').reshape(h,w)
        x += (slot.advance.x >> 6)
        # embed uv offset for 0, 1 range percentage
        uv_normalized = (char_map[c].offset - (char_map[c].width + char_map[c].bearing.x))

        char_map[c].u_left = (uv_normalized - char_map[c].bearing.x) / width
        char_map[c].u_right = (uv_normalized + char_map[c].width) / width

    font_file.close()
    return (img, char_map)

class TextShader(BaseProgram):

    vertex = """
        #version 400
        in layout(location = 0) vec3 Position;
        in layout(location = 1) vec2 UV;

        uniform mat4 MVP;
        out vertex {
            vec3 position;
            vec2 uv;
        } verts;
        void main()
        {
            gl_Position = MVP * vec4(Position, 1);
            verts.position = Position;
            verts.uv = UV;
        }
    """

    fragment = """
        #version 400
        in vertex {
            vec3 position;
            vec2 uv;
        } verts;

        out vec4 rgba;

        uniform sampler2D text;
        uniform vec4 color;

        void main()
        {
            //float alpha = (texture2D(text, verts.uv).a * color.a);
            rgba = vec4(color.rgb, texture2D(text, verts.uv).a);
        }
    """

    @classmethod
    def create(cls):
        obj = super(TextShader, cls).fromGlsl(
            TextShader.vertex, TextShader.fragment
        )
        obj.setUniforms('MVP', 'text', 'color')
        return obj

class glyphContainer(object):

    char_map = None
    atlas_texture = None

    def __init__(self, z=0, shader=None):
        self.shader = shader
        self.color = glm.vec4(1.0, 1.0, 1.0, 1.0)
        self.z = z
        self.reset()
        self.undo = []

    def createFontAtlasTexture(self, font_atlas):
        # GL atlas texture
        height, width = font_atlas.shape[:2]
        self.atlas_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.atlas_texture)

        glTexImage2D(GL_TEXTURE_2D, 0, GL_ALPHA, width, height, 0,
                        GL_ALPHA, GL_UNSIGNED_BYTE, font_atlas)
        glGenerateMipmap(GL_TEXTURE_2D)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glBindTexture(GL_TEXTURE_2D, 0)
        return self.atlas_texture
    
    def reset(self):
        self.indices = np.array([], dtype=np.int16)
        self.elements = np.array([], dtype=np.float32)
        self.indices_count = 0
        self.ids = np.array([0, 1, 2, 2, 3, 0], dtype=np.int16)

    def newText(self, text, coordinate, scale, char_map=None):
        self.reset()
        self.addText(text, coordinate, scale, char_map)
        self.rebuild()

    def addText(self, text, coordinate, scale, char_map=None):
        o = 0
        z = self.z
        if not char_map:
            char_map = self.char_map
        for i, c in enumerate(text):
            char = char_map[c]
            if c == ' ':
                right = char.offset + 16
                ul = ur = 10
            elif c == 'x':
                right = char.offset
                ul = char.u_left
                ur = char.u_right - 0.0005
            else:
                right = char.offset
                ul = char.u_left - 0.00075
                ur = char.u_right - 0.0005
            left = (char.offset - (char.width + char.bearing.x))

            w = (right - left)
            x = (w / 2) 
            y = (48 / 2)

            elements = np.array(
                [
                    (-x + o), y, z, ul, 0.0, # BL
                    (x + o), y, z, ur, 0.0, # BR
                    (x + o), -y, z, ur, 1.0, # TR
                    (-x + o), -y, z, ul, 1.0, # TL
                ],
                dtype=np.float32,
            )
            # X trasnform
            elements[0:-1:5] = (elements[0:-1:5] * scale) + coordinate.x
            # Y transform
            elements[1:-1:5] = (elements[1:-1:5] * scale) + coordinate.y
            
            self.addGlyphMesh(self.ids, elements)
            self.ids = self.ids + 4

            o += ((right - left) + 2)

    def addGlyphMesh(self, indices, elements):
        self.indices = np.append(self.indices, indices)
        self.elements = np.append(self.elements, elements)
        self.indices_count += len(indices)

    def rebuild(self):
        self.vbo = vbo.VBO(self.elements)
        self.ibo = vbo.VBO(self.indices, target=GL_ELEMENT_ARRAY_BUFFER)

    def draw(self, transpose_mvp, atlas_texture=None):
        with self.shader, self.ibo, self.vbo:
            glUniformMatrix4fv(self.shader.MVP, 1, GL_FALSE, glm.value_ptr(transpose_mvp))
            glUniform4fv(self.shader.color, 1, glm.value_ptr(self.color))
            glUniform1i(self.shader.text, 1)
            if atlas_texture:
                glBindTexture(GL_TEXTURE_2D, atlas_texture)
            else:
                glBindTexture(GL_TEXTURE_2D, self.atlas_texture)

            # Vertices
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 3, GL_FLOAT, False, 5 * 4, c_void_p(0))

            # UV's
            glEnableVertexAttribArray(1)
            glVertexAttribPointer(1, 2, GL_FLOAT, False, 5 * 4, c_void_p(3 * 4))
        
            glDrawElements(GL_TRIANGLES, self.indices_count, GL_UNSIGNED_SHORT, c_void_p(0))

    def moveAll(self, text, start, position):
        byte_size = (len(text) * 4 * 5)
        end = start + byte_size
        self.elements[start:end][0::5] += position.x
        self.elements[start:end][1::5] += position.y
        with self.vbo:
            self.vbo.implementation.glBufferSubData(
                self.vbo.target, 0, self.elements
            )

    def move(self, text, start, position):
        byte_size = (len(text) * 4 * 5)
        end = start + byte_size

        data = self.elements[start:end]
        aslice = self.elements[:start]
        data[0::5] += position.x
        data[1::5] += position.y
        offset = aslice.nbytes
        with self.vbo:
            self.vbo.implementation.glBufferSubData(
                self.vbo.target, offset, data.nbytes, data)


class FrameGlyphs(glyphContainer):

    def __init__(self, *args, **kwargs):
        super(FrameGlyphs, self).__init__(*args, **kwargs)
        self.color = glm.vec4(0.5, 0.9, 0.65, 1.0)
        self.reset()
        self.text = '        ' # empty spaces '00:00:00:00'

    def updateCharacter(self,
            char_map,
            elements,
            coordinate,
            py,
            ny,
            z,
            scale,
            index,
            char_str,
        ):
        char = char_map[char_str]
        if char_str == ' ':
            right = char.offset + 16
            ul = ur = 10
            z = -2
        else:
            right = char.offset
            ul = char.u_left - 0.00075
            ur = char.u_right - 0.0005
        left = (char.offset - (char.width + char.bearing.x))

        w = (right - left)
        x = (w / 2)
        o = index * 24
        px = ((x + o) * scale) + coordinate.x
        nx = ((-x + o) * scale) + coordinate.x
        new_data = [
            nx, py, z, ul, 0.0, # BL
            px, py, z, ur, 0.0, # BR
            px, ny, z, ur, 1.0, # TR
            nx, ny, z, ul, 1.0, # TL
        ]
        begin = index * 20
        end = begin + 20
        elements[begin:end] = new_data

    def updateText(self, text, coordinate, scale):
        z = self.z
        py = (24 * scale) + coordinate.y #y = (48 / 2)
        ny = (-24 * scale) + coordinate.y #y = (48 / 2)
        padded = ''.join([text, self.text[len(text):]])
        char_map = self.char_map
        elements = self.elements
        vbo = self.vbo
        addition = partial(self.updateCharacter,
            char_map,
            elements,
            coordinate,
            py,
            ny,
            z,
            scale
        )
        #[addition(i, char) for i, char in enumerate(padded)]
        list(map(addition, range(len(padded)), padded))

        with vbo:
            vbo.implementation.glBufferSubData(
                vbo.target, 0, elements)

class HandleGlyphs(glyphContainer):

    def __init__(self, *args, **kwargs):
        super(HandleGlyphs, self).__init__(*args, **kwargs)
        self.color = glm.vec4(0.875, 0.490, 0.455, 1) 
        self.z = -0.1

class tickGlyphs(glyphContainer):

    def __init__(self, *args, **kwargs):
        super(tickGlyphs, self).__init__(*args, **kwargs)
        self.color = glm.vec4(0.5, 0.5, 0.5, 1.0)

    def buildFromArray(self, tick_frames, tick_step, font_scale, y, char_map=None):
        step_tolerance = 50
        timecode = False
        if len(tick_frames) > 1:
            if tick_frames[-1] >= 10000:
                timecode = True

        #self.addText('0', glm.vec2(0, y), font_scale, char_map)
        switch = False
        for i, frame in enumerate(tick_frames):
            frame_name = str(frame)
            if tick_step >= step_tolerance and int(i % 2) == 0:
                continue
            if switch:
                switch = not switch
                if tick_step >= step_tolerance:
                    continue
            switch = not switch
            if timecode and tick_step >= 20:
                hours, remainder = divmod((frame / 24), 3600)
                minutes, seconds = divmod(remainder, 60)
                frame_name = '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))

            self.addText(frame_name, glm.vec2(frame + (font_scale*15), y), font_scale, char_map)
        self.rebuild()


class glCharacter(object):
    __slots__= [
        "offset",
        "width",
        "bearing",
        "u_left",
        "u_right"
    ]

    def __init__(self, offset, width, bearing, u_left=None, u_right=None):
        self.offset = offset
        self.width = width
        self.bearing = bearing
        self.u_left = u_left
        self.u_right = u_right
