using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class CanvasManager : MonoBehaviour
{
    public static CanvasManager Instance;
    public GameObject TaskPanel;
    public GameObject mainPanel;
    public GameObject cameraPanel;
    public CatCameraControl cameraControl;
    public GameObject TaskPrefab;
    public Transform TaskContent;
    // Start is called before the first frame update
    void Start()
    {
        if(Instance == null) Instance = this;
        //StartCoroutine(RefreshTaskPanelStart());
    }

    private void Update()
    {
        if (Input.GetKeyDown(KeyCode.F1))
        {
            SetPanelHideOrShow(mainPanel);
        }
        if (SceneManager.IsRefreshTask)
        {
            RefreshTaskPanel();
        }
    }

    public void RefreshTaskPanel()
    {
        for (int i = 0; i < TaskContent.childCount; i++)
        {
            TaskContent.GetChild(i).gameObject.SetActive(false);
        }
        for (int i = 0; i < SceneManager.Instance.taskSub.TaskList.Count; i++)
        {
            if (i < TaskContent.childCount)
            {
                //有子物体
                TaskContent.GetChild(i).Find("Name").GetComponent<Text>().text = SceneManager.Instance.taskSub.TaskList[i].task_id;
                TaskContent.GetChild(i).Find("TaskState").GetComponent<Text>().text = GetTaskStateWithID(SceneManager.Instance.taskSub.TaskListData[i].TaskState);
                //Dropdown Dropvalue = TaskContent.GetChild(i).Find("Dropdown").GetComponent<Dropdown>();
                if (SceneManager.Instance.taskSub.TaskListData[i].TaskCarID == -1)
                {
                    TaskContent.GetChild(i).Find("TaskCar").GetComponent<Text>().text = "未分配小车";
                }
                int id = i;
                TaskContent.GetChild(i).Find("TaskBtn").GetComponent<Button>().onClick.RemoveAllListeners();
                TaskContent.GetChild(i).Find("TaskBtn").GetComponent<Button>().onClick.AddListener(() =>
                    {
                        
                        //验证小车状态
                        if (SceneManager.Instance.carQueue.Count <= 0 || SceneManager.Instance.taskSub.TaskListData[id].TaskState != 0)
                        {
                            //无空闲小车
                        }
                        else 
                        {
                            CarControl_2 car = SceneManager.Instance.carQueue.Dequeue();
                            TaskContent.GetChild(id).Find("TaskCar").GetComponent<Text>().text = car.CarID + "号小车";
                            //Debug.Log(SceneManager.Instance.taskSub.TaskListData.Count + " : " + id + " : " + Dropvalue.value);
                            SceneManager.Instance.taskSub.TaskListData[id].TaskState = 1;
                            SceneManager.Instance.taskSub.TaskListData[id].TaskCarID = car.CarID;
                            car.runningTaskId = id;
                            car.StarTask(SceneManager.Instance.taskSub.TaskList[id]);

                        }
                    });
                TaskContent.GetChild(i).gameObject.SetActive(true);

            }
            else
            {
                GameObject obj = Instantiate(TaskPrefab, TaskContent);
                obj.transform.Find("Name").GetComponent<Text>().text = SceneManager.Instance.taskSub.TaskList[i].task_id;
                obj.transform.Find("TaskState").GetComponent<Text>().text = GetTaskStateWithID(SceneManager.Instance.taskSub.TaskListData[i].TaskState);
                //Dropdown Dropvalue = obj.transform.Find("Dropdown").GetComponent<Dropdown>();
                if (SceneManager.Instance.taskSub.TaskListData[i].TaskCarID == -1)
                {
                    obj.transform.Find("TaskCar").GetComponent<Text>().text = "未分配小车";
                }

                int id = i;
                obj.transform.Find("TaskBtn").GetComponent<Button>().onClick.AddListener(() =>
                {
                    
                    //验证小车状态
                    if (SceneManager.Instance.carQueue.Count <= 0 || SceneManager.Instance.taskSub.TaskListData[id].TaskState!=0)
                    {
                        //无空闲小车或者任务已执行
                    }
                    else
                    {
                        CarControl_2 car = SceneManager.Instance.carQueue.Dequeue();
                        obj.transform.Find("TaskCar").GetComponent<Text>().text = car.CarID + "号小车";
                        //Debug.Log(SceneManager.Instance.taskSub.TaskListData.Count + " : " + id + " : drop: " + Dropvalue.value);
                        SceneManager.Instance.taskSub.TaskListData[id].TaskState = 1;
                        SceneManager.Instance.taskSub.TaskListData[id].TaskCarID = car.CarID;
                        car.runningTaskId = id;
                        car.StarTask(SceneManager.Instance.taskSub.TaskList[id]);
                    }
                });
                obj.SetActive(true);
            }
        }
        SceneManager.IsRefreshTask = false;
    }

    public void ShowCameraPanel(int id)
    {
        cameraPanel.SetActive(true);
        cameraControl.SetCameraPosToChooseCar(SceneManager.Instance.carList[id].CarCameraPos);
    }

    public void SetPanelHideOrShow(GameObject panel)
    {
        panel.SetActive(!panel.activeSelf);
    }

    private string GetTaskStateWithID(int state)
    {
        if (state == 0)
        {
            return "未执行";
        }
        else if (state == 1)
        {

            return "执行中";
        }
        else
        {
            return "执行结束";
        }
    }

    public void ReloadScene()
    {
        UnityEngine.SceneManagement.SceneManager.LoadScene("TestNav");
    }
}
