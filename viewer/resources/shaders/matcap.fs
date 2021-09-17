#version 330 core
in vec3 fVertexNormal;
in vec3 fVertexPosition;

uniform vec3 lightPosition;
uniform sampler2D tex2D;

out vec4 color;

vec2 matcap(vec3 eye, vec3 normal) {
	vec3 r = reflect(eye, normal);
	float m = 2.0 * sqrt( pow( r.x, 2.0 ) + pow( r.y, 2.0 ) + pow( r.z + 1.0, 2.0 ) );
	vec2 vN = r.xy / m + 0.5;
	return vN;
}

void main()
{
	vec2 uv = matcap(lightPosition, fVertexNormal).xy;
  	color = vec4(texture2D(tex2D, uv).rgb, 1.0);
}