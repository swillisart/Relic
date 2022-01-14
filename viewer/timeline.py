import glob
import re
from ctypes import c_void_p
from collections import defaultdict
from functools import partial
# -- Third-party --
from OpenGL.GL import *
from OpenGL.arrays import vbo

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from sequencePath import sequencePath as Path

import numpy as np
import glm

# -- Module --
import sys
from viewer.viewport import ImagePlane
from viewer.gl.text import (
    glyphContainer, tickGlyphs, FrameGlyphs, createFontAtlas, TextShader, HandleGlyphs
)
from viewer.gl.primitives import (
    TickGrid, TimeCursor, CacheProgress, AnnotationCursors, PrimitiveShader,
    BasePrimitive, LineRect, HandleCursors, Line)
from viewer.gl.util import Camera, ticksFromView, CursorSnapper
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
        self.last = 24
        self.head = 0
        self.tail = 0
        self.annotations = []
        self.path = file_path
        self.glyph_offset = 0
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

    def clear(self):
        self.label = ''
        self.path = ''
        self.timeline_in = 0
        self.timeline_in = -1
        self.timeline_out = -2

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
        self.last = (self.first - 1) + len(frames)
        self.setImageGeometry(frames[0])


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
        address = index * 4
        v_reverse = self.vertices[::-1]
        right, top = v_reverse[address, :2]
        left, bot = v_reverse[address+2, :2]
        return QRectF(QPointF(left, top*scale), QPointF(right, bot*scale))

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
        if not self.vertex_count:
            self.vertices = vertices
        else:
            self.vertices = np.append(vertices, self.vertices, axis=0)
        self.count += 1
        self.buildFromVertices(self.vertices)

    def moveAll(self, clip, movement):
        vertices = self.vertices
        reverse = vertices[::-1]
        reverse[:,0] += movement.x
        reverse[:,1] += movement.y

        with self.vbo:
            self.vbo.implementation.glBufferSubData(
                self.vbo.target, 0, vertices)

    def updateDuration(self, clip, duration):
        start = clip.index * 4
        end = start + 4
        reverse = self.vertices[::-1]

        reverse[start:end][0, 0] += duration
        reverse[start:end][1, 0] += duration
        offset = reverse[end:].nbytes
        data = reverse[start:end]

        with self.vbo:
            self.vbo.implementation.glBufferSubData(
                self.vbo.target, offset, data.nbytes, data)

    def move(self, clip, movement):
        start = clip.index * 4
        end = start + 4
        vertices = self.vertices

        reverse = vertices[::-1]
        reverse[start:end][:,0] += movement.x
        reverse[start:end][:,1] += movement.y
    
        aslice = reverse[end:]
        data = reverse[start:end]
        offset = aslice.nbytes
        # Optimize the exact 'offset' and 'size' in bytes for partial GPU upload.
        with self.vbo:
            self.vbo.implementation.glBufferSubData(
                self.vbo.target, offset, data.nbytes, data)

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


class SelectionOverlay(ClipNodes):

    def __init__(self, *args, **kwargs):
        super(SelectionOverlay, self).__init__(*args, **kwargs)
        self.color = glm.vec4(0.4, 0.35, 0.9, 0.8)
        self.vertices = np.ndarray([], dtype=np.float32)
        self.vertex_count = None


