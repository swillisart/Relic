#version 330 core
in layout(location = 0) vec3 vertexPosition;
in layout(location = 1) vec3 vertexNormal;
in layout(location = 2) vec2 vertexUv;

uniform mat4 MVP;

out vec3 fVertexNormal;
out vec3 fVertexPosition;
out vec2 fVertexUv;

void main()
{
    gl_Position = MVP * vec4(vertexPosition, 1);
    fVertexNormal = vertexNormal;
    fVertexPosition = vertexPosition;
    // flipV
    fVertexUv = vertexUv.st * vec2(-1.0, 1.0);
}