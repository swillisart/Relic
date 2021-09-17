#version 430
in layout(location = 0) vec3 vertexPosition;
in layout(location = 1) vec2 vertexUV;

uniform mat4 MVP;
uniform mat4 textureMatrix;

out vec2 fVertexUV;
out vec3 fVertexPosition;
out vec4 textureCoordProj;
void main()
{
    textureCoordProj = textureMatrix * vec4(vertexPosition, 1);
    gl_Position = MVP * vec4(vertexPosition, 1);
    fVertexUV = vertexUV;
    fVertexPosition = vertexPosition;
}