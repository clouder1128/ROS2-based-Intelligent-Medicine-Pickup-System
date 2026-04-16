using RosMessageTypes.Task;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class SendMsgManager : MonoBehaviour
{
    public SendCabinetState sendCabinetState;
    public SendCabinet_Running sendCabinetRunning;
    public SendCarState sendCarState;
    public SendTaskState sendTaskState;

    public float SendCarTime = 1;
    public float SendCabinetsRunningTime = 1.2f;
    public float SendCabinetsStateTime = 1.5f;
    public float SendTaskTime = 2;
    void Start()
    {
        StartCoroutine(SendCarMessage());

        StartCoroutine(SendCabinetsRunningMessage());
        StartCoroutine(SendCabinetsStateMessage());
        StartCoroutine(SendTaskMessage());
    }

    IEnumerator SendCarMessage()
    {
        while (true)
        {
            yield return new WaitForSeconds(SendCarTime);
            SendCarState();
            //SendCabinetsRunning();
            //SendCabinetsState();
            //SendTaskState();
        }
    }

    IEnumerator SendCabinetsRunningMessage()
    {
        while (true)
        {
            yield return new WaitForSeconds(SendCabinetsRunningTime);
            SendCabinetsRunning();
        }
    }

    IEnumerator SendCabinetsStateMessage()
    {
        while (true)
        {
            yield return new WaitForSeconds(SendCabinetsStateTime);
            SendCabinetsState();
        }
    }

    IEnumerator SendTaskMessage()
    {
        while (true)
        {
            yield return new WaitForSeconds(SendTaskTime);
            SendTaskState();
        }
    }

    public void SendCabinetsState()
    {
        for (int i = 0; i < SceneManager.Instance.cabinetList.Count; i++)
        {
            CabinetStateMsg state = new CabinetStateMsg();
            state.cabinet_id = (byte)i;
            state.medicine_list = new MedicineDataMsg[45];
            int n = 0;
            for (int j = 0; j < SceneManager.Instance.cabinetList[i].MedicineCount.GetLength(0); j++)
            {
                for (int k = 0; k < SceneManager.Instance.cabinetList[i].MedicineCount.GetLength(1); k++)
                {
                    MedicineDataMsg md = new MedicineDataMsg((byte)j, (byte)k, (byte)SceneManager.Instance.cabinetList[i].MedicineCount[j,k]);
                    state.medicine_list[n] = md;
                    n++;
                }
            }

            sendCabinetState.SendMessage_Ros(state);
        }
    }

    public void SendCabinetsRunning()
    {
        for (int i = 0; i < SceneManager.Instance.cabinetList.Count; i++)
        {
            byte type;
            if (SceneManager.Instance.cabinetList[i].isRunning) type = 1;
            else type = 0;
            sendCabinetRunning.SendMessage_Ros((byte)i, type);
        }
    }

    public void SendCarState()
    {
        for (int i = 0; i < SceneManager.Instance.carList.Count; i++)
        {
            sendCarState.SendMessage_Ros((byte)SceneManager.Instance.carList[i].CarID, (byte)SceneManager.Instance.carList[i].CarState
                , SceneManager.Instance.carList[i].transform);
        }
    }    
    
    public void SendTaskState()
    {
        for (int i = 0; i < SceneManager.Instance.taskSub.TaskListData.Count; i++)
        {
            TaskStateMsg data = new TaskStateMsg();
            data.taskid = SceneManager.Instance.taskSub.TaskList[0].task_id;
            data.car_id = SceneManager.Instance.taskSub.TaskListData[i].TaskCarID;
            data.task_state = SceneManager.Instance.taskSub.TaskListData[i].TaskState;

            //Debug.Log(" : " + data.task_state + " : " + data.car_id);
            sendTaskState.SendMessage_Ros(data);
        }
    }
}
