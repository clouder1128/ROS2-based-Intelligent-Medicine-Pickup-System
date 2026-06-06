import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import agent.engine.medical_agent as ma
from agent.engine.medical_agent import MedicalAgent
from agent.subagents.form import (
    AllergyInfo,
    ConsultationForm,
    MedicalHistory,
    PatientDemographics,
    RedFlags,
    SymptomEntry,
    VitalSigns,
)
from agent.subagents.models import PatientInfo, StructuredSymptoms


def _agent(mock_llm_client, mock_message_manager):
    return MedicalAgent(
        llm_client=mock_llm_client,
        message_manager=mock_message_manager,
    )


def _basics_form(phase="form_collection"):
    form = ConsultationForm(
        patient=PatientDemographics(age=35, weight_kg=65, gender="女"),
        phase=phase,
    )
    form.filled_fields.update(
        {
            "patient.age",
            "patient.weight_kg",
            "patient.gender",
            "allergies.drug_allergies",
            "current_medications",
        }
    )
    return form


def _confirmed_form():
    form = _basics_form("drug_matching")
    form.confirmed = True
    form.chief_complaint = "头痛伴恶心"
    form.symptoms = [
        SymptomEntry(
            location="头部",
            quality="胀痛",
            severity_0_10=6,
            onset_time="两天前",
            pattern="间歇性",
            trigger_factors="熬夜",
            accompanying_symptoms=["恶心"],
        )
    ]
    form.patient.pregnant = "是"
    form.patient.gestational_weeks = 12
    form.patient.breastfeeding = True
    form.allergies = AllergyInfo(
        drug_allergies=["青霉素"],
        food_allergies=["花生"],
        excipient_allergies=["乳糖"],
    )
    form.medical_history = MedicalHistory(
        chronic_diseases=["高血压"],
        has_liver_disease="是",
        has_arrhythmia="有",
        recent_surgery="阑尾手术",
    )
    form.vital_signs = VitalSigns(
        temperature_c=38.2,
        has_fever="是",
        fever_duration_days=2,
        heart_rate_bpm=95,
        blood_pressure_systolic=130,
        blood_pressure_diastolic=85,
    )
    form.supplementary = {"睡眠": "差"}
    return form


def test_submit_basics_accepts_units_strings_lists_and_invalid_numbers(
    mock_llm_client, mock_message_manager, monkeypatch
):
    agent = _agent(mock_llm_client, mock_message_manager)
    monkeypatch.setattr(agent, "_load_form_from_session", lambda: None)
    monkeypatch.setattr(agent, "_save_form_to_session", MagicMock())

    agent.submit_basics(
        {
            "gender": "女",
            "age": "30",
            "weight": "120",
            "weight_unit": "斤",
            "drug_allergies": "青霉素",
            "current_medications": [" 阿司匹林 ", "", "维生素C"],
            "chronic_diseases": ["高血压"],
        }
    )

    form = agent.consultation_form
    assert form.patient.age == 30
    assert form.patient.weight_kg == 60
    assert form.allergies.drug_allergies == ["青霉素"]
    assert [m.medication_name for m in form.current_medications] == ["阿司匹林", "维生素C"]
    assert form.medical_history.chronic_diseases == ["高血压"]
    assert form.conversation_log

    agent.submit_basics({"age": object(), "weight": object(), "drug_allergies": []})
    assert form.patient.age == 30
    assert form.patient.weight_kg == 60


def test_form_session_round_trip_and_invalid_drug_matching_state(
    tmp_path, mock_llm_client, mock_message_manager, monkeypatch
):
    monkeypatch.setattr(ma.Config, "SESSION_STATE_DIR", str(tmp_path))
    agent = _agent(mock_llm_client, mock_message_manager)
    agent.patient_id = "patient-1"
    agent.consultation_form = _basics_form("drug_matching")
    agent._save_form_to_session()

    restored = _agent(mock_llm_client, mock_message_manager)
    restored.patient_id = "patient-1"
    restored._load_form_from_session()

    assert restored.consultation_form.patient.age == 35
    assert restored.consultation_form.phase == "form_collection"
    assert restored.consultation_form.confirmed is False


