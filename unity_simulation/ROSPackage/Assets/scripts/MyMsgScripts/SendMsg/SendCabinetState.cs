using RosMessageTypes.Task;
using System.Collections;
using System.Collections.Generic;
using Unity.Robotics.ROSTCPConnector;
using UnityEngine;

public class SendCabinetState : MonoBehaviour
{
    ROSConnection ros;
    public string topicName = "CabinetState_U";

    // ¥´ ‰∆µ¬ √ø/√Î
    public float publishMessageFrequency = 1f;

    void Awake()
    {
        //start the ROS connection
        ros = ROSConnection.GetOrCreateInstance();
        ros.RegisterPublisher<CabinetStateMsg>(topicName);
        //StartCoroutine(SendMessage());
    }



    public void SendMessage_Ros(byte ID)
    {
        CabinetStateMsg Msg = new CabinetStateMsg();
        Msg.cabinet_id = ID;

        ros.Publish(topicName, Msg);
    }
    public void SendMessage_Ros(CabinetStateMsg data)
    {
        CabinetStateMsg Msg = data;

        ros.Publish(topicName, Msg);
    }
}
