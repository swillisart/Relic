import re
import numpy as np
import glm
from OpenGL.arrays import vbo
from OpenGL.GL import *
from ctypes import c_void_p
#from OpenGL.GL import GL_ELEMENT_ARRAY_BUFFER
from PySide6.QtCore import QPointF
from sequence_path.main import SequencePath as Path
from viewer.gl.shading import BaseProgram


class InstanceShader(BaseProgram):

	vertex = """
	#version 400
	in layout(location = 0) vec3 vertexPosition;
	in layout(location = 1) vec2 vertexUV;
    in layout(location = 2) vec3 instanceTransform;

	uniform mat4 MVP;

	out vertex {
		vec2 UV;
		vec3 Position;
	} verts;

	void main()
	{
		gl_Position = MVP * vec4(vertexPosition + instanceTransform, 1);
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

	//uniform sampler2D tex2D;

	out vec4 rgba;

	void main()
	{
		rgba = vec4(1.0, 0.5, 1.0, 1.0);//texture2D(tex2D, verts.UV);
	}
	"""

	@classmethod
	def create(cls):
		obj = super(InstanceShader, cls).fromGlsl(
			InstanceShader.vertex, InstanceShader.fragment
		)
		obj.setUniforms('MVP')#, 'tex2D')
		return obj


class InstancedSquare(object):
	#__slots__ = [
	#	'vbo',
	#	'ibo',
	#	'ubo',
	#	'shader',
	#	'indices',
	#]

	def __init__(self):
		x = 1.25
		y = 1.0
		z = 0.01
		self.shader = InstanceShader.create()
		self.indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.int16)
		self.elements = np.array([
				-x,  y, z, 0.0, 0.0,
				x,  y, z, 1.0, 0.0,
				x, -y, z, 1.0, 1.0,
				-x, -y, z, 0.0, 1.0,
			], dtype=np.float32,
		)
		self.transforms = np.array([
			 50.0, 50.0, 0.0,
			 -50.0, -50.0, 0.0,
			 100.0,-100.0, 0.0,
		], dtype=np.float32)

		self.vbo = vbo.VBO(self.elements)
		self.ibo = vbo.VBO(self.indices, target=GL_ELEMENT_ARRAY_BUFFER)
		self.tbo = vbo.VBO(self.transforms, usage=GL_STATIC_DRAW)


	def draw(self, transpose_mvp):
		with self.shader, self.ibo, self.vbo:
			glUniformMatrix4fv(self.shader.MVP, 1, GL_FALSE, glm.value_ptr(transpose_mvp))

			glEnableVertexAttribArray(0)
			glVertexAttribPointer(0, 3, GL_FLOAT, False, 5*4, c_void_p(0))

			glEnableVertexAttribArray(1)
			glVertexAttribPointer(1, 2, GL_FLOAT, False, 5*4, c_void_p(3 * 4))

			self.tbo.bind()
			glEnableVertexAttribArray(2)
			glVertexAttribPointer(2, 3, GL_FLOAT, False, 5*4, c_void_p(0))
			glVertexAttribDivisor(2, 1)

			glDrawElementsInstanced(GL_TRIANGLES, 6, GL_UNSIGNED_SHORT, c_void_p(0), 3)
			self.tbo.unbind()



class CursorSnapper(object):

	def __init__(self):
		self.snap = QPointF()
		self.step = glm.vec2(1, 5)

	def getPosition(self, movement):
		snap = movement + self.snap
		new_pos = None
		x = snap.x()
		y = snap.y()
		step = self.step
		if y >= step.y or y <= -step.y:
			new_pos = glm.vec2(0, round(y, 0))
			snap.setY(0.0)

		if x >= step.x or x <= -step.x:
			new_x = round(x, 0)
			new_pos = glm.vec2(new_x, 0)
			snap.setX(0.0)
		self.snap = snap
		if new_pos:
			return new_pos


