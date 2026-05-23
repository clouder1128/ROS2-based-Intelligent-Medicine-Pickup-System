using UnityEngine;

public class CameraController : MonoBehaviour
{
    [Header("移动设置")]
    [SerializeField] private float moveSpeed = 10f;           // 基础移动速度
    [SerializeField] private float sprintMultiplier = 2f;    // 冲刺倍率
    [SerializeField] private float verticalSpeed = 5f;       // 垂直移动速度

    [Header("视角设置")]
    [SerializeField] private float lookSpeed = 2f;           // 视角旋转速度
    [SerializeField] private float maxLookAngle = 80f;       // 最大俯仰角度

    [Header("平滑设置")]
    [SerializeField] private bool enableSmoothing = true;    // 启用平滑移动
    [SerializeField] private float smoothTime = 0.1f;        // 平滑时间

    private Vector3 currentVelocity = Vector3.zero;          // 当前速度（用于平滑）
    private float rotationX = 0f;                            // X轴旋转角度
    private float rotationY = 0f;                            // Y轴旋转角度

    void Start()
    {
        // 初始化旋转角度为当前相机的角度
        Vector3 currentRotation = transform.eulerAngles;
        rotationX = currentRotation.x;
        rotationY = currentRotation.y;

        // 锁定鼠标光标
        //Cursor.lockState = CursorLockMode.Locked;
        //Cursor.visible = false;
    }

    void Update()
    {
        HandleMouseLook();
        HandleMovement();
    }

    /// <summary>
    /// 处理鼠标视角旋转
    /// </summary>
    void HandleMouseLook()
    {
        if (Input.GetMouseButton(1)) // 按住鼠标右键
        {
            // 获取鼠标移动输入
            float mouseX = Input.GetAxis("Mouse X") * lookSpeed;
            float mouseY = Input.GetAxis("Mouse Y") * lookSpeed;

            // 计算旋转角度
            rotationY += mouseX;
            rotationX -= mouseY;

            // 限制X轴旋转角度（防止翻转）
            rotationX = Mathf.Clamp(rotationX, -maxLookAngle, maxLookAngle);

            // 应用旋转
            transform.rotation = Quaternion.Euler(rotationX, rotationY, 0f);
        }
    }

    /// <summary>
    /// 处理键盘移动
    /// </summary>
    void HandleMovement()
    {
        // 计算当前移动速度（考虑冲刺）
        float currentSpeed = moveSpeed;
        if (Input.GetKey(KeyCode.LeftShift))
        {
            currentSpeed *= sprintMultiplier;
        }

        // 初始化移动向量
        Vector3 moveDirection = Vector3.zero;

        // 获取相机的方向向量（投影到水平面）
        Vector3 cameraForward = transform.forward;
        Vector3 cameraRight = transform.right;

        // 将前向和右向向量投影到水平面（移除Y分量）
        cameraForward.y = 0f;
        cameraRight.y = 0f;

        // 归一化以确保一致的速度
        if (cameraForward.magnitude > 0.001f)
            cameraForward.Normalize();
        if (cameraRight.magnitude > 0.001f)
            cameraRight.Normalize();

        // 前后移动（W/S）
        if (Input.GetKey(KeyCode.W))
            moveDirection += cameraForward;
        if (Input.GetKey(KeyCode.S))
            moveDirection -= cameraForward;

        // 左右移动（A/D） - 现在使用水平投影的右向量
        if (Input.GetKey(KeyCode.A))
            moveDirection -= cameraRight;
        if (Input.GetKey(KeyCode.D))
            moveDirection += cameraRight;

        // 垂直移动（E/Q） - 使用世界坐标的垂直方向
        Vector3 verticalMove = Vector3.zero;
        if (Input.GetKey(KeyCode.E))
            verticalMove += Vector3.up;
        if (Input.GetKey(KeyCode.Q))
            verticalMove -= Vector3.up;

        // 归一化水平移动向量并应用速度
        if (moveDirection != Vector3.zero)
        {
            moveDirection.Normalize();
            moveDirection *= currentSpeed * Time.deltaTime;
        }

        // 应用垂直移动速度
        if (verticalMove != Vector3.zero)
        {
            verticalMove.Normalize();
            verticalMove *= verticalSpeed * Time.deltaTime;
        }

        // 合并水平和垂直移动
        Vector3 totalMove = moveDirection + verticalMove;

        // 应用移动（平滑或直接）
        if (enableSmoothing && totalMove != Vector3.zero)
        {
            transform.position = Vector3.SmoothDamp(
                transform.position,
                transform.position + totalMove,
                ref currentVelocity,
                smoothTime
            );
        }
        else if (totalMove != Vector3.zero)
        {
            transform.position += totalMove;
        }
    }

    /// <summary>
    /// 在编辑器模式下绘制辅助线
    /// </summary>
    void OnDrawGizmosSelected()
    {
        // 绘制移动方向线
        Gizmos.color = Color.blue;
        Vector3 forwardProjected = transform.forward;
        forwardProjected.y = 0;
        if (forwardProjected.magnitude > 0.001f)
        {
            forwardProjected.Normalize();
            Gizmos.DrawRay(transform.position, forwardProjected * 2f);
        }

        // 绘制右侧线（水平投影）
        Gizmos.color = Color.red;
        Vector3 rightProjected = transform.right;
        rightProjected.y = 0;
        if (rightProjected.magnitude > 0.001f)
        {
            rightProjected.Normalize();
            Gizmos.DrawRay(transform.position, rightProjected * 2f);
        }

        // 绘制上方线
        Gizmos.color = Color.green;
        Gizmos.DrawRay(transform.position, Vector3.up * 2f);
    }
}