class Graph(object):
    def __init__(self, shader):
        self.nodes = ClipNodes(shader)
        self.nodes.vertices = None
        self.nodes.vertex_count = None
        self.hover = ClipNodes(shader)
        self.clips = [] # Flat list of all clips.
        self.selection = SelectionOverlay(shader)
        self.selected_clips = []
        self.sequences = defaultdict(list)
        self.sequence_callbacks = defaultdict(int)
        self.empty_clip_indices = []

    def appendClip(self, clip, sequence_index):
        clip.sequence = sequence_index
        if self.empty_clip_indices:
            clip.index = self.empty_clip_indices.pop(0)
            self.nodes.move(clip, glm.vec2(clip.timeline_in, clip.sequence))
            self.nodes.updateDuration(clip, clip.duration + 1)
            self.clips[clip.index] = clip
            self.sequences[sequence_index].append(clip.index)
        else:
            clip.index = self.nodes.count
            self.nodes.append(clip.timeline_in, clip.timeline_out, sequence_index * 2)
            self.sequences[sequence_index].append(len(self.clips))
            self.clips.append(clip)

    def deleteClip(self, clip):
        self.nodes.move(clip, glm.vec2(-clip.timeline_in, -clip.sequence))
        self.nodes.updateDuration(clip, -clip.duration - 1)
        self.sequences[clip.sequence].remove(clip.index)
        clip.clear()
        self.empty_clip_indices.append(clip.index)

    def snapToSelected(self):
        a_vtx = self.selection.vertices[::-1]
        b_vtx = self.nodes.vertices[::-1]
        x, y, z = range(3)
        for i, clip in enumerate(self.selected_clips):
            # Destination Highlighting here
            a_index = i * 4
            b_index = clip.index * 4
            a_x_pos = a_vtx[a_index][x]
            a_y_pos = a_vtx[a_index][y]
            b_x_pos = b_vtx[b_index][x]
            b_y_pos = b_vtx[b_index][y]
            x_diff = a_x_pos - b_x_pos
            y_diff = a_y_pos - b_y_pos
            self.nodes.move(clip, glm.vec2(x_diff, y_diff))

    def iterateSequences(self):
        clips = self.clips
        for sequence, clip_indices in reversed(self.sequences.items()):
            for index in clip_indices:
                yield sequence, clips[index]

    def reassignClips(self):
        callbacks = self.sequence_callbacks
        sequences = self.sequences
        for clip in self.selected_clips:
            new_sequence = callbacks.pop(clip)
            old_idx = sequences[clip.sequence].index(clip.index)
            sequences[clip.sequence].pop(old_idx)
            clip.sequence += int(new_sequence)
            sequences[clip.sequence].append(clip.index)

        ordered = defaultdict(list)
        for x in sorted(sequences.keys()):
            values = sequences[x]
            if values:
                ordered[x] = values
        self.sequences = ordered


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
        self.edit_mode = None

    @Slot()
    def _toAnnotatedFrame(self, direction):
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
        #if hasattr(self.current_clip, 'geometry'):
        #    self.current_clip.geometry.clear() # Not sure if this is relevant
        self.current_clip = clip
        self.graph = Graph(shader=self.primitive_shader)
        self.current_frame = 0
        self.updateNodeGlyphs()

    def getClipOnFrame(self, frame):
        for sequence, clip in self.graph.iterateSequences():
            local_frame = clip.mapToLocalFrame(frame)
            if local_frame:
                return clip, local_frame

        return False, False


    def updatedFrame(self, frame):
        self.current_frame = frame
        #local_frame = False
        #if len(self.graph.sequences) < 2 and self.current_clip:
        #    local_frame = self.current_clip.mapToLocalFrame(frame)

        #if local_frame:
        #    return self.current_clip, local_frame
        #else:
        self.current_clip, local_frame = self.getClipOnFrame(frame)
        super(timelineGLView, self).paintGL()
        frame_translation = glm.translate(glm.mat4(1.0), glm.vec3(frame, 0, 0))
        time_mvp = self.camera.perspective * self.glmview * frame_translation

        self.frame_glyphs.draw(self.MVP)
        self.time_cursor.draw(time_mvp)
        self.update()
        return self.current_clip, local_frame



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
        clip_scale = glm.scale(ct, glm.vec3(1, self.zoom2d * 7.0756, 1))

        time_mvp = self.camera.perspective * self.glmview * frame_translation
        clip_mvp = self.camera.perspective * self.glmview * clip_scale

        self.grid.draw(self.MVP)
        if self.graph.nodes.vertex_count:
            if self.graph.selected_clips:
                self.graph.selection.draw(clip_mvp, GL_LINE_LOOP, size=2,
                    color=glm.vec4(0.41, 0.66, 0.8, 1))
            self.graph.nodes.draw(clip_mvp, GL_LINE_LOOP, size=3.0,
                color=glm.vec4(0.23, 0.26, 0.34, 1))
            self.graph.nodes.draw(clip_mvp, GL_QUADS,
                color=glm.vec4(0.299, 0.33, 0.442, 1))
            #self.graph.hover.draw(self.MVP, GL_LINE_LOOP, size=1.0,
            #    color=glm.vec4(0.4, 0.48, 0.6, 1))

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


    def drawViewport(self, orbit=False, scale=False, pan=False):
        self.font_scale = self.zoom2d * 0.266
        x, y, w, h = self._screen_dimensions
        glViewport(x, y, w, h)
        #TODO: reimplement this in the camera class instead of the view.
        cam = self.camera
        pan2d = self.pan2d
        last_zoom = self.lastzoom2d
        if pan:
            pan2d.x = (
                (self.m_pos.x - self.m_lastpos.x) * last_zoom
            ) + pan2d.x
            pan2d.y = (
                (self.m_pos.y - self.m_lastpos.y) * last_zoom
            ) + pan2d.y
        elif scale:
            self.zoom2d = self.zoom2d + (
                (-(self.m_pos.x - self.m_lastpos.x) * self.zoom2d) * 0.002
            )
            if self.zoom2d < 0.002:
                self.zoom2d = 0.002

            center = glm.vec2((w / 2), (h / 2)) * self.zoom2d

            origin = self.origin_pos
            offsetx = (((origin.x) - (w / 2)) * last_zoom) - pan2d.x
            offsety = (((origin.y) - (h / 2)) * last_zoom) - pan2d.y

            worldoffset_x = (origin.x * self.zoom2d) - center.x
            worldoffset_y = (origin.y * self.zoom2d) - center.y
            pan2d.x = worldoffset_x - offsetx
            #pan2d.y = worldoffset_y - offsety # Enable zooming on Y axis

        if orbit | scale | pan:
            center = glm.vec2((w / 2), (h / 2)) * self.zoom2d
            if -pan2d.x <= center.x:
                pan2d.x = -center.x + self.clip_scale
            cam.left = -(center.x + pan2d.x)
            cam.right = center.x - pan2d.x
            cam.bottom = -(center.y + pan2d.y)
            cam.top = center.y - pan2d.y
            cam.updatePerspective()
            self.pan2d = pan2d
            # Update time Cursor size
            self.time_cursor.resize(cam.top, cam.bottom)
            self.scrub_area.resize(cam.left, cam.right, cam.top-(28*self.font_scale))
            self.cache_cursor.move(cam.bottom)

            self.glmview = cam.getMVP()
            self.updateTicks()

        self.updateFrameGlyphs()


    def updateCacheSize(self, left, right):
        """Update Cache display size
        """
        self.cache_cursor.resize(left, right)
        self.update()

    def updateTicks(self):
        """Update Ticks spacing and labels
        """
        frames_array, step = ticksFromView(self.camera)
        top = self.camera.top - self.clip_scale
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
        frame = self.current_frame
        font_scale = self.font_scale
        x = frame + self.clip_scale
        y = self.camera.bottom + (font_scale * 36)
        self.frame_glyphs.updateText(str(frame), glm.vec2(x, y), font_scale * 1.125)

    def updateNodeGlyphs(self):
        # Update Node names & sizes
        annotation_cursors = AnnotationCursors(shader=self.primitive_shader)
        handle_cursors = HandleCursors(shader=self.primitive_shader)
        # Text glyphs & Fonts
        node_glyphs = glyphContainer(shader=self.text_shader)
        handle_glyphs = HandleGlyphs(shader=self.text_shader)
        
        clip_scale = self.clip_scale
        font_scale = self.font_scale
        switch = True

        for sequence, clip in self.graph.iterateSequences():
            # Build clip glyph text
            if self.tick_step >= 50 and switch:
                switch = not switch
                continue
            
            local_center = (clip.duration / 2)
            text_width = ((len(clip.label) / 2) * clip_scale)
            # Don't add if text is larger than clip bounds.
            if int(text_width) < int(local_center):
                clip_center = clip.timeline_in + local_center
                x = clip_center - text_width
                y = ((sequence * (self.zoom2d * 7.0756)) * 2) - clip_scale

                # Label 
                position = glm.vec2(x, y)
                clip.glyph_offset = len(node_glyphs.elements)
                node_glyphs.addText(clip.label, position, font_scale)

                ins_text = ' {} |'.format(clip.first)
                out_text = '| {}'.format(clip.last)

                # In / Out frames
                in_pos = glm.vec2(clip.timeline_in, position.y)
                node_glyphs.addText(ins_text, in_pos, font_scale)

                text_width = len(out_text) * clip_scale
                out_pos = glm.vec2(clip.timeline_out - text_width, position.y)
                node_glyphs.addText(out_text, out_pos, font_scale)
            
                # Handles
                head_text = ' ' + str(clip.head)
                tail_text = str(clip.tail) + ' '

                h_pos = clip.timeline_in + (len(ins_text)) * clip_scale
                t_pos = clip.timeline_out - (len(out_text + tail_text) * clip_scale)
                handle_glyphs.addText(head_text, glm.vec2(h_pos, position.y), font_scale)
                handle_glyphs.addText(tail_text, glm.vec2(t_pos, position.y), font_scale)

                # Handle bars
                top = ((sequence * (self.zoom2d * 7.0756)) * 2) - (clip_scale * 2)
                handle_cursors.append(clip.timeline_in, clip.timeline_in + clip.head, top)
                handle_cursors.append(clip.timeline_out - clip.tail, clip.timeline_out, top)

            # Annotations
            for local_frame in clip.annotations:
                timeline_frame = clip.mapToGlobalFrame(local_frame)
                annotation_cursors.append(timeline_frame, (font_scale * 50))


        self.node_glyphs = node_glyphs
        self.node_glyphs.rebuild()
        self.annotation_cursors = annotation_cursors
        self.annotation_cursors.build()
        self.handle_cursors = handle_cursors
        self.handle_cursors.build()
        self.handle_glyphs = handle_glyphs
        self.handle_glyphs.rebuild()
        self.update()

    def createGlyphs(self):
        # Create and Assigns Class variables
        font_atlas, char_map = createFontAtlas(':/resources/LucidaTypewriterRegular.ttf')

        self.tick_glyphs = tickGlyphs(z=-0.1, shader=self.text_shader)
        self.node_glyphs = glyphContainer(shader=self.text_shader)
        self.handle_glyphs = HandleGlyphs(shader=self.text_shader)
        self.frame_glyphs = FrameGlyphs(shader=self.text_shader)

        glyphContainer.atlas_texture = self.tick_glyphs.createFontAtlasTexture(font_atlas)
        glyphContainer.char_map = char_map

        self.tick_glyphs.addText(str(0), glm.vec2(0, 12), 0.050)
        self.frame_glyphs.addText(self.frame_glyphs.text, glm.vec2(0, 12), 0.050)
        self.tick_glyphs.rebuild()
        self.node_glyphs.rebuild()
        self.frame_glyphs.rebuild()
        self.handle_glyphs.rebuild()


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
            extend = mods == Qt.ShiftModifier
            detach = mods == Qt.ControlModifier
            if clip:
                if not extend:
                    extend = clip in self.graph.selected_clips
                self.selectNode(clip, append=extend, detach=detach)
                self.edit_mode = MOVE_CLIP
            else:
                self.selectNodes()


    def selectAll(self):
        make_selection = self.selectNode
        for seq_index, clip in self.graph.iterateSequences():
            make_selection(clip, append=True)
        self.update()

    def mouseMoveEvent(self, event):
        super(timelineGLView, self).mouseMoveEvent(event)
        buttons = event.buttons()

        if self.scrubbing or self.withinScrubArea():
            self.setCursor(QCursor(Qt.SizeHorCursor))
        else:
            self.setCursor(QCursor(Qt.ArrowCursor))
            

        if self.pressing and buttons == Qt.LeftButton:
            if self.edit_mode:
                self.moveSelectedClips()
            elif self.scrubbing:
                self.jumpToCursor()
            else:
                self.selectNodes()
        elif not self.cursorOverNode():
            self.graph.hover.resize(-2, -1, 0, 0)

    def moveSelectedClips(self):
        movement = self.w_pos - self.screenToWorld(self.m_lastpos)
        position = glm.vec2(movement.x(), movement.y())
        y = position.y / self.clip_scale or 0

        snap_movement = glm.vec2(position.x, y)
        graph = self.graph
        nodes = self.graph.nodes
        glyphs = self.node_glyphs

        a_vtx = self.graph.selection.vertices[::-1]
        b_vtx = nodes.vertices[::-1]
        x, y, = range(2)
        for i, clip in enumerate(self.graph.selected_clips):
            nodes.move(clip, snap_movement)
            glyphs.move(clip.label, clip.glyph_offset, position)

            # Destination Highlighting here
            a_idx = i * 4
            b_idx = clip.index * 4
            a_x_pos = a_vtx[a_idx][x]
            a_y_pos = a_vtx[a_idx][y]
            b_x_pos = b_vtx[b_idx][x]
            b_y_pos = b_vtx[b_idx][y]

            x_diff = b_x_pos - a_x_pos
            y_diff = b_y_pos - a_y_pos
            rounded = glm.vec2(round(x_diff, 0), round(y_diff, 0))
            rounded.y = rounded.y - (rounded.y % 2)
            sequence_offset = rounded.y / 2
            graph.sequence_callbacks[clip] += sequence_offset

            clip.timeline_in += int(rounded.x)
            clip.setTimelineOut()

        graph.selection.moveAll(clip, rounded)

    def withinScrubArea(self):
        top = self.camera.top
        bot = self.camera.top - (self.clip_scale * 2)
        y = self.w_pos.y()
        if y <= top and y >= bot:
            return True

    def jumpToCursor(self):
        cursor_frame = int(self.w_pos.x() + 0.5)
        self.frameJump.emit(cursor_frame)

    def selectNode(self, clip, append=True, detach=False):
        graph = self.graph
        selected_clips = graph.selected_clips

        if detach:
            for index, sel_clip in enumerate(selected_clips):
                if sel_clip is clip:
                    selected_clips.pop(index)
                    break
            
            graph.selection = SelectionOverlay(self.primitive_shader)
            for clip in selected_clips:
                graph.selection.append(clip.timeline_in, clip.timeline_out, clip.sequence * 2)
            return

        elif not append:
            graph.selection = SelectionOverlay(self.primitive_shader)
            graph.selected_clips = []

        if clip and clip not in graph.selected_clips:
            graph.selected_clips.append(clip)
            graph.selection.append(clip.timeline_in, clip.timeline_out, clip.sequence * 2)


    def selectNodes(self):
        a = self.w_firstpos
        b = glm.vec2(self.w_pos.x(), self.w_pos.y())
        sel_rect = QRectF(QPointF(a.x, a.y), QPointF(b.x, b.y))
        local_scale = self.clip_scale
        make_selection = self.selectNode
        graph = self.graph
        clear_selection = True
        for seq_index, clip in graph.iterateSequences():
            clip_rect = graph.nodes.rect(clip.index, local_scale)
            if clip_rect.intersects(sel_rect):
                make_selection(clip, append=True)
                clear_selection = False
                
        if clear_selection:
            make_selection(None, append=False)
        else:
            for clip in graph.selected_clips:
                clip_rect = graph.nodes.rect(clip.index, local_scale)
                if not clip_rect.intersects(sel_rect):
                    make_selection(clip, append=False, detach=True)

        self.selection_rect.resize(
            sel_rect.left(), sel_rect.right(), sel_rect.bottom(), sel_rect.top())

    @property
    def clip_scale(self):
        return self.font_scale * 26.6

    def cursorOverNode(self):
        local_scale = self.clip_scale
        for sequence, clip in self.graph.iterateSequences():
             if self.graph.nodes.vertex_count:
                clip_rect = self.graph.nodes.rect(clip.index, local_scale)
                if clip_rect.contains(self.w_pos):
                    top = sequence * local_scale
                    bot = sequence - (local_scale*2)
                    l = clip.timeline_in
                    r = clip.timeline_out
                    self.graph.hover.resize(l, r, top, bot)
                    return clip
        return False


    def mouseReleaseEvent(self, event):
        super(timelineGLView, self).mouseReleaseEvent(event)
        self.selection_rect.resize(-1,-1.1,0.1,0)
        if self.graph.sequence_callbacks:
            self.graph.reassignClips()
            self.graph.snapToSelected()
        self.updateNodeGlyphs()
        self.mouseInteracted.emit(True)
        self.scrubbing = False
        self.edit_mode = None

    def wheelEvent(self, event):
        super(timelineGLView, self).wheelEvent(event)
        self.updateNodeGlyphs()
        self.cursorOverNode()


    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_F:
            self.frameGeometry()
        if key == Qt.Key_Delete:
            selection = self.graph.selected_clips
            if selection:
                list(map(self.graph.deleteClip, selection))
                self.updateNodeGlyphs()
    

    def frameGeometry(self):
        clip = self.current_clip
        if self.graph.selected_clips:
            first = self.graph.selected_clips[0].timeline_in
            last = self.graph.selected_clips[0].timeline_out
            for clip in self.graph.selected_clips:
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
        self.drawViewport(orbit=True)
        self.updateNodeGlyphs()
        self.updateTicks()
        self.updateFrameGlyphs()
        self.cursorOverNode()


    def cut(self):
        pass