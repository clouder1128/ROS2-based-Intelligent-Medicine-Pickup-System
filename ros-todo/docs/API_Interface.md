# ROS2接口文档

本文档描述了ROS2智能取药系统仿真项目中的所有ROS接口，包括Topic、消息格式和数据流。

## 概述

系统使用ROS2作为通信中间件，连接Unity仿真环境与ROS2工作空间。所有通信通过TCP/IP协议进行，使用ROS-TCP-Endpoint作为桥接器。

## ROS Topic列表

### 1. 任务相关Topic

| Topic名称 | 消息类型 | 发布者 | 订阅者 | 描述 |
|-----------|----------|--------|--------|------|
| `/task_topic` | `task_msgs/msg/Task` | ROS2 (`test_task_publisher.py`) | Unity (`TaskSubscriber.cs`) | 发布取药任务到Unity仿真 |
| `/TaskData_U` | 待确认 | Unity | ROS2 | 任务数据反馈（待确认） |

### 2. 状态监控Topic

| Topic名称 | 消息类型 | 发布者 | 订阅者 | 描述 |
|-----------|----------|--------|--------|------|
| `/CabinetRunning_U` | `task_msgs/msg/CabinetRunning` | Unity | ROS2 | 药柜运行状态 |
| `/CabinetState_U` | `task_msgs/msg/CabinetState` | Unity | ROS2 | 药柜当前状态（药品库存） |
| `/CarState_U` | `task_msgs/msg/CarState` | Unity | ROS2 | 车辆状态（位置、运行状态） |
| `/TaskState_U` | `task_msgs/msg/TaskState` | Unity | ROS2 | 任务执行状态 |

## 消息格式详解

### 1. Task消息 (`task_msgs/msg/Task`)
```ros
# Task.msg
string task_id                # 任务ID，如"task_001"
CabinetOrder[] cabinets       # 药柜订单列表
string type                   # 任务类型："0"=发货区，"1"=取药区
```

### 2. CabinetOrder消息 (`task_msgs/msg/CabinetOrder`)
```ros
# CabinetOrder.msg
string cabinet_id             # 药柜ID，如"cab_01"
MedicineData[] medicine_list  # 药品数据列表
```

### 3. MedicineData消息 (`task_msgs/msg/MedicineData`)
```ros
# MedicineData.msg
uint8 row     # 药品所在行（1-9）
uint8 column  # 药品所在列（1-5）
uint8 count   # 药品数量
```

### 4. CabinetRunning消息 (`task_msgs/msg/CabinetRunning`)
```ros
# CabinetRunning.msg
uint8 cabinet_id  # 药柜ID（0-255）
uint8 isrunning   # 运行状态：0=空闲，1=运行中
```

### 5. CabinetState消息 (`task_msgs/msg/CabinetState`)
```ros
# CabinetState.msg
uint8 cabinet_id            # 药柜ID（0-255）
MedicineData[] medicine_list # 当前药品库存列表
```

### 6. CarState消息 (`task_msgs/msg/CarState`)
```ros
# CarState.msg
uint8 car_id     # 车辆ID（0-255）
float32 x        # 车辆X坐标
float32 y        # 车辆Y坐标
uint8 isrunning  # 运行状态：0=空闲，1=运行中
```

### 7. TaskState消息 (`task_msgs/msg/TaskState`)
```ros
# TaskState.msg
string taskid      # 任务ID
int32 task_state   # 任务状态码
int32 car_id       # 执行任务的车辆ID
```

## 数据流图

```
┌─────────────────┐                ┌─────────────────┐
│    Unity仿真     │                │     ROS2工作空间 │
│                 │                │                 │
│  TaskSubscriber │◄──/task_topic──┤test_task_publisher│
│                 │                │                 │
│  SendMsgManager │──►/CarState_U──┤  状态监控节点     │
│                 │──►/CabinetState_U┤                 │
│                 │──►/CabinetRunning_U               │
│                 │──►/TaskState_U─►│                 │
└─────────────────┘                └─────────────────┘
```

## Unity脚本与ROS Topic对应关系

根据 `scripts_desc.md` 分析，Unity中的脚本与ROS Topic对应关系如下：

### 发布者脚本（Unity → ROS2）
- `SendCarState.cs` → `/CarState_U`
- `SendCabinetState.cs` → `/CabinetState_U`
- `SendCabinet_Running.cs` → `/CabinetRunning_U`
- `SendTaskState.cs` → `/TaskState_U`
- `SendTaskMsg.cs` → `/TaskData_U`（待确认）
- `SendMsgManager.cs` → 周期性状态消息调度器

### 订阅者脚本（ROS2 → Unity）
- `TaskSubscriber.cs` ← `/task_topic`（订阅任务指令）

### 传感器数据发布
- `PointCloudRadar.cs` + `PointCloud2Publish.cs` → 雷达点云数据
- `ROSImagePublish.cs` → 相机图像数据

## 通信配置

### ROS服务器配置
Unity通过 `ip.txt` 文件配置ROS服务器连接信息：
```
ROS_IP=192.168.x.x  # ROS2服务器IP地址
ROS_TCP_PORT=10000  # TCP端口号
```

文件位置：`Unity项目/StreamingAssets/ip.txt`

### ROS2启动命令
```bash
# 启动ROS-TCP-Endpoint服务器
ros2 run ros_tcp_endpoint default_server_endpoint --ros-args \
  -p ROS_IP:=0.0.0.0 \
  -p ROS_TCP_PORT:=10000
```

## 消息发布频率

1. **任务发布**：按需发布，通常由外部系统触发
2. **状态发布**：周期性发布，建议频率 1-10 Hz
3. **传感器数据**：根据仿真需求调整，通常 10-30 Hz

## 调试与监控

### 常用ROS2命令
```bash
# 查看所有活跃的Topic
ros2 topic list

# 实时监控特定Topic
ros2 topic echo /CabinetRunning_U --full
ros2 topic echo /CabinetState_U --full
ros2 topic echo /CarState_U --full
ros2 topic echo /TaskData_U --full

# 查看Topic信息
ros2 topic info /task_topic
ros2 interface show task_msgs/msg/Task
```

### 网络诊断
```bash
# 检查网络连接
ping <ROS服务器IP>

# 检查端口是否开放
telnet <ROS服务器IP> 10000
```

## 注意事项

1. **消息一致性**：确保Unity和ROS2使用相同的消息定义
2. **网络延迟**：TCP通信可能引入延迟，影响实时性
3. **数据同步**：状态消息需要时间戳以确保数据一致性
4. **错误处理**：实现适当的超时和重连机制

## 扩展接口

如需扩展系统功能，可参考以下模式：

1. **新增消息类型**：在 `task_msgs/msg/` 目录下创建新的 `.msg` 文件
2. **新增Topic**：在Unity和ROS2中分别实现发布者/订阅者
3. **服务调用**：如需请求-响应模式，可使用ROS Service

---
*文档更新时间：2026-04-07*