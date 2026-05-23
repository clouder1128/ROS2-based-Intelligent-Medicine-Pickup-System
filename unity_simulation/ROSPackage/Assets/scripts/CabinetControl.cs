using DG.Tweening;
using RosMessageTypes.Task;
using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class CabinetControl : MonoBehaviour
{
    public Transform firstMove;
    public float[] firstMovePos;
    public Transform SecMove;
    public float[] SecMovePos;

    public Transform[] LeftRightBox;

    [SerializeField]
    public List<TransformListWrapper> pushBoxList;


    public Vector2 TestNumID;

    public bool isRunning;

    private Vector2Int LastMoveID;

    public int[,] MedicineCount;

    void Start()
    {
        isRunning = false;
        MedicineCount = new int[9,5];
        for (int i = 0; i < MedicineCount.GetLength(0); i++)
        {
            for (int j = 0; j < MedicineCount.GetLength(1); j++)
            {
                MedicineCount[i, j] = 9;
            }
        }

        LastMoveID = new Vector2Int();
    }

    void Update()
    {
        //if (Input.GetKeyDown(KeyCode.F1))
        //{
        //    FirstMoveStart((int)TestNumID.x);
        //    SecondMoveStart((int)TestNumID.y);
        //}
        //if (Input.GetKeyDown(KeyCode.F2))
        //{
        //    ResetFirstASecMove();
        //}
        //if (Input.GetKeyDown(KeyCode.F3))
        //{
        //    CabinetOrderMsg msg = new CabinetOrderMsg();
        //    msg.medicine_list = new MedicineDataMsg[3];
        //    msg.medicine_list[0] = new MedicineDataMsg();
        //    msg.medicine_list[1] = new MedicineDataMsg();
        //    msg.medicine_list[2] = new MedicineDataMsg();
        //    msg.medicine_list[0].row = 0;
        //    msg.medicine_list[0].column = 1;
        //    msg.medicine_list[1].row = 8;
        //    msg.medicine_list[1].column = 4;
        //    msg.medicine_list[2].row = 4;
        //    msg.medicine_list[2].column = 1;
        //    StartCoroutine(StartGetMedicenAnim(msg));
        //}

        //if (Input.GetKeyDown(KeyCode.F5))
        //{
        //    OpenOrClosePushBox(true);
        //}
        //if (Input.GetKeyDown(KeyCode.F6))
        //{
        //    OpenOrClosePushBox(false);
        //}
    }
    public void StartPlayGetMedicine(CabinetOrderMsg msg)
    {
        StartCoroutine(StartGetMedicenAnim(msg));
    }

    IEnumerator StartGetMedicenAnim(CabinetOrderMsg msg)
    {
        isRunning = true;
        //获取所有药品
        for (int i = 0; i < msg.medicine_list.Length; i++)
        {
            //移动到位
            var time = GetMaxDurData(msg.medicine_list[i].row, msg.medicine_list[i].column);
            FirstMoveStart(msg.medicine_list[i].row);
            SecondMoveStart(msg.medicine_list[i].column);
            //Debug.Log("time:" + time);
            yield return new WaitForSeconds(time);
            //取药
            StartCoroutine(MovePushBox(msg.medicine_list[i].row, msg.medicine_list[i].column));
            //设置药品数量
            if (MedicineCount[msg.medicine_list[i].row, msg.medicine_list[i].column] <= 0)
            {
                MedicineCount[msg.medicine_list[i].row, msg.medicine_list[i].column] = 0;
            }
            else
            {
                MedicineCount[msg.medicine_list[i].row, msg.medicine_list[i].column]--;
            }

            yield return new WaitForSeconds(2);
        }
        //归位
        ResetFirstASecMove();
        yield return new WaitForSeconds(2);
        OpenOrClosePushBox(true);
        yield return new WaitForSeconds(2);
        OpenOrClosePushBox(false);
        isRunning = false;
    }

    IEnumerator MovePushBox(int row,int col)
    {
        pushBoxList[row].transforms[col].DOLocalMoveZ(-0.22f, 1);
        yield return new WaitForSeconds(1.5f);
        pushBoxList[row].transforms[col].DOLocalMoveZ(0, 1);
    }

    public void FirstMoveStart(int id)
    {
        if (id >= firstMovePos.Length) return;

        float dur = MapToFixedInterval(Mathf.Abs(id - LastMoveID.x), new Vector2Int(0,8), new Vector2Int(1,3));
        //Debug.Log("first:" + dur);
        firstMove.DOLocalMoveZ(firstMovePos[id], dur).SetEase(Ease.Linear);
        LastMoveID.x = id;
    }
    public void SecondMoveStart(int id)
    {
        if (id >= SecMovePos.Length) return;

        float dur = MapToFixedInterval(Mathf.Abs(id - LastMoveID.y), new Vector2Int(0,4), new Vector2Int(1,2));
        //Debug.Log("sec:" + dur);
        SecMove.DOLocalMoveX(SecMovePos[id], dur).SetEase(Ease.Linear);
        LastMoveID.y = id;
    }

    public void OpenOrClosePushBox(bool isOpen)
    {
        if (isOpen)
        {
            //开
            LeftRightBox[0].DOLocalRotate(new Vector3(0, 90, 0), 1);
            LeftRightBox[1].DOLocalRotate(new Vector3(0, -90, 0), 1);
        }
        else
        {
            //关
            LeftRightBox[0].DOLocalRotate(new Vector3(0, 0, 0), 1);
            LeftRightBox[1].DOLocalRotate(new Vector3(0, 0, 0), 1);
        }
    }

    public void ResetFirstASecMove()
    {
        firstMove.DOLocalMoveZ(0.5f, 1.5f).SetEase(Ease.Linear);
        SecMove.DOLocalMoveX(0, 1.5f).SetEase(Ease.Linear);
        LastMoveID = new Vector2Int();
    }

    #region TOOLS

    public static float MapToFixedInterval(int value,Vector2Int data,Vector2Int minMax)
    {
        // 输入值约束在 [1, 9] 区间内
        value = Math.Max(data.x, Math.Min(data.y, value));

        // 线性插值公式：y = y1 + (x - x1) * (y2 - y1) / (x2 - x1)
        float x1 = data.x, y1 = minMax.x; 
        float x2 = data.y, y2 = minMax.y;

        return y1 + (value - x1) * (y2 - y1) / (x2 - x1);
    }

    private float GetMaxDurData(int row,int col)
    {
        float dur1 = MapToFixedInterval(Mathf.Abs(row - LastMoveID.x), new Vector2Int(0, 8), new Vector2Int(1, 3));
        float dur2 = MapToFixedInterval(Mathf.Abs(col - LastMoveID.y), new Vector2Int(0, 4), new Vector2Int(1, 2));
        //Debug.Log("dur1:" + dur1 + "  dur2:" + dur2);
        float time = dur1 > dur2 ? dur1 : dur2;
        return time + 0.5f;
    }

    #endregion
}

[System.Serializable]
public class TransformListWrapper
{
    public List<Transform> transforms = new List<Transform>();
}