#version 400
in layout(location = 0) vec3 i_position;
in layout(location = 1) vec3 i_normal;
in layout(location = 2) vec2 i_texcoord_0;
in layout(location = 3) vec3 i_tangent;

uniform mat4 MVP;

out VertexData
{
    vec3 tangentWorld;
    vec3 positionWorld;
    vec3 normalWorld;
    vec2 texcoord_0;
} vd;

void main()
{
    gl_Position = MVP * vec4(i_position, 1);
    //vec3 bitangent = cross(tangent, normal);
    vd.tangentWorld = i_tangent;
    vd.positionWorld = i_position;
    vd.normalWorld = i_normal;
    vd.texcoord_0 = i_texcoord_0.st * vec2(-1.0, 1.0); // flipV
}
