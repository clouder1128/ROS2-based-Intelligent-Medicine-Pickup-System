using UnityEngine;

public class FixedAspectRatio : MonoBehaviour
{
    private Camera mainCamera;
    private float targetAspect = 16f / 9f; // 16:9比例

    void Start()
    {
        mainCamera = GetComponent<Camera>();
        UpdateCameraViewport();
    }

    void Update()
    {
        // 监听窗口大小变化
        if (Screen.width != lastScreenWidth || Screen.height != lastScreenHeight)
        {
            lastScreenWidth = Screen.width;
            lastScreenHeight = Screen.height;
            UpdateCameraViewport();
        }
    }

    private int lastScreenWidth = 0;
    private int lastScreenHeight = 0;

    void UpdateCameraViewport()
    {
        // 计算当前窗口的宽高比
        float windowAspect = (float)Screen.width / (float)Screen.height;

        // 计算缩放比例
        float scaleHeight = windowAspect / targetAspect;

        Rect rect = new Rect(0, 0, 1, 1);

        if (scaleHeight < 1.0f) // 窗口比16:9更宽
        {
            rect.width = 1.0f;
            rect.height = scaleHeight;
            rect.y = (1.0f - scaleHeight) / 2.0f;
        }
        else // 窗口比16:9更高
        {
            float scaleWidth = 1.0f / scaleHeight;
            rect.width = scaleWidth;
            rect.height = 1.0f;
            rect.x = (1.0f - scaleWidth) / 2.0f;
        }

        mainCamera.rect = rect;
    }
}
