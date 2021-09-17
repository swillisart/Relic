#version 400
#define M_PI 3.1415926535897932384626433832795
#define M_PI_INV 1.0/3.1415926535897932384626433832795
#define M_GOLDEN_RATIO 1.6180339887498948482045868343656
#define M_FLOAT_EPS 1e-8
#define BSDF vec3

in vec3 fVertexNormal;
in vec3 fVertexPosition;
in vec2 fVertexUv;

// Uniform block: PrivateUniforms
uniform mat4 u_envMatrix = mat4(
    1.000000, 0.000000, 0.000000, 0.000000,
    0.000000, -1.000000, 0.000000, 0.000000,
    0.000000, 0.000000, -1.000000, 0.000000,
    0.000000, 0.000000, 0.000000, -1.000000
);
uniform int u_envRadianceMips = 1;
uniform int u_envRadianceSamples = 16;
uniform sampler2D u_envRadiance;
uniform sampler2D u_envIrradiance;

uniform vec3 u_viewPosition; // camPos
//uniform vec2 frameSize; // Film Back / view resolution
uniform sampler2D tex2D;

out vec4 rgba;

float mx_square(float x)
{
    return x*x;
}

float mx_oren_nayar_diffuse(vec3 L, vec3 V, vec3 N, float NdotL, float roughness)
{
    float LdotV = clamp(dot(L, V), M_FLOAT_EPS, 1.0);
    float NdotV = clamp(dot(N, V), M_FLOAT_EPS, 1.0);
    float s = LdotV - NdotL * NdotV;
    float stinv = (s > 0.0f) ? s / max(NdotL, NdotV) : 0.0;

    float sigma2 = mx_square(roughness * M_PI);
    float A = 1.0 - 0.5 * (sigma2 / (sigma2 + 0.33));
    float B = 0.45 * sigma2 / (sigma2 + 0.09);

    return A + B * stinv;
}
vec3 mx_diffuse_brdf_reflection(vec3 L, vec3 V, float weight, vec3 color, float roughness, vec3 N)
{
    if (weight < M_FLOAT_EPS)
    {
        return vec3(0.0);
    }

    float NdotL = clamp(dot(N, L), M_FLOAT_EPS, 1.0);

    vec3 result = color * weight * NdotL * M_PI_INV;
    if (roughness > 0.0)
    {
        result *= mx_oren_nayar_diffuse(L, V, N, NdotL, roughness);
    }
    return result;
}

vec2 mx_latlong_projection(vec3 dir)
{
    float latitude = -asin(dir.y) * M_PI_INV + 0.5;
    float longitude = atan(dir.x, -dir.z) * M_PI_INV * 0.5 + 0.5;
    return vec2(longitude, latitude);
}

vec3 mx_latlong_map_lookup(vec3 dir, mat4 transform, float lod, sampler2D sampler)
{
    vec3 envDir = normalize((transform * vec4(dir,0.0)).xyz);
    vec2 uv = mx_latlong_projection(envDir);
    return textureLod(sampler, uv, lod).rgb;
}

vec3 mx_environment_irradiance(vec3 N)
{
    return mx_latlong_map_lookup(N, u_envMatrix, 0.0, u_envIrradiance);
}

vec3 mx_diffuse_brdf_indirect(vec3 V, float weight, vec3 color, vec3 N)
{
    if (weight < M_FLOAT_EPS)
    {
        return vec3(0.0);
    }

    vec3 Li = mx_environment_irradiance(N);
    return Li * color * weight;
}

vec2 opU( vec2 d1, vec2 d2 )
{
	return (d1.x<d2.x) ? d1 : d2;
}


void main()
{
    vec3 N = normalize(fVertexNormal);
    vec3 V = normalize(u_viewPosition);
    vec3 P = fVertexPosition;
	
    vec3 Y = vec3(0, 1, 0);
    vec3 X = vec3(1, 0, 0);

    //vec3 light = vec3(0.514434, -0.479014, -0.711269);
    vec3 scene_lights[2] = vec3[2](
        normalize(vec3(-0.479014, 0.711269, 0.514434)) * 1000,
        u_viewPosition
    );

    vec3 irradiance = mx_environment_irradiance(N);
    vec3 color = vec3(2.5);//texture(tex2D, fVertexUv).rgb;
    float roughness = 1.0;
    float weight = 1.0;
    vec3 direct_diffuse = vec3(0.0);
    vec3 direct_spec = vec3(0.0);
    for (int i = 0; i < 1; ++i) {
        vec3 L = normalize(scene_lights[i] - fVertexPosition);
        direct_diffuse += mx_diffuse_brdf_reflection(L, V, weight, color, roughness, N);
    }
    vec3 shader_mix = direct_diffuse;// + irradiance;
    //(gl_FragCoord.x *0.01)
    rgba = vec4(shader_mix.r, shader_mix.g, shader_mix.b, 1.0);
    //rgba = vec4(color.r * irradiance.r, color.g * irradiance.g, color.b * irradiance.b, 1.0);
}