# tests/test_backend_config.py
"""Tests for common.config (backend configuration)."""

import os
import sys
import pytest
from unittest.mock import patch

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

_ENV_BASE = {"ANTHROPIC_API_KEY": "pytest-dummy-key"}


def _reload_config():
    import importlib

    import common.config as cc

    return importlib.reload(cc)


def test_config_class_exists():
    from common.config import Config

    assert Config is not None
    assert hasattr(Config, "to_dict")


def test_config_default_values():
    with patch.dict(os.environ, _ENV_BASE, clear=True):
        cc = _reload_config()
        C = cc.Config

        assert C.HOST == "0.0.0.0"
        assert C.PORT == 8001
        assert C.LOG_LEVEL == "INFO"
        assert C.ENABLE_ROS2 is True
        assert C.CORS_ORIGINS == "*"
        assert str(C.DATABASE_PATH).endswith("pharmacy.db")


def test_config_port_validation():
    cases = [
        ("9000", 9000),
        ("8080", 8080),
        ("1", 1),
        ("65535", 65535),
        ("not_a_number", 8001),
        ("", 8001),
        ("0", 8001),
        ("-1", 8001),
        ("65536", 8001),
        ("70000", 8001),
    ]
    for env_value, expected in cases:
        env = {**_ENV_BASE, "PORT": env_value}
        with patch.dict(os.environ, env, clear=True):
            cc = _reload_config()
            assert cc.Config.PORT == expected, f"PORT={env_value!r} -> expected {expected}"


def test_config_environment_overrides():
    env = {
        **_ENV_BASE,
        "HOST": "127.0.0.1",
        "LOG_LEVEL": "DEBUG",
        "ENABLE_ROS2": "false",
        "CORS_ORIGINS": "http://localhost:3000",
        "DATABASE_PATH": "/custom/path/database.db",
    }
    with patch.dict(os.environ, env, clear=True):
        cc = _reload_config()
        C = cc.Config

        assert C.HOST == "127.0.0.1"
        assert C.LOG_LEVEL == "DEBUG"
        assert C.ENABLE_ROS2 is False
        assert C.CORS_ORIGINS == "http://localhost:3000"
        assert C.DATABASE_PATH == "/custom/path/database.db"


def test_config_to_dict_method():
    with patch.dict(os.environ, _ENV_BASE, clear=True):
        cc = _reload_config()
        d = cc.Config.to_dict()

        for key in ("database_path", "host", "port", "log_level", "enable_ros2", "cors_origins"):
            assert key in d

        assert d["host"] == "0.0.0.0"
        assert d["port"] == 8001
        assert d["log_level"] == "INFO"
        assert d["enable_ros2"] is True
        assert d["cors_origins"] == "*"


def test_config_ros2_boolean_parsing():
    cases = [
        ("true", True),
        ("True", True),
        ("TRUE", True),
        ("false", False),
        ("False", False),
        ("FALSE", False),
        ("1", True),
        ("0", False),
        ("yes", False),
        ("no", False),
    ]
    for env_value, expected in cases:
        env = {**_ENV_BASE, "ENABLE_ROS2": env_value}
        with patch.dict(os.environ, env, clear=True):
            cc = _reload_config()
            assert cc.Config.ENABLE_ROS2 is expected, (
                f"ENABLE_ROS2={env_value!r} -> expected {expected}"
            )


def test_config_database_path_default_is_absolute():
    with patch.dict(os.environ, _ENV_BASE, clear=True):
        cc = _reload_config()
        db_path = cc.Config.DATABASE_PATH
        assert os.path.isabs(db_path), f"expected absolute path, got {db_path!r}"
        assert str(db_path).endswith("pharmacy.db")

    custom = "/custom/path/to/database.db"
    with patch.dict(os.environ, {**_ENV_BASE, "DATABASE_PATH": custom}, clear=True):
        cc = _reload_config()
        assert cc.Config.DATABASE_PATH == custom


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
