#version 400
in vertex {
    vec3 position;
    vec3 color;
} verts;

out vec4 rgba;

void main()
{
    rgba = vec4(verts.color, 1);
}