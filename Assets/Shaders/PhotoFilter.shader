Shader "Hidden/PhotoFilter"
{
    Properties
    {
        _MainTex ("Texture", 2D) = "white" {}
        _Brightness ("Brightness", Float) = 1.0
        _Contrast ("Contrast", Float) = 1.0
        _Saturation ("Saturation", Float) = 1.0
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" }
        LOD 100
        Cull Off ZWrite Off ZTest Always

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag

            #include "UnityCG.cginc"

            struct appdata
            {
                float4 vertex : POSITION;
                float2 uv : TEXCOORD0;
            };

            struct v2f
            {
                float2 uv : TEXCOORD0;
                float4 vertex : SV_POSITION;
            };

            sampler2D _MainTex;
            float _Brightness;
            float _Contrast;
            float _Saturation;

            v2f vert (appdata v)
            {
                v2f o;
                o.vertex = UnityObjectToClipPos(v.vertex);
                o.uv = v.uv;
                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
                fixed4 col = tex2D(_MainTex, i.uv);

                // Brightness
                col.rgb *= _Brightness;

                // Contrast
                col.rgb = (col.rgb - 0.5) * _Contrast + 0.5;

                // Saturation (BT.709 luminance)
                float lum = dot(col.rgb, float3(0.2126, 0.7152, 0.0722));
                col.rgb = lerp(float3(lum, lum, lum), col.rgb, _Saturation);

                col.rgb = saturate(col.rgb);
                return col;
            }
            ENDCG
        }
    }
}