def test_confirmation_keywords_and_initial_basics_question(
    mock_llm_client, mock_message_manager, monkeypatch
):
    assert MedicalAgent._check_confirmation(" YES ") is True
    assert MedicalAgent._check_confirmation("需要修改") is False

    agent = _agent(mock_llm_client, mock_message_manager)
    monkeypatch.setattr(agent, "_load_form_from_session", lambda: None)
    monkeypatch.setattr(agent, "_save_form_to_session", lambda: None)

    reply, steps = agent._run_form_phases("你好")

    assert "性别" in reply
    assert steps[0]["type"] == "assistant"
    assert agent._pending_questions[0].field == "patient.gender"


def test_basics_answer_can_finish_round_one(
    mock_llm_client, mock_message_manager, monkeypatch
):
    agent = _agent(mock_llm_client, mock_message_manager)
    form = ConsultationForm(phase="basics_collection")
    form.filled_fields.update(
        {
            "patient.gender",
            "patient.age",
            "patient.weight_kg",
            "allergies.drug_allergies",
        }
    )
    form.conversation_log.append({"role": "assistant", "content": "有在用药吗"})
    agent.consultation_form = form
    monkeypatch.setattr(agent, "_load_form_from_session", lambda: None)
    monkeypatch.setattr(agent, "_save_form_to_session", lambda: None)

    reply, _ = agent._run_form_phases("没有用药")

    assert "基础信息已记录" in reply
    assert form.phase == "form_collection"


def test_form_collection_handles_red_flag_continue_and_confirmation(
    mock_llm_client, mock_message_manager, monkeypatch
):
    agent = _agent(mock_llm_client, mock_message_manager)
    monkeypatch.setattr(agent, "_load_form_from_session", lambda: None)
    monkeypatch.setattr(agent, "_save_form_to_session", lambda: None)

    red_form = _basics_form()
    red_form.red_flags.chest_pain = True
    agent.consultation_form = red_form
    agent.incremental_extractor = MagicMock()
    agent.incremental_extractor.extract_and_merge.return_value = red_form
    reply, _ = agent._run_form_phases("胸痛")
    assert "立即就医" in reply
    assert agent.workflow_completed is True

    agent.workflow_completed = False
    continue_form = _basics_form()
    agent.consultation_form = continue_form
    agent.incremental_extractor.extract_and_merge.return_value = continue_form
    monkeypatch.setattr(
        ma,
        "check_form_completeness",
        lambda form: {
            "phase": "continue",
            "missing_global": ["chief_complaint"],
            "missing_symptom_core": [],
            "missing_conditional": [],
        },
    )
    reply, _ = agent._run_form_phases("不舒服")
    assert "主要的症状" in reply

    complete_form = _basics_form()
    complete_form.chief_complaint = "头痛"
    complete_form.symptoms = [SymptomEntry(location="头部")]
    agent.consultation_form = complete_form
    agent.incremental_extractor.extract_and_merge.return_value = complete_form
    monkeypatch.setattr(
        ma,
        "check_form_completeness",
        lambda form: {
            "phase": "needs_confirmation",
            "missing_global": [],
            "missing_symptom_core": [],
            "missing_conditional": [],
        },
    )
    reply, _ = agent._run_form_phases("头痛")
    assert "诊断信息汇总" in reply
    assert complete_form.phase == "form_confirmation"


def test_confirmation_phase_rejects_empty_symptoms_accepts_valid_form_and_edits(
    mock_llm_client, mock_message_manager, monkeypatch
):
    agent = _agent(mock_llm_client, mock_message_manager)
    monkeypatch.setattr(agent, "_load_form_from_session", lambda: None)
    monkeypatch.setattr(agent, "_save_form_to_session", lambda: None)

    empty = _basics_form("form_confirmation")
    agent.consultation_form = empty
    reply, steps = agent._run_form_phases("确认")
    assert "未检测到有效" in reply
    assert steps

    valid = _basics_form("form_confirmation")
    valid.chief_complaint = "头痛"
    agent.consultation_form = valid
    reply, steps = agent._run_form_phases("确认无误")
    assert reply == ""
    assert steps is None
    assert valid.phase == "drug_matching"
    assert valid.confirmed is True

    edited = _basics_form("form_confirmation")
    edited.chief_complaint = "头痛"
    agent.consultation_form = edited
    agent.incremental_extractor = MagicMock()
    agent.incremental_extractor.extract_and_merge.return_value = edited
    monkeypatch.setattr(
        ma,
        "check_form_completeness",
        lambda form: {
            "phase": "continue",
            "missing_global": ["patient.age"],
            "missing_symptom_core": [],
            "missing_conditional": [],
        },
    )
    reply, steps = agent._run_form_phases("年龄需要修改")
    assert "年龄" in reply
    assert steps


