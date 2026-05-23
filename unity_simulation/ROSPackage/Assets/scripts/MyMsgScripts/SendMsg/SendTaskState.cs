using RosMessageTypes.Task;
using System.Collections;
using System.Collections.Generic;
using Unity.Robotics.ROSTCPConnector;
using UnityEngine;

public class SendTaskState : MonoBehaviour
{
    ROSConnection ros;
    public string topicName = "TaskState_U";

    // ¥´ ‰∆µ¬ √ø/√Î
    public float publishMessageFrequency = 1f;

    void Awake()
    {
        //start the ROS connection
        ros = ROSConnection.GetOrCreateInstance();
        ros.RegisterPublisher<TaskStateMsg>(topicName);
        //StartCoroutine(SendMessage());
    }


    IEnumerator SendMessage()
    {
        while (true)
        {
            yield return new WaitForSeconds(1);
            SendMessage_Ros(1);
        }
    }

    public void SendMessage_Ros(byte ID)
    {
        TaskStateMsg Msg = new TaskStateMsg();
        //Msg.task_id = "001";
        Msg.task_state = 1;
        Msg.car_id = 2;

        ros.Publish(topicName, Msg);
    }

    public void SendMessage_Ros(TaskStateMsg data)
    {

        ros.Publish(topicName, data);
    }
}
