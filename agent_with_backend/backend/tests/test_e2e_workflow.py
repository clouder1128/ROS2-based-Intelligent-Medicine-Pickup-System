"""
端到端工作流测试 - 从API调用到ROS2发布完整流程
"""
import pytest
import json
import time
from flask import Flask
from flask.testing import FlaskClient

@pytest.mark.e2e
class TestEndToEndWorkflow:
    """端到端工作流测试"""

    @pytest.fixture
    def app(self):
        """创建测试Flask应用"""
        import sys
        import os
        # 添加backend目录到路径
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from main import app as flask_app
        flask_app.config['TESTING'] = True
        return flask_app

    @pytest.fixture
    def client(self, app):
        """测试客户端"""
        return app.test_client()

    def test_complete_medication_pickup_flow(self, client):
        """完整取药流程测试"""
        # 1. 检查系统健康
        health_response = client.get('/api/health')
        assert health_response.status_code == 200
        health_data = json.loads(health_response.data)
        assert health_data['success'] is True

        # 2. 检查ROS2详细状态
        ros2_response = client.get('/api/health/ros2')
        assert ros2_response.status_code == 200
        ros2_data = json.loads(ros2_response.data)
        print(f"ROS2 Status: {ros2_data}")

        # 3. 创建药品（如果需要）
        # 这里可以添加药品创建逻辑

        # 4. 创建订单（触发ROS2发布）
        order_data = {
            "drug_name": "布洛芬",
            "quantity": 3,
            "doctor_name": "测试医生",
            "patient_name": "测试患者"
        }

        order_response = client.post('/api/orders', json=order_data)
        # 注意：实际API可能需要调整

        # 5. 验证ROS2消息发布
        # 这里需要集成TestRos2FullIntegration的监控能力

    def test_expiry_cleanup_flow(self, client):
        """过期清理流程测试"""
        # 1. 模拟过期药品
        # 2. 触发过期清扫
        # 3. 验证ROS2清理消息发布
        pass