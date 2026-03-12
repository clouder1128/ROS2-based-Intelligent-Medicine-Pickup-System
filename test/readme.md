## 文件夹内容

`test_world.sdf` 中创建了一个简易的世界，用于模拟小车的巡线功能。

`models/` 中包含了带摄像头的轮式差速小车模型、场地模型（忽略另外两个模型）。

- **models/new_car**: 小车模型，在 `/cmd_vel` 话题下接受速度消息（`geometry_msgs/Twist`）并移动。相机在 `/camera` 话题发布图像。
- **models/road**: 场地模型，`road.png` 上绘制了黑色巡线轨道和红色停车标记点。
- **models/reddot**: 红点标记模型（备用）。
- **models/line**: 黑线模型（备用）。

## 巡线包 line_follower

`line_follower/` 是一个 ROS2 Python 包，实现了"沿黑线巡线 + 在红点自动停车"功能。

### 算法说明

1. **巡线（FOLLOW_LINE 状态）**：取相机图像下方 25% 区域，灰度化后二值化提取黑线，计算黑色像素质心与图像中心的偏差，用 PD 控制器输出转向角速度。弯道时自动减速。
2. **红点停车（STOP 状态）**：在 ROI 中用 HSV 检测红色像素，超过阈值时进入停车状态，发布零速度并停留指定时间（默认 3 秒）。
3. **冷却机制**：恢复巡线后有 2 秒冷却期，避免同一个红点重复触发停车。

### 可调参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `linear_speed` | 0.5 | 直线前进速度 (m/s) |
| `kp` | 0.005 | 转向比例系数 |
| `kd` | 0.001 | 转向微分系数 |
| `stop_duration` | 3.0 | 每个红点停留时间 (秒) |
| `red_pixel_threshold` | 300 | 红色像素数触发阈值 |
| `binary_thresh` | 80 | 灰度二值化阈值 |
| `roi_ratio` | 0.25 | ROI 占图像高度的比例 |
| `red_cooldown` | 2.0 | 停车后冷却时间 (秒) |

## 环境要求

- Ubuntu 24.04
- ROS2 Jazzy
- Gazebo Harmonic
- 额外依赖：`ros-jazzy-cv-bridge`、`ros-jazzy-ros-gz-bridge`

```bash
sudo apt install ros-jazzy-cv-bridge ros-jazzy-ros-gz-bridge
```

## 使用步骤

### 1. 编译

将 `line_follower` 包链接或复制到 ROS2 工作区并编译：

```bash
# 方式一：软链接（推荐，改代码后不用重复复制）
cd ~/ros2_ws/src
ln -s ~/ROS2-based-Intelligent-Medicine-Pickup-System/test/line_follower .
cd ~/ros2_ws
colcon build --packages-select line_follower
source install/setup.bash
```

### 2. 启动 Gazebo 仿真

```bash
cd ~/ROS2-based-Intelligent-Medicine-Pickup-System/test
gz sim test_world.sdf
```

### 3. 启动巡线节点（新终端）

```bash
source ~/ros2_ws/install/setup.bash
ros2 launch line_follower line_follower.launch.py
```

启动后小车会自动沿黑线行驶，遇到红点自动停车 3 秒后继续。

### 4. 调试

查看当前话题：

```bash
ros2 topic list
```

手动发布速度测试小车运动：

```bash
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.5}, angular: {z: 0.0}}"
```

查看相机图像（需要 rqt）：

```bash
ros2 run rqt_image_view rqt_image_view
```

### 5. 如果话题名不对

如果 `ros2 topic list` 中看不到 `/camera` 或 `/cmd_vel`，说明 Gazebo 实际话题名与默认不同。先在 Gazebo 中查看实际话题：

```bash
gz topic -l
```

然后在 launch 时覆盖：

```bash
ros2 launch line_follower line_follower.launch.py \
    gz_camera_topic:=/world/empty/model/mycar/link/camera/sensor/camera/image
```

## TODO 

- 希望实现通过python程序控制小车自动巡线。 ✅
- 希望实现小车可以在指定位置停下（红点可以作为提示），直到接收到一个消息（目前未定义）后继续巡线移动。 ✅（当前为定时恢复，可改为等待消息）
- 希望上述过程可以在整个巡线过程中发生多次。 ✅

参考教程：https://www.bilibili.com/video/BV1RjS2YHE7Z?spm_id_from=333.788.videopod.sections&vd_source=70ad62eeba83c73634a3120fe532319b
