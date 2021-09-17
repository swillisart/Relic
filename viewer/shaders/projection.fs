in vec2 fVertexUV;
in vec4 textureCoordProj;

uniform sampler2D tex2D;
layout(location = 0) out vec4 rgba;
void main()
{
    vec4 texturedrgba = texture2D(tex2D, fVertexUV);
    rgba = texturedrgba;
}
