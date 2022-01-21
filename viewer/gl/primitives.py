from ctypes import c_void_p

# Third-party
from OpenGL.GL import *
from OpenGL.GL.shaders import compileShader, compileProgram, ShaderProgram
from OpenGL.arrays import vbo

import numpy as np
import glm
import math
from viewer.gl.shading import BaseProgram
from viewer.io.util import openResource

class PrimitiveShader(BaseProgram):
	vertex = """
	#version 330 core
	in layout(location = 0) vec3 position;

	uniform mat4 MVP;

	void main()
	{
		gl_Position = MVP * vec4(position, 1);
	}
	"""

	fragment = """
	#version 330
	uniform vec4 color;
	out vec4 outputColor;
	void main()
	{
		outputColor = color;
	}
	"""

	@classmethod
	def create(cls):
		obj = super(PrimitiveShader, cls).fromGlsl(
			PrimitiveShader.vertex, PrimitiveShader.fragment
		)
		obj.setUniforms('MVP', 'color')
		return obj


class BasePrimitive(object):

	def __init__(self, shader=None):
		if shader:
			self.shader = shader
		else:
			self.shader = PrimitiveShader.create()

		self.color = glm.vec4(0.4, 0.390, 0.375, 1.0)

	def buildFromVertices(self, vertices): 
		self.vbo = vbo.VBO(vertices)
		self.vertex_count = len(vertices) * 3 * 2
		indices = np.array([[range(0, self.vertex_count)]], dtype=np.int16)
		self.ibo = vbo.VBO(indices, target=GL_ELEMENT_ARRAY_BUFFER)

	def draw(self, transpose_mvp):
		with self.shader, self.ibo, self.vbo:
			glUniformMatrix4fv(self.shader.MVP, 1, GL_FALSE, glm.value_ptr(transpose_mvp))
			glUniform4fv(self.shader.color, 1, glm.value_ptr(self.color))
			glEnableVertexAttribArray(0)
			element_count = int(self.vertex_count)
			glVertexAttribPointer(0, 3, GL_FLOAT, False, 0, c_void_p(0))
			glDrawElements(GL_LINES, element_count, GL_UNSIGNED_SHORT, c_void_p(0))


class grid(BasePrimitive):

	def __init__(self, *args, **kwargs):
		super(grid, self).__init__(*args, **kwargs)

		self.buildGrid()

	def buildGrid(self):
		vertical_vertices = np.array([
				[0, -500, -0.1], [0, 500, -0.1],
				[5, -500, -0.1], [5, 500, -0.1],
				[10, -500, -0.1], [10, 500, -0.1],
				[15, -500, -0.1], [15, 500, -0.1],
				[20, -500, -0.1], [20, 500, -0.1],
				[25, -500, -0.1], [25, 500, -0.1],
				[30, -500, -0.1], [30, 500, -0.1],
				[35, -500, -0.1], [35, 500, -0.1]
				], dtype=np.float32)

		horizontal_vertices = np.zeros((50, 3), dtype=np.float32)

		# Build grid lines
		switch = False
		count = 0
		for x in range(50):
			if switch:
				horizontal_vertices[x][0] = 35
			else:
				count -= 1
				horizontal_vertices[x][0] = -2

			horizontal_vertices[x][1] = count
			horizontal_vertices[x][2] = -10 # Z depth

			switch = not switch
	
		vertices = np.append(vertical_vertices, horizontal_vertices)
		self.buildFromVertices(vertices)


