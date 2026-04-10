# tests/test_backend_config.py
"""Comprehensive tests for backend configuration module."""
import os
import sys
import pytest
from unittest.mock import patch

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def test_config_class_exists():
    """Test that Config class exists and can be imported."""
    from config.settings import Config
    assert Config is not None
    assert hasattr(Config, 'to_dict')


def test_config_default_values():
    """Test that Config class has default values."""
    from config.settings import Config

    # Clear environment to test defaults
    with patch.dict(os.environ, {}, clear=True):
        # Need to reload the module to pick up new environment
        import importlib
        import config.settings
        importlib.reload(config.settings)
        from config.settings import Config as ReloadedConfig

        assert ReloadedConfig.HOST == '0.0.0.0'
        assert ReloadedConfig.PORT == 8001
        assert ReloadedConfig.LOG_LEVEL == 'INFO'
        assert ReloadedConfig.ENABLE_ROS2 == True
        assert ReloadedConfig.CORS_ORIGINS == '*'
        assert 'pharmacy.db' in ReloadedConfig.DATABASE_PATH  # Should contain the filename


def test_config_port_validation():
    """Test PORT validation with various inputs."""
    from config.settings import Config

    test_cases = [
        # (env_value, expected_port, description)
        ('9000', 9000, 'Valid port number'),
        ('8080', 8080, 'Another valid port'),
        ('3000', 3000, 'Common development port'),
        ('1', 1, 'Minimum valid port'),
        ('65535', 65535, 'Maximum valid port'),
        ('not_a_number', 8001, 'Non-numeric string falls back to default'),
        ('', 8001, 'Empty string falls back to default'),
        ('0', 8001, 'Port 0 is invalid, falls back to default'),
        ('-1', 8001, 'Negative port falls back to default'),
        ('65536', 8001, 'Port too high falls back to default'),
        ('70000', 8001, 'Port way too high falls back to default'),
    ]

    for env_value, expected_port, description in test_cases:
        with patch.dict(os.environ, {'PORT': env_value}, clear=True):
            # Need to reload the module to pick up new environment
            import importlib
            import config.settings
            importlib.reload(config.settings)
            from config.settings import Config as ReloadedConfig

            assert ReloadedConfig.PORT == expected_port, \
                f"{description}: Expected port {expected_port} when PORT='{env_value}', got {ReloadedConfig.PORT}"


def test_config_environment_overrides():
    """Test that environment variables properly override defaults."""
    from config.settings import Config

    with patch.dict(os.environ, {
        'HOST': '127.0.0.1',
        'LOG_LEVEL': 'DEBUG',
        'ENABLE_ROS2': 'false',
        'CORS_ORIGINS': 'http://localhost:3000',
        'DATABASE_PATH': '/custom/path/database.db'
    }, clear=True):
        # Need to reload the module to pick up new environment
        import importlib
        import config.settings
        importlib.reload(config.settings)
        from config.settings import Config as ReloadedConfig

        assert ReloadedConfig.HOST == '127.0.0.1'
        assert ReloadedConfig.LOG_LEVEL == 'DEBUG'
        assert ReloadedConfig.ENABLE_ROS2 == False
        assert ReloadedConfig.CORS_ORIGINS == 'http://localhost:3000'
        assert ReloadedConfig.DATABASE_PATH == '/custom/path/database.db'


def test_config_to_dict_method():
    """Test the to_dict() method returns correct dictionary."""
    from config.settings import Config

    with patch.dict(os.environ, {}, clear=True):
        # Need to reload the module to pick up clean environment
        import importlib
        import config.settings
        importlib.reload(config.settings)
        from config.settings import Config as ReloadedConfig

        config_dict = ReloadedConfig.to_dict()

        expected_keys = ['database_path', 'host', 'port', 'log_level', 'enable_ros2', 'cors_origins']
        for key in expected_keys:
            assert key in config_dict, f"Missing key '{key}' in to_dict() output"

        assert config_dict['host'] == '0.0.0.0'
        assert config_dict['port'] == 8001
        assert config_dict['log_level'] == 'INFO'
        assert config_dict['enable_ros2'] == True
        assert config_dict['cors_origins'] == '*'


def test_config_ros2_boolean_parsing():
    """Test ENABLE_ROS2 boolean parsing from environment."""
    from config.settings import Config

    test_cases = [
        ('true', True),
        ('True', True),
        ('TRUE', True),
        ('false', False),
        ('False', False),
        ('FALSE', False),
        ('1', True),  # Should be treated as string '1', not boolean
        ('0', False), # Should be treated as string '0', not boolean
        ('yes', False),  # Not recognized as true, should be False
        ('no', False),   # Not recognized as true, should be False
    ]

    for env_value, expected in test_cases:
        with patch.dict(os.environ, {'ENABLE_ROS2': env_value}, clear=True):
            # Need to reload the module to pick up new environment
            import importlib
            import config.settings
            importlib.reload(config.settings)
            from config.settings import Config as ReloadedConfig

            assert ReloadedConfig.ENABLE_ROS2 == expected, \
                f"ENABLE_ROS2='{env_value}' should be {expected}, got {ReloadedConfig.ENABLE_ROS2}"


def test_config_database_path_absolute():
    """Test that DATABASE_PATH is converted to absolute path."""
    from config.settings import Config

    with patch.dict(os.environ, {}, clear=True):
        # Need to reload the module to pick up clean environment
        import importlib
        import config.settings
        importlib.reload(config.settings)
        from config.settings import Config as ReloadedConfig

        # The path should be absolute
        db_path = ReloadedConfig.DATABASE_PATH
        assert os.path.isabs(db_path), f"DATABASE_PATH should be absolute, got: {db_path}"
        assert db_path.endswith('pharmacy.db'), f"DATABASE_PATH should end with 'pharmacy.db', got: {db_path}"

    # Test custom path from environment
    custom_path = '/custom/path/to/database.db'
    with patch.dict(os.environ, {'DATABASE_PATH': custom_path}, clear=True):
        import importlib
        import config.settings
        importlib.reload(config.settings)
        from config.settings import Config as ReloadedConfig

        assert ReloadedConfig.DATABASE_PATH == custom_path, \
            f"DATABASE_PATH should be '{custom_path}', got: {ReloadedConfig.DATABASE_PATH}"


if __name__ == '__main__':
    # Simple test runner for backward compatibility
    test_config_class_exists()
    print("✓ test_config_class_exists passed")

    test_config_default_values()
    print("✓ test_config_default_values passed")

    test_config_port_validation()
    print("✓ test_config_port_validation passed")

    test_config_environment_overrides()
    print("✓ test_config_environment_overrides passed")

    test_config_to_dict_method()
    print("✓ test_config_to_dict_method passed")

    test_config_ros2_boolean_parsing()
    print("✓ test_config_ros2_boolean_parsing passed")

    test_config_database_path_absolute()
    print("✓ test_config_database_path_absolute passed")

    print("\nAll tests passed!")