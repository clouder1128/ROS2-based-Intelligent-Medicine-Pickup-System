using RosMessageTypes.Std;
using RosMessageTypes.Task;
using System.Collections;
using System.Collections.Generic;
using Unity.Robotics.ROSTCPConnector;
using UnityEngine;

public class SendTaskMsg : MonoBehaviour
{
    ROSConnection ros;
    public string topicName = "TaskData_U";

    // 传输频率每/秒
    public float publishMessageFrequency = 1f;

    void Awake()
    {
        //start the ROS connection
        ros = ROSConnection.GetOrCreateInstance();
        ros.RegisterPublisher<TaskMsg>(topicName);
        StartCoroutine(SendMessage());
    }

    IEnumerator SendMessage()
    {
        while (true)
        {
            SendMessage_Ros();
            yield return new WaitForSeconds(publishMessageFrequency);
        }
    }

    public void SendMessage_Ros()
    {
        TaskMsg task = new TaskMsg();
        CabinetOrderMsg[] ca = new CabinetOrderMsg[3];
        ca[0] = new CabinetOrderMsg();
        ca[0].cabinet_id = 1.ToString();
        ca[0].medicine_list = new MedicineDataMsg[3];
        ca[0].medicine_list[0] = new MedicineDataMsg(1,2,3);
        ca[0].medicine_list[1] = new MedicineDataMsg(3,2,3);
        ca[0].medicine_list[2] = new MedicineDataMsg(5,2,3);
        ca[1] = new CabinetOrderMsg();
        ca[2] = new CabinetOrderMsg();
        //固定数据传输
        task.task_id = Random.Range(0, 100).ToString();
        task.cabinets = ca;
        task.type = Random.Range(0, 3).ToString();

        ros.Publish(topicName, task);
    }
}
