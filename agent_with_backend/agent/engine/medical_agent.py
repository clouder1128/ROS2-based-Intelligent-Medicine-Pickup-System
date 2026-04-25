# medical_agent.py
"""医疗助手Agent核心类，支持状态保存和恢复"""

import logging
import pickle
import os
import time
import json
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


# ==================== P3集成占位 ====================
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


try:
    from agent.planner.models import TodoManager, TaskCategory
    TodoManager
    TaskCategory
except ImportError:
    TodoManager = _PlaceholderTodoManager
    TaskCategory = None
    logger.warning("P3 planner not found, using placeholder")

try:
    from agent.subagents.symptom_extractor import extract_symptoms
except ImportError as e:
    logger.warning(f"P3 symptom extractor not found: {e}, using placeholder")
    extract_symptoms = _placeholder_extract_symptoms


# ==================== 系统提示词 ====================
SYSTEM_PROMPT = """你是一个医疗用药助手。请按以下流程工作：

[药品查询]
- 注意：如果系统消息中已经提供了匹配的药品列表，则跳过 query_drug 直接进入筛选步骤
- 如果需要自行调用 query_drug(symptom) 且返回空列表 (status="not_found")：
  - 换个相近的症状词汇重新查询，最多尝试 3 次
  - 示例：轻度头疼→头痛→偏头痛
- 如果 3 次都未找到：告知患者当前症状未找到匹配药品，建议就医，终止流程

[药品筛选与决策]
- 从药品列表中根据患者症状选出合适的药品
- 对每种候选药品调用 check_allergy 检查过敏风险
- 对通过过敏检查的药品调用 calc_dosage 计算剂量
- 可根据需要选择多种药品联用（重复过敏检查和剂量计算）

[提交审批]
- 调用 generate_advice 生成用药建议
- 调用 submit_approval 将建议提交给医生审批

重要规则：
- 如果系统中已经提供了药品列表，不要重复调用 query_drug
- 如果药品列表为空，不要重复调用 query_drug 超过 3 次
- 3 次失败后直接建议就医并结束
- 回复保持简洁，不要多余的叙述，不要输出思考过程
- 已提供的患者信息不要重复询问
- 每次只调用一个工具，等待结果后再继续
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
        self.planner_enabled = Config.ENABLE_WORKFLOW_PLANNER
        self.todo_manager = TodoManager()
        if self.planner_enabled:
            try:
                from agent.planner.storage import SQLiteStorage
                self.todo_manager = TodoManager(
                    storage=SQLiteStorage(db_path="tasks.db")
                )
            except Exception as e:
                logger.warning(f"Planner storage init failed, using in-memory: {e}")
                self.todo_manager = TodoManager()
        self.workflow_manager = WorkflowManager()
        self.patient_id: Optional[str] = None
        self.approval_id: Optional[str] = None
        self.last_steps: List[Dict] = []
        self.workflow_completed: bool = False

    def _query_drugs_with_retry(self, symptoms: List[str], llm_client) -> List[Dict]:
        """尝试用不同关键词查询药品，支持 LLM 生成同义词重试"""
        from database.pharmacy_client import query_drugs_by_symptom, query_drug_by_name

        tried_keywords = set()
        max_retries = 3

        # 第一轮：用提取到的所有症状关键词查询
        for symptom in symptoms:
            if symptom in tried_keywords:
                continue
            tried_keywords.add(symptom)
            drugs = query_drugs_by_symptom(symptom)
            if drugs:
                return drugs

        # 第二轮：尝试按药品名称查询（兼容直接输入药名的情况）
        if symptoms:
            drug = query_drug_by_name(symptoms[0])
            if drug:
                return [drug]

        # 第三轮：让 LLM 生成同义词来重试
        retry_count = 0
        while retry_count < max_retries:
            # 让 LLM 生成一个相近的症状关键词
            prompt = (
                f"患者描述了症状：{'、'.join(symptoms[:3])}。"
                f"已尝试过关键词：{'、'.join(tried_keywords)}，均未找到匹配药品。"
                f"请生成一个相近的医学症状关键词来重新搜索（只回复关键词本身，不要其他内容）："
            )
            try:
                resp = llm_client.chat([
                    {"role": "user", "content": prompt}
                ])
                new_keyword = resp.get("content", "").strip()
                if not new_keyword or new_keyword in tried_keywords:
                    break  # LLM 词穷了
                tried_keywords.add(new_keyword)
                drugs = query_drugs_by_symptom(new_keyword)
                if drugs:
                    return drugs
            except Exception:
                pass
            retry_count += 1

        return []  # 全部失败

    def _create_workflow_plan(self, symptoms: List[str], drug_count: int) -> None:
        """创建工作流任务计划（planner 启用时）"""
        if not self.planner_enabled:
            return

        # 清空旧会话任务
        for task_id in list(self.todo_manager.tasks.keys()):
            self.todo_manager.delete_todo(task_id)

        t1 = self.todo_manager.add_todo(
            content=f"症状分析: {'、'.join(symptoms)}",
            category=TaskCategory.SYMPTOM.value,
            priority=5,
            related_symptoms=symptoms,
        )
        self.todo_manager.mark_completed(t1.id, notes=f"找到 {drug_count} 种匹配药品")

        self.todo_manager.add_todo(
            content="过敏风险检查",
            category=TaskCategory.CHECK.value,
            priority=4,
            dependencies=[t1.id],
        )
        self.todo_manager.add_todo(
            content="用药剂量计算",
            category=TaskCategory.DOSAGE.value,
            priority=3,
        )
        self.todo_manager.add_todo(
            content="生成用药建议",
            category=TaskCategory.OTHER.value,
            priority=3,
        )
        self.todo_manager.add_todo(
            content="提交医生审批",
            category=TaskCategory.APPROVAL.value,
            priority=5,
        )

    def _format_plan_for_llm(self) -> str:
        """将当前任务计划格式化为 LLM 可读上下文"""
        if not self.planner_enabled:
            return ""

        lines = ["\n[当前工作流进度]"]
        for task in self.todo_manager.get_todo_list(sort_by_priority=True):
            if task.status == "completed":
                marker = "[已完成]"
            elif task.status == "in_progress":
                marker = "[进行中]"
            elif task.status == "blocked":
                marker = "[已阻塞]"
            else:
                marker = "[待处理]"
            lines.append(f"  {marker} {task.content}")
        return "\n".join(lines)

    def run(
        self, user_message: str, patient_id: Optional[str] = None
    ) -> Tuple[str, List[Dict]]:
        """执行Agent循环，处理用户消息"""
        self.patient_id = patient_id or "anonymous"
        steps: List[Dict] = []

        workflow = self.workflow_manager.create_workflow(self.patient_id)

        # 1. 调用子代理提取症状
        structured_info = extract_symptoms(user_message, self.llm_client)

        # 2. 后端批量查询药品（带重试）
        symptoms = structured_info.symptoms or [user_message]
        drug_list = self._query_drugs_with_retry(symptoms, self.llm_client)

        if not drug_list:
            # 所有重试都失败，建议就医
            msg = "已尝试多种关键词查询，未找到与您症状匹配的药品。建议您尽快就医，由医生进行专业诊断。"
            self.message_manager.add_message("assistant", msg)
            self.workflow_completed = True
            steps.append({"step": 0, "type": "assistant", "content": msg, "duration_ms": 0})
            self.last_steps = steps
            workflow.mark_step_completed(WorkflowStep.DRUG_QUERY_FAILED, {"reason": "no_drugs_found"})
            return msg, steps

        # 3. 创建工作流任务计划
        self._create_workflow_plan(symptoms, len(drug_list))

        # 4. 由提取的症状信息增强用户消息
        symptoms_text = "、".join(symptoms)
        severity_text = ""
        if structured_info.severity:
            severity_text = "，".join(
                f"{symptom}({degree})" for symptom, degree in structured_info.severity.items()
            )
        patient_info = structured_info.patient_info
        allergies_text = '无'
        if patient_info.allergies:
            if isinstance(patient_info.allergies, list):
                allergies_text = '、'.join(patient_info.allergies) if patient_info.allergies else '无'
            else:
                allergies_text = str(patient_info.allergies)

        # 构建包含药品列表的增强消息
        drug_summary = "\n".join(
            f"  - {d['name']}（{d.get('retail_price', '?')}元）适应症：{'、'.join(d.get('indications', ['未知']))}"
            for d in drug_list[:20]  # 限制显示数量
        )

        enhanced_message = (
            f"[患者描述] {user_message}\n"
            f"[系统提取信息]\n"
            f"- 症状: {symptoms_text}\n"
            f"- 程度: {severity_text or '未指定'}\n"
            f"- 年龄: {patient_info.age or '未提供'}岁\n"
            f"- 体重: {patient_info.weight or '未提供'}kg\n"
            f"- 过敏史: {allergies_text}\n"
            f"- 主诉: {structured_info.chief_complaint}\n"
            f"\n[系统中匹配的药品列表（共{len(drug_list)}种）—— 已查询完毕，无需再调用 query_drug]\n"
            f"{drug_summary}\n"
            f"\n请根据上述药品列表为患者筛选药品、检查过敏、计算剂量。如果列表中有适合的药品，直接进行后续步骤（过敏检查→剂量计算→生成建议→提交审批）。"
        )
        enhanced_message += self._format_plan_for_llm()
        self.message_manager.add_message("user", enhanced_message)

        # 5. Agent循环（简化版）
        max_iterations = Config.MAX_ITERATIONS
        last_tool_called = None

        for i in range(max_iterations):
            step_start = time.time()
            messages = self.message_manager.get_full_messages()

            with log_duration(logger, f"Iteration {i} LLM call"):
                response = self.llm_client.chat(
                    messages=messages, tools=TOOLS, temperature=Config.LLM_TEMPERATURE
                )

            tool_calls = response.get("tool_calls")
            if tool_calls:
                # 构建 OpenAI 格式的 tool_calls 列表（用于消息历史）
                openai_tc_list = []
                for tc in tool_calls:
                    tc_id = tc.get("id") or f"call_{int(time.time()*1000)}"
                    openai_tc_list.append({
                        "id": tc_id,
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc.get("input", {}), ensure_ascii=False)
                        }
                    })

                # 单条 assistant 消息：content + tool_calls 合并
                assistant_content = response.get("content") or ""
                self.message_manager.add_message(
                    "assistant", assistant_content, tool_calls=openai_tc_list
                )

                if assistant_content:
                    steps.append({
                        "step": i,
                        "type": "assistant",
                        "content": assistant_content,
                        "duration_ms": int((time.time() - step_start) * 1000),
                    })

                # 逐个执行工具
                for tc in tool_calls:
                    tool_name = tc["name"]
                    last_tool_called = tool_name
                    tool_input = tc["input"]
                    tool_call_id = tc.get("id") or f"call_{int(time.time()*1000)}"

                    step_record = {
                        "step": i,
                        "type": "tool_call",
                        "tool": tool_name,
                        "input": tool_input,
                        "tool_call_id": tool_call_id,
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

                    # tool role 格式：role=tool，带 tool_call_id
                    self.message_manager.add_tool_result(tool_call_id, tool_result)

                    if tool_name == "submit_approval":
                        data = extract_json_from_text(tool_result)
                        if data and "approval_id" in data:
                            self.approval_id = data["approval_id"]
                            self.workflow_manager.set_approval_id(
                                self.patient_id, self.approval_id
                            )
                        self.workflow_completed = True

                    self._update_workflow_and_todo(tool_name, tool_result)
                continue  # 有工具调用就继续循环

            # 没有工具调用，纯文本回复
            if response.get("content"):
                assistant_reply = response["content"]
                self.message_manager.add_message("assistant", assistant_reply)
                steps.append({
                    "step": i,
                    "type": "assistant",
                    "content": assistant_reply,
                    "duration_ms": int((time.time() - step_start) * 1000),
                })
                self.last_steps = steps
                return assistant_reply, steps

            break  # 没有工具调用也没有内容，退出

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

    def _update_workflow_and_todo(self, tool_name: str, tool_result: str) -> None:
        """根据工具调用更新工作流状态和任务进度"""
        self._update_workflow_for_tool(tool_name, tool_result)

        if not self.planner_enabled:
            return

        tool_to_category = {
            "check_allergy": TaskCategory.CHECK.value,
            "calc_dosage": TaskCategory.DOSAGE.value,
            "generate_advice": TaskCategory.OTHER.value,
            "submit_approval": TaskCategory.APPROVAL.value,
        }
        category = tool_to_category.get(tool_name)
        if category:
            for task in self.todo_manager.get_tasks_by_category(category):
                self.todo_manager.mark_completed(task.id)

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
