using RosMessageTypes.Task;
using System.Collections;
using System.Collections.Generic;
using Unity.Robotics.ROSTCPConnector;
using UnityEngine;

public class SendCarState : MonoBehaviour
{
    ROSConnection ros;
    public string topicName = "CarState_U";

    // ¥´ ‰∆µ¬ √ø/√Î
    public float publishMessageFrequency = 1f;

    void Awake()
    {
        //start the ROS connection
        ros = ROSConnection.GetOrCreateInstance();
        ros.RegisterPublisher<CarStateMsg>(topicName);
        //StartCoroutine(SendMessage());
    }

    IEnumerator SendMessage()
    {
        while (true)
        {
            //SendMessage_Ros((byte)Random.Range(0, 50));
            yield return new WaitForSeconds(publishMessageFrequency);
        }
    }

    public void SendMessage_Ros(byte ID,byte isrunning,Transform carPos)
    {
        CarStateMsg Msg = new CarStateMsg();
        Msg.car_id = ID;
        Msg.x = carPos.position.x;
        Msg.y = carPos.position.z;
        Msg.isrunning = isrunning;
        //Msg.medicine_list;

        ros.Publish(topicName, Msg);
    }
}
