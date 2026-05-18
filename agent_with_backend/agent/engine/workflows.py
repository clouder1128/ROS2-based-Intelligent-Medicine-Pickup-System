# workflows.py
"""工作流管理器，用于跟踪医疗助手Agent的工作流程状态"""

import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


class WorkflowStep(Enum):
    """工作流步骤枚举"""
    COLLECT_INFO = "collect_info"
    QUERY_DRUG = "query_drug"
    CHECK_ALLERGY = "check_allergy"
    CALC_DOSAGE = "calc_dosage"
    GENERATE_ADVICE = "generate_advice"
    SUBMIT_APPROVAL = "submit_approval"
    FILL_PRESCRIPTION = "fill_prescription"
    USER_FEEDBACK = "user_feedback"
    TERMINATED_WITHOUT_APPROVAL = "terminated_without_approval"
    SYMPTOM_CORRECTION = "symptom_correction"
    DRUG_QUERY_FAILED = "drug_query_failed"


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
    termination_reason: Optional[str] = None
    user_feedback_data: Optional[Dict[str, Any]] = None
    awaiting_user_input: bool = False
    symptoms_corrected: bool = False
    original_user_input: Optional[str] = None

    def mark_step_completed(self, step: WorkflowStep, data: Optional[Dict[str, Any]] = None) -> None:
        if step not in self.completed_steps:
            self.completed_steps.append(step)
        if data:
            self.step_data[step] = data
        if not self.is_completed:
            try:
                all_steps = list(WorkflowStep)
                current_index = all_steps.index(step)
                if current_index + 1 < len(all_steps):
                    self.current_step = all_steps[current_index + 1]
                else:
                    self.current_step = step
            except ValueError:
                pass
        self.last_update_time = time.time()
        if len(self.completed_steps) == len(WorkflowStep):
            self.is_completed = True

    def get_progress(self) -> float:
        return len(self.completed_steps) / len(WorkflowStep)

    def get_duration(self) -> float:
        return time.time() - self.start_time

    def get_step_duration(self, step: WorkflowStep) -> Optional[float]:
        if step in self.step_data and "start_time" in self.step_data[step]:
            step_start = self.step_data[step]["start_time"]
            step_end = self.step_data[step].get("end_time", time.time())
            return step_end - step_start
        return None

    def to_dict(self) -> Dict[str, Any]:
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
        if patient_id in self.workflows:
            self.workflows[patient_id] = WorkflowState(patient_id=patient_id)
        else:
            self.workflows[patient_id] = WorkflowState(patient_id=patient_id)
        return self.workflows[patient_id]

    def get_workflow(self, patient_id: str) -> Optional[WorkflowState]:
        return self.workflows.get(patient_id)

    def update_workflow_step(self, patient_id: str, step: WorkflowStep, data: Optional[Dict[str, Any]] = None) -> bool:
        workflow = self.get_workflow(patient_id)
        if not workflow:
            workflow = self.create_workflow(patient_id)
        if step not in workflow.step_data:
            step_data = data or {}
            step_data["start_time"] = time.time()
            data = step_data
        elif data:
            data["end_time"] = time.time()
        workflow.mark_step_completed(step, data)
        return True

    def set_approval_id(self, patient_id: str, approval_id: str) -> bool:
        workflow = self.get_workflow(patient_id)
        if workflow:
            workflow.approval_id = approval_id
            return True
        return False

    def get_all_workflows(self) -> List[Dict[str, Any]]:
        return [wf.to_dict() for wf in self.workflows.values()]

    def clear_completed(self, older_than_hours: int = 24) -> int:
        current_time = time.time()
        cleared_count = 0
        patient_ids_to_remove = []
        for patient_id, workflow in self.workflows.items():
            if workflow.is_completed:
                if current_time - workflow.last_update_time > older_than_hours * 3600:
                    patient_ids_to_remove.append(patient_id)
        for patient_id in patient_ids_to_remove:
            del self.workflows[patient_id]
            cleared_count += 1
        return cleared_count

    def reset_workflow(self, patient_id: str) -> bool:
        if patient_id in self.workflows:
            self.workflows[patient_id] = WorkflowState(patient_id=patient_id)
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        total = len(self.workflows)
        completed = sum(1 for wf in self.workflows.values() if wf.is_completed)
        in_progress = total - completed
        avg_progress = sum(wf.get_progress() for wf in self.workflows.values()) / total if total > 0 else 0.0
        return {
            "total_workflows": total,
            "completed": completed,
            "in_progress": in_progress,
            "average_progress": avg_progress,
            "oldest_workflow_hours": self._get_oldest_workflow_age_hours(),
        }

    def _get_oldest_workflow_age_hours(self) -> float:
        if not self.workflows:
            return 0.0
        current_time = time.time()
        oldest_age = 0.0
        for workflow in self.workflows.values():
            age = (current_time - workflow.start_time) / 3600
            if age > oldest_age:
                oldest_age = age
        return oldest_age
