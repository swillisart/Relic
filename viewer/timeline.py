import glob
import re
import timeit
from ctypes import c_void_p

# -- Third-party --
from OpenGL.GL import *
from OpenGL.arrays import vbo

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from qtshared2.utils import getPrimaryScreenPixelRatio

from sequencePath import sequencePath as Path

import numpy as np
import glm

# -- Module --

from viewer.viewport import ImagePlane
from viewer.gl.text import (
    glyphContainer, tickGlyphs, frameGlyphs, createFontAtlas, TextShader, HandleGlyphs
)
from viewer.gl.primitives import (
    TickGrid, TimeCursor, CacheProgress, AnnotationCursors, PrimitiveShader,
    BasePrimitive, LineRect, HandleCursors, Line)
from viewer.gl.nodes import baseNode
from viewer.gl.util import Camera, ticksFromView, useGL, CursorSnapper
from viewer.gl.widgets import InteractiveGLView
from viewer.gl.shading import BaseProgram
from viewer import io

# -- Globals --
TIMECODE = 0 
FRAMES = 1

# edit constants
MOVE_CLIP = 1
SIZE_CLIP = 2

class BaseClip(object):

    mode = FRAMES

    __slots__ = [
        'path',
        'first',
        'last',
        'head',
        'tail',
        'framerate',
        'timeline_in',
        'timeline_out',
        'annotations',
        'label',
        'geometry',
        'index',
        'sequence',
        'glyph_offset',
        # Frame only
        'width',
        'height',
        'channels',
        'aspect',
        'pixel_format',
    ]

    def __init__(self, file_path=None, timeline_in=1):
        self.first = 0
        self.last = 1
        self.head = 8
        self.tail = 8
        self.annotations = []
        self.path = file_path
        if file_path:
            self.loadFile(file_path)
            self.label = file_path.name
            self.getImageAnnotations()

        # Set and update the timeline offset (start frame)
        self.timeline_in = timeline_in + 1
        self.setTimelineOut()

    def loadFile(self, file_path):
        # Set the frames range, rate and shape
        self.first = 1
        self.last = 24
        self.setImageGeometry(str(file_path))

    def setBlankImage(self):
        self.geometry = ImagePlane(self.width, self.height, aspect=self.aspect,
            pixels=np.zeros(shape=(self.height, self.width, self.channels), dtype=self.pixel_format)
        )

    def setImageGeometry(self, frame):
        self.width, self.height, channels, self.aspect, self.pixel_format, self.framerate = \
            io.image.getImageResolution(frame)
        if channels > 4:
            self.channels = 4
        else:
            self.channels = channels

        self.setBlankImage()

    def setTimelineOut(self):
        self.timeline_out = self.timeline_in + (self.last - self.first)

    def mapToGlobalFrame(self, frame):
        timeline_frame = (frame - self.first) + self.timeline_in 
        return timeline_frame

    def mapToLocalFrame(self, frame):
        ins = self.timeline_in
        out = self.timeline_out
        if frame >= ins and frame <= out:
            return int(self.first + (frame - ins))
        else:
            return False

    def frameToTimecode(self, frame):
        return frame / self.framerate

    @property
    def duration(self):
        duration = (self.last - self.first)
        if BaseClip.mode == TIMECODE:
            return duration / self.framerate
        elif BaseClip.mode == FRAMES:
            return duration

    @classmethod
    def fromData(cls, **kwargs):
        obj = cls()
        for k, v in kwargs.items():
            setattr(obj, k, v)
        return obj

    def loadGeometricFile(self, file_path):
        # TODO: 
        self.framerate = 23.976
        #self.geometry = modelNode(path)

    @property
    def annotation_folder(self):
        return self.path.parents(0) / 'annotations'

    def annotated(self, frame):
        folder = self.annotation_folder
        r = folder / '{}.{}.png'.format(self.path.name, frame)
        return r

    def loadAnnotation(self, frame):
        annotated_path = self.annotated(frame)
        result = QImage(str(annotated_path))
        return result

    def getImageAnnotations(self):
        self.annotations.clear()
        folder = self.annotation_folder
        if folder.exists:
            for _file in folder:
                if _file.name == self.path.name:
                    self.annotations.append(int(_file.frame))


