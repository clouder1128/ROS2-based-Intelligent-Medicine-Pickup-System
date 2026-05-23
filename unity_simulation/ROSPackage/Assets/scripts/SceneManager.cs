using DG.Tweening;
using RosMessageTypes.Task;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using Unity.Robotics.ROSTCPConnector;
using UnityEngine;

public class SceneManager : MonoBehaviour
{
    public ROSConnection rosMain;
    public static SceneManager Instance;
    public static bool IsRefreshTask;
    public TaskSubscriber taskSub;
    public List<CarControl_2> carList;
    public Queue<CarControl_2> carQueue;

    public List<CabinetControl> cabinetList;

    public Transform HSCube;
    public Transform QyCube;
    void Awake()
    {
        string textTxt = File.ReadAllText(Application.streamingAssetsPath + "/ip.txt");
        rosMain.RosIPAddress = textTxt;
        rosMain.RosPort = 10000;
        IsRefreshTask = false;
        carQueue = new Queue<CarControl_2>();
        for (int i = 0; i < carList.Count; i++)
        {
            carQueue.Enqueue(carList[i]);
        }
        if (Instance == null) { Instance = this; }
    }


    public void TestQueue()
    {
        CarControl_2 carControl = carQueue.Dequeue() ;
    }


    public void StartHSOrQy(Transform obj)
    {
        StartCoroutine(HsOrQyAnim(obj));
    }
    IEnumerator HsOrQyAnim(Transform obj)
    {
        obj.DOLocalMoveY(5, 3).SetEase(Ease.Linear).OnComplete(() => { obj.DOLocalMoveY(12, 1); });
        yield return null;
    }
}
