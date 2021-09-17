in vec2 fVertexUV;

uniform sampler2D framebufferTexture;
uniform sampler3D tex3D;

uniform float exposure;
uniform float gamma;

out vec4 out_rgba;

void main()
{
    vec4 rgba = texture(framebufferTexture, fVertexUV);
    vec4 gain = vec4(rgba.rgb * pow(2.0, exposure), rgba.a);
    vec4 knee = vec4(pow(gain.rgb, vec3(1.0/gamma)), rgba.a);
    out_rgba = OCIODisplay(knee, tex3D);
}