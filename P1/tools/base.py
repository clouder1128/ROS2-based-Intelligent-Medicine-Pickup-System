from typing import Any, Dict, Optional
from abc import ABC, abstractmethod


class BaseTool(ABC):
    """工具基类，定义标准接口"""

    name: str
    description: str
    input_schema: Dict[str, Any]

    def __init__(self, name: str, description: str, input_schema: Dict[str, Any]):
        self.name = name
        self.description = description
        self.input_schema = input_schema

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """执行工具逻辑"""
        pass

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入是否符合schema"""
        # 简化验证：检查必需字段
        required = self.input_schema.get("required", [])
        for field in required:
            if field not in input_data:
                return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """转换为LLM工具定义格式"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema
        }