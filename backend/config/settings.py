import os

class Config:
    """应用配置"""
    # 数据库配置
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'pharmacy.db')

    # 服务器配置
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8001))

    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    # ROS2配置
    ENABLE_ROS2 = os.getenv('ENABLE_ROS2', 'true').lower() == 'true'

    # CORS配置
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')

    @classmethod
    def to_dict(cls):
        """转换为字典格式"""
        return {
            'database_path': cls.DATABASE_PATH,
            'host': cls.HOST,
            'port': cls.PORT,
            'log_level': cls.LOG_LEVEL,
            'enable_ros2': cls.ENABLE_ROS2,
            'cors_origins': cls.CORS_ORIGINS
        }