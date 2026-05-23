Shader "Custom/GridPlane"
{
Properties {
        _PlaneColor("Plane Color", Color) = (1, 1, 1, 1) // 地面颜色
        _LineColor("Line Color", Color) = (1, 1, 1, 1) // 线条颜色
        _LineGap("Line Gap", Int) = 1 // 线段间距
        _LineWidth("Line Width", Range(0, 1)) = 0.1 // 线段宽度
        _PlaneCenter("Plane Center", Vector) = (0, 0, 0, 0) // 地面中心
    }
 
    SubShader {
        Pass {
            cull off
            CGPROGRAM
 
            #include "UnityCG.cginc"
            #pragma vertex vert
            #pragma fragment frag
 
            float4 _PlaneColor; // 地面颜色
            float4 _LineColor; // 线条颜色
            int _LineGap; // 线段间距
            float _LineWidth; // 线段宽度
            float4 _PlaneCenter; // 地面中心
 
            struct v2f {
                float4 pos : SV_POSITION; // 裁剪空间顶点坐标
                float2 worldPos : TEXCOORD0; // 世界空间顶点坐标(只包含xz)
            };
 
            v2f vert(float4 vertex: POSITION) {
                v2f o;
                o.pos = UnityObjectToClipPos(vertex); // 模型空间顶点坐标变换到裁剪空间, 等价于: mul(UNITY_MATRIX_MVP, vertex)
                o.worldPos = mul(unity_ObjectToWorld, vertex).xz; // 将模型空间顶点坐标变换到世界空间
                return o;
            }
 
            fixed4 frag(v2f i) : SV_Target {
                float2 vec = abs(i.worldPos - _PlaneCenter.xz);
                float2 mod = fmod(vec, _LineGap);
                float2 xz = min(mod, _LineGap - mod);
                float dist = min(xz.x, xz.y);
                float factor = 1 - smoothstep(0, _LineWidth, dist);
                fixed4 color = lerp(_PlaneColor, _LineColor, factor);
                return fixed4(color.xyz, 1);
            }
 
            ENDCG
        }
    }
}
