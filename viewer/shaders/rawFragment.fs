in vec2 fVertexUV;
uniform sampler2D tex2D;
uniform float exposure;
uniform float gamma;
out vec4 rgba;
void main()
{
    vec4 col = texture2D(tex2D, fVertexUV);
    vec4 gain = vec4(col.rgb * pow(2.0, exposure), col.w);
    rgba = vec4(pow(gain.rgb, vec3(1.0/gamma)), col.w);
}
