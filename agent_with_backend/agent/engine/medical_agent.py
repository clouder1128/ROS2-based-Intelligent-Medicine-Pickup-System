# medical_agent.py
"""医疗助手Agent核心类，支持状态保存和恢复"""

import logging
import pickle
import os
import time
from typing import List, Dict, Any, Tuple, Optional

from common.config import Config
from agent.llm import LLMClient
from agent.memory import MessageManager
from agent.tools.registry import TOOLS, execute_tool
from common.exceptions import AgentError, ToolExecutionError
from common.utils.json_tools import extract_json_from_text
from common.utils.text_utils import log_duration
from agent.engine.workflows import WorkflowManager, WorkflowStep

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
    from agent.planner.models import TodoManager
    TodoManager
except ImportError:
    TodoManager = _PlaceholderTodoManager
    logger.warning("P3 planner not found, using placeholder")

try:
    from agent.subagents.symptom_extractor import extract_symptoms
except ImportError as e:
    logger.warning(f"P3 symptom extractor not found: {e}, using placeholder")
    extract_symptoms = _placeholder_extract_symptoms


# ==================== 系统提示词 ====================
SYSTEM_PROMPT = """你是一个医疗用药助手，必须严格遵循以下自动工作流程：

自动工作流程（严格按照此顺序执行，不要添加任何额外解释）：
1. 收集患者信息：症状、年龄、体重、过敏史。
   - 如果患者已提供明确的过敏史信息（包括"无过敏历史"、"没有过敏史"等表述），则直接进入下一步
   - 只有当患者完全没有提到过敏史时，才需要询问一次
2. 立即调用 query_drug 查询与症状相关的药物（使用症状关键词）。
3. 立即调用 check_allergy 确认患者对推荐药物无过敏风险。
4. 立即调用 calc_dosage 计算合适的剂量。
5. 立即调用 generate_advice，使用 calc_dosage 结果中的 "drug_name" 和 "dosage" 字段。
6. 立即调用 submit_approval，使用 generate_advice 结果中的 "advice_text" 作为 advice 参数。

强制规则（必须遵守）：
1. 工作流是自动的，一旦开始就连续执行所有步骤，不要停顿
2. 如果患者已提供过敏史，不要重复询问
3. 每次只调用一个工具，等待结果后再继续
4. 严格按照顺序：query_drug → check_allergy → calc_dosage → generate_advice → submit_approval
5. 不要添加任何文本解释，直接调用工具
6. 完成 submit_approval 后，向用户显示审批ID和后续步骤

工作流示例：
用户：老王,30岁,60kg,偏头痛,无过敏历史
助手：调用 query_drug(症状="偏头痛")
[工具返回结果]
助手：调用 check_allergy(patient_allergies="无", drug_name="布洛芬")
[工具返回结果]
助手：调用 calc_dosage(drug_name="布洛芬", age=30, weight_kg=60, condition_severity="轻")
[工具返回结果]
助手：调用 generate_advice(drug_name="布洛芬", dosage="成人剂量：200-400mg，每4-6小时一次")
[工具返回结果]
助手：调用 submit_approval(patient_name="老王", advice="[advice_text内容]", patient_age=30, patient_weight=60, symptoms="偏头痛", drug_name="布洛芬")
[工具返回结果]
助手：审批已提交，审批ID: AP-20260415-XXXX。请等待医生审批。

记住：工作流一旦启动，必须连续执行到 submit_approval 完成。
"""