class MovClip(BaseClip):

    def __init__(self, file_path=None, timeline_in=1):
        # Omit file as it's loaded within a thread
        super(MovClip, self).__init__(timeline_in=timeline_in)
        self.path = file_path
        if file_path:
            self.label = file_path.name
            self.getImageAnnotations()

    def loadFile(self, duration, resolution, framerate):
        calc_duration = (float(duration) * float(framerate))
        w, h = resolution.split('x')
        width = int(w)
        height = int(h)
        aspect = 1
        self.first = 1
        self.last = int(round(calc_duration))
        self.framerate = float(framerate)
        self.geometry = ImagePlane(width, height, aspect=aspect, order='bgr',
            pixels=np.zeros(shape=(height, width, 3), dtype=np.uint8)
        )
        self.setTimelineOut()


class ImageClip(BaseClip):
    def __init__(self, *args, **kwargs):
        super(ImageClip, self).__init__(*args, **kwargs)

    def loadFile(self, file_path):
        # Set the frames range, rate and shape
        self.first = 1
        self.last = 24
        self.framerate = 23.976
        img_data, spec = io.image.read_file(str(file_path), 0)
        self.height, self.width, self.channels = img_data.shape
        self.aspect = spec.get_int_attribute('PixelAspectRatio') or 1
        self.geometry = ImagePlane(self.width, self.height, aspect=self.aspect, pixels=img_data)


class SeqClip(BaseClip):

    def __init__(self, *args, **kwargs):
        super(SeqClip, self).__init__(*args, **kwargs)
        if not kwargs.get('file_path'):
            self.framerate = 23.976
            self.width = 1920
            self.height = 1080
            self.channels = 3
            self.aspect = 1
            self.pixel_format = 'uint8'
            self.setBlankImage()

    def loadFile(self, file_path):
        frames = sorted(glob.glob(file_path.sequence_path))
        self.first = int(re.search(file_path.SEQUENCE_REGEX, frames[0]).group(1))
        self.last = self.first + len(frames)
        self.setImageGeometry(frames[0])

    def setTimelineOut(self):
        self.timeline_out = self.timeline_in + (self.last - self.first) - 1


#class GeoClip(BaseClip):
# TODO: Geometry loading

#------------------------------- OPENGL ---------------------------------

class ScrubArea(Line):
    def __init__(self, *args, **kwargs):
        super(ScrubArea, self).__init__(*args, **kwargs)
        self.vertices = np.array(
            [[0, 0, -1.5], [0, 0, -1.5]], dtype=np.float32
        )
        self.buildFromVertices(self.vertices)
        self.color = glm.vec4(0.108, 0.108, 0.108, 1)

    def resize(self, a, b, bottom):
        self.vertices[0, :2] = a
        self.vertices[1, :2] = b
        self.vertices[:, 1] = bottom
        self.updateVBO()


