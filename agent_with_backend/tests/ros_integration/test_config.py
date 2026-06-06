"""ros_integration.config 及 TopicConfig 单元测试"""

from ros_integration.config import Config, TopicConfig


class TestConfigDefaults:
    def test_default_integration_mode(self):
        c = Config()
        assert c.INTEGRATION_MODE == "new"

    def test_default_ros_domain_id(self):
        c = Config()
        assert c.ROS_DOMAIN_ID == 0

    def test_default_tcp_settings(self):
        c = Config()
        assert c.TCP_SERVER_ENABLED is True
        assert c.TCP_IP == "0.0.0.0"
        assert c.TCP_PORT == 10000

    def test_default_topic_names(self):
        c = Config()
        assert c.TASK_TOPIC_NEW == "/task_topic"
        assert c.TASK_TOPIC_LEGACY == "/task_request"
        assert c.TASK_STATE_TOPIC == "/TaskState_U"
        assert c.CAR_STATE_TOPIC == "/CarState_U"
        assert c.CABINET_STATE_TOPIC == "/CabinetState_U"

    def test_default_performance_settings(self):
        c = Config()
        assert c.PUBLISH_TIMEOUT_SEC == 5.0
        assert c.MAX_RETRY_ATTEMPTS == 3
        assert c.RETRY_DELAYS == [1.0, 5.0, 15.0]

    def test_default_health_settings(self):
        c = Config()
        assert c.HEALTH_CHECK_INTERVAL_SEC == 30
        assert c.DEGRADATION_THRESHOLD == 10

    def test_ros_node_name(self):
        c = Config()
        assert c.ROS_NODE_NAME == "backend_ros_integration"


class TestConfigEnvOverrides:
    def test_integration_mode_from_env(self, monkeypatch):
        monkeypatch.setenv("ROS_INTEGRATION_MODE", "parallel")
        c = Config()
        assert c.INTEGRATION_MODE == "parallel"

    def test_ros_domain_id_from_env(self, monkeypatch):
        monkeypatch.setenv("ROS_DOMAIN_ID", "5")
        c = Config()
        assert c.ROS_DOMAIN_ID == 5

    def test_tcp_port_from_env(self, monkeypatch):
        monkeypatch.setenv("ROS_TCP_PORT", "20000")
        c = Config()
        assert c.TCP_PORT == 20000

    def test_tcp_ip_from_env(self, monkeypatch):
        monkeypatch.setenv("ROS_IP", "192.168.1.100")
        c = Config()
        assert c.TCP_IP == "192.168.1.100"

    def test_tcp_disabled_from_env(self, monkeypatch):
        monkeypatch.setenv("ROS_TCP_ENABLED", "false")
        c = Config()
        assert c.TCP_SERVER_ENABLED is False


class TestConfigValidation:
    def test_validate_valid(self):
        c = Config()
        assert c.validate() is True

    def test_validate_invalid_mode(self):
        c = Config()
        c.INTEGRATION_MODE = "invalid"
        import re
        with pytest.raises(ValueError, match="Invalid INTEGRATION_MODE"):
            c.validate()

    def test_validate_invalid_tcp_port_zero(self):
        c = Config()
        c.TCP_PORT = 0
        with pytest.raises(ValueError, match="Invalid TCP_PORT"):
            c.validate()

    def test_validate_invalid_tcp_port_negative(self):
        c = Config()
        c.TCP_PORT = -1
        with pytest.raises(ValueError, match="Invalid TCP_PORT"):
            c.validate()

    def test_validate_invalid_tcp_port_overflow(self):
        c = Config()
        c.TCP_PORT = 65536
        with pytest.raises(ValueError, match="Invalid TCP_PORT"):
            c.validate()


class TestTopicConfig:
    def test_topic_constants(self):
        tc = TopicConfig()
        assert tc.TASK_TOPIC_NEW == "/task_topic"
        assert tc.TASK_TOPIC_LEGACY == "/task_request"
        assert tc.TASK_STATE_TOPIC == "/TaskState_U"
        assert tc.CAR_STATE_TOPIC == "/CarState_U"
        assert tc.CABINET_STATE_TOPIC == "/CabinetState_U"

    def test_qos_settings(self):
        tc = TopicConfig()
        assert tc.QOS_DEPTH == 10
        assert tc.QOS_RELIABILITY == "RELIABLE"
        assert tc.QOS_DURABILITY == "VOLATILE"


import pytest  # noqa: F811 — keep import at bottom for top-level test classes above
