# workflows.py
"""工作流管理器，用于跟踪医疗助手Agent的工作流程状态"""

import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


class WorkflowStep(Enum):
    """工作流步骤枚举"""

    # 原有步骤
    COLLECT_INFO = "collect_info"        # 收集患者信息
    QUERY_DRUG = "query_drug"            # 查询药物
    CHECK_ALLERGY = "check_allergy"      # 检查过敏
    CALC_DOSAGE = "calc_dosage"          # 计算剂量
    GENERATE_ADVICE = "generate_advice"  # 生成建议
    SUBMIT_APPROVAL = "submit_approval"  # 提交审批
    FILL_PRESCRIPTION = "fill_prescription"  # 配药（系统自动）

    # 新增交互步骤
    USER_FEEDBACK = "user_feedback"      # 等待用户反馈（药品未找到时）
    TERMINATED_WITHOUT_APPROVAL = "terminated_without_approval"  # 未创建审批单结束
    SYMPTOM_CORRECTION = "symptom_correction"  # 症状纠正处理


@dataclass
class WorkflowState:
    """工作流状态数据类"""

    patient_id: str
    current_step: WorkflowStep = WorkflowStep.COLLECT_INFO
    completed_steps: List[WorkflowStep] = field(default_factory=list)
    step_data: Dict[WorkflowStep, Dict[str, Any]] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)
    last_update_time: float = field(default_factory=time.time)
    is_completed: bool = False
    approval_id: Optional[str] = None

    # 新增字段
    termination_reason: Optional[str] = None          # 终止原因
    user_feedback_data: Optional[Dict[str, Any]] = None  # 用户反馈数据
    awaiting_user_input: bool = False                 # 是否等待用户输入
    symptoms_corrected: bool = False                  # 症状是否已纠正
    original_user_input: Optional[str] = None         # 原始用户输入（用于重新提取）

    def mark_step_completed(
        self, step: WorkflowStep, data: Optional[Dict[str, Any]] = None
    ) -> None:
        """标记步骤完成"""
        if step not in self.completed_steps:
            self.completed_steps.append(step)

        if data:
            self.step_data[step] = data

        # 更新当前步骤
        if not self.is_completed:
            try:
                # 找到下一个未完成的步骤
                all_steps = list(WorkflowStep)
                current_index = all_steps.index(step)
                if current_index + 1 < len(all_steps):
                    self.current_step = all_steps[current_index + 1]
                else:
                    self.current_step = step  # 保持在最后一步
            except ValueError:
                pass

        self.last_update_time = time.time()

        # 检查是否所有步骤都已完成
        if len(self.completed_steps) == len(WorkflowStep):
            self.is_completed = True

    def get_progress(self) -> float:
        """获取进度百分比"""
        return len(self.completed_steps) / len(WorkflowStep)

    def get_duration(self) -> float:
        """获取总持续时间（秒）"""
        return time.time() - self.start_time

    def get_step_duration(self, step: WorkflowStep) -> Optional[float]:
        """获取特定步骤的持续时间（如果有记录）"""
        if step in self.step_data and "start_time" in self.step_data[step]:
            step_start = self.step_data[step]["start_time"]
            step_end = self.step_data[step].get("end_time", time.time())
            return step_end - step_start
        return None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "patient_id": self.patient_id,
            "current_step": self.current_step.value,
            "completed_steps": [step.value for step in self.completed_steps],
            "step_data": {step.value: data for step, data in self.step_data.items()},
            "start_time": self.start_time,
            "last_update_time": self.last_update_time,
            "is_completed": self.is_completed,
            "approval_id": self.approval_id,
            "progress": self.get_progress(),
            "duration": self.get_duration(),
            "termination_reason": self.termination_reason,
            "user_feedback_data": self.user_feedback_data,
            "awaiting_user_input": self.awaiting_user_input,
            "symptoms_corrected": self.symptoms_corrected,
            "original_user_input": self.original_user_input,
        }


class WorkflowManager:
    """工作流管理器，管理多个患者的工作流状态"""

    def __init__(self):
        self.workflows: Dict[str, WorkflowState] = {}

    def create_workflow(self, patient_id: str) -> WorkflowState:
        """为患者创建工作流"""
        if patient_id in self.workflows:
            # 如果已存在，重置工作流
            self.workflows[patient_id] = WorkflowState(patient_id=patient_id)
        else:
            self.workflows[patient_id] = WorkflowState(patient_id=patient_id)
        return self.workflows[patient_id]

    def get_workflow(self, patient_id: str) -> Optional[WorkflowState]:
        """获取患者的工作流状态"""
        return self.workflows.get(patient_id)

    def update_workflow_step(
        self, patient_id: str, step: WorkflowStep, data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """更新工作流步骤"""
        workflow = self.get_workflow(patient_id)
        if not workflow:
            workflow = self.create_workflow(patient_id)

        # 记录步骤开始时间（如果这是第一次进入该步骤）
        if step not in workflow.step_data:
            step_data = data or {}
            step_data["start_time"] = time.time()
            data = step_data
        elif data:
            # 记录步骤结束时间
            data["end_time"] = time.time()

        workflow.mark_step_completed(step, data)
        return True

    def set_approval_id(self, patient_id: str, approval_id: str) -> bool:
        """设置审批ID"""
        workflow = self.get_workflow(patient_id)
        if workflow:
            workflow.approval_id = approval_id
            return True
        return False

    def get_all_workflows(self) -> List[Dict[str, Any]]:
        """获取所有工作流状态"""
        return [wf.to_dict() for wf in self.workflows.values()]

    def clear_completed(self, older_than_hours: int = 24) -> int:
        """清理已完成的工作流（默认清理24小时前的）"""
        current_time = time.time()
        cleared_count = 0

        patient_ids_to_remove = []
        for patient_id, workflow in self.workflows.items():
            if workflow.is_completed:
                # 检查是否超过指定时间
                if current_time - workflow.last_update_time > older_than_hours * 3600:
                    patient_ids_to_remove.append(patient_id)

        for patient_id in patient_ids_to_remove:
            del self.workflows[patient_id]
            cleared_count += 1

        return cleared_count

    def reset_workflow(self, patient_id: str) -> bool:
        """重置患者的工作流"""
        if patient_id in self.workflows:
            self.workflows[patient_id] = WorkflowState(patient_id=patient_id)
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self.workflows)
        completed = sum(1 for wf in self.workflows.values() if wf.is_completed)
        in_progress = total - completed

        # 计算平均进度
        if total > 0:
            avg_progress = (
                sum(wf.get_progress() for wf in self.workflows.values()) / total
            )
        else:
            avg_progress = 0.0

        return {
            "total_workflows": total,
            "completed": completed,
            "in_progress": in_progress,
            "average_progress": avg_progress,
            "oldest_workflow_hours": self._get_oldest_workflow_age_hours(),
        }

    def _get_oldest_workflow_age_hours(self) -> float:
        """获取最旧工作流的年龄（小时）"""
        if not self.workflows:
            return 0.0

        current_time = time.time()
        oldest_age = 0.0
        for workflow in self.workflows.values():
            age = (current_time - workflow.start_time) / 3600  # 转换为小时
            if age > oldest_age:
                oldest_age = age

        return oldest_age