class ClipNodes(LineRect):

    def __init__(self, *args, **kwargs):
        super(ClipNodes, self).__init__(*args, **kwargs)
        self.color = glm.vec4(0.4, 0.35, 0.9, 0.8)
        self.count = 0

    def rect(self, index, scale):
        address = (index + 1) * 4
        v_reverse = self.vertices[::-1]
        right, top = v_reverse[address, :2]
        left, bot = v_reverse[address+2, :2]
        return QRectF(QPointF(left, top), QPointF(right, bot*scale))

    def buildFromVertices(self, vertices): 
        self.vbo = vbo.VBO(vertices)
        self.vertex_count = len(vertices) * 3 * 2
        indices = np.array([range(0, self.vertex_count)], dtype=np.uint16)
        n = 4
        indices_i = np.insert(indices, range(n, self.vertex_count, n), 0xFFFF) 
        self.ibo = vbo.VBO(indices_i, target=GL_ELEMENT_ARRAY_BUFFER)

    def append(self, first, last, y=0):
        vertices = np.array([
            [first, y, -1.0], [first, y-2, -1.0],
            [last, y-2, -1.0], [last, y, -1.0],
            ], dtype=np.float32
        )

        self.vertices = np.append(vertices, self.vertices, axis=0)
        self.buildFromVertices(self.vertices)
        self.count += 1

    def updateDuration(self, clip, duration):
        start = (clip.index + 1) * 4
        end = start + 4
        self.vertices[::-1][start:end][0, 0] += duration
        self.vertices[::-1][start:end][1, 0] += duration
        #self.vertices[::-1][start:end][-1, :1] += duration

        with self.vbo:
            self.vbo.implementation.glBufferSubData(
                self.vbo.target, 0, self.vertices
            )

    def move(self, clip, movement):
        start = (clip.index + 1) * 4
        end = start + 4

        self.vertices[::-1][start:end][:,0] += movement.x
        self.vertices[::-1][start:end][:,1] += movement.y

        with self.vbo:
            self.vbo.implementation.glBufferSubData(
                self.vbo.target, 0, self.vertices
            )
        #with self.vbo: # TODO: optimize with byte offsets to lighten upload payload
        #    self.vbo.implementation.glBufferSubData(
        #        self.vbo.target, self.vertices.nbytes, len(vertices)*4, vertices)

    def draw(self, transpose_mvp, mode, size=4.0, color=None):
        self.color = color or self.color
        glLineWidth(size)
        glEnable(GL_PRIMITIVE_RESTART)
        glPrimitiveRestartIndex(0xFFFF)

        with self.shader, self.ibo, self.vbo:
            glUniformMatrix4fv(self.shader.MVP, 1, GL_FALSE, glm.value_ptr(transpose_mvp))
            glUniform4fv(self.shader.color, 1, glm.value_ptr(self.color))
            glEnableVertexAttribArray(0)
            element_count = int(self.vertex_count)
            glVertexAttribPointer(0, 3, GL_FLOAT, False, 0, c_void_p(0))
            glDrawElements(mode, element_count, GL_UNSIGNED_SHORT, c_void_p(0))
        glDisable(GL_PRIMITIVE_RESTART)
        glLineWidth(1.0)


class Graph(object):
    def __init__(self, shader):
        self.nodes = ClipNodes(shader)
        self.hover = ClipNodes(shader)
        self.clips = [[]] # Each list is a sequence
        self.sequence_num = 0
        self.selection = None

    def appendClip(self, clip, sequence):
        clip.index = self.nodes.count #len(self.GRAPH.clips[sequence])
        self.nodes.append(clip.timeline_in, clip.timeline_out, sequence)
        self.clips[sequence].append(clip)
        clip.sequence = sequence #slice(sequence, len(self.clips[sequence]))

    def iterateSequence(self, sequence=None, clip=0):
        for clip in self.clips[sequence][clip:]:
            yield sequence, clip

    def iterateSequences(self, clip=0):
        for sequence in range(self.sequence_num + 1):
            for clip in self.clips[sequence][clip:]:
                yield sequence, clip