def test_query_drugs_uses_direct_matches_name_lookup_and_llm_synonyms(
    mock_llm_client, mock_message_manager, monkeypatch
):
    import database.pharmacy_client as pharmacy

    agent = _agent(mock_llm_client, mock_message_manager)
    direct = {"drug_id": 1, "name": "药A", "indications": ["头痛"]}
    monkeypatch.setattr(pharmacy, "query_drugs_by_symptom", lambda symptom: [direct])
    monkeypatch.setattr(pharmacy, "query_drug_by_name", lambda name: None)
    assert agent._query_drugs_with_retry(["头痛", "头痛"], mock_llm_client) == [direct]

    named = {"drug_id": 2, "name": "布洛芬"}
    monkeypatch.setattr(pharmacy, "query_drugs_by_symptom", lambda symptom: [])
    monkeypatch.setattr(pharmacy, "query_drug_by_name", lambda name: named)
    assert agent._query_drugs_with_retry(["布洛芬"], mock_llm_client) == [named]

    monkeypatch.setattr(pharmacy, "query_drug_by_name", lambda name: None)
    monkeypatch.setattr(
        pharmacy,
        "query_drugs_by_symptom",
        lambda symptom: (
            [{"drug_id": 3, "name": "止痛药", "indications": ["头痛"]}]
            if symptom == "偏头痛"
            else []
        ),
    )
    mock_llm_client.chat.return_value = {"content": "偏头痛"}
    assert agent._query_drugs_with_retry(["头痛"], mock_llm_client)[0]["drug_id"] == 3

    mock_llm_client.chat.return_value = {"content": ""}
    assert agent._query_drugs_with_retry(["未知症状"], mock_llm_client) == []


def test_confirmed_form_builds_full_context_and_returns_llm_reply(
    mock_llm_client, mock_message_manager, monkeypatch
):
    agent = _agent(mock_llm_client, mock_message_manager)
    agent.patient_id = "p-rich"
    agent.consultation_form = _confirmed_form()
    monkeypatch.setattr(ma.Config, "ENABLE_FORM_COLLECTION", True)
    monkeypatch.setattr(
        agent,
        "_query_drugs_with_retry",
        lambda symptoms, client: [
            {
                "drug_id": 1,
                "name": "对乙酰氨基酚",
                "retail_price": 12.5,
                "indications": ["头痛", "发热"],
            }
        ],
    )
    mock_llm_client.chat.return_value = {
        "content": "建议由医生确认后使用。",
        "tool_calls": [],
    }

    reply, steps = agent._execute_drug_matching_phase("请推荐药物", [])

    assert "医生确认" in reply
    enhanced = mock_message_manager.add_message.call_args_list[0].args[1]
    for text in ["头痛伴恶心", "孕12周", "花生", "肝病", "体温:38.2", "对乙酰氨基酚"]:
        assert text in enhanced
    assert steps[-1]["type"] == "assistant"


def test_confirmed_form_rejects_empty_symptoms_red_flags_and_no_drugs(
    mock_llm_client, mock_message_manager, monkeypatch
):
    monkeypatch.setattr(ma.Config, "ENABLE_FORM_COLLECTION", True)
    agent = _agent(mock_llm_client, mock_message_manager)
    agent.patient_id = "p"
    monkeypatch.setattr(agent, "_save_form_to_session", lambda: None)

    empty = _basics_form("drug_matching")
    empty.confirmed = True
    agent.consultation_form = empty
    reply, _ = agent._execute_drug_matching_phase("继续", [])
    assert "缺少有效" in reply
    assert empty.confirmed is False

    red = _confirmed_form()
    red.red_flags = RedFlags(dyspnea=True)
    agent.consultation_form = red
    reply, _ = agent._execute_drug_matching_phase("继续", [])
    assert "立即就医" in reply

    no_drugs = _confirmed_form()
    agent.consultation_form = no_drugs
    monkeypatch.setattr(agent, "_query_drugs_with_retry", lambda symptoms, client: [])
    reply, _ = agent._execute_drug_matching_phase("继续", [])
    assert "未找到" in reply


