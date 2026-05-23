using UnityEngine;
//using WebSocketSharp;

public class ROSWebSocketClient : MonoBehaviour
{
    //private WebSocket ws;

    void Start()
    {
        //ws = new WebSocket("ws://192.168.94.151:9090"); // ROS bridge WebSocket地址
        //ws.OnMessage += (sender, e) =>
        //{
        //    Debug.Log("Received: " + e.Data);
        //    // 处理接收到的消息
        //};
        //ws.Connect();
    }

    void Update()
    {
        // 可以在这里发送消息到ROS
    }

    void OnDestroy()
    {
        //ws.Close();
    }
}