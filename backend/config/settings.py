import os
from pathlib import Path
from typing import Dict, Any


def _get_port() -> int:
    """Get port from environment with validation."""
    port_str = os.getenv('PORT', '8001')
    try:
        port = int(port_str)
    except ValueError:
        print(f"[Config] Warning: Invalid PORT value '{port_str}', using default 8001")
        port = 8001

    # Validate port range
    if port < 1 or port > 65535:
        print(f"[Config] Warning: Port {port} out of range (1-65535), using 8001")
        port = 8001

    return port


class Config:
    """应用配置"""
    # 数据库配置
    DATABASE_PATH: str = os.getenv('DATABASE_PATH', str(Path(__file__).parent.parent / 'pharmacy.db'))

    # 服务器配置
    HOST: str = os.getenv('HOST', '0.0.0.0')
    PORT: int = _get_port()

    # 日志配置
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')

    # ROS2配置
    ENABLE_ROS2: bool = os.getenv('ENABLE_ROS2', 'true').lower() in ['true', '1']

    # CORS配置
    CORS_ORIGINS: str = os.getenv('CORS_ORIGINS', '*')

    @classmethod
    def validate(cls) -> Dict[str, Any]:
        """Validate all configuration values and return validation results.

        Returns:
            Dict[str, Any]: Dictionary with validation results for each field
        """
        results = {
            'port': {
                'value': cls.PORT,
                'valid': 1 <= cls.PORT <= 65535,
                'message': 'Port must be between 1 and 65535'
            },
            'log_level': {
                'value': cls.LOG_LEVEL,
                'valid': cls.LOG_LEVEL.upper() in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                'message': 'Log level must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL'
            },
            'host': {
                'value': cls.HOST,
                'valid': bool(cls.HOST),  # Non-empty string
                'message': 'Host must not be empty'
            },
            'database_path': {
                'value': cls.DATABASE_PATH,
                'valid': bool(cls.DATABASE_PATH),  # Non-empty string
                'message': 'Database path must not be empty'
            },
            'enable_ros2': {
                'value': cls.ENABLE_ROS2,
                'valid': isinstance(cls.ENABLE_ROS2, bool),
                'message': 'ENABLE_ROS2 must be a boolean'
            },
            'cors_origins': {
                'value': cls.CORS_ORIGINS,
                'valid': bool(cls.CORS_ORIGINS),  # Non-empty string
                'message': 'CORS origins must not be empty'
            }
        }

        # Check if all validations passed
        results['all_valid'] = all(item['valid'] for item in results.values() if isinstance(item, dict))

        return results

    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'database_path': cls.DATABASE_PATH,
            'host': cls.HOST,
            'port': cls.PORT,
            'log_level': cls.LOG_LEVEL,
            'enable_ros2': cls.ENABLE_ROS2,
            'cors_origins': cls.CORS_ORIGINS
        }