def test_legacy_path_handles_red_flags_no_drugs_and_tool_loop(
    mock_llm_client, mock_message_manager, monkeypatch
):
    monkeypatch.setattr(ma.Config, "ENABLE_FORM_COLLECTION", False)
    agent = _agent(mock_llm_client, mock_message_manager)
    agent.patient_id = "legacy"

    monkeypatch.setattr(
        ma,
        "extract_symptoms",
        lambda message, client: StructuredSymptoms("胸痛", ["胸痛"]),
    )
    reply, _ = agent._execute_drug_matching_phase("胸痛", [])
    assert "立即就医" in reply

    monkeypatch.setattr(
        ma,
        "extract_symptoms",
        lambda message, client: StructuredSymptoms("罕见不适", []),
    )
    monkeypatch.setattr(agent, "_query_drugs_with_retry", lambda symptoms, client: [])
    reply, _ = agent._execute_drug_matching_phase("罕见不适", [])
    assert "未找到" in reply

    agent.workflow_completed = False
    monkeypatch.setattr(
        ma,
        "extract_symptoms",
        lambda message, client: {
            "chief_complaint": "头痛",
            "symptoms": ["头痛"],
            "severity": {"头痛": "中度"},
            "patient_info": {
                "age": 30,
                "weight": 60,
                "gender": "F",
                "allergies": ["青霉素"],
            },
        },
    )
    drug = {
        "drug_id": 1,
        "name": "布洛芬",
        "retail_price": 10,
        "indications": ["头痛"],
    }
    monkeypatch.setattr(agent, "_query_drugs_with_retry", lambda symptoms, client: [drug])
    monkeypatch.setattr(ma, "execute_tool", lambda name, payload: '{"approval_id": "AP-1"}')
    mock_llm_client.chat.side_effect = [
        {
            "content": "正在提交",
            "tool_calls": [
                {
                    "id": "call-1",
                    "name": "submit_approval",
                    "input": {
                        "drug_name": "布洛芬",
                        "quantity": 2,
                        "advice": "饭后服用",
                    },
                }
            ],
        },
        {"content": "审批已提交", "tool_calls": []},
    ]
    reply, steps = agent._execute_drug_matching_phase("头痛", [])
    assert reply.startswith("饭后服用")
    assert agent.approval_id == "AP-1"
    assert agent.drug_name == "布洛芬"
    assert any(step["type"] == "tool_call" for step in steps)


def test_cached_query_tool_and_tool_error_paths(
    mock_llm_client, mock_message_manager, monkeypatch
):
    agent = _agent(mock_llm_client, mock_message_manager)
    agent.patient_id = "cached"
    agent._matched_drugs = [
        {
            "name": "药A",
            "specification": "10mg",
            "retail_price": 8,
            "quantity": 5,
            "is_prescription": 1,
            "indications": ["头痛"],
            "category": "止痛药",
        }
    ]
    monkeypatch.setattr(ma.Config, "ENABLE_FORM_COLLECTION", False)
    monkeypatch.setattr(
        ma,
        "extract_symptoms",
        lambda message, client: StructuredSymptoms(
            "头痛", ["头痛"], patient_info=PatientInfo()
        ),
    )
    monkeypatch.setattr(agent, "_query_drugs_with_retry", lambda symptoms, client: agent._matched_drugs)
    mock_llm_client.chat.side_effect = [
        {
            "content": "",
            "tool_calls": [
                {"id": "q1", "name": "query_drug", "input": {"query": "头痛"}}
            ],
        },
        {"content": "", "tool_calls": []},
    ]

    reply, steps = agent._execute_drug_matching_phase("头痛", [])

    assert reply == "处理超时，请稍后重试。"
    cached_result = next(step["result"] for step in steps if step["type"] == "tool_call")
    assert json.loads(cached_result)["count"] == 1


