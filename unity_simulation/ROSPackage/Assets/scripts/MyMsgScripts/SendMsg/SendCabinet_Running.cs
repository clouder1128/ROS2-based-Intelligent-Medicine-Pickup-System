using RosMessageTypes.Std;
using RosMessageTypes.Task;
using System.Collections;
using System.Collections.Generic;
using Unity.Robotics.ROSTCPConnector;
using UnityEngine;


public class SendCabinet_Running : MonoBehaviour
{
    ROSConnection ros;
    public string topicName = "CabinetRunning_U";

    // ¥´ ‰∆µ¬ √ø/√Î
    public float publishMessageFrequency = 1f;

    void Awake()
    {
        //start the ROS connection
        ros = ROSConnection.GetOrCreateInstance();
        ros.RegisterPublisher<CabinetRunningMsg>(topicName);
        //StartCoroutine(SendMessage());
    }

    IEnumerator SendMessage()
    {
        while (true)
        {
            SendMessage_Ros((byte)Random.Range(0,50), (byte)Random.Range(0, 2));
            yield return new WaitForSeconds(publishMessageFrequency);
        }
    }

    public void SendMessage_Ros(byte ID, byte isRunning)
    {
        CabinetRunningMsg Msg = new CabinetRunningMsg();
        Msg.cabinet_id = ID;
        Msg.isrunning = isRunning;

        ros.Publish(topicName, Msg);
    }
}
