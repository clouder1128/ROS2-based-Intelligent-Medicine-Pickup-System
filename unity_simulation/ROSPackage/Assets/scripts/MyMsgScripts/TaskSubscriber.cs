using RosMessageTypes.Task;
using System.Collections;
using System.Collections.Generic;
using Unity.Robotics.ROSTCPConnector;
using UnityEngine;

public class TaskSubscriber : MonoBehaviour
{
    public List<TaskMsg> TaskList;
    public List<TaskData> TaskListData;

    public CanvasManager canvas;
    [SerializeField]
    private string topicName = "/unity_commands";

    void Start()
    {
        TaskListData = new List<TaskData>();
        TaskList = new List<TaskMsg>();
        // 订阅 PoseStamped 消息
        ROSConnection.GetOrCreateInstance().Subscribe<TaskMsg>(
            topicName,
            PoseCallback);
    }

    void PoseCallback(TaskMsg poseMsg)
    {
        for (int i = 0; i < TaskList.Count; i++)
        {
            if (poseMsg.task_id == TaskList[i].task_id)
            {
                return;
            }
        }
        TaskList.Add(poseMsg);

        TaskListData.Add(new TaskData(poseMsg, 0, 200, 0));
        TaskListData[TaskListData.Count - 1].TaskUnityID = TaskListData.Count - 1;
        //Debug.Log($"位置: {poseMsg.task_id}, 旋转: {poseMsg.type}" + poseMsg.cabinets.Length);
        SceneManager.IsRefreshTask = true;
    }
}

public class TaskData
{
    public TaskMsg taskMsg;
    //0-未执行 1-执行中 2-执行结束
    public int TaskState;
    public int TaskCarID;
    public int TaskUnityID;

    public TaskData(TaskMsg msg,int state,int catId,int unityID)
    {
        taskMsg = msg;
        TaskState = state;
        TaskCarID = -1;
        TaskUnityID = unityID;


    }
}