def test_workflow_accessors_approval_status_and_state_persistence(
    tmp_path, mock_llm_client, mock_message_manager, monkeypatch
):
    agent = _agent(mock_llm_client, mock_message_manager)
    assert agent.get_approval_id() is None
    assert agent.get_last_steps() == []
    assert agent.get_workflow_state() is None

    agent.patient_id = "p-state"
    agent.approval_id = "AP-2"
    agent.workflow_manager.create_workflow("p-state")
    assert agent.get_workflow_state()["patient_id"] == "p-state"
    assert agent.get_all_workflows()
    assert isinstance(agent.get_workflow_stats(), dict)

    fake_client = MagicMock()
    fake_client.get_approval.return_value = {
        "success": True,
        "approval": {"status": "approved"},
    }
    fake_client._make_request.return_value = SimpleNamespace()
    fake_client._run_async.return_value = {
        "success": True,
        "data": [{"order_id": "O-1"}],
    }
    import common.utils.http_client as http_client

    monkeypatch.setattr(http_client, "PharmacyHTTPClient", lambda: fake_client)
    status = agent.get_approval_status()
    assert status["status"] == "approved"
    assert status["order_info"]["order_id"] == "O-1"

    state_file = tmp_path / "nested" / "agent.pkl"
    agent.save_state(str(state_file))
    restored = _agent(mock_llm_client, mock_message_manager)
    assert restored.load_state(str(tmp_path / "missing.pkl")) is False
    assert restored.load_state(str(state_file)) is True
    assert restored.patient_id == "p-state"
    assert restored.approval_id == "AP-2"


def test_planner_plan_formatting_and_todo_completion(
    mock_llm_client, mock_message_manager
):
    agent = _agent(mock_llm_client, mock_message_manager)
    agent.planner_enabled = True
    old = agent.todo_manager.add_todo("old")

    agent._create_workflow_plan(["头痛", "恶心"], 3)

    assert agent.todo_manager.get_todo(old.id) is None
    tasks = agent.todo_manager.get_todo_list()
    assert len(tasks) == 5
    assert any(task.status == "completed" for task in tasks)
    tasks[1].mark_in_progress()
    tasks[2].mark_blocked()
    formatted = agent._format_plan_for_llm()
    assert "[已完成]" in formatted
    assert "[进行中]" in formatted
    assert "[已阻塞]" in formatted
    assert "[待处理]" in formatted

    agent.patient_id = "planner"
    agent._update_workflow_and_todo("check_allergy", "{}")
    check_tasks = agent.todo_manager.get_tasks_by_category("check")
    assert check_tasks[0].status == "completed"
    agent._update_workflow_and_todo("unknown", "{}")


def test_run_form_dispatch_and_remaining_form_phase_branches(
    mock_llm_client, mock_message_manager, monkeypatch
):
    agent = _agent(mock_llm_client, mock_message_manager)
    monkeypatch.setattr(ma.Config, "ENABLE_FORM_COLLECTION", True)
    monkeypatch.setattr(
        agent,
        "_run_form_phases",
        MagicMock(return_value=("question", [{"type": "assistant"}])),
    )
    assert agent.run("hello", "p")[0] == "question"

    monkeypatch.setattr(agent, "_load_form_from_session", lambda: None)
    monkeypatch.setattr(agent, "_save_form_to_session", lambda: None)
    form = _basics_form("basics_collection")
    agent.consultation_form = form
    reply, _ = MedicalAgent._run_form_phases(agent, "继续")
    assert "基础信息已记录" in reply

    red_by_completeness = _basics_form()
    agent.consultation_form = red_by_completeness
    agent.incremental_extractor = MagicMock()
    agent.incremental_extractor.extract_and_merge.return_value = red_by_completeness
    monkeypatch.setattr(ma, "any_red_flag_active", lambda form: False)
    monkeypatch.setattr(ma, "check_form_completeness", lambda form: {"phase": "red_flag"})
    reply, _ = MedicalAgent._run_form_phases(agent, "继续")
    assert "立即就医" in reply

    edited = _basics_form("form_confirmation")
    edited.chief_complaint = "头痛"
    edited.symptoms = [SymptomEntry(location="头部")]
    agent.consultation_form = edited
    agent.incremental_extractor.extract_and_merge.return_value = edited
    monkeypatch.setattr(
        ma,
        "check_form_completeness",
        lambda form: {
            "phase": "needs_confirmation",
            "missing_global": [],
            "missing_symptom_core": [],
            "missing_conditional": [],
        },
    )
    reply, _ = MedicalAgent._run_form_phases(agent, "改为头部胀痛")
    assert "诊断信息汇总" in reply

    edited.phase = "drug_matching"
    assert MedicalAgent._run_form_phases(agent, "继续") == ("", None)
    edited.phase = "unknown"
    assert MedicalAgent._run_form_phases(agent, "继续") == ("", None)


