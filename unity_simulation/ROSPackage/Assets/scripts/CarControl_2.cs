using DG.Tweening;
using RosMessageTypes.Task;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;


public class CarControl_2 : MonoBehaviour
{
    public int CarID;
    //小车状态 0-空闲 1-运行中 2-回收
    public int CarState;

    public List<Vector3> MedicineTargetPos;
    public Transform HsTargetPos;
    public Transform QyTargetPos;
    public Transform EndTargetPos;
    public Transform CarCameraPos;

    public float DeleteRayDis = 0.5f;

    //当前小车执行任务在链表中的下标
    public int runningTaskId;

    private Vector3 StartPos;
    private Quaternion StartRoa;

    private Tween CarTweenPos;

    private bool isStartRay;
    private bool isCanMove;
    private bool isCanLeave;
    private TaskMsg lastTask;
    void Start()
    {
        CarState = 0;
        StartPos = transform.position;
        StartRoa = transform.rotation;
        isStartRay = false;
        isCanMove = false;
        isCanLeave = false;
        StartCoroutine(updateRay());
    }

    IEnumerator updateRay()
    {
        while (true)
        {
            if (isStartRay)
            {
                Ray ray = new Ray(CarCameraPos.position, CarCameraPos.forward);
                RaycastHit hitInfo;
                if (Physics.Raycast(ray, out hitInfo, DeleteRayDis))
                {
                    isCanMove = false;
                    DOTween.Pause(transform);
                    //Debug.Log(hitInfo.collider.gameObject.name);
                }
                else
                {
                    DOTween.Play(transform);
                }
            }
            yield return new WaitForSeconds(0.1f);
        }
    }

    private void Update()
    {
        //if (Input.GetKeyDown(KeyCode.F1))
        //{
        //    if(CarID ==1)
        //        StarTask(SceneManager.Instance.taskSub.TaskList[0]);
        //}
    }

