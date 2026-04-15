# ROS2智能取药系统仿真项目

## 项目概述

本项目是一个基于ROS2和Unity的智能取药系统仿真平台。系统模拟医院/药房自动化运输流程，通过ROS2与Unity仿真环境进行实时通信，实现"小车取药-运输-交付"的全流程自动化仿真。

## 系统架构

```
┌─────────────────┐    ROS2通信    ┌─────────────────┐
│   Unity仿真环境  │◄─────────────►│   ROS2工作空间  │
│   (Windows)     │    TCP/IP     │   (Linux)      │
└─────────────────┘                └─────────────────┘
```

### 技术栈
- **ROS2 Humble** - 机器人操作系统
- **Unity 2022.3 LTS** - 3D仿真环境
- **Unity.Robotics.ROSTCPConnector** - ROS-Unity通信插件
- **Dreamteck Splines** - Unity轨迹控制插件
- **DOTween** - Unity动画补间插件

## 功能模块

### 1. Unity仿真模块
- **车辆控制**：多小车轨迹跟随、任务分配、防撞检测
- **药柜控制**：9×5药品矩阵管理、机械臂控制、药品库存跟踪
- **ROS通信**：任务订阅、状态发布、传感器数据仿真
- **UI管理**：任务面板显示、任务分配、状态监控

### 2. ROS2通信模块
- **ROS-TCP-Endpoint**：Unity与ROS2的TCP通信接口
- **任务消息定义**：自定义ROS消息类型，支持任务数据交换
- **状态监控**：实时发布系统运行状态

## 环境要求

### 硬件要求
- **Windows端**：运行Unity仿真程序
- **Linux端**：运行ROS2系统（推荐Ubuntu 22.04）

### 软件要求
- **Unity 2022.3 LTS** 或更高版本
- **ROS2 Humble** 或兼容版本
- **Python 3.8+** (用于ROS2脚本)

## 目录结构

```
ROS2-based-Intelligent-Medicine-Pickup-System/
├── ros_workspace/                    # ROS2工作空间
│   ├── src/
│   │   ├── ROS-TCP-Endpoint/        # ROS-TCP连接器
│   │   └── task_msgs/               # 任务消息定义
│   ├── build/                       # ROS构建产物
│   ├── install/                     # ROS安装产物
│   └── log/                         # ROS日志文件
│
├── unity_simulation/                 # Unity仿真
│   ├── ROSPackage/                  # Unity项目源码
│   │   ├── Assets/                  # 资源文件（脚本、模型、材质等）
│   │   ├── ProjectSettings/         # Unity项目设置
│   │   ├── Packages/                # Unity包管理
│   │   └── build/                   # Unity构建产物
│   ├── RosCar/                      # Unity可执行程序
│   ├── ROSPackage.rar               # Unity项目源码压缩包
│   └── RosCar.rar                   # 可执行程序压缩包
│
├── docs/                            # 项目文档
│   ├── README.md                    # 项目总说明（本文档）
│   ├── API_Interface.md             # ROS接口文档
│   └── QuickStart.md                # 快速开始指南
│
├── configs/                         # 配置文件
│   ├── ros2.txt                     # ROS2使用说明
│   ├── tasks.json                   # 任务配置文件
│   └── 说明.txt                      # 项目说明
│
└── .gitignore                       # Git忽略规则
```

## 快速开始

详细步骤请参考 [QuickStart.md](QuickStart.md)，简要流程如下：

1. **Linux端（ROS2）**：
   - 配置ROS2环境
   - 启动ROS-TCP-Endpoint服务器
   - 运行测试任务发布器

2. **Windows端（Unity）**：
   - 运行Unity可执行程序
   - 配置ROS服务器IP地址
   - 启动仿真系统

## 项目特点

1. **模块化设计**：ROS通信、车辆控制、药柜操作、UI管理分离清晰
2. **状态驱动**：任务状态、车辆状态、药柜状态全程跟踪
3. **配置灵活**：ROS IP外部配置、车辆参数Inspector可调
4. **仿真完备**：包含点云雷达、视觉摄像头等传感器仿真
5. **生产就绪**：包含完整的错误处理和日志输出

## 接口文档

详细的ROS Topic和消息格式请参考 [API_Interface.md](API_Interface.md)。

## 许可证

本项目基于开源许可证发布，具体请查看各子目录中的LICENSE文件。

## 贡献指南

欢迎提交Issue和Pull Request来改进本项目。

## 联系方式

如有问题，请通过GitHub Issues页面提交。

---
*文档更新时间：2026-04-07*