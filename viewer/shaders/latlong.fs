#version 330 core
in vec3 fVertexNormal;
in vec3 fVertexPosition;
in vec2 fVertexUv;
in vec2 uv0;
in vec2 uv1;

uniform sampler2D tex2D;

out vec4 rgba;

void main()
{
    vec2 uvT;
    uvT.x = ( fwidth( uv0.x ) < fwidth( uv1.x )-0.001 )? uv0.x : uv1.x;
    uvT.y = ( fwidth( uv0.y ) < fwidth( uv1.y )-0.001 )? uv0.y : uv1.y;
    rgba = texture2D(tex2D, uvT * vec2(-1, 1));
}