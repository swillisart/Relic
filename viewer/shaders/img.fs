#version 330 core
in vec2 fVertexUV;

uniform sampler2D tex2D;

out vec4 rgba;

void main()
{
    rgba = texture2D(tex2D, fVertexUV);
}
