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

    // ����Ƶ��ÿ/��
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
            Debug.Log("��������");
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
            Debug.LogError("GPU��ȡʧ��");
            return;
        }

        // ֱ�Ӵ������л�ȡԭʼ���ֽ����ݣ�ÿ����3�ֽڣ�RGB˳��
        byte[] rawBytes = request.GetData<byte>().ToArray();

        // ��תͼ�����µߵ���
        byte[] flippedData = FlipImageData(rawBytes, cameraData.width, cameraData.height, 3);

        // ����ROS��Ϣ
        ImageMsg imgData = new ImageMsg();
        HeaderMsg hm = new HeaderMsg();
        hm.frame_id = "image";

        imgData.height = (uint)cameraData.height;
        imgData.width = (uint)cameraData.width;
        imgData.encoding = "rgb8";                      // 3ͨ��8λRGB
        imgData.is_bigendian = (byte)(System.BitConverter.IsLittleEndian ? 0 : 1);
        imgData.step = imgData.width * 3;                // һ�е��ֽ�����RGBÿ������3�ֽڣ�
        imgData.data = flippedData;

        // ��ѡ��־
        Debug.Log($"���ݳ���: {flippedData.Length}, step: {imgData.step}, height: {imgData.height}");

        ros.Publish(topicName, imgData);
    }

    /// <summary>
    /// ��ͼ���������·�ת���������ţ�
    /// </summary>
    /// <param name="originalData">ԭʼ�ֽ����飬���д洢��ÿ���� channel �ֽ�</param>
    /// <param name="width">ͼ����ȣ����أ�</param>
    /// <param name="height">ͼ��߶ȣ����أ�</param>
    /// <param name="channels">ÿ�����ֽ���������RGBΪ3��</param>
    /// <returns>��ת����ֽ�����</returns>
    private byte[] FlipImageData(byte[] originalData, int width, int height, int channels)
    {
        int rowBytes = width * channels;               // ÿ�е��ֽ���
        byte[] flipped = new byte[originalData.Length]; // ��������С��ͬ

        for (int y = 0; y < height; y++)
        {
            // Դ�У�ԭͼ�ĵ� y �У��ӵײ�0��ʼ�� �� Ŀ���У���ת��ĵ� (height - 1 - y) �У��Ӷ���0��ʼ��
            int sourceIndex = y * rowBytes;
            int targetIndex = (height - 1 - y) * rowBytes;

            // ����һ����
            System.Array.Copy(originalData, sourceIndex, flipped, targetIndex, rowBytes);
        }

        return flipped;
    }
}
