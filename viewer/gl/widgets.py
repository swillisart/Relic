import os
import sys

# -- Third-party -- 
import glm
import numpy as np

from OpenGL.GL import *
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtOpenGL import *
from PySide2.QtWidgets import *
from qtshared2.utils import getPrimaryScreenPixelRatio

# -- Module -- 
from viewer.gl.util import Camera

# ------------------------------- Globals ---------------------------------


class InteractiveGLView(QOpenGLWindow):

    def __init__(self, *args, **kwargs):
        super(InteractiveGLView, self).__init__(*args, **kwargs)
        self.setScreenDimensions()
        self.m_pos = self.m_lastpos = self.origin_pos = self.pan2d = glm.vec2(0, 0)
        self.zoom2d = 1.0
        self.lastzoom2d = 1.0
        self.pressing = False
        self.bgc = 0.15
        self.c_pos = self.w_pos = QPoint()

    def initializeGL(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glBlendEquation(GL_FUNC_ADD)
        glClampColor(GL_CLAMP_READ_COLOR, GL_FALSE)
        glClampColor(GL_CLAMP_VERTEX_COLOR, GL_FALSE)
        glClampColor(GL_CLAMP_FRAGMENT_COLOR, GL_FALSE)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glLineWidth(1.0)

        # Camera Setup
        self.camera = Camera(
            glm.vec3(0.0, 0.0, 1.0),
            self.width() / self.height(),
            0.1,
            100000,
            fov=25,
            ortho=True,
        )
        self.glmview = self.camera.getMVP()
        self.cmodeltransformation = glm.mat4(1.0)

    def setScreenDimensions(self):
        dpi_scale = getPrimaryScreenPixelRatio()
        x = y = 0
        w = int(self.width() * dpi_scale)
        h = int(self.height() * dpi_scale)
        self._screen_dimensions = (x, y, w, h)

    def resizeGL(self, width, height):
        self.makeCurrent()
        self.setScreenDimensions()
        self.drawViewport(orbit=True)
        self.camera.setAspect(width / height)

    def paintGL(self):
        self.makeCurrent()
        glClearColor(self.bgc, self.bgc, self.bgc, 0.01)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glDepthFunc(GL_LESS)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # GL_MULTISAMPLE
        glActiveTexture(GL_TEXTURE1)
        glEnable(GL_MULTISAMPLE)
        #glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

        self.MVP = self.camera.perspective * self.glmview * self.cmodeltransformation
        self.time_MVP = glm.mat4(1.0)

    def mousePressEvent(self, event):
        buttons = event.buttons()
        mods = event.modifiers()
        self.lastPos = event.pos()
        self.pressing = True
        self.origin_pos = glm.vec2(self.lastPos.x(), -(self.lastPos.y()) + self.height())

    def mouseReleaseEvent(self, event):
        self.pressing = False
        self.lastPos = event.pos()

    def mouseMoveEvent(self, event):
        self.makeCurrent()
        buttons = event.buttons()
        mods = event.modifiers()
        self.c_pos = event.pos()
        self.update()

        self.m_lastpos = glm.vec2(self.m_pos.x, self.m_pos.y)
        self.lastzoom2d = self.zoom2d
        self.m_pos = glm.vec2(self.c_pos.x(), -(self.c_pos.y()))
        self.w_pos = self.screenToWorld(self.m_pos)
        #QToolTip.showText(self.mapToGlobal(self.c_pos), str(self.w_pos), self)

        if (
            mods == Qt.AltModifier
            and self.pressing
            and not buttons == Qt.RightButton
            and not buttons == Qt.MiddleButton
        ):
            self.drawViewport(orbit=True)
        elif buttons == Qt.RightButton and mods == Qt.AltModifier:
            self.drawViewport(scale=True)
        elif buttons == Qt.MiddleButton and mods == Qt.AltModifier:
            self.drawViewport(pan=True)
        elif buttons == Qt.RightButton and mods == Qt.ShiftModifier:
            self.moveParentWindow()

    def wheelEvent(self, event):
        self.makeCurrent()
        delta = (-(event.delta()) * 0.00075) + 1

        if event.modifiers() == Qt.ShiftModifier:
            delta = event.delta() * 0.33
            self.scaleParentWindow(delta)
        else:
            self.zoom(delta)
        self.drawViewport(orbit=True)
        self.update()

    def moveParentWindow(self):
        parent = self.parent()
        win_geo = parent.geometry()
        x = (win_geo.x() - self.lastPos.x()) + self.c_pos.x()
        y = (win_geo.y() - self.lastPos.y()) + self.c_pos.y()
        if self.c_pos != self.lastPos:
            parent.setGeometry(x, y, parent.width(), parent.height())

    def scaleParentWindow(self, delta): 
        # Resize the window
        delta_h = delta / 2
        parent = self.parent()
        new_size = parent.size() + QSize(delta, delta)
        new_pos = parent.pos() + QPoint(-delta_h, -delta_h)
        parent.resize(new_size)
        parent.move(new_pos)

    def zoom(self, delta):
        # Prevent negative zoom level
        if self.zoom2d + delta < 0:
            self.zoom2d = 0.01
            return
        self.zoom2d = self.zoom2d * delta

    def drawViewport(self, orbit=False, scale=False, pan2d=False):
        x, y, w, h = self._screen_dimensions
        glViewport(x, y, w, h)
        center = glm.vec2((w / 2), (h / 2)) * self.zoom2d

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

                offsetx = (
                    ((self.origin_pos.x) - (w / 2)) * self.lastzoom2d
                ) - self.pan2d.x
                offsety = (
                    ((self.origin_pos.y) - (h / 2)) * self.lastzoom2d
                ) - self.pan2d.y

                worldoffset_x = (self.origin_pos.x * self.zoom2d) - center.x
                worldoffset_y = (self.origin_pos.y * self.zoom2d) - center.y
                self.pan2d.x = worldoffset_x - offsetx
                self.pan2d.y = worldoffset_y - offsety

            self.camera.left = -(center.x + self.pan2d.x)
            self.camera.right = center.x - self.pan2d.x
            self.camera.bottom = -(center.y + self.pan2d.y)
            self.camera.top = center.y - self.pan2d.y
            self.camera.updatePerspective()

        else:  # Place Perspective Camera
            dst_mult = glm.length(glm.vec3(0, 0, 0) - self.camera._position)
            horizontalAngle = (self.m_pos.x - self.m_lastpos.x) * 0.00147
            verticalAngle = (self.m_pos.t - self.m_lastpos.y) * 0.00147
            if scale:
                self.camera.zoom(
                    horizontalAngle * dst_mult, verticalAngle * dst_mult
                )

            elif pan2d:
                self.camera.pan(horizontalAngle * dst_mult, verticalAngle * dst_mult)

            elif orbit:
                self.camera.orbit(horizontalAngle * 3, verticalAngle * 3)

        self.glmview = self.camera.getMVP()
        self.update()

    def screenToWorld(self, position):
        w = self.width()
        h = self.height()
        mousex = (position.x - (w / 2))
        mousey = (position.y + (h / 2))

        offsetx = ((
            mousex * self.lastzoom2d
        ) - self.pan2d.x)
        offsety = ((
            mousey * self.lastzoom2d
        ) - self.pan2d.y)

        return QPointF(offsetx, offsety)


    @property
    def cursorTransform(self):
        w, h = (self.width(), self.height())
        x, y = (self.c_pos.x(), -self.c_pos.y())
        center_x = float(x - (w / 2))
        center_y = float(y + (h / 2))
        offset_x = ((center_x * self.zoom2d) - self.pan2d.x)
        offset_y = ((center_y * self.zoom2d) - self.pan2d.y)
        post = glm.vec3(offset_x, offset_y, 0.0)
        cursor_transform = glm.translate(glm.mat4(1.0), post)
        return cursor_transform

    def frameGeometry(self):
        if self.camera.ortho:
            self.pan2d = glm.vec2(-17, 12)
            self.origin_pos = glm.vec2(0, 0)
            th = 28 / self.height()
            self.zoom2d = th

        self.drawViewport()
