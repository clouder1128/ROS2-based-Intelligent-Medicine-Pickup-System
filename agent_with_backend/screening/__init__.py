"""
组件3：智能筛选系统

避免在包导入时加载 SQLAlchemy 模型（加快 main 启动、减少硬依赖）。
需要模型时请使用：`from screening.models import ...`
"""

__version__ = "1.0.0"
