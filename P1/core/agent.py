# agent.py
"""医疗助手Agent核心类，支持状态保存和恢复"""

import logging
import pickle
import os
import time
from typing import List, Dict, Any, Tuple, Optional

from config import Config
from llm import LLMClient
from memory import MessageManager
from tools.registry import TOOLS, execute_tool
from exceptions import AgentError, ToolExecutionError
from utils.json_tools import extract_json_from_text
from utils.text_utils import log_duration
from .workflows import WorkflowManager, WorkflowStep

logger = logging.getLogger(__name__)


# ==================== 与P3的集成占位 ====================
class _PlaceholderTodoManager:
    """P3的TodoManager占位，P3实现后替换"""

    def get_todo_list(self) -> List[str]:
        return []

    def update_todo(self, task: str, status: str) -> bool:
        return True

    def add_todo(self, task: str, priority: int = 0) -> None:
        pass


def _placeholder_extract_symptoms(user_input: str) -> Dict[str, Any]:
    """P3的症状提取子代理占位"""
    return {"symptoms": user_input, "age": None, "weight": None}


# 尝试导入P3的真实模块，如果失败则使用占位
try:
    from planner import TodoManager

    TodoManager  # 避免IDE警告
except ImportError:
    TodoManager = _PlaceholderTodoManager
    logger.warning("P3 planner not found, using placeholder")

try:
    from subagents.symptom_extractor import extract_symptoms
except ImportError:
    extract_symptoms = _placeholder_extract_symptoms
    logger.warning("P3 symptom extractor not found, using placeholder")


# ==================== 系统提示词 ====================
SYSTEM_PROMPT = """你是一个医疗用药助手，必须严格遵循以下流程：
1. 收集患者信息：症状、年龄、体重、过敏史。若患者未提供过敏史，必须主动询问。
2. 使用 query_drug 查询与症状相关的药物。
3. 使用 check_allergy 确认患者对推荐药物无过敏风险。
4. 使用 calc_dosage 计算合适的剂量。
5. 调用 generate_advice 生成结构化的用药建议。
6. 调用 submit_approval 提交给医生审批（所有药物建议都必须审批）。
7. 等待医生审批结果后，由系统自动调用 fill_prescription 完成配药（你不需要调用它，系统会处理）。

注意：
- 你只能提供参考建议，最终决定权在医生。
- 每次只调用一个工具，等待结果后再继续。
- 如果缺少必要信息（如过敏史），必须先询问。
- 不要编造药品信息，所有药物必须通过 query_drug 查询确认。
"""


