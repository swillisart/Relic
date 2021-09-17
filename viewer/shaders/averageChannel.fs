in vec2 fVertexUV;
uniform sampler2D tex2D;
uniform sampler3D tex3D;
uniform float exposure;
uniform float gamma;
out vec4 rgba;
void main()
{
    vec4 col = texture2D(tex2D, fVertexUV);
    vec4 gain = vec4(col.rgb * pow(2.0, exposure), col.w);
    vec4 knee = vec4(pow(gain.rgb, vec3(1.0/gamma)), col.w);
    vec4 ocio_transformed = OCIODisplay(knee, tex3D);
    float avg = (ocio_transformed.r + ocio_transformed.g + ocio_transformed.b) / 3.0;
    rgba = vec4(vec3(avg), 1.0);
}