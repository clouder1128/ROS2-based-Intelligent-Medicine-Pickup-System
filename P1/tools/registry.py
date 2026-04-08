from typing import List, Dict, Any, Callable
from .executor import ToolExecutor

# 全局工具执行器实例
_executor = ToolExecutor()

# ==================== 工具定义（JSON Schema） ====================
TOOLS: List[Dict] = [
    {
        "name": "query_drug",
        "description": "根据症状或药品名称查询相关药物信息，返回药品列表（含规格、价格、库存、是否处方药）",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "症状关键词或药品名称"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "check_allergy",
        "description": "检查患者是否对某种药物过敏。需要提供患者过敏史和药物名称。",
        "input_schema": {
            "type": "object",
            "properties": {
                "patient_allergies": {"type": "string", "description": "患者已知过敏史，如'青霉素, 头孢'"},
                "drug_name": {"type": "string", "description": "要检查的药物名称"}
            },
            "required": ["patient_allergies", "drug_name"]
        }
    },
    {
        "name": "calc_dosage",
        "description": "根据患者年龄、体重、药品规格计算推荐剂量。",
        "input_schema": {
            "type": "object",
            "properties": {
                "drug_name": {"type": "string"},
                "age": {"type": "integer"},
                "weight_kg": {"type": "number"},
                "condition_severity": {"type": "string", "enum": ["轻", "轻度", "中", "中度", "重", "重度"]}
            },
            "required": ["drug_name", "age", "weight_kg"]
        }
    },
    {
        "name": "generate_advice",
        "description": "生成结构化的用药建议文本，供医生审批参考。",
        "input_schema": {
            "type": "object",
            "properties": {
                "drug_name": {"type": "string"},
                "dosage": {"type": "string"},
                "duration": {"type": "string"},
                "notes": {"type": "string"}
            },
            "required": ["drug_name", "dosage"]
        }
    },
    {
        "name": "submit_approval",
        "description": "将AI生成的用药建议提交给医生审批。必须调用此工具才能进入审批流程。",
        "input_schema": {
            "type": "object",
            "properties": {
                "patient_name": {"type": "string"},
                "patient_age": {"type": "integer"},
                "patient_weight": {"type": "number"},
                "symptoms": {"type": "string"},
                "advice": {"type": "string"},
                "drug_name": {"type": "string"},
                "drug_type": {"type": "string", "enum": ["prescription", "otc"]},
                "quantity": {"type": "integer"}
            },
            "required": ["patient_name", "symptoms", "advice", "drug_name"]
        }
    },
    {
        "name": "fill_prescription",
        "description": "在医生审批通过后，调用此工具将处方发送给药房系统进行配药。",
        "input_schema": {
            "type": "object",
            "properties": {
                "prescription_id": {"type": "string"},
                "patient_name": {"type": "string"},
                "drugs": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "dosage": {"type": "string"},
                            "quantity": {"type": "integer"}
                        }
                    }
                }
            },
            "required": ["prescription_id", "patient_name", "drugs"]
        }
    }
]


def register_tool_handler(name: str, handler: Callable) -> None:
    """注册工具的实际处理函数（向后兼容）"""
    _executor.register_handler(name, handler)


def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> str:
    """执行工具，返回结果字符串（向后兼容）"""
    return _executor.execute(tool_name, tool_input)


def get_registered_tools() -> List[str]:
    """返回已注册的工具名称列表（向后兼容）"""
    return _executor.get_registered_tools()


def is_tool_registered(name: str) -> bool:
    """检查工具是否已注册（向后兼容）"""
    return _executor.is_registered(name)


def get_executor() -> ToolExecutor:
    """获取工具执行器实例（新接口）"""
    return _executor


# 自动注册医疗工具
try:
    from .medical import register_tools
    register_tools(_executor)
except ImportError:
    pass