from ctypes import c_void_p

# Third-party
from OpenGL.GL import *
from OpenGL.GL.shaders import compileShader, compileProgram, ShaderProgram

import glm



class BaseProgram(ShaderProgram):
	"""
	Example
	--------
	shader = BaseProgram.fromGlsl(
		vertex_shader_text,
		fragment_shader_text,
	)
	shader.setUniforms('MVP', 'UV', 'color')
	"""

	@classmethod
	def fromGlsl(cls, vertex, fragment):
		"""Create a new program, attach shaders and validates

		Parameters
		----------
		vertex : str
			vertex shader (glsl)
		fragment : str
			fragment shader (glsl)

		Returns
		-------
		OpenGL.GL.shaders.ShaderProgram
			the compiled shader object
		"""
		vs = compileShader(vertex, GL_VERTEX_SHADER)
		fs = compileShader(fragment, GL_FRAGMENT_SHADER)
		program = glCreateProgram()
		glAttachShader(program, vs)
		glAttachShader(program, fs)
		obj = cls(program)
		glLinkProgram(obj)
		obj.check_linked()
		# Clean up 
		glDeleteShader(vs)
		glDeleteShader(fs)
		return obj

	def setUniforms(self, *uniforms):
		for uniform in uniforms:
			location = glGetUniformLocation(self, uniform)
			setattr(self, uniform, location)
