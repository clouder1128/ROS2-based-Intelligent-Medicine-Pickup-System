using RosMessageTypes.Sensor;
using RosMessageTypes.Std;
using System;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using Unity.Robotics.ROSTCPConnector;
using Unity.VisualScripting;
using UnityEngine;
using static UnityEngine.GraphicsBuffer;
using UnityEngine.Rendering;
using UnityEngine.UI;

public class ROSImagePublish : MonoBehaviour
{
    ROSConnection ros;
    public string topicName = "RosImage";

    public RawImage showImage;

    public RenderTexture cameraData;

    // 传输频率每/秒
    public float publishMessageFrequency = 0.5f;

    void Awake()
    {
        //start the ROS connection
        ros = ROSConnection.GetOrCreateInstance();
        ros.RegisterPublisher<ImageMsg>(topicName);
    }

    private void Update()
    {
        if (Input.GetKeyDown(KeyCode.Q))
        {
            Debug.Log("发送数据");
            SendMessage_Ros();
        }
    }

    public void SendMessage_Ros()
    {
        
        AsyncGPUReadback.Request(cameraData, 0, TextureFormat.RGB24, OnCompleteReadback);
    }

    private void OnCompleteReadback(AsyncGPUReadbackRequest request)
    {
        if (request.hasError)
        {
            Debug.LogError("GPU读取失败");
            return;
        }

        // 直接从请求中获取原始的字节数据（每像素3字节，RGB顺序）
        byte[] rawBytes = request.GetData<byte>().ToArray();

        // 翻转图像（上下颠倒）
        byte[] flippedData = FlipImageData(rawBytes, cameraData.width, cameraData.height, 3);

        // 构建ROS消息
        ImageMsg imgData = new ImageMsg();
        HeaderMsg hm = new HeaderMsg("image"); // 如果HeaderMsg需要时间戳，请自行设置

        imgData.height = (uint)cameraData.height;
        imgData.width = (uint)cameraData.width;
        imgData.encoding = "rgb8";                      // 3通道8位RGB
        imgData.is_bigendian = (byte)(System.BitConverter.IsLittleEndian ? 0 : 1);
        imgData.step = imgData.width * 3;                // 一行的字节数（RGB每个像素3字节）
        imgData.data = flippedData;

        // 可选日志
        Debug.Log($"数据长度: {flippedData.Length}, step: {imgData.step}, height: {imgData.height}");

        ros.Publish(topicName, imgData);
    }

    /// <summary>
    /// 将图像数据上下翻转（按行重排）
    /// </summary>
    /// <param name="originalData">原始字节数组，按行存储，每像素 channel 字节</param>
    /// <param name="width">图像宽度（像素）</param>
    /// <param name="height">图像高度（像素）</param>
    /// <param name="channels">每像素字节数（例如RGB为3）</param>
    /// <returns>翻转后的字节数组</returns>
    private byte[] FlipImageData(byte[] originalData, int width, int height, int channels)
    {
        int rowBytes = width * channels;               // 每行的字节数
        byte[] flipped = new byte[originalData.Length]; // 输出数组大小相同

        for (int y = 0; y < height; y++)
        {
            // 源行：原图的第 y 行（从底部0开始） → 目标行：翻转后的第 (height - 1 - y) 行（从顶部0开始）
            int sourceIndex = y * rowBytes;
            int targetIndex = (height - 1 - y) * rowBytes;

            // 复制一整行
            System.Array.Copy(originalData, sourceIndex, flipped, targetIndex, rowBytes);
        }

        return flipped;
    }
}