    public void StarTask(TaskMsg task)
    {
        if (lastTask != null)
            StopCoroutine(StartTaskMove(lastTask));
        isCanMove = false;
        isCanLeave = false;
        lastTask = task;
        CarState = 1;
        StartCoroutine(StartTaskMove(task));
    }
    IEnumerator StartTaskMove(TaskMsg task)
    {
        yield return new WaitForSeconds(2);
        for (int i = 0; i < task.cabinets.Length; i++)
        {
            //移动到取药柜
            float var = CarMoveToTarget(MedicineTargetPos[int.Parse(task.cabinets[i].cabinet_id)]);
            while (Vector3.Distance(CarCameraPos.position, MedicineTargetPos[int.Parse(task.cabinets[i].cabinet_id)]) > 0.5f)
            {
                Ray ray = new Ray(CarCameraPos.position, CarCameraPos.forward);
                RaycastHit hitInfo;
                if (Physics.Raycast(ray, out hitInfo, DeleteRayDis))
                {
                    CarTweenPos.Pause();
                    //Debug.Log(hitInfo.collider.gameObject.name);
                }
                else
                {
                    CarTweenPos.Play();
                }
                yield return new WaitForSeconds(0.1f);
                //Debug.DrawLine(CarCameraPos.position, CarCameraPos.position + (CarCameraPos.forward * 0.5f), Color.red);
            }


            //yield return new WaitForSeconds(var);
            //等待取药
            SceneManager.Instance.cabinetList[int.Parse(task.cabinets[i].cabinet_id)].StartPlayGetMedicine(
                task.cabinets[i]);
            while (SceneManager.Instance.cabinetList[int.Parse(task.cabinets[i].cabinet_id)].isRunning)
            {
                yield return new WaitForSeconds(0.5f);
            }
        }
        isStartRay = true;
        //取药完成去往分类区
        if (task.type == "0")
        {
            //正常取药
            //CarState = 2;
            //var dur = CarMoveToTarget(MedicineTargetPos[int.Parse(task.cabinets[task.cabinets.Length - 1].cabinet_id)] + Vector3.right);
            //yield return new WaitForSeconds(dur);
            //this.transform.DOLocalRotate(new Vector3(transform.eulerAngles.x, 0, transform.eulerAngles.z), 1);
            //yield return new WaitForSeconds(1);

            //transform.DOLocalMoveZ(2.8f, 2);
            //yield return new WaitForSeconds(2);
            //this.transform.DOLocalRotate(new Vector3(transform.eulerAngles.x, -90, transform.eulerAngles.z), 1);
            //yield return new WaitForSeconds(1);
            //CarMoveToTarget_LookAt(QyTargetPos);

            CarState = 2;
            this.transform.DOLocalMove(MedicineTargetPos[int.Parse(task.cabinets[task.cabinets.Length - 1].cabinet_id)] - Vector3.right, 1)
                .OnKill(() => { isCanMove = true; });
            isCanMove = false;
            yield return new WaitUntil(() => isCanMove);
            this.transform.DOLocalRotate(new Vector3(transform.eulerAngles.x, 0, transform.eulerAngles.z), 1);
            yield return new WaitForSeconds(1);
            transform.DOLocalMoveZ(1.8f, 4).OnComplete(() => { isCanMove = true; });
            isCanMove = false;
            yield return new WaitUntil(() => isCanMove);
            this.transform.DOLocalRotate(new Vector3(transform.eulerAngles.x, -90, transform.eulerAngles.z), 1);
            yield return new WaitForSeconds(1);
            CarMoveToTarget_LookAt(QyTargetPos);
        }
        else
        {
            //过期回收
            //CarState = 3;
            //var dur = CarMoveToTarget(MedicineTargetPos[int.Parse(task.cabinets[task.cabinets.Length - 1].cabinet_id)] - Vector3.right);
            //yield return new WaitForSeconds(dur);
            //this.transform.DOLocalRotate(new Vector3(transform.eulerAngles.x, -180, transform.eulerAngles.z), 1);
            //yield return new WaitForSeconds(1);
            //transform.DOLocalMoveZ(-4f, 3);
            //yield return new WaitForSeconds(3);
            //this.transform.DOLocalRotate(new Vector3(transform.eulerAngles.x, -90, transform.eulerAngles.z), 1);
            //yield return new WaitForSeconds(1);
            //CarMoveToTarget_LookAt(HsTargetPos);

            CarState = 3;
            this.transform.DOLocalMove(MedicineTargetPos[int.Parse(task.cabinets[task.cabinets.Length - 1].cabinet_id)] - Vector3.right, 1)
                .OnKill(() => { isCanMove = true; } );
            isCanMove = false;
            yield return new WaitUntil(() => isCanMove);
            this.transform.DOLocalRotate(new Vector3(transform.eulerAngles.x, -180, transform.eulerAngles.z), 1);
            yield return new WaitForSeconds(1);
            transform.DOLocalMoveZ(-3.5f, 5).OnComplete(() => { isCanMove = true; });
            isCanMove = false;
            yield return new WaitUntil(() => isCanMove);
            this.transform.DOLocalRotate(new Vector3(transform.eulerAngles.x, -90, transform.eulerAngles.z), 1);
            yield return new WaitForSeconds(1);
            CarMoveToTarget_LookAt(HsTargetPos);
        }

        while (!isCanLeave)
        {
            yield return new WaitForSeconds(1);
        }

        //回归排队
        if (task.type == "0")
        {
            this.transform.DOLocalRotate(new Vector3(transform.eulerAngles.x, 0, transform.eulerAngles.z), 1);
            yield return new WaitForSeconds(1);
            transform.DOLocalMoveZ(4.8f, 3).OnComplete(() => { isCanMove = true; });
            isCanMove = false;
            yield return new WaitUntil(() => isCanMove);
            this.transform.DOLocalRotate(new Vector3(transform.eulerAngles.x, 90, transform.eulerAngles.z), 1);
            yield return new WaitForSeconds(1);
            transform.DOLocalMoveX(11f, 5).OnComplete(() => { isCanMove = true; });
            isCanMove = false;
            yield return new WaitUntil(() => isCanMove);
            this.transform.DOLocalRotate(new Vector3(transform.eulerAngles.x, 180, transform.eulerAngles.z), 1);
            yield return new WaitForSeconds(1);
            transform.DOMoveZ(0.14f, 3).OnComplete(() => { isCanMove = true; });
            isCanMove = false;
            yield return new WaitUntil(() => isCanMove);
            this.transform.DOLocalRotate(new Vector3(transform.eulerAngles.x, 270, transform.eulerAngles.z), 1);
            yield return new WaitForSeconds(1);

            transform.DOMove(new Vector3(2.42f, 0, 0.14f), 3).OnComplete(() => { isCanMove = true; });
            isCanMove = false;
            yield return new WaitUntil(() => isCanMove);

            //this.transform.position = StartPos;
            this.transform.rotation = StartRoa;

            CarState = 0;
            SceneManager.Instance.carQueue.Enqueue(this);
        }
        else
        {
            this.transform.DOLocalRotate(new Vector3(transform.eulerAngles.x, -180, transform.eulerAngles.z), 1);
            yield return new WaitForSeconds(1);
            transform.DOLocalMoveZ(-6f, 3).OnComplete(() => { isCanMove = true; });
            isCanMove = false;
            yield return new WaitUntil(() => isCanMove);
            this.transform.DOLocalRotate(new Vector3(transform.eulerAngles.x, -270, transform.eulerAngles.z), 1);
            yield return new WaitForSeconds(1);
            transform.DOLocalMoveX(11, 5).OnComplete(() => { isCanMove = true; });
            isCanMove = false;
            yield return new WaitUntil(() => isCanMove);
            this.transform.DOLocalRotate(new Vector3(transform.eulerAngles.x, -360, transform.eulerAngles.z), 1);
            yield return new WaitForSeconds(1);
            transform.DOMoveZ(0.14f, 3).OnComplete(() => { isCanMove = true; });
            isCanMove = false;
            yield return new WaitUntil(() => isCanMove);
            this.transform.DOLocalRotate(new Vector3(transform.eulerAngles.x, -90, transform.eulerAngles.z), 1);
            yield return new WaitForSeconds(1);

            transform.DOMove(new Vector3(2.42f,0,0.14f), 3).OnComplete(() => { isCanMove = true; });
            isCanMove = false;
            yield return new WaitUntil(() => isCanMove);

            //this.transform.position = StartPos;
            this.transform.rotation = StartRoa;
            CarState = 0;
            SceneManager.Instance.carQueue.Enqueue(this);
        }
    }

    public float CarMoveToTarget(Vector3 Target)
    {
        float dur = Vector3.Distance(transform.position, Target);
        CarTweenPos = this.transform.DOLocalMove(Target, dur).SetEase(Ease.Linear);
        return dur;
    }

    public void CarMoveToTarget_LookAt(Transform target)
    {
        float dur = Vector3.Distance(transform.position, target.position);
        this.transform.DOLocalMove(target.position,dur*1.5f).SetEase(Ease.Linear).OnComplete(() => {
            //等待取药
            isCanLeave = false;
            StartCoroutine(SetIsCanLeaveTime(5));

        });
    }

    IEnumerator SetIsCanLeaveTime(float time)
    {
        yield return new WaitForSeconds(1);
        if(lastTask.type == "0")
            SceneManager.Instance.StartHSOrQy(SceneManager.Instance.QyCube);
        else
            SceneManager.Instance.StartHSOrQy(SceneManager.Instance.HSCube);
        yield return new WaitForSeconds(time);

        SceneManager.Instance.taskSub.TaskListData[runningTaskId].TaskState = 2;
        isCanLeave = true;
    }
}
