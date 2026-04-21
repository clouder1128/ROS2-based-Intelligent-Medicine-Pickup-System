# agent.py
"""医疗助手Agent核心类，支持状态保存和恢复"""

import logging
import pickle
import os
import time
from typing import List, Dict, Any, Tuple, Optional

from .config import Config
from ..llm import LLMClient
from ..memory import MessageManager
from ..tools.registry import TOOLS, execute_tool
from .exceptions import AgentError, ToolExecutionError
from ..utils.json_tools import extract_json_from_text
from ..utils.text_utils import log_duration
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
    from ..planner.models import TodoManager

    TodoManager  # 避免IDE警告
except ImportError:
    TodoManager = _PlaceholderTodoManager
    logger.warning("P3 planner not found, using placeholder")

try:
    from ..subagents.symptom_extractor import extract_symptoms
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


# ==================== MedicalAgent 类 ====================
class MedicalAgent:
    """医疗助手Agent核心，支持状态保存和恢复"""

    def __init__(
        self, llm_client: LLMClient = None, message_manager: MessageManager = None
    ) -> None:
        """
        初始化MedicalAgent

        Args:
            llm_client: LLM客户端实例，如果为None则创建默认实例
            message_manager: 消息管理器实例，如果为None则创建默认实例
        """
        self.llm_client = llm_client or LLMClient()
        self.message_manager = message_manager or MessageManager(
            system_prompt=SYSTEM_PROMPT
        )
        self.todo_manager = TodoManager()
        self.workflow_manager = WorkflowManager()
        self.patient_id: Optional[str] = None
        self.approval_id: Optional[str] = None
        self.last_steps: List[Dict] = []
        self.workflow_completed: bool = False  # 新增：工作流完成标志

    def run(
        self, user_message: str, patient_id: Optional[str] = None
    ) -> Tuple[str, List[Dict]]:
        """
        执行Agent循环，处理用户消息。
        返回: (最终回复内容, 步骤记录列表)
        """
        self.patient_id = patient_id or "anonymous"
        steps: List[Dict] = []

        # 为患者创建工作流（如果不存在）。workflow是一个未使用的对象，主要是为了为患者ID初始化工作流状态，重点在于workflow_manager内部的状态管理
        workflow = self.workflow_manager.create_workflow(self.patient_id)

        # 1. 调用子代理提取症状
        structured_info = extract_symptoms(user_message,self.llm_client)

        # 2. 由提取的症状信息增强用户消息
        # 症状列表存在并且非空，并且症状信息与原始用户消息不同
        if structured_info.symptoms and structured_info.symptoms != [user_message]:

            symptoms_text = "、".join(structured_info.symptoms) # 将结构化信息转化为人类可读的文本形式
            patient_info = structured_info.patient_info # 获取患者信息对象

            # 构建增强的用户消息
            # 处理过敏史，如果是列表则用顿号连接，如果是字符串则直接使用，如果没有则显示无
            allergies_text = '无'
            if patient_info.allergies:
                if isinstance(patient_info.allergies, list):
                    allergies_text = '、'.join(patient_info.allergies) if patient_info.allergies else '无'
                else:
                    allergies_text = str(patient_info.allergies)
            
            # 构建增强消息，包含患者描述和系统提取的信息
            enhanced_message = (
                f"[患者描述] {user_message}\n"
                f"[系统提取信息]\n"
                f"- 症状: {symptoms_text}\n"
                f"- 年龄: {patient_info.age or '未提供'}岁\n"
                f"- 体重: {patient_info.weight or '未提供'}kg\n"
                f"- 过敏史: {allergies_text}\n"
                f"- 主诉: {structured_info.chief_complaint}"
            )
            user_message = enhanced_message #将用户消息替换为增强消息，让LLM看到更清晰的信息，提升工具调用的准确性

        # 3. 将用户消息添加到消息历史（message_manager）中，LLM和工具调用都依赖这个消息历史来获取上下文
        self.message_manager.add_message("user", user_message)

        # 4. 获取当前待办事项
        todo_list = self.todo_manager.get_todo_list()
        if todo_list:
            todo_prompt = f"\n当前待办任务: {todo_list}\n请按顺序完成。"
            self.message_manager.add_message("user", todo_prompt)

        # 5. Agent循环
        max_iterations = Config.MAX_ITERATIONS
        last_tool_called = None
        tools_called = []  # 记录已调用的工具

        for i in range(max_iterations):
            step_start = time.time()
            messages = self.message_manager.get_full_messages()

            # === 新增：工作流完整性检查 ===
            if i >= 3 and len(tools_called) > 0 and not self.workflow_completed:
                # 检查工作流是否停滞
                expected_workflow = ["query_drug", "check_allergy", "calc_dosage", "generate_advice", "submit_approval"]
                current_progress = len([t for t in tools_called if t in expected_workflow])

                if current_progress >= 3 and last_tool_called == "generate_advice":
                    # 如果generate_advice已调用但submit_approval未调用，添加提示
                    logger.warning(f"工作流可能停滞在 {last_tool_called}，添加提示继续")
                    self.message_manager.add_message(
                        "user", "工作流下一步：请立即调用 submit_approval 提交审批"
                    )
            # === 新增结束 ===

            # 调用LLM
            with log_duration(logger, f"Iteration {i} LLM call"):
                response = self.llm_client.chat(
                    messages=messages, tools=TOOLS, temperature=Config.LLM_TEMPERATURE
                )

            # 处理LLM响应中的文本内容
            if response.get("content"):
                #取出回复的文本内容，添加到消息历史中，并记录步骤
                assistant_reply = response["content"]
                self.message_manager.add_message("assistant", assistant_reply)
                steps.append(
                    {
                        "step": i,
                        "type": "assistant",
                        "content": assistant_reply,
                        "duration_ms": int((time.time() - step_start) * 1000),
                    }
                )
                # 如果回复中没有工具调用，判断是否需要返回
                if not response.get("tool_calls"):
                    # 如果工作流已完成，返回结果
                    if self.workflow_completed:
                        self.last_steps = steps
                        return assistant_reply, steps

                    # 如果LLM在询问用户信息，返回等待用户输入
                    if self._needs_user_input(assistant_reply):
                        self.last_steps = steps
                        return assistant_reply, steps

                    # 否则，继续循环，让LLM看到自己的回复后继续工作流
                    # 添加一个简短的提示，鼓励LLM继续调用工具
                    self.message_manager.add_message(
                        "user", "请根据工作流继续执行下一步。"
                    )
                    continue

            # 处理工具调用
            tool_calls = response.get("tool_calls")
            if tool_calls:
                for tc in tool_calls:
                    tool_name = tc["name"]

                    # 记录调用的工具
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
                    self.message_manager.add_message(
                        "assistant", f"调用工具 {tool_name}"
                    )
                    self.message_manager.add_message(
                        "user", f"工具 {tool_name} 返回结果: {tool_result}"
                    )

                    # 特殊处理：如果提交了审批，记录approval_id
                    if tool_name == "submit_approval":
                        data = extract_json_from_text(tool_result)
                        if data and "approval_id" in data:
                            self.approval_id = data["approval_id"]
                            # 更新工作流中的审批ID
                            self.workflow_manager.set_approval_id(
                                self.patient_id, self.approval_id
                            )
                        # 标记工作流完成
                        self.workflow_completed = True

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

    def _needs_user_input(self, text: str) -> bool:
        """
        判断LLM的响应是否需要用户输入

        改进：排除工作流相关的标准询问，避免误判
        """
        if not text:
            return False

        # 工作流相关的标准询问，不需要用户输入
        workflow_actions = [
            "调用 query_drug",
            "调用 check_allergy",
            "调用 calc_dosage",
            "调用 generate_advice",
            "调用 submit_approval",
            "请根据工作流继续执行下一步",
            "正在执行工作流",
            "工作流下一步",
            "请立即调用",
            "使用默认药品"
        ]

        for action in workflow_actions:
            if action in text:
                return False

        # 明确表示工作流完成或需要继续
        if "审批已提交" in text or "审批ID:" in text:
            return False

        # 原有逻辑（保留）
        question_indicators = [
            "？", "?", "请问", "请提供", "请告诉我", "需要您", "您是否",
            "您有", "您能", "吗？", "吗?", "什么", "如何", "怎样", "能否"
        ]

        text_lower = text.lower()
        for indicator in question_indicators:
            if indicator in text_lower:
                # 但排除这些特殊情况
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
        # 不清除工作流管理器，因为可能有多患者

    def get_approval_id(self) -> Optional[str]:
        """获取最后一次提交的审批ID"""
        return self.approval_id

    def get_last_steps(self) -> List[Dict]:
        """获取最后一次运行的步骤记录"""
        return self.last_steps

    def get_workflow_state(
        self, patient_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
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

    # ========== 审批状态查询 ==========
    def get_approval_status(
        self, approval_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """查询审批单状态

        Args:
            approval_id: 审批ID，如果为None则使用上次提交的审批ID

        Returns:
            审批状态字典，包含状态、订单信息等，失败返回None
        """
        target_id = approval_id or self.approval_id
        if not target_id:
            logger.warning("无法查询审批状态：未提供审批ID且无上次提交的审批ID")
            return None

        try:
            from ..utils.http_client import PharmacyHTTPClient

            client = PharmacyHTTPClient()
            result = client.get_approval(target_id)

            if result and result.get("success"):
                approval_data = result.get("approval", {})

                # 获取关联的订单信息（如果已批准）
                status = approval_data.get("status", "unknown")
                order_info = None
                if status == "approved":
                    try:
                        # 尝试获取订单信息
                        order_result = client._run_async(
                            client._make_request("GET", "/api/orders")
                        )
                        if order_result and order_result.get("success"):
                            orders = order_result.get("data", [])
                            # 查找与此审批相关的订单（通过药品名称匹配）
                            for order in orders:
                                # 简化匹配：假设最近创建的订单属于此审批
                                # 实际实现中需要更好的关联逻辑
                                order_info = order
                                break
                    except Exception as e:
                        logger.debug(f"获取订单信息失败: {e}")
                        # 订单信息非必需，忽略错误

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

    # ========== 会话持久化（P1职责：仅状态保存，不涉及数据库） ==========
    # 在cli中有调用，/save时候将内容保存到session目录下。
    def save_state(self, filepath: str) -> None:
        """保存Agent状态到文件（用于长任务恢复）"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        state = {
            "messages": self.message_manager.get_full_messages(),
            "patient_id": self.patient_id,
            "approval_id": self.approval_id,
            # 注意：工作流状态不保存，因为它是临时的
        }
        with open(filepath, "wb") as f:
            pickle.dump(state, f)
        logger.info(f"Agent state saved to {filepath}")

    def load_state(self, filepath: str) -> bool:
        """从文件加载Agent状态，返回是否成功"""
        if not os.path.exists(filepath):
            logger.warning(f"State file not found: {filepath}")
            return False
        with open(filepath, "rb") as f:
            state = pickle.load(f)
        # 重建消息管理器
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
