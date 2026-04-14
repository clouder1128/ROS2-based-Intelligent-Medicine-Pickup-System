"""
配置管理 - 统一管理ROS2集成相关配置
"""

import os
from dataclasses import dataclass, field
from typing import List

@dataclass
class Config:
    """主配置类"""

    # 集成模式控制
    INTEGRATION_MODE: str = field(default_factory=lambda: os.getenv("ROS_INTEGRATION_MODE", "new"))
    """集成模式: 'new'(新模块), 'legacy'(旧模块), 'parallel'(并行)"""

    # ROS2配置
    ROS_NODE_NAME: str = "backend_ros_integration"
    ROS_DOMAIN_ID: int = field(default_factory=lambda: int(os.getenv("ROS_DOMAIN_ID", "0")))

    # TCP服务器配置
    TCP_SERVER_ENABLED: bool = field(default_factory=lambda: os.getenv("ROS_TCP_ENABLED", "True").lower() == "true")
    TCP_IP: str = field(default_factory=lambda: os.getenv("ROS_IP", "0.0.0.0"))
    TCP_PORT: int = field(default_factory=lambda: int(os.getenv("ROS_TCP_PORT", "10000")))

    # 话题配置
    TASK_TOPIC_NEW: str = "/task_topic"
    TASK_TOPIC_LEGACY: str = "/task_request"
    TASK_STATE_TOPIC: str = "/TaskState_U"
    CAR_STATE_TOPIC: str = "/CarState_U"
    CABINET_STATE_TOPIC: str = "/CabinetState_U"

    # 性能配置
    PUBLISH_TIMEOUT_SEC: float = 5.0
    MAX_RETRY_ATTEMPTS: int = 3
    RETRY_DELAYS: List[float] = field(default_factory=lambda: [1.0, 5.0, 15.0])  # 指数退避延迟

    # 健康检查配置
    HEALTH_CHECK_INTERVAL_SEC: int = 30
    DEGRADATION_THRESHOLD: int = 10  # 连续失败次数阈值

    def validate(self) -> bool:
        """验证配置有效性"""
        if self.INTEGRATION_MODE not in ["new", "legacy", "parallel"]:
            raise ValueError(f"Invalid INTEGRATION_MODE: {self.INTEGRATION_MODE}")
        if self.TCP_PORT <= 0 or self.TCP_PORT > 65535:
            raise ValueError(f"Invalid TCP_PORT: {self.TCP_PORT}")
        return True


@dataclass
class TopicConfig:
    """话题配置常量"""

    # 发布话题
    TASK_TOPIC_NEW: str = "/task_topic"
    TASK_TOPIC_LEGACY: str = "/task_request"

    # 订阅话题
    TASK_STATE_TOPIC: str = "/TaskState_U"
    CAR_STATE_TOPIC: str = "/CarState_U"
    CABINET_STATE_TOPIC: str = "/CabinetState_U"

    # 服务质量配置
    QOS_DEPTH: int = 10
    QOS_RELIABILITY: str = "RELIABLE"  # ROS2 QoS可靠性策略
    QOS_DURABILITY: str = "VOLATILE"   # ROS2 QoS持久性策略