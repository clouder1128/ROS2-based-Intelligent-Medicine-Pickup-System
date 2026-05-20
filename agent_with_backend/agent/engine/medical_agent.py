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

try:
    from agent.subagents.form import (
        ConsultationForm,
        IncrementalExtractor,
        check_form_completeness,
        generate_follow_up,
        generate_form_summary,
        generate_basics_question,
        any_red_flag_active,
        basics_are_filled,
        BASICS_REQUIRED_FIELDS,
        BASICS_QUESTIONS,
        rule_extract_basics,
    )
except ImportError as e:
    logger.warning(f"Form collection module not found: {e}")
    ConsultationForm = None
    IncrementalExtractor = None


# 危险信号（red flag）—— 出现任一症状立即建议就医，不执行药品推荐流程
RED_FLAG_SYMPTOMS = [
    "呼吸困难", "呼吸急促", "喘不上气",
    "高热不退", "高烧不退", "体温超过39",
    "胸痛", "胸闷",
    "意识模糊", "昏迷", "晕厥",
    "大出血", "吐血", "便血",
    "剧烈头痛", "抽搐",
    "过敏反应", "过敏性休克",
]


# ==================== 系统提示词 ====================
SYSTEM_PROMPT = """你是一个医疗用药助手。请按以下流程工作：

[危险信号检查]
- 如果患者的症状包含呼吸困难、高热（≥39°C）、胸痛、意识模糊、大出血等急重症表现，请立即建议就医并终止流程
- 不要对急重症患者推荐任何药品

[药品查询]
- 注意：如果系统消息中已经提供了匹配的药品列表，则跳过 query_drug 直接进入筛选步骤
- 如果需要自行调用 query_drug(symptom) 且返回空列表 (status="not_found")：
  - 换个相近的症状词汇重新查询，最多尝试 3 次
  - 示例：轻度头疼→头痛→偏头痛
- 如果 3 次都未找到：告知患者当前症状未找到匹配药品，建议就医，终止流程

[药品筛选与决策]
- 从药品列表中根据患者症状选出合适的药品
- 核对每项药品的适应症是否与患者的主诉（chief_complaint）直接相关
- 对每种候选药品调用 check_allergy 检查过敏风险
- 对通过过敏检查的药品调用 calc_dosage 计算剂量
- 可根据需要选择多种药品联用（重复过敏检查和剂量计算）
- 输出推荐方案时，附上简要的推理依据：为什么选这些药、排除了哪些药

[提交审批]
- 调用 generate_advice 生成用药建议
- 调用 submit_approval 将建议提交给医生审批

重要规则：
- 每次只调用一个工具，等待结果后再继续
- 如果系统中已经提供了药品列表，不要重复调用 query_drug
- 如果药品列表为空，不要重复调用 query_drug 超过 3 次
- 3 次失败后直接建议就医并结束
- 回复保持简洁，不要多余的叙述
- 每次推荐药品时，必须附带免责声明：「本推荐由 AI 生成，仅供参考，请以医生诊断为准。」

在给出最终推荐方案时，请包含以下格式的结构化分析报告：

━━━━━━━━━━━━━━━━━━━━━━
📋 分析报告

1️⃣ 症状分析
   · 患者信息：[年龄/过敏史/性别]
   · 主诉：[简要总结患者主诉]
   · 初步判断：[可能的疾病方向]

2️⃣ 药品匹配逻辑
   · [药品名称]：[选用理由，如对症、药效温和]
   · [排除的药品]：[排除原因，如无需抗生素]

3️⃣ 安全审查
   · 过敏史检查：[结果]
   · 禁忌症检查：[结果]
   · 剂量建议：[药品] [用法用量]

4️⃣ 最终推荐方案
   → [药品名称] [用法用量]
   → [辅助建议]

⚠️ 本推荐由 AI 生成，仅供参考，请以医生诊断为准。
━━━━━━━━━━━━━━━━━━━━━━
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
        self.drug_name: Optional[str] = None
        self.quantity: Optional[int] = None
        self.patient_display_name: Optional[str] = None
        self.last_steps = []
        self._last_advice = None
        self._last_advice: Optional[str] = None
        self.workflow_completed: bool = False
        self.consultation_form: Optional["ConsultationForm"] = None
        self.incremental_extractor: Optional["IncrementalExtractor"] = None
        self._matched_drugs: Optional[List[Dict]] = None
        self._pending_questions: List[Dict] = []

    def _load_form_from_session(self) -> None:
        """从 session 文件恢复表单状态"""
        if not self.patient_id or ConsultationForm is None:
            return
        state_file = os.path.join(Config.SESSION_STATE_DIR, f"{self.patient_id}_form.pkl")
        if os.path.exists(state_file):
            try:
                with open(state_file, "rb") as f:
                    self.consultation_form = pickle.load(f)
                logger.info("Loaded consultation form for %s (phase=%s)",
                            self.patient_id, self.consultation_form.phase)
            except Exception as e:
                logger.warning("Failed to load form for %s: %s", self.patient_id, e)
                self.consultation_form = None

        # 完整性校验：phase=drug_matching 但 symptoms 为空或未确认 → 回退
        if self.consultation_form and self.consultation_form.phase == "drug_matching":
            has_symptom_data = (
                any(s.location for s in self.consultation_form.symptoms)
                or bool(self.consultation_form.chief_complaint)
            )
            if not has_symptom_data or not self.consultation_form.confirmed:
                logger.warning(
                    "Session phase=drug_matching but symptoms empty or not confirmed, "
                    "resetting to form_collection"
                )
                self.consultation_form.phase = "form_collection"
                self.consultation_form.confirmed = False

    def _save_form_to_session(self) -> None:
        """保存表单状态到 session 文件"""
        if not self.patient_id or self.consultation_form is None:
            return
        state_dir = Config.SESSION_STATE_DIR
        os.makedirs(state_dir, exist_ok=True)
        state_file = os.path.join(state_dir, f"{self.patient_id}_form.pkl")
        try:
            with open(state_file, "wb") as f:
                pickle.dump(self.consultation_form, f)
        except Exception as e:
            logger.error("Failed to save form: %s", e)

    @staticmethod
    def _check_confirmation(message: str) -> bool:
        """检查用户是否确认总结报告"""
        keywords = ["确认", "正确", "没错", "是的", "对", "可以", "好", "同意",
                     "没问题", "确认无误", "yes", "y", "correct", "confirm"]
        msg_lower = message.strip().lower()
        return any(kw in msg_lower for kw in keywords)

    def submit_basics(self, data: Dict[str, Any]) -> None:
        """直接从结构化数据填充基础信息（Round 1 固定表单），不经过 LLM。"""
        self._load_form_from_session()
        if self.consultation_form is None:
            self.consultation_form = ConsultationForm()

        cf = self.consultation_form

        # 性别
        if data.get("gender"):
            cf.patient.gender = data["gender"]
            cf.filled_fields.add("patient.gender")

        # 年龄
        age = data.get("age")
        if age is not None:
            try:
                cf.patient.age = float(age)
                cf.patient.age_unit = data.get("age_unit", "岁")
                cf.filled_fields.add("patient.age")
                cf.filled_fields.add("patient.age_unit")
            except (TypeError, ValueError):
                pass

        # 体重（支持斤→公斤转换）
        weight_raw = data.get("weight_kg") or data.get("weight")
        weight_unit = data.get("weight_unit", "kg")
        if weight_raw is not None:
            try:
                w = float(weight_raw)
                if weight_unit == "斤":
                    w = w / 2.0
                cf.patient.weight_kg = w
                cf.filled_fields.add("patient.weight_kg")
            except (TypeError, ValueError):
                pass

        # 药物过敏
        drug_allergies = data.get("drug_allergies", [])
        if isinstance(drug_allergies, list):
            cf.allergies.drug_allergies = drug_allergies
        elif isinstance(drug_allergies, str):
            cf.allergies.drug_allergies = [drug_allergies] if drug_allergies else []
        if cf.allergies.drug_allergies or drug_allergies == []:
            cf.filled_fields.add("allergies.drug_allergies")

        # 当前用药
        current_meds = data.get("current_medications", [])
        if isinstance(current_meds, list):
            for med_name in current_meds:
                if med_name.strip():
                    from agent.subagents.form import MedicationRecord
                    cf.current_medications.append(
                        MedicationRecord(medication_name=med_name.strip())
                    )
        cf.filled_fields.add("current_medications")

        # 慢性病史（可选，用 supplementary 存储）
        chronic = data.get("chronic_diseases", [])
        if isinstance(chronic, list) and chronic:
            cf.medical_history.chronic_diseases = chronic
            cf.filled_fields.add("medical_history.chronic_diseases")

        # 切换阶段
        cf.phase = "basics_collection"
        cf.conversation_log.append({
            "role": "system",
            "content": f"基础信息已提交：性别={cf.patient.gender}，年龄={cf.patient.age}，体重={cf.patient.weight_kg}kg，"
                       f"过敏={cf.allergies.drug_allergies}，用药={current_meds}"
        })
        self._save_form_to_session()
        logger.info("Basics submitted for %s: age=%s, weight=%s, gender=%s",
                    self.patient_id, cf.patient.age, cf.patient.weight_kg, cf.patient.gender)

    def _query_drugs_with_retry(self, symptoms: List[str], llm_client) -> List[Dict]:
        """尝试用不同关键词查询药品，支持 LLM 生成同义词重试"""
        from database.pharmacy_client import query_drugs_by_symptom, query_drug_by_name

        tried_keywords = set()
        max_retries = 3

        # 第一轮：用提取到的所有症状关键词查询，合并去重
        all_drugs = []
        seen_ids = set()
        for symptom in symptoms:
            if symptom in tried_keywords:
                continue
            tried_keywords.add(symptom)
            drugs = query_drugs_by_symptom(symptom)
            for d in drugs:
                did = d.get("drug_id")
                if did not in seen_ids:
                    seen_ids.add(did)
                    all_drugs.append(d)
        if all_drugs:
            return all_drugs

        # 第二轮：尝试按药品名称查询（兼容直接输入药名的情况）
        if symptoms:
            drug = query_drug_by_name(symptoms[0])
            if drug:
                return [drug]

        # 构建完整临床上下文（用于 LLM 同义词生成）
        clinical_context = "、".join(symptoms[:5])
        if self.consultation_form and self.consultation_form.chief_complaint:
            clinical_context += f"。主诉：{self.consultation_form.chief_complaint}"

        # 第三轮：让 LLM 生成同义词来重试
        original_symptoms = set(symptoms)  # 保留原始症状用于相关性校验
        retry_count = 0
        while retry_count < max_retries:
            # 让 LLM 生成一个相近的医学症状关键词
            prompt = (
                f"患者症状：{clinical_context}\n"
                f"已尝试过关键词：{'、'.join(tried_keywords)}，均未找到匹配药品。\n"
                f"请分析患者症状，将口语化症状转换为标准医学症状关键词（如'上吐'→'呕吐'、'下泄'→'腹泻'），"
                f"然后输出一个最可能匹配的关键词用于重新搜索（只回复关键词本身，不要其他内容）："
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
                    # 相关性校验：药品必须有至少一个 indication 包含原始症状关键词
                    relevant = []
                    for d in drugs:
                        indications = d.get("indications", [])
                        if any(orig_kw in ind for ind in indications for orig_kw in original_symptoms):
                            relevant.append(d)
                    if relevant:
                        return relevant
                    # 无直接相关药品，记日志并继续重试
                    logger.info(
                        "LLM synonym '%s' matched %d drugs but none relevant to original symptoms %s, retrying",
                        new_keyword, len(drugs), original_symptoms
                    )
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
        """执行Agent循环，处理用户消息，支持三阶段表单收集"""
        self.patient_id = patient_id or "anonymous"
        steps: List[Dict] = []

        # === Phase A/B: 表单收集与确认（启用时）===
        if Config.ENABLE_FORM_COLLECTION and ConsultationForm is not None:
            reply, phase_steps = self._run_form_phases(user_message)
            if phase_steps is not None:
                # Phase A 或 B 已处理，直接返回
                steps.extend(phase_steps)
                return reply, steps
            # phase_steps is None → 表单已确认，继续到 Phase C

        # === Phase C: 药品匹配与Agent决策（现有流程）===
        return self._execute_drug_matching_phase(user_message, steps)

    def _run_form_phases(self, user_message: str) -> Tuple[str, Optional[List[Dict]]]:
        """Phase A/B: 表单收集和确认。
        返回 (reply, steps) 表示已处理；返回 (_, None) 表示可继续到 Phase C。
        """
        steps: List[Dict] = []
        self._pending_questions = []

        # 1. 加载表单
        self._load_form_from_session()

        # 2. 表单收集阶段（包括基础信息 Round 1 和症状收集 Round 2+）
        if (
            self.consultation_form is None
            or self.consultation_form.phase in ("basics_collection", "form_collection")
        ):
            if self.consultation_form is None:
                self.consultation_form = ConsultationForm()
            if self.incremental_extractor is None:
                self.incremental_extractor = IncrementalExtractor(
                    llm_client=self.llm_client
                )

            # Round 1 问卷：基础信息逐条采集
            if not basics_are_filled(self.consultation_form):
                self.consultation_form.phase = "basics_collection"

                # 如果有对话记录，用规则从用户消息中提取（不调用 LLM）
                if len(self.consultation_form.conversation_log) > 0:
                    target_field = None
                    for q_def in BASICS_QUESTIONS:
                        if q_def["field"] not in self.consultation_form.filled_fields:
                            target_field = q_def["field"]
                            break
                    if target_field:
                        rule_extract_basics(
                            self.consultation_form, user_message, target_field
                        )
                    self.consultation_form.conversation_log.append(
                        {"role": "user", "content": user_message}
                    )

                # 检查是否已全部填完
                if basics_are_filled(self.consultation_form):
                    self.consultation_form.phase = "form_collection"
                    self._save_form_to_session()
                    msg = "基础信息已记录！请详细描述您的症状，包括部位、性质、持续时间等。"
                    self.consultation_form.conversation_log.append(
                        {"role": "assistant", "content": msg}
                    )
                    steps.append(
                        {"step": 0, "type": "assistant", "content": msg, "duration_ms": 0}
                    )
                    self.last_steps = steps
                    return msg, steps

                # 生成下一个问题
                next_q = generate_basics_question(self.consultation_form)
                if next_q:
                    self._pending_questions = [next_q]
                    msg = next_q.text
                else:
                    msg = "请回答以上问题。"
                self.consultation_form.conversation_log.append(
                    {"role": "assistant", "content": msg}
                )
                steps.append(
                    {"step": 0, "type": "assistant", "content": msg, "duration_ms": 0}
                )
                self.last_steps = steps
                self._save_form_to_session()
                return msg, steps

            # 刚从 basics_collection 转入 → 提示描述症状
            if self.consultation_form.phase == "basics_collection":
                self.consultation_form.phase = "form_collection"
                self._save_form_to_session()
                msg = "基础信息已记录！请详细描述您的症状，包括部位、性质、持续时间等。"
                self.consultation_form.conversation_log.append(
                    {"role": "assistant", "content": msg}
                )
                steps.append(
                    {"step": 0, "type": "assistant", "content": msg, "duration_ms": 0}
                )
                self.last_steps = steps
                return msg, steps

            # 2a. 增量提取并合并
            self.consultation_form = self.incremental_extractor.extract_and_merge(
                self.consultation_form, user_message
            )
            self.consultation_form.conversation_log.append(
                {"role": "user", "content": user_message}
            )

            # 2b. 红色警报检查
            if any_red_flag_active(self.consultation_form):
                active = self.consultation_form.red_flags.active_list()
                flag_text = "、".join(active)
                logger.warning(
                    "Red flags detected via form: %s (user: %s)",
                    active, user_message[:50]
                )
                msg = (
                    f"⚠️ **紧急情况提示**\n\n"
                    f"根据您提供的信息，检测到以下警示信号：{flag_text}。"
                    f"这可能属于需要紧急医疗干预的情况。\n\n"
                    f"**建议您立即就医，由医生进行专业诊断和治疗。**\n\n"
                    f"请勿自行用药，以免延误病情。"
                )
                self.consultation_form.conversation_log.append(
                    {"role": "assistant", "content": msg}
                )
                self.workflow_completed = True
                steps.append(
                    {"step": 0, "type": "assistant", "content": msg, "duration_ms": 0}
                )
                self.last_steps = steps
                self._save_form_to_session()
                return msg, steps

            # 2c. 完整性检查
            completeness = check_form_completeness(self.consultation_form)
            if completeness.get("phase") == "red_flag":
                msg = (
                    f"⚠️ **紧急情况提示**\n\n"
                    f"根据您提供的信息，检测到需紧急就医的情况。"
                    f"**建议您立即就医，由医生进行专业诊断和治疗。**\n\n"
                    f"请勿自行用药，以免延误病情。"
                )
                self.consultation_form.conversation_log.append(
                    {"role": "assistant", "content": msg}
                )
                self.workflow_completed = True
                steps.append(
                    {"step": 0, "type": "assistant", "content": msg, "duration_ms": 0}
                )
                self.last_steps = steps
                self._save_form_to_session()
                return msg, steps

            # 2d. 字段缺失 → 追问（支持可点击选项）
            if completeness.get("phase") == "continue":
                follow_up = generate_follow_up(
                    self.consultation_form,
                    completeness.get("missing_global", []),
                    completeness.get("missing_symptom_core", []),
                    completeness.get("missing_conditional", []),
                )
                question = follow_up.get("text", "")
                self._pending_questions = follow_up.get("questions", [])
                self.consultation_form.conversation_log.append(
                    {"role": "assistant", "content": question}
                )
                steps.append(
                    {"step": 0, "type": "assistant", "content": question, "duration_ms": 0}
                )
                self.last_steps = steps
                self._save_form_to_session()

                workflow = self.workflow_manager.create_workflow(self.patient_id)
                workflow.mark_step_completed(WorkflowStep.FORM_COLLECTION, {
                    "filled": list(self.consultation_form.filled_fields),
                    "missing_global": completeness.get("missing_global", []),
                    "missing_conditional": completeness.get("missing_conditional", []),
                })
                return question, steps

            # 2e. 全局必填已齐 → 进入确认阶段
            self.consultation_form.phase = "form_confirmation"
            self._save_form_to_session()

            workflow = self.workflow_manager.create_workflow(self.patient_id)
            workflow.mark_step_completed(WorkflowStep.FORM_COLLECTION, {
                "filled": list(self.consultation_form.filled_fields),
                "status": "completed",
            })

            summary = generate_form_summary(self.consultation_form)
            self.consultation_form.conversation_log.append(
                {"role": "assistant", "content": summary}
            )
            steps.append(
                {"step": 0, "type": "assistant", "content": summary, "duration_ms": 0}
            )
            self.last_steps = steps
            return summary, steps

        # 3. 确认阶段
        if self.consultation_form.phase == "form_confirmation":
            if self._check_confirmation(user_message):
                has_symptom_data = (
                    any(s.location for s in self.consultation_form.symptoms)
                    or bool(self.consultation_form.chief_complaint)
                )
                if not has_symptom_data:
                    self.consultation_form.phase = "form_collection"
                    self._save_form_to_session()
                    msg = '未检测到有效的症状信息，请描述您的主要症状（如"我头痛"）。'
                    self.consultation_form.conversation_log.append(
                        {"role": "assistant", "content": msg}
                    )
                    steps.append({"step": 0, "type": "assistant", "content": msg, "duration_ms": 0})
                    self.last_steps = steps
                    return msg, steps

                self.consultation_form.confirmed = True
                self.consultation_form.phase = "drug_matching"
                self._save_form_to_session()

                self.workflow_manager.update_workflow_step(
                    self.patient_id,
                    WorkflowStep.FORM_CONFIRMATION,
                    {"confirmed": True},
                )
                return "", None
            else:
                self.consultation_form.phase = "form_collection"
                if self.incremental_extractor is None:
                    self.incremental_extractor = IncrementalExtractor(
                        llm_client=self.llm_client
                    )
                self.consultation_form = self.incremental_extractor.extract_and_merge(
                    self.consultation_form, user_message
                )
                self._save_form_to_session()

                completeness = check_form_completeness(self.consultation_form)
                if completeness.get("phase") == "continue":
                    follow_up = generate_follow_up(
                        self.consultation_form,
                        completeness.get("missing_global", []),
                        completeness.get("missing_symptom_core", []),
                        completeness.get("missing_conditional", []),
                    )
                    question = follow_up.get("text", "")
                    self._pending_questions = follow_up.get("questions", [])
                    self.consultation_form.conversation_log.append(
                        {"role": "assistant", "content": question}
                    )
                    steps.append(
                        {"step": 0, "type": "assistant", "content": question, "duration_ms": 0}
                    )
                    self.last_steps = steps
                    return question, steps

                self.consultation_form.phase = "form_confirmation"
                self._save_form_to_session()
                summary = generate_form_summary(self.consultation_form)
                self.consultation_form.conversation_log.append(
                    {"role": "assistant", "content": summary}
                )
                steps.append(
                    {"step": 0, "type": "assistant", "content": summary, "duration_ms": 0}
                )
                self.last_steps = steps
                return summary, steps

        # 4. drug_matching 阶段
        if self.consultation_form.phase == "drug_matching":
            return "", None

        return "", None

    def _execute_drug_matching_phase(
        self, user_message: str, steps: List[Dict]
    ) -> Tuple[str, List[Dict]]:
        """Phase C: 药品查询 + Agent循环（从现有 run() 中提取）"""
        workflow = self.workflow_manager.create_workflow(self.patient_id)

        # 当从表单收集模式进入时，使用已收集的表单数据
        if (
            Config.ENABLE_FORM_COLLECTION
            and ConsultationForm is not None
            and self.consultation_form is not None
            and self.consultation_form.confirmed
        ):
            form = self.consultation_form
            # 从表单构建结构化信息：优先使用 location，其次 quality，最后 accompanying_symptoms
            symptoms = []
            for s in form.symptoms:
                if s.location:
                    symptoms.append(s.location)
                if s.quality:
                    symptoms.append(s.quality)
                if s.accompanying_symptoms:
                    symptoms.extend(s.accompanying_symptoms)
            # 从 chief_complaint 拆分补充关键词（当 symptoms 为空时）
            if not symptoms and form.chief_complaint:
                for sep in ['、', '，', ',', '.', '。', ' ']:
                    if sep in form.chief_complaint:
                        symptoms = [kw.strip() for kw in form.chief_complaint.split(sep) if kw.strip()]
                        break
                if not symptoms:
                    symptoms = [form.chief_complaint]
            # 症状仍为空 → 表单无效，回退到收集阶段
            if not symptoms:
                logger.warning("No symptoms in confirmed form, resetting to form_collection")
                form.phase = "form_collection"
                form.confirmed = False
                self._save_form_to_session()
                return "表单中缺少有效的症状信息，请重新描述您的症状。", steps
            chief_complaint = form.chief_complaint or ""

            # 红色警报检查（基于已收集的红色警报字段）
            if any_red_flag_active(form):
                active = form.red_flags.active_list()
                flag_text = "、".join(active)
                msg = (
                    f"⚠️ **紧急情况提示**\n\n"
                    f"根据您提供的信息，检测到以下警示信号：{flag_text}。"
                    f"**建议您立即就医，由医生进行专业诊断和治疗。**\n\n"
                    f"请勿自行用药，以免延误病情。"
                )
                self.message_manager.add_message("assistant", msg)
                self.workflow_completed = True
                steps.append(
                    {"step": 0, "type": "assistant", "content": msg, "duration_ms": 0}
                )
                self.last_steps = steps
                workflow.mark_step_completed(
                    WorkflowStep.DRUG_QUERY_FAILED,
                    {"reason": "red_flag_detected", "flags": active},
                )
                return msg, steps

            # 药品查询（分级：先用主诉精确查，无结果再降级用拆分症状）
            if chief_complaint:
                drug_list = self._query_drugs_with_retry([chief_complaint], self.llm_client)
            else:
                drug_list = []
            if not drug_list:
                drug_list = self._query_drugs_with_retry(symptoms, self.llm_client)
            self._matched_drugs = drug_list
            if not drug_list:
                msg = (
                    "已尝试多种关键词查询，未找到与您症状匹配的药品。"
                    "建议您尽快就医，由医生进行专业诊断。"
                )
                self.message_manager.add_message("assistant", msg)
                self.workflow_completed = True
                steps.append(
                    {"step": 0, "type": "assistant", "content": msg, "duration_ms": 0}
                )
                self.last_steps = steps
                workflow.mark_step_completed(
                    WorkflowStep.DRUG_QUERY_FAILED, {"reason": "no_drugs_found"}
                )
                return msg, steps

            # 创建工作流计划
            self._create_workflow_plan(symptoms, len(drug_list))

            # 构建增强消息（使用表单数据）
            symptoms_text = "、".join(symptoms)
            allergies_text = (
                "、".join(form.allergies.drug_allergies)
                if form.allergies.drug_allergies
                else "无"
            )
            drug_summary_lines = "\n".join(
                f"  - {d['name']}（{d.get('retail_price', '?')}元）"
                f"适应症：{'、'.join(d.get('indications', ['未知']))}"
                for d in drug_list[:20]
            )

            # 补充缺失字段说明
            completeness = check_form_completeness(form)
            missing_notes = ""
            if completeness.get("missing_conditional"):
                missing_notes = (
                    f"\n[注意] 以下信息未获取（基于默认假设，供医生复核）：\n"
                    f"  {'、'.join(completeness['missing_conditional'])}\n"
                )

            # 怀孕/哺乳状态
            preg_text = "未提供"
            if form.patient.pregnant:
                preg_text = form.patient.pregnant
                if form.patient.gestational_weeks:
                    preg_text += f"（孕{form.patient.gestational_weeks}周）"
                if form.patient.breastfeeding:
                    preg_text += "、哺乳期"

            # 食物/辅料过敏
            food_allergy_parts = []
            if form.allergies.food_allergies:
                food_allergy_parts.append(
                    "食物:" + "、".join(form.allergies.food_allergies))
            if form.allergies.excipient_allergies:
                food_allergy_parts.append(
                    "辅料:" + "、".join(form.allergies.excipient_allergies))
            food_allergy_text = "、".join(food_allergy_parts) if food_allergy_parts else "无"

            # 病史摘要
            mh = form.medical_history
            history_parts = []
            if mh.chronic_diseases:
                history_parts.append(f"慢性病: {'、'.join(mh.chronic_diseases)}")
            disease_map = {
                "has_peptic_ulcer": "胃溃疡", "has_gi_bleeding": "消化道出血",
                "has_liver_disease": "肝病", "has_kidney_disease": "肾病",
                "has_epilepsy": "癫痫", "has_glaucoma": "青光眼",
                "has_prostate_hyperplasia": "前列腺增生", "has_thyroid_disease": "甲状腺病",
                "has_heart_failure": "心力衰竭", "has_arrhythmia": "心律失常",
                "has_bleeding_disorder": "出血性疾病",
            }
            for attr, label in disease_map.items():
                val = getattr(mh, attr, None)
                if val and str(val) in ("是", "有", "yes"):
                    history_parts.append(label)
            if mh.recent_surgery:
                history_parts.append(f"近期手术: {mh.recent_surgery}")
            history_text = "、".join(history_parts) if history_parts else "无"

            # 症状详情
            symptom_detail_lines = []
            for s in form.symptoms:
                detail_parts = []
                if s.location:
                    detail_parts.append(f"部位:{s.location}")
                if s.quality:
                    detail_parts.append(f"性质:{s.quality}")
                if s.severity_0_10 is not None:
                    detail_parts.append(f"程度:{s.severity_0_10}/10")
                if s.duration:
                    detail_parts.append(f"持续:{s.duration}")
                if s.onset_time:
                    detail_parts.append(f"起病:{s.onset_time}")
                if s.pattern:
                    detail_parts.append(f"规律:{s.pattern}")
                if s.trigger_factors:
                    detail_parts.append(f"诱发:{s.trigger_factors}")
                if detail_parts:
                    symptom_detail_lines.append("，".join(detail_parts))
            symptom_details_text = " | ".join(symptom_detail_lines) if symptom_detail_lines else "未提供"

            # 生命体征
            vs_parts = []
            vs = form.vital_signs
            if vs.temperature_c is not None:
                vs_parts.append(f"体温:{vs.temperature_c}℃")
            if vs.has_fever:
                vs_parts.append(f"发烧:{vs.has_fever}")
            if vs.fever_duration_days is not None:
                vs_parts.append(f"发烧天数:{vs.fever_duration_days}")
            if vs.heart_rate_bpm is not None:
                vs_parts.append(f"心率:{vs.heart_rate_bpm}bpm")
            if vs.blood_pressure_systolic is not None and vs.blood_pressure_diastolic is not None:
                vs_parts.append(f"血压:{vs.blood_pressure_systolic}/{vs.blood_pressure_diastolic}")
            vitals_text = "、".join(vs_parts) if vs_parts else "未提供"

            enhanced_message = (
                f"[患者描述] {user_message}\n"
                f"[系统提取信息（来自结构化表单）]\n"
                f"- 主诉: {chief_complaint}\n"
                f"- 症状: {symptoms_text}\n"
                f"- 症状详情: {symptom_details_text}\n"
                f"- 年龄: {form.patient.age or '未提供'}岁\n"
                f"- 体重: {form.patient.weight_kg or '未提供'}kg\n"
                f"- 性别: {form.patient.gender or '未提供'}\n"
                f"- 怀孕/哺乳: {preg_text}\n"
                f"- 过敏史(药物): {allergies_text}\n"
                f"- 过敏史(食物/辅料): {food_allergy_text}\n"
                f"- 病史: {history_text}\n"
                f"- 生命体征: {vitals_text}\n"
                f"- 当前用药: {len(form.current_medications)}种\n"
                f"{missing_notes}"
                f"[附加信息] {json.dumps(form.supplementary, ensure_ascii=False) if form.supplementary else '无'}"
                f"\n[系统中匹配的药品列表（共{len(drug_list)}种）"
                f"—— 已查询完毕，禁止再调用 query_drug，直接使用以下列表]\n"
                f"{drug_summary_lines}\n"
                f"\n请根据上述药品列表为患者筛选药品、检查过敏、计算剂量。"
                f"如果列表中有适合的药品，直接进行后续步骤"
                f"（过敏检查→剂量计算→生成建议→提交审批）。"
            )
            enhanced_message += self._format_plan_for_llm()
            self.message_manager.add_message("user", enhanced_message)

        else:
            # 旧路径：直接提取症状（未启用表单收集）
            # 1. 调用子代理提取症状
            structured_info = extract_symptoms(user_message, self.llm_client)
            if isinstance(structured_info, dict):
                from agent.subagents.models import StructuredSymptoms
                structured_info = StructuredSymptoms.from_dict(structured_info)

            # 1.5 危险信号检测
            all_text = (
                user_message + " " + " ".join(structured_info.symptoms)
            ).lower()
            detected_red_flags = [
                s for s in RED_FLAG_SYMPTOMS if s in all_text
            ]
            if detected_red_flags:
                flag_text = "、".join(detected_red_flags)
                logger.warning(
                    "Red flags detected: %s (user: %s)",
                    detected_red_flags, user_message[:50]
                )
                msg = (
                    f"⚠️ **紧急情况提示**\n\n"
                    f"您描述的症状中包含「{flag_text}」，"
                    f"这可能属于需要紧急医疗干预的情况。\n\n"
                    f"**建议您立即就医，由医生进行专业诊断和治疗。**\n\n"
                    f"请勿自行用药，以免延误病情。"
                )
                self.message_manager.add_message("assistant", msg)
                self.workflow_completed = True
                steps.append(
                    {"step": 0, "type": "assistant", "content": msg, "duration_ms": 0}
                )
                self.last_steps = steps
                workflow.mark_step_completed(
                    WorkflowStep.DRUG_QUERY_FAILED,
                    {"reason": "red_flag_detected", "flags": detected_red_flags},
                )
                return msg, steps

            # 2. 后端批量查询药品（带重试）
            symptoms = structured_info.symptoms or [user_message]
            drug_list = self._query_drugs_with_retry(symptoms, self.llm_client)

            if not drug_list:
                msg = (
                    "已尝试多种关键词查询，未找到与您症状匹配的药品。"
                    "建议您尽快就医，由医生进行专业诊断。"
                )
                self.message_manager.add_message("assistant", msg)
                self.workflow_completed = True
                steps.append(
                    {"step": 0, "type": "assistant", "content": msg, "duration_ms": 0}
                )
                self.last_steps = steps
                workflow.mark_step_completed(
                    WorkflowStep.DRUG_QUERY_FAILED, {"reason": "no_drugs_found"}
                )
                return msg, steps

            # 3. 创建工作流任务计划
            self._create_workflow_plan(symptoms, len(drug_list))

            # 4. 由提取的症状信息增强用户消息
            symptoms_text = "、".join(symptoms)
            severity_text = ""
            if structured_info.severity:
                severity_text = "，".join(
                    f"{symptom}({degree})"
                    for symptom, degree in structured_info.severity.items()
                )
            patient_info = structured_info.patient_info
            allergies_text = "无"
            if patient_info.allergies:
                if isinstance(patient_info.allergies, list):
                    allergies_text = (
                        "、".join(patient_info.allergies)
                        if patient_info.allergies
                        else "无"
                    )
                else:
                    allergies_text = str(patient_info.allergies)

            drug_summary_lines = "\n".join(
                f"  - {d['name']}（{d.get('retail_price', '?')}元）"
                f"适应症：{'、'.join(d.get('indications', ['未知']))}"
                for d in drug_list[:20]
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
                f"\n[系统中匹配的药品列表（共{len(drug_list)}种）"
                f"—— 已查询完毕，禁止再调用 query_drug，直接使用以下列表]\n"
                f"{drug_summary_lines}\n"
                f"\n请根据上述药品列表为患者筛选药品、检查过敏、计算剂量。"
                f"如果列表中有适合的药品，直接进行后续步骤"
                f"（过敏检查→剂量计算→生成建议→提交审批）。"
            )
            enhanced_message += self._format_plan_for_llm()
            self.message_manager.add_message("user", enhanced_message)

        # 5. Agent循环（两种路径共享）
        max_iterations = Config.MAX_ITERATIONS
        last_tool_called = None

        for i in range(max_iterations):
            step_start = time.time()
            messages = self.message_manager.get_full_messages()

            with log_duration(logger, f"Iteration {i} LLM call"):
                response = self.llm_client.chat(
                    messages=messages,
                    tools=TOOLS,
                    temperature=Config.LLM_TEMPERATURE,
                )

            tool_calls = response.get("tool_calls")
            if tool_calls:
                openai_tc_list = []
                for tc in tool_calls:
                    tc_id = tc.get("id") or f"call_{int(time.time()*1000)}"
                    openai_tc_list.append({
                        "id": tc_id,
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(
                                tc.get("input", {}), ensure_ascii=False
                            ),
                        },
                    })

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

                for tc in tool_calls:
                    tool_name = tc["name"]
                    last_tool_called = tool_name
                    tool_input = tc["input"]
                    tool_call_id = tc.get("id") or f"call_{int(time.time()*1000)}"

                    if tool_name == "submit_approval" and self.patient_display_name:
                        tool_input["patient_name"] = self.patient_display_name

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
                        # 拦截重复的 query_drug 调用：已有药品列表时返回缓存
                        if tool_name == "query_drug" and self._matched_drugs:
                            logger.info("Intercepting query_drug call, returning cached %d drugs", len(self._matched_drugs))
                            formatted = []
                            for d in self._matched_drugs:
                                formatted.append({
                                    "name": d.get("name", "未知"),
                                    "specification": d.get("specification", ""),
                                    "price": d.get("retail_price", 0.0),
                                    "stock": d.get("quantity", 0),
                                    "is_prescription": bool(d.get("is_prescription", False)),
                                    "indications": d.get("indications", []),
                                    "category": d.get("category", ""),
                                })
                            tool_result = json.dumps({
                                "status": "success",
                                "count": len(formatted),
                                "query": tool_input.get("query", ""),
                                "drugs": formatted,
                            }, ensure_ascii=False)
                        else:
                            tool_result = execute_tool(tool_name, tool_input)
                        step_record["result"] = tool_result
                    except ToolExecutionError as e:
                        tool_result = f"工具执行错误: {str(e)}"
                        step_record["error"] = str(e)

                    step_record["duration_ms"] = int(
                        (time.time() - tool_start) * 1000
                    )
                    steps.append(step_record)

                    self.message_manager.add_tool_result(
                        tool_call_id, tool_result
                    )

                    if tool_name == "submit_approval":
                        if tool_input.get("drug_name"):
                            self.drug_name = tool_input["drug_name"]
                        if tool_input.get("quantity"):
                            self.quantity = tool_input["quantity"]
                        if tool_input.get("advice"):
                            self._last_advice = tool_input["advice"]
                        data = extract_json_from_text(tool_result)
                        if data and "approval_id" in data:
                            self.approval_id = data["approval_id"]
                            self.workflow_manager.set_approval_id(
                                self.patient_id, self.approval_id
                            )
                        self.workflow_completed = True

                    self._update_workflow_and_todo(tool_name, tool_result)
                continue

            if response.get("content"):
                assistant_reply = response["content"]
                if self.workflow_completed and getattr(
                    self, "_last_advice", None
                ):
                    assistant_reply = (
                        self._last_advice + "\n\n" + assistant_reply
                    )
                self.message_manager.add_message(
                    "assistant", assistant_reply
                )
                steps.append({
                    "step": i,
                    "type": "assistant",
                    "content": assistant_reply,
                    "duration_ms": int((time.time() - step_start) * 1000),
                })
                self.last_steps = steps
                return assistant_reply, steps

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
        # 先删除 form pickle（需要 patient_id）
        if self.patient_id:
            state_file = os.path.join(
                Config.SESSION_STATE_DIR, f"{self.patient_id}_form.pkl"
            )
            if os.path.exists(state_file):
                try:
                    os.unlink(state_file)
                except Exception:
                    pass
        self.patient_id = None
        self.approval_id = None
        self.drug_name = None
        self.quantity = None
        self.patient_display_name = None
        self.last_steps = []
        self.workflow_completed = False
        self._matched_drugs = None
        self.consultation_form = None
        self._pending_questions = []

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
