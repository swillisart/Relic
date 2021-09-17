#version 330 core
in layout(location = 0) vec3 vertexPosition;
in layout(location = 1) vec2 vertexUV;

out vec2 fVertexUV;

void main()
{
    gl_Position = vec4(vertexPosition, 1.0);
    fVertexUV = vertexUV;
}