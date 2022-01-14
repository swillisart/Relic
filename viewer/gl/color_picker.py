from OpenGL.GL import *
from PySide6.QtCore import Signal
from PySide6.QtGui import Qt
from .widgets import InteractiveGLView
from .primitives import ColorWheel, Crosshair
import glm
import numpy as np

class ColorPickerGL(InteractiveGLView):

	userPickedColor = Signal(np.ndarray, float)  

	def __init__(self, *args, **kwargs):
		super(ColorPickerGL, self).__init__(*args, **kwargs)
		self.cursor_mvp = glm.mat4(1.0)
		self.draw_gl_cursor = True
		self.bgc = 0.270

	def initializeGL(self):
		super(ColorPickerGL, self).initializeGL()
		self.color_wheel = ColorWheel()
		self.crosshair = Crosshair()

	def paintGL(self):
		super(ColorPickerGL, self).paintGL()
		self.color_wheel.draw(self.MVP)
		if self.draw_gl_cursor:
			self.crosshair.draw(self.MVP)

	def getColorAt(self, pos):
		# Get screen position from Qt Cursor to OpenGL dispaly buffer
		glPixelStorei(GL_PACK_ALIGNMENT, 1)
		glReadBuffer(GL_FRONT)
		color_sample = glReadPixels(pos.x, pos.y, 1, 1, GL_RGBA, GL_FLOAT)[0][0]
		return color_sample 

	def mouseReleaseEvent(self, event):
		self.setCursor(Qt.ArrowCursor)
		self.draw_gl_cursor = True

	def mouseMoveEvent(self, event):
		super(ColorPickerGL, self).mouseMoveEvent(event)
		pos = event.position()
		screen_pos = glm.vec2(pos.x(), -pos.y() + self.height())
		screen_center = glm.vec2(self.width(), self.height()) / 2
		world_pos = (screen_pos - screen_center) * self.zoom2d
		clamped_pos = glm.vec3(glm.clamp(world_pos, -1, 1), 0.0)
		normalized_pos = glm.normalize(clamped_pos) * 0.9

		buttons = event.buttons()
		if Qt.LeftButton == buttons:
			self.draw_gl_cursor = False

			self.setCursor(Qt.CrossCursor)
			if glm.length(clamped_pos) <= 1:
				self.crosshair.translate(clamped_pos)
			else:
				self.draw_gl_cursor = True
				self.crosshair.translate(normalized_pos)

			color_sample = self.getColorAt(screen_pos)
			hue = np.degrees(np.arctan2(world_pos.x, world_pos.y)) % 360
			self.userPickedColor.emit(color_sample, hue)


	def positionFromSaturation(self, saturation):
		c_p = self.crosshair.position
		vnorm = glm.normalize(c_p) * saturation * 0.9
		self.crosshair.translate(vnorm)


	def resizeGL(self, width, height):
		scale = min(width, height)
		self.zoom2d = 2 / scale
		super(ColorPickerGL, self).resizeGL(width, height)