class timelineGLView(InteractiveGLView):
    annotatedLoad = Signal(int, BaseClip)

    frameJump = Signal(int)

    mouseInteracted = Signal(bool)

    def __init__(self, *args, **kwargs):
        super(timelineGLView, self).__init__(*args, **kwargs)
        self.current_frame = 0
        self.font_scale = 1
        self.tick_frames = [0]
        self.tick_step = 1
        self.current_clip = None
        self.snap_cursor = CursorSnapper()
        self.scrubbing = None
        self.selected_clips = []
        self.edit_mode = None

    @Slot()
    def _toAnnotatedFrame(self, direction):
        self.makeCurrent()
        filtered = []
        frame = self.current_frame + 0.5 # need to bias for direction opertors
        clip = self.current_clip
        local_frame = clip.mapToLocalFrame(frame)

        for frame_number in clip.annotations:
            if direction(frame_number, local_frame):
                filtered.append(frame_number)
    
        if filtered:
            nearest = min(filtered, key=lambda x: abs(x - local_frame))

            timeline_frame = clip.mapToGlobalFrame(nearest)

            self.frameJump.emit(timeline_frame)
            self.annotatedLoad.emit(nearest, clip)

    def reset(self, clip):
        self.current_clip = clip
        self.graph = Graph(shader=self.primitive_shader)
        #self.controller.jumpFirst()
        self.current_frame = 0
        self.updateNodeGlyphs()

    def getClipOnFrame(self, frame):
        for sequence, clip in self.graph.iterateSequences():
            local_frame = clip.mapToLocalFrame(frame)
            if local_frame:
                return clip, local_frame

        return False, False

    @useGL
    def updatedFrame(self, frame):
        self.current_frame = frame
        if not self.graph.nodes.count:
            return None, None

        try:
            local_frame = self.current_clip.mapToLocalFrame(frame)
        except: # no clip currently
            local_frame = False
        if local_frame:
            return self.current_clip, local_frame
        else:
            clip, local_frame = self.getClipOnFrame(frame)
            if clip:
                self.current_clip = clip

            return clip, local_frame

    def initializeGL(self):
        super(timelineGLView, self).initializeGL()
        self.primitive_shader = PrimitiveShader.create()
        self.text_shader = TextShader.create()
        self.selection_rect = ClipNodes(shader=self.primitive_shader)
        self.graph = Graph(shader=self.primitive_shader)
        self.grid = TickGrid(shader=self.primitive_shader)
        self.time_cursor = TimeCursor(shader=self.primitive_shader)
        self.cache_cursor = CacheProgress(shader=self.primitive_shader)
        self.scrub_area = ScrubArea(shader=self.primitive_shader)
        self.annotation_cursors = AnnotationCursors(shader=self.primitive_shader)
        self.annotation_cursors.build()
        self.handle_cursors = HandleCursors(shader=self.primitive_shader)
        self.handle_cursors.build()

        self.createGlyphs()
        glLineWidth(2.0)
        self.drawViewport(orbit=True)


    def paintGL(self):
        super(timelineGLView, self).paintGL()
        frame = self.current_frame
        frame_translation = glm.translate(glm.mat4(1.0), glm.vec3(frame, 0, 0))
        ct = glm.translate(glm.mat4(1.0), glm.vec3(0.0, 0.0, 0.0))
        clip_scale = glm.scale(ct, glm.vec3(1, self.zoom2d*7, 1))

        time_mvp = self.camera.perspective * self.glmview * frame_translation
        clip_mvp = self.camera.perspective * self.glmview * clip_scale

        self.grid.draw(self.MVP)
        if self.graph.selection:
            self.graph.selection.draw(clip_mvp, GL_LINE_LOOP, size=2,
                color=glm.vec4(0.41, 0.66, 0.8, 1))
        self.graph.nodes.draw(clip_mvp, GL_LINE_LOOP, size=3.0,
            color=glm.vec4(0.23, 0.26, 0.34, 1))
        self.graph.nodes.draw(clip_mvp, GL_QUADS,
            color=glm.vec4(0.299, 0.33, 0.442, 1))
        self.graph.hover.draw(self.MVP, GL_LINE_LOOP, size=1.0,
            color=glm.vec4(0.4, 0.48, 0.6, 1))

        self.frame_glyphs.draw(self.MVP)
        self.annotation_cursors.draw(self.MVP)
        self.handle_cursors.draw(self.MVP)
        self.scrub_area.draw(self.MVP, size=30)
        self.tick_glyphs.draw(self.MVP)
        self.node_glyphs.draw(self.MVP)
        self.handle_glyphs.draw(self.MVP)
        self.cache_cursor.draw(self.MVP)
        self.selection_rect.draw(self.MVP, GL_LINE_LOOP, size=1, color=glm.vec4(0.8, 0.75, 0.75, 1))
        self.selection_rect.draw(self.MVP, GL_QUADS, size=1, color=glm.vec4(0.8, 0.75, 0.75, 0.15))
        self.time_cursor.draw(time_mvp)


    def drawViewport(self, orbit=False, scale=False, pan2d=False):
        dpi_scale = getPrimaryScreenPixelRatio()
        self.font_scale = self.zoom2d * 0.266

        w = int(self.width())
        h = int(self.height())
        x = y = 0
        glViewport(x, y, int(w * dpi_scale), int(h * dpi_scale))
        center = glm.vec2((w / 2), (h / 2)) * self.zoom2d
        #TODO: reimplement this in the camera class instead of the view.
        if self.camera.ortho:  # Place ortho camera
            if pan2d:
                self.pan2d.x = (
                    (self.m_pos.x - self.m_lastpos.x) * self.lastzoom2d
                ) + self.pan2d.x
                self.pan2d.y = (
                    (self.m_pos.y - self.m_lastpos.y) * self.lastzoom2d
                ) + self.pan2d.y
            elif scale:
                self.zoom2d = self.zoom2d + (
                    (-(self.m_pos.x - self.m_lastpos.x) * self.zoom2d) * 0.002
                )
                if self.zoom2d < 0.002:
                    self.zoom2d = 0.002

                center = glm.vec2((w / 2), (h / 2)) * self.zoom2d

                origin = self.origin_pos
                offsetx = (((origin.x) - (w / 2)) * self.lastzoom2d) - self.pan2d.x
                offsety = (((origin.y) - (h / 2)) * self.lastzoom2d) - self.pan2d.y

                worldoffset_x = (origin.x * self.zoom2d) - center.x
                worldoffset_y = (origin.y * self.zoom2d) - center.y
                self.pan2d.x = worldoffset_x - offsetx
                # Disabled zooming on Y axis
                #self.pan2d.y = worldoffset_y - offsety

            if -self.pan2d.x <= center.x:
                self.pan2d.x = -center.x + (self.font_scale * 20)
            self.camera.left = -(center.x + self.pan2d.x)
            self.camera.right = center.x - self.pan2d.x
            self.camera.bottom = -(center.y + self.pan2d.y)
            self.camera.top = center.y - self.pan2d.y
            self.camera.updatePerspective()

        # Update time Cursor size
        self.time_cursor.resize(self.camera.top, self.camera.bottom)
        self.scrub_area.resize(self.camera.left, self.camera.right, self.camera.top-(28*self.font_scale))
        self.cache_cursor.move(self.camera.bottom)

        self.updateTicks()
        self.updateFrameGlyphs()
        #self.updateNodeGlyphs()
        self.glmview = self.camera.getMVP()
        self.update()

    def updateCacheSize(self, left, right):
        """Update Cache display size
        """
        #self.makeCurrent()
        self.cache_cursor.resize(left, right)
        #self.drawViewport()

    def updateTicks(self):
        """Update Ticks spacing and labels
        """
        frames_array, step = ticksFromView(self.camera)
        top = self.camera.top - (self.font_scale * 25) 
        self.tick_glyphs = tickGlyphs(z=-0.1, shader=self.text_shader)
        self.tick_glyphs.buildFromArray(
            frames_array, step, self.font_scale, top
        )
        grid_top = self.camera.top - (self.font_scale * 55) 
        grid_bot = self.camera.bottom
        self.grid.gridFromArray(frames_array, grid_top, grid_bot)


    def updateFrameGlyphs(self):
        """Update frame glyph position
        """
        self.frame_glyphs = frameGlyphs(shader=self.text_shader)
        x = self.current_frame + (self.font_scale * 25)
        bot = self.camera.bottom + (self.font_scale * 36)
        self.frame_glyphs.addText(str(self.current_frame), glm.vec2(x, bot), self.font_scale * 1.125)
        self.frame_glyphs.rebuild()

    def updateNodeGlyphs(self):
        # Update Node names & sizes
        self.node_glyphs = glyphContainer(shader=self.text_shader)
        self.annotation_cursors = AnnotationCursors(shader=self.primitive_shader)
        self.handle_cursors = HandleCursors(shader=self.primitive_shader)
        self.handle_glyphs = HandleGlyphs(shader=self.text_shader)

        switch = True
        fontscaled = (self.font_scale * 25)
        for sequence, clip in self.graph.iterateSequences():
            # Build clip glyph text
            if self.tick_step >= 50 and switch:
                switch = not switch
                continue
            
            local_center = (clip.duration / 2)
            clip_center = clip.timeline_in + local_center
            text_width = ((len(clip.label) / 2) * fontscaled)
            # Don't add if text is larger than clip bounds.
            if int(text_width) < int(local_center):
                x = clip_center - text_width
                y = (sequence * 25) - fontscaled
                # Label
                position = glm.vec2(x, y)
                clip.glyph_offset = len(self.node_glyphs.elements)
                self.node_glyphs.addText(clip.label, position, self.font_scale)

                ins_text = ' {} |'.format(clip.first)
                out_text = '| {}'.format(clip.last - 1)

                # In / Out frames
                in_pos = glm.vec2(clip.timeline_in, y)
                self.node_glyphs.addText(ins_text, in_pos, self.font_scale)

                text_width = len(out_text) * fontscaled
                out_pos = glm.vec2(clip.timeline_out - text_width, y)
                self.node_glyphs.addText(out_text, out_pos, self.font_scale)
            
                # Handles
                head_text = ' ' + str(clip.head)
                tail_text = str(clip.tail) + ' '

                h_pos = clip.timeline_in + (len(ins_text)) * fontscaled
                t_pos = clip.timeline_out - (len(out_text + tail_text) * fontscaled)
                self.handle_glyphs.addText(head_text, glm.vec2(h_pos, y), self.font_scale)
                self.handle_glyphs.addText(tail_text, glm.vec2(t_pos, y), self.font_scale)

                # Handle bars
                top = (sequence * 25) - (fontscaled * 2.5)
                self.handle_cursors.append(clip.timeline_in, clip.timeline_in + clip.head, top)
                self.handle_cursors.append(clip.timeline_out - clip.tail, clip.timeline_out, top)

            # Annotations
            for local_frame in clip.annotations:
                timeline_frame = clip.mapToGlobalFrame(local_frame)
                self.annotation_cursors.append(timeline_frame, (self.font_scale * 50))


        self.handle_cursors.build()
        self.annotation_cursors.build()
        self.node_glyphs.rebuild()
        self.handle_glyphs.rebuild()
        self.update()

    def createGlyphs(self):
        # Create and Assigns Class variables
        font_atlas, char_map = createFontAtlas(':/resources/LucidaTypewriterRegular.ttf')

        self.tick_glyphs = tickGlyphs(z=-0.1, shader=self.text_shader)
        self.node_glyphs = glyphContainer(shader=self.text_shader)
        self.handle_glyphs = HandleGlyphs(shader=self.text_shader)

        self.frame_glyphs = frameGlyphs(shader=self.text_shader)

        glyphContainer.atlas_texture = self.tick_glyphs.createFontAtlasTexture(font_atlas)
        glyphContainer.char_map = char_map

        self.tick_glyphs.addText(str(0), glm.vec2(0, 12), 0.050)
        self.tick_glyphs.rebuild()
        self.node_glyphs.rebuild()
        self.frame_glyphs.rebuild()
        self.handle_glyphs.rebuild()


    @useGL
    def mousePressEvent(self, event):
        super(timelineGLView, self).mousePressEvent(event)
        buttons = event.buttons()
        mods = event.modifiers()
        self.w_firstpos = glm.vec2(self.w_pos.x(), self.w_pos.y())

        if buttons == Qt.LeftButton:
            self.scrubbing = self.withinScrubArea()
            if self.scrubbing:
                self.jumpToCursor()
                return

            clip = self.cursorOverNode()
            append = mods == Qt.ShiftModifier
            detach = mods == Qt.ControlModifier
            if clip:
                self.selectNode(clip, append, detach)
                self.edit_mode = MOVE_CLIP
            else:
                self.selectNodes()
    @useGL
    def mouseMoveEvent(self, event):
        super(timelineGLView, self).mouseMoveEvent(event)
        buttons = event.buttons()
        
        if not self.cursorOverNode():
            self.graph.hover.resize(-2, -1, 0, 0)

        if self.scrubbing or self.withinScrubArea():
            self.setCursor(QCursor(Qt.SizeHorCursor))
        else:
            self.setCursor(QCursor(Qt.ArrowCursor))
            

        if self.pressing and buttons == Qt.LeftButton:
            if self.edit_mode:
                movement = self.w_pos - self.screenToWorld(self.m_lastpos)
                y = movement.y() / (self.font_scale * 25) or 0
                snap_movement = glm.vec2(movement.x(), y)
                test = glm.vec2(movement.x(), movement.y())
                # TODO: lock this in.
                #for clip in self.selected_clips:
                #    self.graph.nodes.move(clip, snap_movement)
                #    self.node_glyphs.move(clip.label, clip.glyph_offset, test)
            elif self.scrubbing:
                self.jumpToCursor()
            else:
                self.selectNodes()

    def withinScrubArea(self):
        top = self.camera.top
        bot = self.camera.top - (self.font_scale * 25 * 2)
        y = self.w_pos.y()
        if y <= top and y >= bot:
            return True

    def jumpToCursor(self):
        cursor_frame = int(self.w_pos.x() + 0.5)
        self.frameJump.emit(cursor_frame)

    def selectNode(self, clip, append, detach):
        if detach:
            for index, sel_clip in enumerate(self.selected_clips):
                if sel_clip is clip:
                    self.selected_clips.pop(index)
                    break
            
            self.graph.selection = ClipNodes(self.primitive_shader)
            for clip in self.selected_clips:
                self.graph.selection.append(clip.timeline_in, clip.timeline_out, clip.sequence)
            return

        if not append or not self.graph.selection:
            self.graph.selection = ClipNodes(self.primitive_shader)
            self.selected_clips = []

        self.selected_clips.append(clip)
        self.graph.selection.append(clip.timeline_in, clip.timeline_out, clip.sequence)

    def selectNodes(self):
        a = self.w_firstpos
        b = glm.vec2(self.w_pos.x(), self.w_pos.y())
        sel_rect = QRectF(QPointF(a.x, a.y), QPointF(b.x, b.y))
        selection = ClipNodes(self.primitive_shader)
        local_scale = (self.font_scale * 25)
        self.selected_clips = []
        for seq_index, clip in self.graph.iterateSequences():
            clip_rect = self.graph.nodes.rect(clip.index, local_scale)
            if clip_rect.intersects(sel_rect):
                selection.append(clip.timeline_in, clip.timeline_out, seq_index)
                self.selected_clips.append(clip)

        if self.selected_clips:
            self.graph.selection = selection
        else:
            self.graph.selection = None

        self.selection_rect.resize(
            sel_rect.left(), sel_rect.right(), sel_rect.bottom(), sel_rect.top())

    def cursorOverNode(self):
        local_scale = (self.font_scale * 25)
        for seq_index, clip in self.graph.iterateSequences():
            clip_rect = self.graph.nodes.rect(clip.index, local_scale)
            if clip_rect.contains(self.w_pos):
                top = seq_index * local_scale
                bot = seq_index - (local_scale*2)
                l = clip.timeline_in
                r = clip.timeline_out
                self.graph.hover.resize(l, r, top, bot)
                return clip
        return False

    @useGL
    def mouseReleaseEvent(self, event):
        super(timelineGLView, self).mouseReleaseEvent(event)
        self.selection_rect.resize(-1,-1.1,0.1,0)
        self.updateNodeGlyphs()
        self.mouseInteracted.emit(True)
        self.scrubbing = False
        self.edit_mode = None

    @useGL
    def wheelEvent(self, event):
        super(timelineGLView, self).wheelEvent(event)
        self.updateNodeGlyphs()
        self.cursorOverNode()

    @useGL
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F:
            self.frameGeometry()

    @useGL
    def frameGeometry(self):
        clip = self.current_clip
        if self.selected_clips:
            first = self.selected_clips[0].timeline_in
            last = self.selected_clips[0].timeline_out
            for clip in self.selected_clips:
                if clip.timeline_in < first:
                    first = clip.timeline_in
                if clip.timeline_out > last:
                    last = clip.timeline_out
            clip_center = first + ( (last - first) / 2)
            clip_duration = (last - first)
        elif not clip:
            return
        else:
            clip_center = clip.timeline_in + (clip.duration / 2)
            clip_duration = clip.duration

        self.zoom2d = (clip_duration + 20) / self.width()
        self.pan2d = glm.vec2(-clip_center, 0)
        self.origin_pos = self.pan2d
        self.drawViewport()
        self.updateNodeGlyphs()
        self.updateTicks()
        self.updateFrameGlyphs()
        self.cursorOverNode()
