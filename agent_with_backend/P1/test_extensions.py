#!/usr/bin/env python3
"""Test script for workflow extensions"""

import sys
sys.path.insert(0, '.')

from core.workflows import WorkflowStep, WorkflowState

def test_workflowstep_enum_extension():
    """测试WorkflowStep枚举扩展"""

    # 原有步骤
    assert WorkflowStep.COLLECT_INFO.value == "collect_info"
    assert WorkflowStep.QUERY_DRUG.value == "query_drug"

    # 新增交互步骤
    assert WorkflowStep.USER_FEEDBACK.value == "user_feedback"
    assert WorkflowStep.TERMINATED_WITHOUT_APPROVAL.value == "terminated_without_approval"
    assert WorkflowStep.SYMPTOM_CORRECTION.value == "symptom_correction"

    # 验证所有步骤数量
    all_steps = list(WorkflowStep)
    assert len(all_steps) == 10, f"Expected 10 steps, got {len(all_steps)}"
    print("✓ WorkflowStep enum extension test passed")

def test_workflowstate_extension():
    """测试WorkflowState状态扩展"""

    # 创建实例
    state = WorkflowState(patient_id="test_patient")

    # 原有字段
    assert state.patient_id == "test_patient"
    assert state.current_step.value == "collect_info"

    # 新增字段默认值
    assert state.termination_reason is None
    assert state.user_feedback_data is None
    assert state.awaiting_user_input is False
    assert state.symptoms_corrected is False
    assert state.original_user_input is None

    # 测试to_dict包含新字段
    state_dict = state.to_dict()
    assert "termination_reason" in state_dict
    assert "user_feedback_data" in state_dict
    assert "awaiting_user_input" in state_dict
    assert "symptoms_corrected" in state_dict
    assert "original_user_input" in state_dict
    print("✓ WorkflowState extension test passed")

if __name__ == "__main__":
    try:
        test_workflowstep_enum_extension()
        test_workflowstate_extension()
        print("\nAll tests passed!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)