class TickGrid(grid):

	def __init__(self, *args, **kwargs):
		super(TickGrid, self).__init__(*args, **kwargs)
		self.color = glm.vec4(0.3, 0.3, 0.3, 1.0)

	def buildGrid(self, array=None):
		# Vertical Y-axis polyline creation.
		horizontal_ticks = np.arange(0, 8640, 5, dtype=np.float32)
		z = np.zeros((1728), dtype=np.float32)
		y = z + 10
		vertices_top = np.stack((horizontal_ticks, y, z - 1.5), axis=1)
		y = z - 10
		vertices_bot = np.stack((horizontal_ticks, y, z - 1.5), axis=1)
		vertices = np.hstack((vertices_top, vertices_bot))
		self.buildFromVertices(vertices)

	def gridFromArray(self, array, top, bot):
		horizontal_ticks = array.astype('float32')
		z = np.zeros((len(horizontal_ticks)), dtype=np.float32)
		y = z + top
		vertices_top = np.stack((horizontal_ticks, y, z - 1.5), axis=1)
		y = z + bot
		vertices_bot = np.stack((horizontal_ticks, y, z - 1.5), axis=1)
		vertices = np.hstack((vertices_top, vertices_bot))
		self.buildFromVertices(vertices)


class TimeCursor(grid):

	def __init__(self, *args, **kwargs):
		super(TimeCursor, self).__init__(*args, **kwargs)

	def buildGrid(self, top=25, bot=-25):
		self.vertices = np.array(
			[[0, bot, 0], [0, top, 0]], dtype=np.float32
		)
		self.buildFromVertices(self.vertices)
		self.color = glm.vec4(0.5, 0.9, 0.65, 0.5)


	def draw(self, transpose_mvp):
		glLineWidth(3.0)
		super(TimeCursor, self).draw(transpose_mvp)
		glLineWidth(1.0)
	
	def resize(self, top, bottom):
		self.vertices[0, 1] = top
		self.vertices[1, 1] = bottom
		with self.vbo:
			self.vbo.implementation.glBufferSubData(
				self.vbo.target, 0, self.vertices
			)


class AnnotationCursors(BasePrimitive):

	def __init__(self, *args, **kwargs):
		super(AnnotationCursors, self).__init__(*args, **kwargs)
		self.vertices = np.array(
			[[0, 0, -1], [0, 0, -1]], dtype=np.float32
		)
		self.color = glm.vec4(0.884, 0.588, 0.296, 0.5)

	"""
	def extend(self, array)
		horizontal_ticks = np.array(xasix, dtype=np.float32)

		z = np.zeros((len(horizontal_ticks)), dtype=np.float32)
		y = z + 10
		vertices_top = np.stack((horizontal_ticks, y, z - 1.5), axis=1)
		y = z - 10
		vertices_bot = np.stack((horizontal_ticks, y, z - 1.5), axis=1)
		vertices = np.hstack((vertices_top, vertices_bot))
		self.vertices.append(vertices)
	"""

	def build(self):
		self.buildFromVertices(self.vertices)

	def append(self, x, top, bot):
		new_vertices = np.array([[x, bot, 0], [x, top, 0]], dtype=np.float32)
		self.vertices = np.append(self.vertices, new_vertices, axis=0)

	def offset(self, factor):
		self.vertices[:, 0] += factor
		with self.vbo:
			self.vbo.implementation.glBufferSubData(
				self.vbo.target, 0, self.elements
			)

	def draw(self, transpose_mvp):
		glLineWidth(3.0)
		super(AnnotationCursors, self).draw(transpose_mvp)
		glLineWidth(1.0)


class HandleCursors(BasePrimitive):

	def __init__(self, *args, **kwargs):
		super(HandleCursors, self).__init__(*args, **kwargs)
		self.vertices = np.array(
			[[0, 0, -1], [0, 0, -1]], dtype=np.float32
		)
		self.color = glm.vec4(0.505, 0.207, 0.185, 0.875)

	def build(self):
		self.buildFromVertices(self.vertices)

	def append(self, ins, out, y):
		new_vertices = np.array([[ins, y, 0], [out, y, 0]], dtype=np.float32)
		self.vertices = np.append(self.vertices, new_vertices, axis=0)

	def draw(self, transpose_mvp):
		glLineWidth(2.5)
		super(HandleCursors, self).draw(transpose_mvp)
		glLineWidth(1.0)