class Camera(object):
	"""GLM Camera implementation with perspective and ortho views.
	A basic Orbit, Pan and Zoom.
	"""

	def __init__(self, position, aspect, near, far, fov=25, ortho=False):
		self._fov = glm.radians(fov)
		self._target = glm.vec3(0.0, 0.0, 0.0)
		self._up = glm.vec3(0, 1, 0)
		self._aspect = aspect
		self._position = position
		self._near = near
		self._far = far
		self.ortho = ortho

		# Setup ortho defaults
		self.left = -10
		self.right = 10
		self.bottom = -10
		self.top = 10
		self.updatePerspective()

	def getMVP(self):
		self.glmview = glm.lookAt(
			self._position,  # Camera is at (4,3,3), in World Space
			self._target,  # glm.vec3(0,0,0) and looks at the origin
			self._up,  # Head is up (set to glm.vec3(0,-1,0) to look upside-down)
		)
		self.targetDistance = glm.length(self._target - self._position)
		self.cameraDirection = glm.normalize(self._position - self._target)
		return self.glmview

	def zoom(self, horizontalAngle, verticalAngle):
		sight_vector = self._target - self._position
		sight_vector = sight_vector / self.targetDistance
		zoom_vector = self.cameraDirection * -horizontalAngle

		delta_dist = glm.dot(sight_vector, zoom_vector)
		which = self.targetDistance - delta_dist
		if which > 0:
			self._position = self._position + zoom_vector
		if which < 0:
			self._position = self._position - zoom_vector

	def pan(self, horizontalAngle, verticalAngle):
		cam_right = glm.cross(self.cameraDirection, glm.normalize(self._up))
		center = cam_right * horizontalAngle + -(verticalAngle * self._up)
		# center.z = 0.0
		pan_xyz = glm.translate(glm.mat4(1), -center)
		self.glmview = self.glmview * pan_xyz

		C = glm.inverse(self.glmview)
		self._position = glm.vec3(C[3])

		self._target = self._position - glm.vec3(C[2]) * self.targetDistance

	def orbit(self, horizontalAngle, verticalAngle):
		pivotView = glm.vec3(self.glmview * glm.vec4(self._target, 1))

		# rotation around the vies pace x axis
		rotViewX = glm.rotate(glm.mat4(1), -verticalAngle, glm.vec3(1, 0, 0))
		rotPivotViewX = (
			glm.translate(glm.mat4(1), pivotView)
			* rotViewX
			* glm.translate(glm.mat4(1), -pivotView)
		)

		# rotation around the world space up vector
		rotWorldUp = glm.rotate(glm.mat4(1), horizontalAngle, glm.vec3(0, 1, 0))
		rotPivotWorldUp = (
			glm.translate(glm.mat4(1), self._target)
			* rotWorldUp
			* glm.translate(glm.mat4(1), -self._target)
		)

		# update view matrix
		glmview = rotPivotViewX * self.glmview * rotPivotWorldUp

		# decode eye, target and up from view matrix
		C = glm.inverse(glmview)
		self._position = glm.vec3(C[3])
		self._target = self._position - glm.vec3(C[2]) * self.targetDistance
		self._up = glm.vec3(C[1])

	def setAspect(self, aspect):
		self._aspect = aspect
		self.updatePerspective()

	def updatePerspective(self):
		# switches based on if we are in ortho mode
		if self.ortho:
			self.perspective = glm.ortho(
				self.left, self.right, self.bottom, self.top, self._near, self._far)
		else:
			self.perspective = glm.perspective(
				self._fov, self._aspect, self._near, self._far
			)

	def frameMesh(self, bmin, bmax, frameFit=1.25):
		self._target = bmin + bmax
		halfFov = self._fov * 0.5 or 0.5  # don't divide by zero
		lengthToFit = max(bmax - bmin) * frameFit * 0.5
		test = lengthToFit / halfFov

		zoom_vector = glm.normalize(self._position - self._target) * test
		self._position = zoom_vector

		self.updatePerspective()


def ticksFromView(camera):
	scale = glm.distance(glm.vec2(camera.left, 0), glm.vec2(camera.right, 0))
	a = 0 if camera.left <= 0 else camera.left - (scale / 2)
	b = 1 if camera.right <= 1 else camera.right + (scale / 2)
	rescale = (scale * 0.033) + 1

	# round to 5's
	pad = 20 # min-max padding
	step = np.around(rescale/5, decimals=0)*5
	a = np.around(a/pad, decimals=0)*pad
	b = np.around(b/pad, decimals=0)*pad

	if step < 5:
		step = 5
		if step < 2:
			step = 1

	array = np.arange(int(a), int(b), int(step), dtype=np.int)
	return array, step
