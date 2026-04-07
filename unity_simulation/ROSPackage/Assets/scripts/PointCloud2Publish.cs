using RosMessageTypes.Sensor;
using RosMessageTypes.Std;
using System;
using System.Collections;
using System.Collections.Generic;
using Unity.Robotics.ROSTCPConnector;
using UnityEngine;

public class PointCloud2Publish : MonoBehaviour
{
    ROSConnection ros;
    public string topicName = "PC2P1";

    public GameObject target;

    //public DeleteTest test;

    // 传输频率每/秒
    public float publishMessageFrequency = 0.5f;

    private float timeElapsed;

    void Awake()
    {
        //start the ROS connection
        ros = ROSConnection.GetOrCreateInstance();
        ros.RegisterPublisher<PointCloud2Msg>(topicName);
    }

    private void Update()
    {
        //this.transform.position = target.transform.position;
        //if (Input.GetKeyDown(KeyCode.R))
        //{
        //    Debug.LogError("当前时间戳：" + GetTimeStamp());
        //    List<Vector3> dataList = new List<Vector3>();

        //    int num = UnityEngine.Random.Range(3, 10);

        //    Debug.Log("随机数据长度： " + num);
        //    byte[] d = new byte[0];
        //    for (int i = 0; i < num; i++)
        //    {
        //        dataList.Add(new Vector3(UnityEngine.Random.Range(10, 500), UnityEngine.Random.Range(10, 500), UnityEngine.Random.Range(10, 500)));
        //        d = SetPfmData(d, dataList[dataList.Count - 1].x, dataList[dataList.Count - 1].y, dataList[dataList.Count - 1].z);
        //    }
        //    Debug.Log("数据长度： " + d.Length);
        //}
    }

    private static long GetTimeStamp()
    {
        return ((System.DateTime.Now.ToUniversalTime().Ticks - 621355968000000000) / 10000000);
    }

    public void SendMessage_Ros(List<Vector3> dataList)
    {
        //if (topicName == "PC2P1") test.PC1List = dataList;
        //else test.PC2List = dataList;

        PointCloud2Msg pc2m = new PointCloud2Msg();

        //固定数据传输
        HeaderMsg hm = new HeaderMsg("map");
        pc2m.height = 1;
        pc2m.width = (uint)dataList.Count;
        pc2m.point_step = 12;
        pc2m.row_step = pc2m.point_step * pc2m.width;

        byte[] data = new byte[0];
        for (int i = 0; i < dataList.Count; i++)
        {
            float lat = dataList[i].z - transform.position.z;
            float lon = dataList[i].x - transform.position.x;
            //data = SetPfmData(data, lat, lon, dataList[i].y);
            data = SetPfmData(data, lat, lon, 0);
        }
        //Debug.Log(dataList.Count + "  数据长度： " + data.Length);

        pc2m.SetPointCloud2Data(hm, InitPointFieldMsg(), data);

        ros.Publish(topicName, pc2m);
    }

    public void SendMessage_Ros2(List<Vector3> dataList)
    {
        PointCloud2Msg pc2m = new PointCloud2Msg();

        //固定数据传输
        HeaderMsg hm = new HeaderMsg("map");
        pc2m.height = 1;
        pc2m.width = (uint)dataList.Count;
        pc2m.point_step = 12;
        pc2m.row_step = pc2m.point_step * pc2m.width;

        byte[] data = new byte[0];
        for (int i = 0; i < dataList.Count; i++)
        {
            float lat = dataList[i].z - transform.position.z;
            float lon = dataList[i].x - transform.position.x;
            data = SetPfmData(data, lat, lon, dataList[i].y);
        }
        //Debug.Log(dataList.Count + "  数据长度： " + data.Length);

        pc2m.SetPointCloud2Data(hm, InitPointFieldMsg(), data);

        ros.Publish(topicName, pc2m);
    }

    private PointFieldMsg[] InitPointFieldMsg()
    {
        PointFieldMsg[] data = new PointFieldMsg[3];
        data[0] = new PointFieldMsg("x", 0, 7, 1);
        data[1] = new PointFieldMsg("y", 4, 7, 1);
        data[2] = new PointFieldMsg("z", 8, 7, 1);
        return data;
    }

    private byte[] SetPfmData(byte[] data, float x, float y, float z)
    {
        data = JoinArray(data, BitConverter.GetBytes(x));
        data = JoinArray(data, BitConverter.GetBytes(y));
        data = JoinArray(data, BitConverter.GetBytes(z));
        return data;
    }

    private byte[] JoinArray(byte[] byte1, byte[] byte2)
    {
        byte[] finalBytes = new byte[byte1.Length + byte2.Length];
        Array.Copy(byte1, 0, finalBytes, 0, byte1.Length);
        Array.Copy(byte2, 0, finalBytes, byte1.Length, byte2.Length);

        return finalBytes;
    }
}