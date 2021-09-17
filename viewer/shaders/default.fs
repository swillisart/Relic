#version 330 core
in vec3 fVertexNormal;
in vec3 fVertexPosition;
in vec2 fVertexUv;

uniform vec3 lightPosition;

out vec4 color;

void main()
{
    vec3 lightDir = normalize(lightPosition - fVertexPosition);
    float diff = max(dot(fVertexNormal, lightDir), 0.0) * 0.6;
    color = vec4(diff, diff, diff, 1.0f);
}