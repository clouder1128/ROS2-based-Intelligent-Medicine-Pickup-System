"""WorkflowManager / WorkflowState / WorkflowStep 纯逻辑单元测试

无外部依赖：纯内存状态机。
WorkflowStep 为字符串枚举，各字段行为参见 workflows.py 源码。
"""

from agent.engine.workflows import WorkflowStep, WorkflowState, WorkflowManager


class TestWorkflowStep:
    def test_step_values(self):
        """验证 WorkflowStep 枚举值为字符串"""
        assert WorkflowStep.FORM_COLLECTION.value == "form_collection"
        assert WorkflowStep.QUERY_DRUG.value == "query_drug"
        assert WorkflowStep.SUBMIT_APPROVAL.value == "submit_approval"
        assert WorkflowStep.TERMINATED_WITHOUT_APPROVAL.value == "terminated_without_approval"

    def test_step_count(self):
        assert len(WorkflowStep) == 13


class TestWorkflowState:
    def test_initial_state(self):
        state = WorkflowState(patient_id="p001")
        assert state.patient_id == "p001"
        assert state.current_step == WorkflowStep.COLLECT_INFO
        assert state.completed_steps == []
        assert state.step_data == {}
        assert state.is_completed is False
        assert state.approval_id is None

    def test_mark_step_completed(self):
        state = WorkflowState(patient_id="p001")
        state.mark_step_completed(WorkflowStep.COLLECT_INFO, {"key": "value"})
        assert WorkflowStep.COLLECT_INFO in state.completed_steps
        assert state.step_data[WorkflowStep.COLLECT_INFO] == {"key": "value"}
        # current_step 应移动到下一个步骤
        assert state.current_step == WorkflowStep.QUERY_DRUG

    def test_multiple_steps(self):
        state = WorkflowState(patient_id="p001")
        state.mark_step_completed(WorkflowStep.COLLECT_INFO)
        state.mark_step_completed(WorkflowStep.QUERY_DRUG)
        assert len(state.completed_steps) == 2
        assert state.current_step == WorkflowStep.CHECK_ALLERGY

    def test_get_progress(self):
        state = WorkflowState(patient_id="p001")
        progress = state.get_progress()
        assert progress == 0.0  # 0/13
        state.mark_step_completed(WorkflowStep.COLLECT_INFO)
        assert state.get_progress() == 1.0 / 13.0

    def test_get_duration(self):
        state = WorkflowState(patient_id="p001")
        duration = state.get_duration()
        assert duration >= 0

    def test_to_dict(self):
        state = WorkflowState(patient_id="p001")
        state.mark_step_completed(WorkflowStep.COLLECT_INFO)
        state.approval_id = "AP-001"
        d = state.to_dict()
        assert d["patient_id"] == "p001"
        assert "completed_steps" in d
        assert "progress" in d
        assert d["approval_id"] == "AP-001"


class TestWorkflowManager:
    def test_create_and_get_workflow(self):
        mgr = WorkflowManager()
        mgr.create_workflow("p001")
        wf = mgr.get_workflow("p001")
        assert wf is not None
        assert wf.patient_id == "p001"

    def test_get_nonexistent_returns_none(self):
        mgr = WorkflowManager()
        assert mgr.get_workflow("nonexistent") is None

    def test_update_workflow_step(self):
        mgr = WorkflowManager()
        mgr.create_workflow("p001")
        mgr.update_workflow_step("p001", WorkflowStep.QUERY_DRUG, {"drug": "ibuprofen"})
        wf = mgr.get_workflow("p001")
        assert WorkflowStep.QUERY_DRUG in wf.completed_steps
        assert wf.step_data[WorkflowStep.QUERY_DRUG]["drug"] == "ibuprofen"

    def test_update_nonexistent_creates_workflow(self):
        mgr = WorkflowManager()
        mgr.update_workflow_step("p001", WorkflowStep.QUERY_DRUG)
        wf = mgr.get_workflow("p001")
        assert wf is not None

    def test_set_approval_id(self):
        mgr = WorkflowManager()
        mgr.create_workflow("p001")
        mgr.set_approval_id("p001", "AP-001")
        wf = mgr.get_workflow("p001")
        assert wf.approval_id == "AP-001"

    def test_get_all_workflows(self):
        mgr = WorkflowManager()
        mgr.create_workflow("p001")
        mgr.create_workflow("p002")
        all_wf = mgr.get_all_workflows()
        assert len(all_wf) == 2

    def test_clear_completed(self):
        mgr = WorkflowManager()
        mgr.create_workflow("p001")
        mgr.create_workflow("p002")
        # 标记 p001 为已完成并设置时间
        wf = mgr.get_workflow("p001")
        wf.is_completed = True
        wf.last_update_time = 0  # 确保时间 > 24h 前
        count = mgr.clear_completed(older_than_hours=0)  # 0h 即清除所有
        assert count == 1
        assert mgr.get_workflow("p001") is None
        assert mgr.get_workflow("p002") is not None

    def test_reset_workflow(self):
        mgr = WorkflowManager()
        mgr.create_workflow("p001")
        mgr.update_workflow_step("p001", WorkflowStep.QUERY_DRUG)
        mgr.reset_workflow("p001")
        wf = mgr.get_workflow("p001")
        assert wf.completed_steps == []

    def test_get_stats_empty(self):
        mgr = WorkflowManager()
        stats = mgr.get_stats()
        assert stats["total_workflows"] == 0

    def test_get_stats(self):
        mgr = WorkflowManager()
        mgr.create_workflow("p001")
        mgr.create_workflow("p002")
        stats = mgr.get_stats()
        assert stats["total_workflows"] == 2
