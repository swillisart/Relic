#version 400
in layout(location = 0) vec3 vertexPosition;
in layout(location = 1) vec3 vertexColor;

uniform mat4 MVP;

out vertex {
    vec3 position;
    vec3 color;
} verts;

void main()
{
    gl_Position = MVP * vec4(vertexPosition, 1);
    verts.position = vertexPosition;
    verts.color = vertexColor;
}