class CacheProgress(grid):

	def __init__(self, *args, **kwargs):
		super(CacheProgress, self).__init__(*args, **kwargs)
		self.color = glm.vec4(0.0, 0.45, 0.7, 1)


	def buildGrid(self):
		self.vertices = np.array(
			[[0, 0, 0], [1, 0, 0]], dtype=np.float32
		)
		self.left = np.s_[0, 0]
		self.right = np.s_[1, 0]
		self.y = np.s_[:, 1]
		self.buildFromVertices(self.vertices)

	def updateVBO(self):
		with self.vbo:
			self.vbo.implementation.glBufferSubData(
				self.vbo.target, 0, self.vertices
			)

	def draw(self, transpose_mvp):
		glLineWidth(5.0)
		super(CacheProgress, self).draw(transpose_mvp)
		glLineWidth(1.0)

	def move(self, bottom):
		self.vertices[self.y] = bottom
		self.updateVBO()

	def resize(self, left, right):
		self.vertices[self.left] = left
		self.vertices[self.right] = right
		self.updateVBO()


class Circle(BasePrimitive):

	def __init__(self, *args, **kwargs):
		super(Circle, self).__init__(*args, **kwargs)
		self.point_count = 48
		
	def build(self):
		self.vertices = np.zeros((self.point_count, 3), dtype=np.float32)
		radius = 0.5
		_slice = 2 * math.pi / self.point_count
		
		for i in range(self.point_count):
			angle = _slice * i
			x = (radius * math.cos(angle))
			y = (radius * math.sin(angle))
			self.vertices[i] = (x, y, 0)

		self.buildFromVertices(self.vertices)

	def draw(self, transpose_mvp):
		with self.shader, self.ibo, self.vbo:
			glUniformMatrix4fv(self.shader.MVP, 1, GL_FALSE, glm.value_ptr(transpose_mvp))
			glUniform4fv(self.shader.color, 1, glm.value_ptr(self.color))
			glEnableVertexAttribArray(0)
			glVertexAttribPointer(0, 3, GL_FLOAT, False, 0, c_void_p(0))
			glDrawElements(GL_LINE_LOOP, self.point_count, GL_UNSIGNED_SHORT, c_void_p(0))


