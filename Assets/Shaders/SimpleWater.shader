Shader "Nidelven/SimpleWater"
{
    Properties
    {
        _BaseColor ("Base Color", Color) = (0.2, 0.4, 0.6, 0.8)
        _FoamColor ("Foam Color", Color) = (0.9, 0.95, 1.0, 1.0)
        _WaveHeight ("Wave Height", Float) = 0.3
        _WaveSpeed ("Wave Speed", Float) = 2.0
        _WaveScale ("Wave Scale", Float) = 10.0
        _FoamThreshold ("Foam Threshold", Float) = 0.5
        _FlowSpeed ("Flow Speed", Float) = 1.0
        _FlowOffset ("Flow Offset", Vector) = (0, 0, 0, 0)
        _Smoothness ("Smoothness", Range(0, 1)) = 0.9
    }
    
    SubShader
    {
        Tags 
        { 
            "RenderType" = "Transparent" 
            "Queue" = "Transparent"
            "RenderPipeline" = "UniversalPipeline"
        }
        
        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode" = "UniversalForward" }
            
            Blend SrcAlpha OneMinusSrcAlpha
            ZWrite Off
            Cull Back
            
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            
            struct Attributes
            {
                float4 positionOS : POSITION;
                float2 uv : TEXCOORD0;
                float3 normalOS : NORMAL;
            };
            
            struct Varyings
            {
                float4 positionHCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                float2 uv : TEXCOORD1;
                float3 normalWS : TEXCOORD2;
                float4 positionNDC : TEXCOORD3;
            };
            
            CBUFFER_START(UnityPerMaterial)
                float4 _BaseColor;
                float4 _FoamColor;
                float _WaveHeight;
                float _WaveSpeed;
                float _WaveScale;
                float _FoamThreshold;
                float _FlowSpeed;
                float4 _FlowOffset;
                float _Smoothness;
            CBUFFER_END
            
            // Simple noise function
            float2 hash22(float2 p)
            {
                float3 p3 = float3(dot(p, float2(127.1, 311.7)), dot(p, float2(269.5, 183.3)), 0.0);
                return frac(sin(p3) * 43758.5453);
            }
            
            float noise(float2 p)
            {
                float2 i = floor(p);
                float2 f = frac(p);
                f = f * f * (3.0 - 2.0 * f);
                
                float a = hash22(i).x;
                float b = hash22(i + float2(1.0, 0.0)).x;
                float c = hash22(i + float2(0.0, 1.0)).x;
                float d = hash22(i + float2(1.0, 1.0)).x;
                
                return lerp(lerp(a, b, f.x), lerp(c, d, f.x), f.y);
            }
            
            float CalculateWaveHeight(float2 uv, float time)
            {
                float wave = 0.0;
                float2 pos = uv * _WaveScale;
                
                // Layered waves
                wave += sin(pos.x + time * _WaveSpeed) * 0.5;
                wave += cos(pos.y * 0.7 + time * _WaveSpeed * 0.8) * 0.3;
                wave += sin((pos.x + pos.y) * 1.5 + time * _WaveSpeed * 1.2) * 0.2;
                
                // Add noise detail
                wave += noise(pos + time * 0.5) * 0.1;
                
                return wave * _WaveHeight;
            }
            
            Varyings vert(Attributes input)
            {
                Varyings output;
                
                float3 positionOS = input.positionOS.xyz;
                
                // Calculate wave displacement
                float waveHeight = CalculateWaveHeight(input.uv, _Time.y);
                positionOS.y += waveHeight;
                
                // Transform to world space
                VertexPositionInputs posInputs = GetVertexPositionInputs(positionOS);
                
                // Calculate normal from wave derivative
                float waveHeightX = CalculateWaveHeight(input.uv + float2(0.01, 0.0), _Time.y);
                float waveHeightZ = CalculateWaveHeight(input.uv + float2(0.0, 0.01), _Time.y);
                float3 tangentX = float3(0.01, waveHeightX - waveHeight, 0.0);
                float3 tangentZ = float3(0.0, waveHeightZ - waveHeight, 0.01);
                float3 waveNormal = normalize(cross(tangentZ, tangentX));
                
                output.positionHCS = posInputs.positionCS;
                output.positionWS = posInputs.positionWS;
                output.uv = input.uv;
                output.normalWS = TransformObjectToWorldNormal(waveNormal);
                output.positionNDC = posInputs.positionNDC;
                
                return output;
            }
            
            float4 frag(Varyings input) : SV_Target
            {
                // View direction
                float3 viewDirWS = GetWorldNormalizeViewDir(input.positionWS);
                
                // Normal
                float3 normalWS = normalize(input.normalWS);
                
                // Calculate flow foam
                float2 flowUV = input.uv + _FlowOffset.xy;
                float flowNoise = noise(flowUV * _WaveScale * 2.0 + float2(_Time.y * _FlowSpeed, 0.0));
                float foam = smoothstep(_FoamThreshold - 0.1, _FoamThreshold + 0.1, flowNoise);
                
                // Base color with flow variation
                float flowVariation = noise(flowUV * _WaveScale + float2(_Time.y * _FlowSpeed, 0.0));
                float4 baseColor = lerp(_BaseColor * 0.8, _BaseColor, flowVariation);
                
                // Add foam
                float4 finalColor = lerp(baseColor, _FoamColor, foam * 0.3);
                
                // Specular highlight
                float3 lightDir = normalize(_MainLightPosition.xyz);
                float3 halfDir = normalize(lightDir + viewDirWS);
                float specAngle = max(dot(normalWS, halfDir), 0.0);
                float specular = pow(specAngle, 128.0) * _Smoothness;
                finalColor.rgb += specular;
                
                // Fresnel
                float fresnel = pow(1.0 - max(dot(viewDirWS, normalWS), 0.0), 3.0);
                finalColor = lerp(finalColor, _FoamColor, fresnel * 0.2);
                
                // Simple lighting
                float ndotl = saturate(dot(normalWS, lightDir));
                finalColor.rgb *= (0.4 + ndotl * 0.6);
                
                return finalColor;
            }
            ENDHLSL
        }
    }
}
