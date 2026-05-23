# ROS 消息格式说明

> 本文档整理了 Unity 仿真项目中所有 ROS 消息的发送与接收格式。

---

## 一、Unity → ROS（发送）

### 1. `CarState_U` — 小车状态

| 字段 | ROS 类型 | C# 类型 | 说明 |
|------|----------|---------|------|
| `car_id` | `uint8` | `byte` | 小车 ID |
| `x` | `float32` | `float` | 当前位置 X 坐标 |
| `y` | `float32` | `float` | 当前位置 Y 坐标 |
| `isrunning` | `uint8` | `byte` | 1=运行中，0=停止 |

- **脚本**: `Assets/scripts/MyMsgScripts/SendMsg/SendCarState.cs`
- **ROS 消息名**: `task_msgs/CarState`
- **发送频率**: 每 1.0 秒（SendMsgManager 协程循环）
- **数据来源**: `SceneManager.Instance.carList`

---

### 2. `CabinetRunning_U` — 药柜运行状态

| 字段 | ROS 类型 | C# 类型 | 说明 |
|------|----------|---------|------|
| `cabinet_id` | `uint8` | `byte` | 药柜 ID |
| `isrunning` | `uint8` | `byte` | 1=运行中，0=停止 |

- **脚本**: `Assets/scripts/MyMsgScripts/SendMsg/SendCabinet_Running.cs`
- **ROS 消息名**: `task_msgs/CabinetRunning`
- **发送频率**: 每 1.2 秒

---

### 3. `CabinetState_U` — 药柜药品库存状态

| 字段 | ROS 类型 | C# 类型 | 说明 |
|------|----------|---------|------|
| `cabinet_id` | `uint8` | `byte` | 药柜 ID |
| `medicine_list` | `MedicineData[]` | `MedicineDataMsg[]` | 药品数据数组（45格） |

**内嵌 MedicineData 结构**：

| 字段 | ROS 类型 | C# 类型 | 说明 |
|------|----------|---------|------|
| `row` | `uint8` | `byte` | 行号 |
| `column` | `uint8` | `byte` | 列号 |
| `count` | `uint8` | `byte` | 药品数量 |

- **脚本**: `Assets/scripts/MyMsgScripts/SendMsg/SendCabinetState.cs`
- **ROS 消息名**: `task_msgs/CabinetState`
- **发送频率**: 每 1.5 秒
- **说明**: 固定填充 45 个格子（5行×9列），无药品的位置 count=0

---

### 4. `TaskState_U` — 任务状态

| 字段 | ROS 类型 | C# 类型 | 说明 |
|------|----------|---------|------|
| `taskid` | `string` | `string` | 任务 ID |
| `task_state` | `int32` | `int` | 0=未执行，1=执行中，2=执行结束 |
| `car_id` | `int32` | `int` | 执行任务的小车 ID |

- **脚本**: `Assets/scripts/MyMsgScripts/SendMsg/SendTaskState.cs`
- **ROS 消息名**: `task_msgs/TaskState`
- **发送频率**: 每 2.0 秒

---

### 5. `TaskData_U` — 完整任务数据

| 字段 | ROS 类型 | C# 类型 | 说明 |
|------|----------|---------|------|
| `task_id` | `string` | `string` | 任务 ID |
| `cabinets` | `CabinetOrder[]` | `CabinetOrderMsg[]` | 订单中的药柜列表 |
| `type` | `string` | `string` | 任务类型 |

**内嵌 CabinetOrder 结构**：

| 字段 | ROS 类型 | C# 类型 | 说明 |
|------|----------|---------|------|
| `cabinet_id` | `string` | `string` | 药柜 ID |
| `medicine_list` | `MedicineData[]` | `MedicineDataMsg[]` | 该药柜的取药列表 |

**内嵌 MedicineData 结构**：

