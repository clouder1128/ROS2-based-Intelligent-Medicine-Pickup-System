using Dreamteck.Splines;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class CarControl : MonoBehaviour
{
    public int CarID;

    [Header("路径设置")]
    [SerializeField] private SplineFollower splineFollower;
    [SerializeField] private float moveSpeed = 5f;
    [SerializeField] private float rotationSpeed = 5f;

    [Header("停车点设置")]
    [SerializeField] private List<float> stopPercentages = new List<float> { 0.25f, 0.5f, 0.75f };
    [SerializeField] private float stopDuration = 2f;

    [Header("驶离点设置")]
    [SerializeField] private float exitPercentage = 0.85f;

    [Header("起点设置")]
    [SerializeField] private bool startOnSpline = false; // 是否从轨迹上开始
    [SerializeField] private Transform approachStartPoint; // 外部起点（如果不在轨迹上）
    [SerializeField] private float approachSpeed = 3f;
    [SerializeField] private float approachDistance = 0.5f;
    [SerializeField] private float snapDistance = 0.1f; // 对齐到轨迹的阈值

    // 状态
    private enum CarState
    {
        Idle,              // 空闲状态
        ApproachingSpline, // 正在接近轨迹
        FollowingSpline,   // 沿着轨迹移动
        Stopping,          // 停车中
        Exiting            // 正在驶离
    }

    private CarState currentState = CarState.Idle;
    private int currentStopIndex = 0;
    private bool[] stopCompleted;
    private bool exitPointReached = false;
    private Vector3 targetApproachPoint; // 接近轨迹的目标点

    private void Start()
    {
        InitializeComponents();
        InitializeStopPoints();

        // 根据设置决定初始状态
        if (startOnSpline)
        {
            // 直接从轨迹上开始
            StartOnSpline();
        }
        else
        {
            // 从外部移动到轨迹
            StartApproachFromOutside();
        }
    }

    private void Update()
    {
        if (Input.GetKeyDown(KeyCode.Q))
        {
            UpdateFollowing();
        }
    }

    private void InitializeComponents()
    {
        if (splineFollower == null)
            splineFollower = GetComponent<SplineFollower>();

        // 确保spline follower初始为禁用状态
        splineFollower.follow = false;
        //splineFollower.applyDirection = SplineFollower.Direction.Forward;
        splineFollower.updateMethod = SplineFollower.UpdateMethod.Update;
    }

    private void InitializeStopPoints()
    {
        stopCompleted = new bool[stopPercentages.Count];
        for (int i = 0; i < stopCompleted.Length; i++)
        {
            stopCompleted[i] = false;
        }

        // 确保停车点按顺序排列
        stopPercentages.Sort();
    }

    #region 初始化状态
    private void StartOnSpline()
    {
        Debug.Log("小车从轨迹上开始移动");

        // 检查小车当前位置是否在轨迹上
        SplineSample sample = splineFollower.spline.Project(transform.position);
        float distanceToSpline = Vector3.Distance(transform.position, sample.position);

        if (distanceToSpline > 0.5f)
        {
            Debug.LogWarning("小车距离轨迹较远，建议使用外部起点模式");
            // 自动切换到外部接近模式
            startOnSpline = false;
            StartApproachFromOutside();
            return;
        }

        // 对齐到最近的轨迹点
        transform.position = sample.position;
        transform.rotation = sample.rotation;

        // 设置起始百分比
        splineFollower.SetPercent(sample.percent);
        splineFollower.follow = true;
        splineFollower.followSpeed = moveSpeed;

        currentState = CarState.FollowingSpline;

        // 检查是否已经在停车点
        CheckInitialStopPosition((float)sample.percent);
    }

    private void StartApproachFromOutside()
    {
        Debug.Log("小车从外部开始接近轨迹");

        if (approachStartPoint == null)
        {
            // 如果没有指定外部起点，创建一个距离轨迹一定距离的点
            approachStartPoint = new GameObject("ApproachStartPoint").transform;

            // 找到轨迹起点附近的外部点
            Vector3 splineStart = splineFollower.spline.GetPoint(0).position;
            Vector3 offsetDirection = Vector3.Cross(splineFollower.spline.GetPointNormal(0),
                                                  splineFollower.spline.GetPointNormal(0)).normalized;

            approachStartPoint.position = splineStart + offsetDirection * 3f +
                                         splineFollower.spline.GetPointNormal(0).normalized * 2f;
        }

        // 将小车放置在外部起点
        transform.position = approachStartPoint.position;

        // 找到轨迹上最近的点作为目标接近点
        targetApproachPoint = FindNearestPointOnSpline(transform.position);

        // 开始接近轨迹
        currentState = CarState.ApproachingSpline;
        StartCoroutine(ApproachSplineRoutine());
    }

    private void CheckInitialStopPosition(float startPercent)
    {
        // 检查起始位置是否在停车点附近
        for (int i = 0; i < stopPercentages.Count; i++)
        {
            float distance = Mathf.Abs(stopPercentages[i] - startPercent);
            if (distance < 0.02f)
            {
                // 如果起始位置在停车点，自动完成这个停车点
                stopCompleted[i] = true;
                Debug.Log($"起始位置在停车点 {i + 1}，已自动标记为完成");
            }
        }
    }
    #endregion

    #region 功能3：从外部移动到轨迹（修正版）
    private Vector3 FindNearestPointOnSpline(Vector3 position)
    {
        SplineSample sample = splineFollower.spline.Project(position);
        return sample.position;
    }

    private IEnumerator ApproachSplineRoutine()
    {
        Debug.Log("开始接近轨迹...");

        // 旋转朝向轨迹
        Vector3 toTarget = (targetApproachPoint - transform.position).normalized;
        Quaternion targetRotation = Quaternion.LookRotation(toTarget);

        float rotationProgress = 0f;
        while (rotationProgress < 1f)
        {
            rotationProgress += rotationSpeed * Time.deltaTime;
            transform.rotation = Quaternion.Slerp(transform.rotation, targetRotation, rotationProgress);
            yield return null;
        }

        // 等待一小段时间，让旋转完成
        yield return new WaitForSeconds(0.2f);

        // 移动到轨迹附近
        while (currentState == CarState.ApproachingSpline)
        {
            // 计算当前距离
            float currentDistance = Vector3.Distance(transform.position, targetApproachPoint);

            // 移动小车
            transform.position = Vector3.MoveTowards(
                transform.position,
                targetApproachPoint,
                approachSpeed * Time.deltaTime
            );

            // 更新朝向（始终朝向目标点）
            Vector3 currentDirection = (targetApproachPoint - transform.position).normalized;
            if (currentDirection != Vector3.zero)
            {
                Quaternion lookRotation = Quaternion.LookRotation(currentDirection);
                transform.rotation = Quaternion.Slerp(
                    transform.rotation,
                    lookRotation,
                    rotationSpeed * Time.deltaTime
                );
            }

            // 检查是否到达目标距离
            if (currentDistance <= snapDistance)
            {
                // 对齐到轨迹
                AlignToSpline();
                break;
            }

            yield return null;
        }
    }

    private void AlignToSpline()
    {
        Debug.Log("已到达轨迹附近，开始对齐");

        // 找到最近的轨迹点
        SplineSample sample = splineFollower.spline.Project(transform.position);

        // 平滑过渡到轨迹（可选动画）
        StartCoroutine(SmoothAlignToSpline(sample));
    }

    private IEnumerator SmoothAlignToSpline(SplineSample targetSample)
    {
        Vector3 startPosition = transform.position;
        Quaternion startRotation = transform.rotation;

        float alignDuration = 0.5f; // 对齐时间
        float elapsed = 0f;

        while (elapsed < alignDuration)
        {
            elapsed += Time.deltaTime;
            float t = elapsed / alignDuration;

            // 平滑移动到轨迹点
            transform.position = Vector3.Lerp(startPosition, targetSample.position, t);

            // 平滑旋转到轨迹方向
            transform.rotation = Quaternion.Slerp(startRotation, targetSample.rotation, t);

            yield return null;
        }

        // 精确对齐
        transform.position = targetSample.position;
        transform.rotation = targetSample.rotation;

        // 设置spline follower
        splineFollower.SetPercent(targetSample.percent);

        // 开始跟随轨迹
        splineFollower.follow = true;
        splineFollower.followSpeed = moveSpeed;
        currentState = CarState.FollowingSpline;

        Debug.Log("已完成对齐，开始沿轨迹移动");
    }
    #endregion

    #region 功能1：轨迹上停车执行操作（修正版）
    private void UpdateFollowing()
    {
        if (currentState != CarState.FollowingSpline)
            return;

        // 检查是否到达停车点
        if (currentStopIndex < stopPercentages.Count &&
            !stopCompleted[currentStopIndex])
        {
            float currentPercent = (float)splineFollower.result.percent;
            float targetPercent = stopPercentages[currentStopIndex];

            // 计算距离和减速
            float distanceToStop = targetPercent - currentPercent;

            if (distanceToStop > 0 && distanceToStop < 0.05f)
            {
                // 接近停车点时减速
                splineFollower.followSpeed = Mathf.Lerp(0.1f, moveSpeed, distanceToStop * 20f);
            }

            // 到达停车点
            if (currentPercent >= targetPercent - 0.001f)
            {
                StartCoroutine(StopAtPointRoutine());
                return;
            }
        }

        // 检查是否到达驶离点
        if (!exitPointReached && splineFollower.result.percent >= exitPercentage)
        {
            exitPointReached = true;
            StartExiting();
        }
    }

    private IEnumerator StopAtPointRoutine()
    {
        Debug.Log($"到达停车点 {currentStopIndex + 1}");

        currentState = CarState.Stopping;
        splineFollower.follow = false;

        // 确保精确停在指定点
        SplineSample stopSample = splineFollower.spline.Evaluate(stopPercentages[currentStopIndex]);
        transform.position = stopSample.position;
        transform.rotation = stopSample.rotation;

        // 执行停车操作
        yield return StartCoroutine(ExecuteStopActions());

        // 标记完成
        stopCompleted[currentStopIndex] = true;
        currentStopIndex++;

        // 继续移动
        splineFollower.follow = true;
        currentState = CarState.FollowingSpline;

        Debug.Log($"离开停车点 {currentStopIndex}");
    }

    private IEnumerator ExecuteStopActions()
    {
        // 这里添加你的自定义操作
        Debug.Log($"执行停车点 {currentStopIndex + 1} 的操作...");

        // 示例：播放停车动画
        // animator.SetTrigger("Stop");
        // yield return new WaitForSeconds(0.5f);

        // 等待指定时间
        float timer = 0f;
        while (timer < stopDuration)
        {
            timer += Time.deltaTime;

            // 可以在这里添加进度显示或其他逻辑
            // Debug.Log($"停车倒计时: {stopDuration - timer:F1}秒");

            yield return null;
        }

        // 触发完成事件
        OnStopPointCompleted(currentStopIndex);
    }

    private void OnStopPointCompleted(int index)
    {
        // 触发事件，可以在Inspector中绑定
        Debug.Log($"停车点 {index + 1} 操作完成");
    }
    #endregion

    #region 功能2：驶离轨迹
    private void StartExiting()
    {
        Debug.Log("到达驶离点，开始离开轨迹");

        currentState = CarState.Exiting;
        splineFollower.follow = false;

        // 开始驶离协程
        StartCoroutine(ExitSplineRoutine());
    }

    private IEnumerator ExitSplineRoutine()
    {
        // 获取当前方向作为驶离方向
        Vector3 exitDirection = transform.forward;

        // 可选：添加转向
        Vector3 targetDirection = exitDirection + transform.right * 0.5f; // 稍微向右转
        targetDirection.Normalize();

        float exitDuration = 3f; // 驶离持续时间
        float elapsed = 0f;

        while (elapsed < exitDuration)
        {
            elapsed += Time.deltaTime;

            // 移动
            transform.position += exitDirection * moveSpeed * Time.deltaTime;

            // 旋转（平滑转向目标方向）
            if (targetDirection != Vector3.zero)
            {
                Quaternion targetRotation = Quaternion.LookRotation(targetDirection);
                transform.rotation = Quaternion.Slerp(
                    transform.rotation,
                    targetRotation,
                    rotationSpeed * Time.deltaTime
                );
            }

            yield return null;
        }

        Debug.Log("已完全驶离轨迹");
        OnExitCompleted();
    }

    private void OnExitCompleted()
    {
        // 驶离完成后的逻辑
        // 例如：切换到其他行为模式、销毁对象等
    }
    #endregion

    #region 公共方法和编辑器
    [Header("调试")]
    [SerializeField] private bool showGizmos = true;

    private void OnDrawGizmosSelected()
    {
        if (!showGizmos || splineFollower == null || splineFollower.spline == null)
            return;

        // 绘制停车点
        Gizmos.color = Color.yellow;
        foreach (float percent in stopPercentages)
        {
            Vector3 point = splineFollower.spline.EvaluatePosition(percent);
            Gizmos.DrawSphere(point, 0.3f);
            Gizmos.DrawWireSphere(point, 0.5f);
        }

        // 绘制驶离点
        Gizmos.color = Color.red;
        Vector3 exitPoint = splineFollower.spline.EvaluatePosition(exitPercentage);
        Gizmos.DrawSphere(exitPoint, 0.4f);
        Gizmos.DrawWireSphere(exitPoint, 0.6f);

        // 绘制外部起点
        if (!startOnSpline && approachStartPoint != null)
        {
            Gizmos.color = Color.green;
            Gizmos.DrawSphere(approachStartPoint.position, 0.3f);
            Gizmos.DrawLine(approachStartPoint.position, targetApproachPoint);
            Gizmos.DrawWireSphere(targetApproachPoint, 0.2f);
        }
    }

    // 公共方法
    public void AddStopPoint(float percent)
    {
        stopPercentages.Add(percent);
        stopPercentages.Sort();
        System.Array.Resize(ref stopCompleted, stopCompleted.Length + 1);
        stopCompleted[stopCompleted.Length - 1] = false;
    }

    public void SetApproachStartPoint(Transform startPoint)
    {
        approachStartPoint = startPoint;
    }

    public void SetStartOnSpline(bool onSpline)
    {
        startOnSpline = onSpline;
    }

    public string GetCurrentStatus()
    {
        string status = $"状态: {currentState}\n";

        if (currentState == CarState.FollowingSpline)
        {
            status += $"进度: {splineFollower.result.percent:P0}\n";
            status += $"下一个停车点: {(currentStopIndex < stopPercentages.Count ? stopPercentages[currentStopIndex] : 0):P0}";
        }

        return status;
    }
    #endregion
}
