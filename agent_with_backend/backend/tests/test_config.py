"""
测试配置设置
"""
import os

def setup_test_environment():
    """设置测试环境变量"""
    os.environ.update({
        "ROS_INTEGRATION_MODE": "parallel",  # 测试并行模式
        "ROS_DOMAIN_ID": "42",  # 避免与其他ROS2节点冲突
        "ROS_TCP_ENABLED": "False",  # 测试期间禁用TCP
    })
    print("Test environment configured")