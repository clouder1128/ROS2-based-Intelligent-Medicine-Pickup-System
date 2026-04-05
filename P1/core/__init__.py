try:
    from .agent import MedicalAgent
    from .workflows import WorkflowManager, WorkflowStep
except ImportError:
    MedicalAgent = None
    WorkflowManager = None
    WorkflowStep = None

# 全局Agent实例（用于便捷函数）
_global_agent = None


def _get_global_agent() -> MedicalAgent:
    """获取全局Agent实例（懒加载）"""
    global _global_agent
    if _global_agent is None:
        _global_agent = MedicalAgent()
    return _global_agent


def run_agent(user_message: str, patient_id: str = None) -> dict:
    """
    外部调用入口（P4使用）
    返回: {"reply": str, "steps": List[Dict], "approval_id": str | None}
    """
    from .agent import MedicalAgent  # 避免循环导入
    agent = _get_global_agent()
    reply, steps = agent.run(user_message, patient_id)
    return {
        "reply": reply,
        "steps": steps,
        "approval_id": agent.get_approval_id()
    }


def reset_agent() -> None:
    """重置全局Agent"""
    agent = _get_global_agent()
    agent.reset()


def get_agent_status() -> dict:
    """获取Agent当前状态（用于调试）"""
    from llm import LLMClient
    agent = _get_global_agent()
    return {
        "patient_id": agent.patient_id,
        "approval_id": agent.approval_id,
        "message_count": agent.message_manager.get_conversation_length(),
        "estimated_tokens": agent.message_manager.estimate_total_tokens(),
        "llm_stats": LLMClient.get_stats(),
        "workflow_stats": agent.get_workflow_stats()
    }


def save_current_session(filepath: str) -> None:
    """保存当前全局Agent会话"""
    agent = _get_global_agent()
    agent.save_state(filepath)


def load_session(filepath: str) -> bool:
    """加载会话到全局Agent"""
    agent = _get_global_agent()
    return agent.load_state(filepath)


__all__ = [
    'MedicalAgent',
    'WorkflowManager',
    'WorkflowStep',
    'run_agent',
    'reset_agent',
    'get_agent_status',
    'save_current_session',
    'load_session'
]