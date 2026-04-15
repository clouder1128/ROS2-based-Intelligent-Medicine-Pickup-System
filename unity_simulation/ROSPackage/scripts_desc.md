# Assets/scripts 文件夹分析报告

## 📊 文件统计
共发现 **22个C#脚本文件**（排除.meta元文件），分布在以下目录结构：

```
Assets/scripts/
├── PointCloudRadar.cs
├── PointCloud2Publish.cs
├── ROSImage/
│   └── ROSImagePublish.cs
├── Test/
│   ├── RosPublisherExample.cs
│   └── RosSubscriberExample.cs
├── MyMsgScripts/
│   ├── TaskSubscriber.cs
│   └── SendMsg/
│       ├── SendTaskMsg.cs
│       ├── SendCabinetState.cs
│       ├── SendCabinet_Running.cs
│       ├── SendTaskState.cs
│       └── SendCarState.cs
├── CarControl.cs
├── CarControl_2.cs
├── CarSplineController.cs
├── CabinetControl.cs
├── CameraController.cs
├── CatCameraControl.cs
├── MedicineCollider.cs
├── CanvasManager.cs
├── SceneManager.cs
├── SendMsgManager.cs
└── FixedAspectRatio.cs
```

## 🗂️ 功能分类

### 1. **ROS通信模块** (7个文件)
负责与ROS系统的数据交换：

- **发布端**：
  - `PointCloudRadar.cs` + `PointCloud2Publish.cs` - 雷达点云数据采集与发布
  - `ROSImagePublish.cs` - 相机图像数据发布
  - `SendTaskMsg.cs` - 模拟任务数据发布
  - `SendCabinetState.cs`/`SendCabinet_Running.cs`/`SendCarState.cs`/`SendTaskState.cs` - 各类状态信息发布
- **订阅端**：
  - `TaskSubscriber.cs` - 接收ROS任务指令

### 2. **车辆控制模块** (4个文件)
控制小车的运动逻辑：
- `CarControl.cs` - 基于**Dreamteck Splines插件**的轨迹跟随控制，支持停靠点、进出轨迹
- `CarControl_2.cs` - 任务导向的车辆控制，处理取药、运输、返回全流程
- `CarSplineController.cs` - 补充的轨迹控制器
- `CatCameraControl.cs` - 车辆相机控制

### 3. **药柜控制模块** (2个文件)
- `CabinetControl.cs` - 药柜机械控制，管理前后移动轴、左右移动轴、推药盒动作
- `MedicineCollider.cs` - 药品碰撞检测

### 4. **系统管理模块** (3个文件)
- `SceneManager.cs` - **核心管理器**，初始化ROS连接、维护车辆队列、药柜列表
- `CanvasManager.cs` - UI管理，任务面板显示、任务分配逻辑
- `SendMsgManager.cs` - 周期性状态消息发送调度器

### 5. **辅助工具模块** (3个文件)
- `CameraController.cs` - 通用相机控制
- `FixedAspectRatio.cs` - 屏幕宽高比固定
- `Test/`目录 - ROS通信示例代码

### 6. **测试示例模块** (2个文件)
- `RosPublisherExample.cs` - ROS发布示例
- `RosSubscriberExample.cs` - ROS订阅示例

## 🏗️ 项目架构分析

### 系统概述
这是一个**医院/药房自动化运输系统的Unity仿真项目**，通过ROS与外部机器人系统集成，模拟"小车取药-运输-交付"的全流程。

### 核心工作流程
1. **任务接收**：`TaskSubscriber`从ROS订阅任务消息 → 存入`SceneManager.taskSub.TaskList`
2. **UI展示**：`CanvasManager`刷新任务面板，显示"未执行/执行中/执行完成"状态
3. **任务分配**：用户点击任务按钮 → 从`carQueue`取出空闲车辆 → 分配给`CarControl_2`
4. **执行阶段**：
   - 车辆移动到指定药柜 (`MedicineTargetPos`)
   - 触发`CabinetControl`执行取药动画（前后/左右轴移动 + 推药盒）
   - 根据任务类型（0=发货区/1=取药区）前往不同目的地
   - 完成交付后返回起点，重新加入队列

### 关键技术栈
- **ROS集成**：使用`Unity.Robotics.ROSTCPConnector`包
- **运动控制**：Dreamteck Splines（轨迹跟随） + DOTween（动画补间）
- **数据管理**：自定义`TaskData`结构维护任务状态
- **物理检测**：Raycast射线检测防碰撞

### 数据流向
```
ROS网络 → TaskSubscriber → SceneManager → CanvasManager
                                     ↓
车辆队列 → CarControl_2 → CabinetControl → 完成反馈
                                     ↓
                          SendMsgManager → ROS状态发布
```

## 🔑 关键脚本详细说明

### [SceneManager.cs](Assets/scripts/SceneManager.cs)
**核心协调者**，负责：
- 从`ip.txt`读取ROS服务器配置
- 维护`carList`（所有车辆）和`carQueue`（空闲车辆队列）
- 管理`cabinetList`（所有药柜）
- 提供`StartHSOrQy()`触发发货/取药动画

### [CarControl_2.cs](Assets/scripts/CarControl_2.cs)
**任务执行主力**，状态机设计：
- `CarState`: 0=空闲, 1=执行中, 2=前往发货区, 3=前往取药区
- 使用DOTween实现平滑移动，Raycast实现防撞暂停
- 与`CabinetControl`协同完成取药流程

### [CabinetControl.cs](Assets/scripts/CabinetControl.cs)
**药柜机械控制器**，9×5药品矩阵管理：
- `FirstMoveStart()`/`SecondMoveStart()` - 控制前后/左右轴定位
- `MovePushBox()` - 推药盒动画
- `MedicineCount[,]` - 实时药品库存跟踪

### [CanvasManager.cs](Assets/scripts/CanvasManager.cs)
**用户交互中枢**：
- 按F1显示/隐藏主面板
- 动态生成任务列表项
- 处理任务分配按钮点击事件
- 显示车辆分配状态和任务进度

## 📈 项目特点

1. **模块化设计**：ROS通信、车辆控制、药柜操作、UI管理分离清晰
2. **状态驱动**：任务状态、车辆状态、药柜状态全程跟踪
3. **配置灵活**：ROS IP外部配置、车辆参数Inspector可调
4. **仿真完备**：包含点云雷达、视觉摄像头等传感器仿真
5. **生产就绪**：包含完整的错误处理和日志输出

## ⚠️ 注意事项

1. **中文注释**：所有脚本使用中文注释，需注意编码问题
2. **硬编码依赖**：部分路径和参数硬编码，如`Application.streamingAssetsPath + "/ip.txt"`
3. **ROS消息类型**：依赖自定义ROS消息类型（`RosMessageTypes.Task`等）
4. **插件依赖**：需要Dreamteck Splines和DOTween插件支持

---

该代码库是一个功能完整的ROS-Unity联合仿真系统，适合医院物流自动化、AGV调度等场景的模拟与测试。

*文档生成时间：2026-04-04*