def test_query_retry_rejects_irrelevant_matches_and_survives_llm_errors(
    mock_llm_client, mock_message_manager, monkeypatch
):
    import database.pharmacy_client as pharmacy

    agent = _agent(mock_llm_client, mock_message_manager)
    agent.consultation_form = ConsultationForm(chief_complaint="头痛")
    monkeypatch.setattr(pharmacy, "query_drug_by_name", lambda name: None)
    monkeypatch.setattr(
        pharmacy,
        "query_drugs_by_symptom",
        lambda symptom: (
            [{"drug_id": 1, "indications": ["咳嗽"]}]
            if symptom == "偏头痛"
            else []
        ),
    )
    mock_llm_client.chat.side_effect = [
        {"content": "偏头痛"},
        RuntimeError("offline"),
        {"content": "偏头痛"},
    ]
    assert agent._query_drugs_with_retry(["头痛"], mock_llm_client) == []


def test_tool_error_patient_name_reset_and_approval_failure_paths(
    tmp_path, mock_llm_client, mock_message_manager, monkeypatch
):
    agent = _agent(mock_llm_client, mock_message_manager)
    agent.patient_id = "p-tools"
    agent.patient_display_name = "张三"
    monkeypatch.setattr(ma.Config, "ENABLE_FORM_COLLECTION", False)
    monkeypatch.setattr(
        ma,
        "extract_symptoms",
        lambda message, client: StructuredSymptoms(
            "头痛", ["头痛"], patient_info=PatientInfo(allergies="青霉素")
        ),
    )
    monkeypatch.setattr(
        agent,
        "_query_drugs_with_retry",
        lambda symptoms, client: [
            {"drug_id": 1, "name": "药A", "retail_price": 1, "indications": ["头痛"]}
        ],
    )
    monkeypatch.setattr(
        ma,
        "execute_tool",
        MagicMock(side_effect=ma.ToolExecutionError("failed")),
    )
    mock_llm_client.chat.side_effect = [
        {
            "content": "",
            "tool_calls": [
                {
                    "id": "a1",
                    "name": "submit_approval",
                    "input": {"drug_name": "药A", "quantity": 1, "advice": "advice"},
                }
            ],
        },
        {"content": "done", "tool_calls": []},
    ]
    _, steps = agent._execute_drug_matching_phase("头痛", [])
    tool_step = next(step for step in steps if step["type"] == "tool_call")
    assert tool_step["input"]["patient_name"] == "张三"
    assert "error" in tool_step

    agent.patient_id = None
    agent._update_workflow_for_tool("query_drug", "{}")
    assert agent.get_approval_status() is None

    import common.utils.http_client as http_client

    failed = MagicMock()
    failed.get_approval.return_value = {"success": False}
    monkeypatch.setattr(http_client, "PharmacyHTTPClient", lambda: failed)
    assert agent.get_approval_status("AP-failed") is None
    monkeypatch.setattr(
        http_client,
        "PharmacyHTTPClient",
        MagicMock(side_effect=RuntimeError("offline")),
    )
    assert agent.get_approval_status("AP-error") is None

    monkeypatch.setattr(ma.Config, "SESSION_STATE_DIR", str(tmp_path))
    agent.patient_id = "reset-me"
    agent.consultation_form = ConsultationForm()
    agent._save_form_to_session()
    assert (tmp_path / "reset-me_form.pkl").exists()
    agent.reset()
    assert not (tmp_path / "reset-me_form.pkl").exists()


def test_load_state_restores_tool_messages(
    tmp_path, mock_llm_client, mock_message_manager
):
    import pickle

    state_file = tmp_path / "tool-state.pkl"
    with state_file.open("wb") as handle:
        pickle.dump(
            {
                "messages": [
                    {"role": "system", "content": "sys"},
                    {
                        "role": "tool",
                        "tool_call_id": "call-1",
                        "content": '{"ok": true}',
                    },
                ],
                "patient_id": "p",
                "approval_id": "a",
            },
            handle,
        )
    agent = _agent(mock_llm_client, mock_message_manager)
    assert agent.load_state(str(state_file)) is True
    assert agent.message_manager.get_full_messages()[-1]["role"] == "tool"