# ==================== MedicalAgent 类 ====================
class MedicalAgent:
    """医疗助手Agent核心，支持状态保存和恢复"""

    def __init__(self, llm_client: LLMClient = None, message_manager: MessageManager = None) -> None:
        """
        初始化MedicalAgent

        Args:
            llm_client: LLM客户端实例，如果为None则创建默认实例
            message_manager: 消息管理器实例，如果为None则创建默认实例
        """
        self.llm_client = llm_client or LLMClient()
        self.message_manager = message_manager or MessageManager(system_prompt=SYSTEM_PROMPT)
        self.todo_manager = TodoManager()
        self.workflow_manager = WorkflowManager()
        self.patient_id: Optional[str] = None
        self.approval_id: Optional[str] = None
        self.last_steps: List[Dict] = []

    def run(self, user_message: str, patient_id: Optional[str] = None) -> Tuple[str, List[Dict]]:
        """
        执行Agent循环，处理用户消息。
        返回: (最终回复内容, 步骤记录列表)
        """
        self.patient_id = patient_id or "anonymous"
        steps: List[Dict] = []

        # 为患者创建工作流（如果不存在）
        workflow = self.workflow_manager.create_workflow(self.patient_id)

        # 1. 调用子代理提取症状（P3实现）
        structured_info = extract_symptoms(user_message)
        if structured_info.get("symptoms") and structured_info.get("symptoms") != user_message:
            user_message = f"[系统提取的症状信息] {user_message}\n提取结果: {structured_info}"

        # 2. 添加用户消息
        self.message_manager.add_message("user", user_message)

        # 3. 获取当前待办事项（P3实现）
        todo_list = self.todo_manager.get_todo_list()
        if todo_list:
            todo_prompt = f"\n当前待办任务: {todo_list}\n请按顺序完成。"
            self.message_manager.add_message("user", todo_prompt)

        # 4. Agent循环
        max_iterations = Config.MAX_ITERATIONS
        for i in range(max_iterations):
            step_start = time.time()
            messages = self.message_manager.get_full_messages()

            # 调用LLM
            with log_duration(logger, f"Iteration {i} LLM call"):
                response = self.llm_client.chat(
                    messages=messages,
                    tools=TOOLS,
                    temperature=Config.LLM_TEMPERATURE
                )

            # 处理LLM响应中的文本内容
            if response.get("content"):
                assistant_reply = response["content"]
                self.message_manager.add_message("assistant", assistant_reply)
                steps.append({
                    "step": i,
                    "type": "assistant",
                    "content": assistant_reply,
                    "duration_ms": int((time.time() - step_start) * 1000)
                })
                # 如果回复中没有工具调用，则返回
                if not response.get("tool_calls"):
                    self.last_steps = steps
                    return assistant_reply, steps

            # 处理工具调用
            tool_calls = response.get("tool_calls")
            if tool_calls:
                for tc in tool_calls:
                    tool_name = tc["name"]
                    tool_input = tc["input"]
                    step_record = {
                        "step": i,
                        "type": "tool_call",
                        "tool": tool_name,
                        "input": tool_input,
                        "duration_ms": 0
                    }
                    tool_start = time.time()

                    # 执行工具
                    try:
                        tool_result = execute_tool(tool_name, tool_input)
                        step_record["result"] = tool_result
                    except ToolExecutionError as e:
                        tool_result = f"工具执行错误: {str(e)}"
                        step_record["error"] = str(e)

                    step_record["duration_ms"] = int((time.time() - tool_start) * 1000)
                    steps.append(step_record)

                    # 将工具结果添加到消息历史
                    self.message_manager.add_message("assistant", f"调用工具 {tool_name}")
                    self.message_manager.add_message("user", f"工具 {tool_name} 返回结果: {tool_result}")

                    # 特殊处理：如果提交了审批，记录approval_id
                    if tool_name == "submit_approval":
                        data = extract_json_from_text(tool_result)
                        if data and "approval_id" in data:
                            self.approval_id = data["approval_id"]
                            # 更新工作流中的审批ID
                            self.workflow_manager.set_approval_id(self.patient_id, self.approval_id)

                    # 更新工作流步骤
                    self._update_workflow_for_tool(tool_name, tool_result)

                # 继续循环，让LLM看到工具结果
                continue

            # 既没有文本回复也没有工具调用（异常情况）
            break

        # 达到最大迭代次数仍未完成
        final_msg = "处理超时，请稍后重试。"
        self.message_manager.add_message("assistant", final_msg)
        self.last_steps = steps
        return final_msg, steps

    def _update_workflow_for_tool(self, tool_name: str, tool_result: str) -> None:
        """根据工具调用更新工作流状态"""
        if not self.patient_id:
            return

        # 映射工具名到工作流步骤
        tool_to_step = {
            "query_drug": WorkflowStep.QUERY_DRUG,
            "check_allergy": WorkflowStep.CHECK_ALLERGY,
            "calc_dosage": WorkflowStep.CALC_DOSAGE,
            "generate_advice": WorkflowStep.GENERATE_ADVICE,
            "submit_approval": WorkflowStep.SUBMIT_APPROVAL,
        }

        if tool_name in tool_to_step:
            step = tool_to_step[tool_name]
            data = {"tool_result": tool_result}
            self.workflow_manager.update_workflow_step(self.patient_id, step, data)

    def reset(self) -> None:
        """重置对话（新会话）"""
        self.message_manager.reset(keep_system=True)
        self.patient_id = None
        self.approval_id = None
        self.last_steps = []
        # 不清除工作流管理器，因为可能有多患者

    def get_approval_id(self) -> Optional[str]:
        """获取最后一次提交的审批ID"""
        return self.approval_id

    def get_last_steps(self) -> List[Dict]:
        """获取最后一次运行的步骤记录"""
        return self.last_steps

    def get_workflow_state(self, patient_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取患者的工作流状态"""
        target_patient_id = patient_id or self.patient_id
        if not target_patient_id:
            return None

        workflow = self.workflow_manager.get_workflow(target_patient_id)
        if workflow:
            return workflow.to_dict()
        return None

    def get_all_workflows(self) -> List[Dict[str, Any]]:
        """获取所有工作流状态"""
        return self.workflow_manager.get_all_workflows()

    def get_workflow_stats(self) -> Dict[str, Any]:
        """获取工作流统计信息"""
        return self.workflow_manager.get_stats()

    # ========== 会话持久化（P1职责：仅状态保存，不涉及数据库） ==========
    def save_state(self, filepath: str) -> None:
        """保存Agent状态到文件（用于长任务恢复）"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        state = {
            "messages": self.message_manager.get_full_messages(),
            "patient_id": self.patient_id,
            "approval_id": self.approval_id,
            # 注意：工作流状态不保存，因为它是临时的
        }
        with open(filepath, 'wb') as f:
            pickle.dump(state, f)
        logger.info(f"Agent state saved to {filepath}")

    def load_state(self, filepath: str) -> bool:
        """从文件加载Agent状态，返回是否成功"""
        if not os.path.exists(filepath):
            logger.warning(f"State file not found: {filepath}")
            return False
        with open(filepath, 'rb') as f:
            state = pickle.load(f)
        # 重建消息管理器
        self.message_manager = MessageManager(system_prompt=SYSTEM_PROMPT)
        for msg in state["messages"]:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "tool":
                self.message_manager.add_tool_result(msg.get("tool_call_id", ""), content)
            else:
                self.message_manager.add_message(role, content)
        self.patient_id = state["patient_id"]
        self.approval_id = state["approval_id"]
        logger.info(f"Agent state loaded from {filepath}")
        return True