| 字段 | ROS 类型 | C# 类型 | 说明 |
|------|----------|---------|------|
| `row` | `uint8` | `byte` | 行号 |
| `column` | `uint8` | `byte` | 列号 |
| `count` | `uint8` | `byte` | 需取数量 |

- **脚本**: `Assets/scripts/MyMsgScripts/SendMsg/SendTaskMsg.cs`
- **ROS 消息名**: `task_msgs/Task`
- **发送频率**: 每 1.0 秒（独立协程，不由 SendMsgManager 管理）
- **说明**: 目前发送硬编码测试数据，未接入实际业务逻辑

---

### 6. `PC2P1` — 点云数据

| 字段 | ROS 类型 | C# 类型 | 说明 |
|------|----------|---------|------|
| `header` | `Header` | `HeaderMsg` | frame_id = "map" |
| `height` | `uint32` | `uint` | 固定为 1（无序点云） |
| `width` | `uint32` | `uint` | 点的数量 |
| `fields` | `PointField[]` | `PointFieldMsg[]` | 3 个字段: x, y, z (float32) |
| `is_bigendian` | `bool` | `bool` | false |
| `point_step` | `uint32` | `uint` | 固定 12（3 × float32） |
| `row_step` | `uint32` | `uint` | point_step × width |
| `data` | `uint8[]` | `byte[]` | 点云二进制数据 |
| `is_dense` | `bool` | `bool` | false |

**PointField 结构**（x, y, z 各一个）：

| 字段 | 值 |
|------|-----|
| name | "x" / "y" / "z" |
| offset | 0 / 4 / 8 |
| datatype | 7 (FLOAT32) |
| count | 1 |

- **脚本**: `Assets/scripts/PointCloud2Publish.cs`
- **ROS 消息名**: `test/PointCloud2`
- **数据来源**: `PointCloudRadar.cs` 射线检测碰撞点
- **发送频率**: 每 0.5 秒

---

### 7. `RosImage` — 相机图像

| 字段 | ROS 类型 | C# 类型 | 说明 |
|------|----------|---------|------|
| `header` | `Header` | `HeaderMsg` | frame_id = "image" |
| `height` | `uint32` | `uint` | 图像高度（像素） |
| `width` | `uint32` | `uint` | 图像宽度（像素） |
| `encoding` | `string` | `string` | 固定 "rgb8" |
| `is_bigendian` | `uint8` | `byte` | 小端 = 0 |
| `step` | `uint32` | `uint` | width × 3（每行字节数） |
| `data` | `uint8[]` | `byte[]` | RGB 像素数据（已上下翻转） |

- **脚本**: `Assets/scripts/ROSImage/ROSImagePublish.cs`
- **ROS 消息名**: `Assets/Image`
- **触发方式**: 按键盘 Q 键发送
- **数据来源**: `RenderTexture` → `AsyncGPUReadback`

---

### 8. `pos_rot` — 位置旋转（测试用）

| 字段 | ROS 类型 | C# 类型 | 说明 |
|------|----------|---------|------|
| `pos_x` | `float32` | `float` | 位置 X |
| `pos_y` | `float32` | `float` | 位置 Y |
| `pos_z` | `float32` | `float` | 位置 Z |
| `rot_x` | `float32` | `float` | 四元数 X |
| `rot_y` | `float32` | `float` | 四元数 Y |
| `rot_z` | `float32` | `float` | 四元数 Z |
| `rot_w` | `float32` | `float` | 四元数 W |

- **脚本**: `Assets/scripts/Test/RosPublisherExample.cs`
- **ROS 消息名**: `unity_robotics_demo_msgs/PosRot`
- **发送频率**: 每 0.5 秒（仅测试 Demo）

---

## 二、ROS → Unity（接收）

### 1. `/task_topic` — 接收任务指令

**消息类型**: `task_msgs/Task`