class ColorWheel(object):

	def __init__(self):
		self.vertices = np.array([
			0.4564, -0.7906, 0.0, 1.0, 0.0, 1.0,
			-0.4565, -0.7903, 0.0, 1.0, 0.0, 0.0,
			-0.9127, 0.0005, 0.0, 1.0, 1.0, 0.0,
			-0.456, 0.791, 0.0, 0.0, 1.0, 0.0,
			0.457, 0.7907, 0.0, 0.0, 1.0, 1.0,
			0.9132, -0.0001, 0.0, 0.0, 0.0, 1.0,
			0.0, -0.0, 0.0, 1.0, 1.0, 1.0,
			0.0005, 0.9132, 0.0, 0.0, 1.0, 0.5,
			0.791, 0.4564, 0.0, 0.0, 0.5, 1.0,
			0.7907, -0.4565, 0.0, 0.5, 0.0, 1.0,
			-0.0001, -0.9127, 0.0, 1.0, 0.0, 0.5,
			-0.7906, -0.456, 0.0, 1.0, 0.5, 0.0,
			-0.7903, 0.457, 0.0, 0.5, 1.0, 0.0,
			-0.8815, 0.2368, 0.0, 0.75, 1.0, 0.0,
			-0.8817, -0.2358, 0.0, 1.0, 0.75, 0.0,
			-0.6455, -0.6451, 0.0, 1.0, 0.25, 0.0,
			-0.2364, -0.8815, 0.0, 1.0, 0.0, 0.25,
			0.2362, -0.8817, 0.0, 1.0, 0.0, 0.75,
			0.6456, -0.6455, 0.0, 0.75, 0.0, 1.0,
			0.882, -0.2364, 0.0, 0.25, 0.0, 1.0,
			0.8822, 0.2362, 0.0, 0.0, 0.25, 1.0,
			0.646, 0.6456, 0.0, 0.0, 0.75, 1.0,
			0.2368, 0.882, 0.0, 0.0, 1.0, 0.75,
			-0.2358, 0.8822, 0.0, 0.0, 1.0, 0.25,
			-0.6451, 0.646, 0.0, 0.25, 1.0, 0.0,
			-0.3494, -0.8431, 0.0, 1.0, 0.0, 0.125,
			-0.1192, -0.9049, 0.0, 1.0, 0.0, 0.375,
			0.1191, -0.905, 0.0, 1.0, 0.0, 0.625,
			0.3493, -0.8433, 0.0, 1.0, 0.0, 0.875,
			0.5558, -0.7243, 0.0, 0.875, 0.0, 1.0,
			0.7243, -0.5558, 0.0, 0.625, 0.0, 1.0,
			0.8436, -0.3494, 0.0, 0.375, 0.0, 1.0,
			0.9053, -0.1192, 0.0, 0.125, 0.0, 1.0,
			0.9054, 0.1191, 0.0, 0.0, 0.125, 1.0,
			0.8438, 0.3493, 0.0, 0.0, 0.375, 1.0,
			0.7247, 0.5558, 0.0, 0.0, 0.625, 1.0,
			0.5562, 0.7243, 0.0, 0.0, 0.875, 1.0,
			0.3499, 0.8436, 0.0, 0.0, 1.0, 0.875,
			0.1197, 0.9053, 0.0, 0.0, 1.0, 0.625,
			-0.1186, 0.9054, 0.0, 0.0, 1.0, 0.375,
			-0.3489, 0.8438, 0.0, 0.0, 1.0, 0.125,
			-0.5553, 0.7247, 0.0, 0.125, 1.0, 0.0,
			-0.7239, 0.5562, 0.0, 0.375, 1.0, 0.0,
			-0.8431, 0.3499, 0.0, 0.625, 1.0, 0.0,
			-0.9049, 0.1197, 0.0, 0.875, 1.0, 0.0,
			-0.905, -0.1186, 0.0, 1.0, 0.875, 0.0,
			-0.8433, -0.3489, 0.0, 1.0, 0.625, 0.0,
			-0.7243, -0.5553, 0.0, 1.0, 0.375, 0.0,
			-0.5558, -0.7239, 0.0, 1.0, 0.125, 0.0,
			], dtype=np.float32
		)

		self.indices = np.array([
			7, 6, 39, 6, 16, 25, 1, 48, 6, 6, 12, 42, 34, 6, 8, 9, 6,
			31, 38, 6, 7, 8, 6, 35, 30, 6, 9, 0, 28, 6, 6, 14, 45, 6,
			44, 13, 6, 13, 43, 6, 46, 14, 15, 47, 6, 6, 26, 16, 6, 17,
			27, 0, 6, 29, 32, 6, 5, 5, 6, 33, 36, 6, 4, 4, 6, 37, 40,
			6, 3, 6, 41, 3, 6, 25, 1, 6, 10, 26, 6, 27, 10, 6, 28, 17,
			29, 6, 18, 18, 6, 30, 31, 6, 19, 19, 6, 32, 33, 6, 20, 20,
			6, 34, 35, 6, 21, 21, 6, 36, 37, 6, 22, 22, 6, 38, 39, 6,
			23, 23, 6, 40, 6, 24, 41, 6, 42, 24, 6, 43, 12, 6, 2, 44,
			6, 45, 2, 6, 11, 46, 6, 47, 11, 6, 48, 15
			], dtype=np.int16
		)
		self.shader = BaseProgram.fromGlsl(
			openResource(':resources/shaders/vertex_colors.vs'),
			openResource(':resources/shaders/vertex_colors.fs')
		)
		self.shader.setUniforms('MVP')

		self.vbo = vbo.VBO(self.vertices)
		self.indices_count = len(self.indices)
		self.ibo = vbo.VBO(self.indices, target=GL_ELEMENT_ARRAY_BUFFER)

	def draw(self, transpose_mvp):
		axis = glm.vec3(0, 0, 1)
		obj_rot = glm.rotate(glm.mat4(1.0), 60, axis)
		rotated = transpose_mvp * obj_rot
		with self.shader, self.ibo, self.vbo:
			glUniformMatrix4fv(self.shader.MVP, 1, GL_FALSE, glm.value_ptr(rotated))

			# Positions
			glVertexAttribPointer(0, 3, GL_FLOAT, False, 6 * 4, c_void_p(0))
			glEnableVertexAttribArray(0)
			
			# Colors
			glVertexAttribPointer(1, 3, GL_FLOAT, False, 6 * 4, c_void_p(3 * 4))
			glEnableVertexAttribArray(1)
			
			glDrawElements(GL_TRIANGLES, self.indices_count, GL_UNSIGNED_SHORT, c_void_p(0))