class MedicalAgent:
    """医疗助手Agent核心，支持状态保存和恢复"""

    def __init__(
        self, llm_client: LLMClient = None, message_manager: "MessageManager" = None
    ) -> None:
        self.llm_client = llm_client or LLMClient()
        self.message_manager = message_manager or MessageManager(
            system_prompt=SYSTEM_PROMPT
        )
        self.todo_manager = TodoManager()
        self.workflow_manager = WorkflowManager()
        self.patient_id: Optional[str] = None
        self.approval_id: Optional[str] = None
        self.last_steps: List[Dict] = []
        self.workflow_completed: bool = False

    def run(
        self, user_message: str, patient_id: Optional[str] = None
    ) -> Tuple[str, List[Dict]]:
        """执行Agent循环，处理用户消息"""
        self.patient_id = patient_id or "anonymous"
        steps: List[Dict] = []

        workflow = self.workflow_manager.create_workflow(self.patient_id)

        # 1. 调用子代理提取症状
        structured_info = extract_symptoms(user_message, self.llm_client)

        # 2. 由提取的症状信息增强用户消息
        if structured_info.symptoms and structured_info.symptoms != [user_message]:
            symptoms_text = "、".join(structured_info.symptoms)
            patient_info = structured_info.patient_info

            allergies_text = '无'
            if patient_info.allergies:
                if isinstance(patient_info.allergies, list):
                    allergies_text = '、'.join(patient_info.allergies) if patient_info.allergies else '无'
                else:
                    allergies_text = str(patient_info.allergies)

            enhanced_message = (
                f"[患者描述] {user_message}\n"
                f"[系统提取信息]\n"
                f"- 症状: {symptoms_text}\n"
                f"- 年龄: {patient_info.age or '未提供'}岁\n"
                f"- 体重: {patient_info.weight or '未提供'}kg\n"
                f"- 过敏史: {allergies_text}\n"
                f"- 主诉: {structured_info.chief_complaint}"
            )
            user_message = enhanced_message

        # 3. 将用户消息添加到消息历史
        self.message_manager.add_message("user", user_message)

        # 4. 获取当前待办事项
        todo_list = self.todo_manager.get_todo_list()
        if todo_list:
            todo_prompt = f"\n当前待办任务: {todo_list}\n请按顺序完成。"
            self.message_manager.add_message("user", todo_prompt)

        # 5. Agent循环
        max_iterations = Config.MAX_ITERATIONS
        last_tool_called = None
        tools_called = []

        for i in range(max_iterations):
            step_start = time.time()
            messages = self.message_manager.get_full_messages()

            if i >= 3 and len(tools_called) > 0 and not self.workflow_completed:
                expected_workflow = ["query_drug", "check_allergy", "calc_dosage", "generate_advice", "submit_approval"]
                current_progress = len([t for t in tools_called if t in expected_workflow])

                if current_progress >= 3 and last_tool_called == "generate_advice":
                    logger.warning(f"工作流可能停滞在 {last_tool_called}，添加提示继续")
                    self.message_manager.add_message(
                        "user", "工作流下一步：请立即调用 submit_approval 提交审批"
                    )

            with log_duration(logger, f"Iteration {i} LLM call"):
                response = self.llm_client.chat(
                    messages=messages, tools=TOOLS, temperature=Config.LLM_TEMPERATURE
                )

            if response.get("content"):
                assistant_reply = response["content"]
                self.message_manager.add_message("assistant", assistant_reply)
                steps.append({
                    "step": i,
                    "type": "assistant",
                    "content": assistant_reply,
                    "duration_ms": int((time.time() - step_start) * 1000),
                })
                if not response.get("tool_calls"):
                    if self.workflow_completed:
                        self.last_steps = steps
                        return assistant_reply, steps

                    if self._needs_user_input(assistant_reply):
                        self.last_steps = steps
                        return assistant_reply, steps

                    self.message_manager.add_message(
                        "user", "请根据工作流继续执行下一步。"
                    )
                    continue

            tool_calls = response.get("tool_calls")
            if tool_calls:
                for tc in tool_calls:
                    tool_name = tc["name"]
                    last_tool_called = tool_name
                    tools_called.append(tool_name)

                    tool_input = tc["input"]
                    step_record = {
                        "step": i,
                        "type": "tool_call",
                        "tool": tool_name,
                        "input": tool_input,
                        "duration_ms": 0,
                    }

                    tool_start = time.time()
                    try:
                        tool_result = execute_tool(tool_name, tool_input)
                        step_record["result"] = tool_result
                    except ToolExecutionError as e:
                        tool_result = f"工具执行错误: {str(e)}"
                        step_record["error"] = str(e)

                    step_record["duration_ms"] = int((time.time() - tool_start) * 1000)
                    steps.append(step_record)

                    self.message_manager.add_message(
                        "assistant", f"调用工具 {tool_name}"
                    )
                    self.message_manager.add_message(
                        "user", f"工具 {tool_name} 返回结果: {tool_result}"
                    )

                    if tool_name == "submit_approval":
                        data = extract_json_from_text(tool_result)
                        if data and "approval_id" in data:
                            self.approval_id = data["approval_id"]
                            self.workflow_manager.set_approval_id(
                                self.patient_id, self.approval_id
                            )
                        self.workflow_completed = True

                    self._update_workflow_for_tool(tool_name, tool_result)
                continue

            break

        final_msg = "处理超时，请稍后重试。"
        self.message_manager.add_message("assistant", final_msg)
        self.last_steps = steps
        return final_msg, steps

    def _update_workflow_for_tool(self, tool_name: str, tool_result: str) -> None:
        """根据工具调用更新工作流状态"""
        if not self.patient_id:
            return

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

    def _needs_user_input(self, text: str) -> bool:
        """判断LLM的响应是否需要用户输入"""
        if not text:
            return False

        workflow_actions = [
            "调用 query_drug", "调用 check_allergy", "调用 calc_dosage",
            "调用 generate_advice", "调用 submit_approval",
            "请根据工作流继续执行下一步", "正在执行工作流",
            "工作流下一步", "请立即调用", "使用默认药品"
        ]

        for action in workflow_actions:
            if action in text:
                return False

        if "审批已提交" in text or "审批ID:" in text:
            return False

        question_indicators = [
            "？", "?", "请问", "请提供", "请告诉我", "需要您", "您是否",
            "您有", "您能", "吗？", "吗?", "什么", "如何", "怎样", "能否"
        ]

        text_lower = text.lower()
        for indicator in question_indicators:
            if indicator in text_lower:
                if "过敏" in text and "已提供" in text:
                    continue
                return True

        if text.strip().endswith(("？", "?")):
            return True

        input_requests = ["请回答", "请回复", "请告知", "请说明", "请描述"]
        for request in input_requests:
            if request in text:
                return True

        return False

    def reset(self) -> None:
        """重置对话（新会话）"""
        self.message_manager.reset(keep_system=True)
        self.patient_id = None
        self.approval_id = None
        self.last_steps = []
        self.workflow_completed = False

    def get_approval_id(self) -> Optional[str]:
        return self.approval_id

    def get_last_steps(self) -> List[Dict]:
        return self.last_steps

    def get_workflow_state(self, patient_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        target_patient_id = patient_id or self.patient_id
        if not target_patient_id:
            return None
        workflow = self.workflow_manager.get_workflow(target_patient_id)
        if workflow:
            return workflow.to_dict()
        return None

    def get_all_workflows(self) -> List[Dict[str, Any]]:
        return self.workflow_manager.get_all_workflows()

    def get_workflow_stats(self) -> Dict[str, Any]:
        return self.workflow_manager.get_stats()

    def get_approval_status(self, approval_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        target_id = approval_id or self.approval_id
        if not target_id:
            logger.warning("无法查询审批状态：未提供审批ID且无上次提交的审批ID")
            return None

        try:
            from common.utils.http_client import PharmacyHTTPClient

            client = PharmacyHTTPClient()
            result = client.get_approval(target_id)

            if result and result.get("success"):
                approval_data = result.get("approval", {})

                status = approval_data.get("status", "unknown")
                order_info = None
                if status == "approved":
                    try:
                        order_result = client._run_async(
                            client._make_request("GET", "/api/orders")
                        )
                        if order_result and order_result.get("success"):
                            orders = order_result.get("data", [])
                            for order in orders:
                                order_info = order
                                break
                    except Exception as e:
                        logger.debug(f"获取订单信息失败: {e}")

                return {
                    "success": True,
                    "approval_id": target_id,
                    "status": status,
                    "approval_data": approval_data,
                    "order_info": order_info,
                    "last_checked": time.time(),
                    "instructions": {
                        "pending": "请等待医生审批。",
                        "approved": "审批已通过，药品正在配发中。",
                        "rejected": "审批被拒绝，请咨询医生了解详情。",
                        "unknown": "审批状态未知。",
                    }.get(status, "审批状态未知。"),
                }
            else:
                logger.warning(f"查询审批状态失败: {target_id}")
                return None
        except Exception as e:
            logger.error(f"查询审批状态异常: {e}")
            return None

    def save_state(self, filepath: str) -> None:
        """保存Agent状态到文件（用于长任务恢复）"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        state = {
            "messages": self.message_manager.get_full_messages(),
            "patient_id": self.patient_id,
            "approval_id": self.approval_id,
        }
        with open(filepath, "wb") as f:
            pickle.dump(state, f)
        logger.info(f"Agent state saved to {filepath}")

    def load_state(self, filepath: str) -> bool:
        """从文件加载Agent状态"""
        if not os.path.exists(filepath):
            logger.warning(f"State file not found: {filepath}")
            return False
        with open(filepath, "rb") as f:
            state = pickle.load(f)
        self.message_manager = MessageManager(system_prompt=SYSTEM_PROMPT)
        for msg in state["messages"]:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "tool":
                self.message_manager.add_tool_result(
                    msg.get("tool_call_id", ""), content
                )
            else:
                self.message_manager.add_message(role, content)
        self.patient_id = state["patient_id"]
        self.approval_id = state["approval_id"]
        logger.info(f"Agent state loaded from {filepath}")
        return True