| 字段 | ROS 类型 | C# 类型 | 说明 |
|------|----------|---------|------|
| `task_id` | `string` | `string` | 任务 ID |
| `cabinets` | `CabinetOrder[]` | `CabinetOrderMsg[]` | 药柜订单列表 |
| `type` | `string` | `string` | 任务类型 |

完整嵌套结构与发送端 **TaskData_U** 的 `TaskMsg` 完全一致（见 一.5）。

- **处理逻辑**: 收到任务后存入 `TaskList` 和 `TaskListData`，标记 `SceneManager.IsRefreshTask = true`
- **Topic 名称**: `task_topic`（实测确认，2026-05-23 重建后 Unity 订阅此话题）

---

### 2. `color` — 颜色指令（测试用）

| 字段 | ROS 类型 | C# 类型 | 说明 |
|------|----------|---------|------|
| `r` | `int32` | `int` | 红色分量 |
| `g` | `int32` | `int` | 绿色分量 |
| `b` | `int32` | `int` | 蓝色分量 |
| `a` | `int32` | `int` | 透明度 |

- **脚本**: `Assets/scripts/Test/RosSubscriberExample.cs`
- **ROS 消息名**: `unity_robotics_demo_msgs/UnityColor`
- **功能**: 改变测试物体的材质颜色

---

## 三、消息总览

| Topic | 方向 | ROS 消息名 | 发送频率 | 用途 |
|-------|------|------------|----------|------|
| `CarState_U` | → | `task_msgs/CarState` | 1.0 s | 小车位置与运行状态上报 |
| `CabinetRunning_U` | → | `task_msgs/CabinetRunning` | 1.2 s | 药柜运行状态上报 |
| `CabinetState_U` | → | `task_msgs/CabinetState` | 1.5 s | 药柜药品库存上报 |
| `TaskState_U` | → | `task_msgs/TaskState` | 2.0 s | 任务执行状态上报 |
| `TaskData_U` | → | `task_msgs/Task` | 1.0 s | 完整任务数据下发 |
| `PC2P1` | → | `test/PointCloud2` | 0.5 s | 激光雷达点云数据 |
| `RosImage` | → | `Assets/Image` | 按键 Q | 相机画面采集 |
| `pos_rot` | → | `unity_robotics_demo_msgs/PosRot` | 0.5 s | Demo 测试 |
| `task_topic` | ← | `task_msgs/Task` | — | 接收任务指令（ROS 发布） |
| `color` | ← | `unity_robotics_demo_msgs/UnityColor` | — | Demo 测试（ROS 发布） |

## 四、发送架构

所有周期性发送的消息由 `SendMsgManager` 统一管理（除 `TaskData_U` 和 `pos_rot` 外）：

```
SendMsgManager (MonoBehaviour)
├── SendCarMessage()          → 每 1.0 s
│   └── SendCarState()        → sendCarState.SendMessage_Ros()
│                               → ros.Publish("CarState_U", CarStateMsg)
├── SendCabinetsRunningMessage() → 每 1.2 s
│   └── SendCabinetsRunning() → sendCabinetRunning.SendMessage_Ros()
│                               → ros.Publish("CabinetRunning_U", CabinetRunningMsg)
├── SendCabinetsStateMessage() → 每 1.5 s
│   └── SendCabinetsState()   → sendCabinetState.SendMessage_Ros()
│                               → ros.Publish("CabinetState_U", CabinetStateMsg)
└── SendTaskMessage()         → 每 2.0 s
    └── SendTaskState()       → sendTaskState.SendMessage_Ros()
                                → ros.Publish("TaskState_U", TaskStateMsg)

独立发送：
├── SendTaskMsg (独立协程)    → 每 1.0 s
│                               → ros.Publish("TaskData_U", TaskMsg)
├── PointCloudRadar → PointCloud2Publish → 每 0.5 s
│                               → ros.Publish("PC2P1", PointCloud2Msg)
└── ROSImagePublish (按键触发) → 按 Q
                                → ros.Publish("RosImage", ImageMsg)
```