class Crosshair(BasePrimitive):

	def __init__(self, *args, **kwargs):
		super(Crosshair, self).__init__(*args, **kwargs)
		self.vertices = np.array([
			[-0.1, 0, 0.1], [0.1, 0, 0.1],
			[0, -0.1, 0.1], [0, 0.1, 0.1],
			], dtype=np.float32
		)
		self.buildFromVertices(self.vertices)
		self.color = glm.vec4(0.0, 0.0, 0.0, 1.0)
		self.position = glm.vec3(0.0)

	def translate(self, vector):
		vertices = self.vertices + vector
		with self.vbo:
			self.vbo.implementation.glBufferSubData(
				self.vbo.target, 0, vertices
			)
		self.position = vector

	def draw(self, transpose_mvp):
		glLineWidth(2.0)
		super(Crosshair, self).draw(transpose_mvp)
		glLineWidth(1.0)


class Line(BasePrimitive):

	def __init__(self, *args, **kwargs):
		super(Line, self).__init__(*args, **kwargs)
		self.vertices = np.array(
			[[0, 0, 0.1], [0, 0, 0.1]], dtype=np.float32
		)
		self.buildFromVertices(self.vertices)
		self.color = glm.vec4(0.5, 0.9, 0.65, 1.0)

	def draw(self, transpose_mvp, size=4.0):
		glLineWidth(size)
		super(Line, self).draw(transpose_mvp)
		glLineWidth(1.0)

	def updateVBO(self):
		with self.vbo:
			self.vbo.implementation.glBufferSubData(
				self.vbo.target, 0, self.vertices
			)

	def resize(self, a, b):
		self.vertices[0, :2] = a
		self.vertices[1, :2] = b
		self.updateVBO()


class LineRect(BasePrimitive):

	def __init__(self, *args, **kwargs):
		super(LineRect, self).__init__(*args, **kwargs)
		self.vertices = np.array([
			[0, 0, 0.5], [0, 0, 0.5],
			[0, 0, 0.5], [0, 0, 0.5],
			], dtype=np.float32
		)
		self.buildFromVertices(self.vertices)
		self.color = glm.vec4(0.5, 0.9, 0.65, 1.0)

	def draw(self, transpose_mvp, size=4.0):
		glLineWidth(size)
		with self.shader, self.ibo, self.vbo:
			glUniformMatrix4fv(self.shader.MVP, 1, GL_FALSE, glm.value_ptr(transpose_mvp))
			glUniform4fv(self.shader.color, 1, glm.value_ptr(self.color))
			glEnableVertexAttribArray(0)
			element_count = int(self.vertex_count)
			glVertexAttribPointer(0, 3, GL_FLOAT, False, 0, c_void_p(0))
			glDrawElements(GL_LINE_LOOP, 4, GL_UNSIGNED_SHORT, c_void_p(0))
		glLineWidth(1.0)
	
	def resize(self, left, right, top, bot):
		self.vertices[0, :2] = (left, top)
		self.vertices[1, :2] = (right, top)
		self.vertices[2, :2] = (right, bot)
		self.vertices[3, :2] = (left, bot)

		with self.vbo:
			self.vbo.implementation.glBufferSubData(
				self.vbo.target, 0, self.vertices
			)


class Ellipse(Circle):

	def __init__(self, *args, **kwargs):
		super(Ellipse, self).__init__(*args, **kwargs)
		self.point_count = 72
		self.transform = glm.vec4(0.0)
		self.build()

	def draw(self, transpose_mvp):
		glLineWidth(3.0)
		super(Ellipse, self).draw(transpose_mvp*self.transform)
		glLineWidth(1.0)
