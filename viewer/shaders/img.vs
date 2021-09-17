#version 330 core
in layout(location = 0) vec3 vertexPosition;
in layout(location = 1) vec2 vertexUV;

uniform mat4 MVP;

out vec2 fVertexUV;
out vec3 fVertexPosition;
void main()
{
    gl_Position = MVP * vec4(vertexPosition, 1);
    fVertexUV = vertexUV;
    fVertexPosition = vertexPosition;
}