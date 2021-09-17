in vec2 fVertexUV;

uniform sampler2D tex2D;
uniform sampler3D tex3D;

uniform float exposure;
uniform float gamma;

out vec4 rgba;

void main()
{
    vec4 texturedrgba = texture2D(tex2D, fVertexUV);
    vec4 gain = vec4(texturedrgba.rgb * pow(2.0, exposure), texturedrgba.w);
    vec4 knee = vec4(pow(gain.rgb, vec3(1.0/gamma)), texturedrgba.w);
    rgba = OCIODisplay(knee, tex3D);
}