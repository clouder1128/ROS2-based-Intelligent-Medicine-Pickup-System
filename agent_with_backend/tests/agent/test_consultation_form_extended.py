import json
from unittest.mock import MagicMock

import pytest

from agent.subagents.form import (
    AllergyInfo,
    ConsultationForm,
    IncrementalExtractor,
    MedicalHistory,
    MedicationRecord,
    PatientDemographics,
    PatientExpectation,
    Question,
    RedFlags,
    SocialHistory,
    SymptomEntry,
    VitalSigns,
    _check_risk_condition,
    analyze_chief_complaint,
    basics_are_filled,
    check_form_completeness,
    generate_basics_question,
    generate_follow_up,
    generate_form_summary,
    get_field_value,
    is_field_filled,
    rule_extract_basics,
)


def _rich_form():
    form = ConsultationForm(
        patient=PatientDemographics(
            age=32,
            age_unit="岁",
            weight_kg=55,
            gender="女",
            pregnant="否",
            breastfeeding=False,
        ),
        chief_complaint="头痛伴发热",
        symptoms=[
            SymptomEntry(
                location="头部",
                quality="胀痛",
                severity_0_10=6,
                onset_time="2天前",
                pattern="间歇性",
                trigger_factors="劳累",
                relieving_factors="休息",
                accompanying_symptoms=["恶心"],
            )
        ],
        vital_signs=VitalSigns(temperature_c=38.5, heart_rate_bpm=96),
        medical_history=MedicalHistory(chronic_diseases=["高血压"]),
        current_medications=[MedicationRecord("氨氯地平", dosage="5mg")],
        allergies=AllergyInfo(drug_allergies=["青霉素"], food_allergies=["花生"]),
        social=SocialHistory(occupation="司机", need_operate_machinery=True),
        expectation=PatientExpectation(patient_goal="缓解疼痛"),
        red_flags=RedFlags(high_fever=True),
        supplements={"备注": "夜间加重"},
        supplementary={"来源": "患者自述"},
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


def test_models_serialize_and_rich_form_summarizes_all_sections():
    form = _rich_form()

    assert not form.patient.is_empty()
    assert PatientDemographics().is_empty()
    assert MedicationRecord("").is_valid() is False
    assert MedicationRecord("药").is_valid() is True
    assert form.symptoms[0].to_dict()["severity_0_10"] == 6
    assert form.vital_signs.to_dict()["temperature_c"] == 38.5
    assert form.medical_history.to_dict()["chronic_diseases"] == ["高血压"]
    assert form.allergies.to_dict()["food_allergies"] == ["花生"]
    assert form.social.to_dict()["need_operate_machinery"] is True
    assert form.expectation.to_dict()["patient_goal"] == "缓解疼痛"
    assert form.red_flags.any_active() is True
    assert form.red_flags.active_list() == ["high_fever"]
    assert Question("问题", "field", ["是"]).to_dict()["options"] == ["是"]

    summary = form.to_summary()
    data = form.to_dict()

    for text in ["患者信息", "头痛伴发热", "青霉素", "氨氯地平", "警示信号"]:
        assert text in summary
    assert data["patient"]["age"] == 32
    assert data["symptoms"][0]["location"] == "头部"
    assert data["filled_fields"]


def test_basics_question_progression_and_field_access():
    form = ConsultationForm()

    assert basics_are_filled(None) is False
    assert basics_are_filled(form) is False
    assert generate_basics_question(form).field == "patient.gender"

    form.filled_fields.update(
        {
            "patient.gender",
            "patient.age",
            "patient.weight_kg",
            "allergies.drug_allergies",
            "current_medications",
        }
    )
    form.patient.age = 20
    form.symptoms.append(SymptomEntry(location="腹部"))

    assert basics_are_filled(form) is True
    assert generate_basics_question(form) is None
    assert get_field_value(form, "patient.age") == 20
    assert get_field_value(form, "symptoms[]") is None
    assert get_field_value(form, "missing.path") is None
    assert is_field_filled(form, "symptoms[].location") is True
    assert is_field_filled(form, "symptoms[].quality") is False


@pytest.mark.parametrize(
    ("condition", "setup", "expected"),
    [
        ("patient.age < 12", lambda f: setattr(f.patient, "age", 8), True),
        ("patient.age > 75", lambda f: setattr(f.patient, "age", 80), True),
        ("gender_female", lambda f: setattr(f.patient, "gender", "女"), True),
        (
            "chronic_diseases_not_empty",
            lambda f: f.medical_history.chronic_diseases.append("哮喘"),
            True,
        ),
        (
            "social.need_operate_machinery",
            lambda f: setattr(f.social, "need_operate_machinery", True),
            True,
        ),
        ("unknown", lambda f: None, False),
    ],
)
def test_risk_condition_variants(condition, setup, expected):
    form = ConsultationForm()
    setup(form)
    assert _check_risk_condition(condition, form) is expected


def test_completeness_handles_red_flags_missing_data_and_confirmation():
    red = ConsultationForm(red_flags=RedFlags(chest_pain=True))
    assert check_form_completeness(red)["phase"] == "red_flag"

    incomplete = ConsultationForm(chief_complaint="咳嗽")
    result = check_form_completeness(incomplete)
    assert result["phase"] == "continue"
    assert "patient.age" in result["missing_global"]
    assert "symptoms[].location" in result["missing_symptom_core"]

    complete = ConsultationForm(
        patient=PatientDemographics(age=30, weight_kg=65, gender="男"),
        chief_complaint="头痛",
        symptoms=[SymptomEntry("头部", "胀痛", 4, "今天")],
    )
    complete.filled_fields.update(
        {
            "patient.age",
            "patient.weight_kg",
            "patient.gender",
            "allergies.drug_allergies",
            "current_medications",
            "chief_complaint",
            "symptoms[].location",
            "symptoms[].quality",
            "symptoms[].severity_0_10",
            "symptoms[].onset_time",
        }
    )
    for name in RedFlags.__dataclass_fields__:
        complete.filled_fields.add(f"red_flags.{name}")

    result = check_form_completeness(complete)
    assert result["complete"] is True
    assert result["phase"] == "needs_confirmation"


def test_system_analysis_followups_and_form_summary():
    form = _rich_form()
    systems = analyze_chief_complaint(
        "胸痛咳嗽腹泻",
        [SymptomEntry(location="咽喉", accompanying_symptoms=["皮疹"])],
    )
    assert systems

    global_followup = generate_follow_up(
        form, ["patient.age", "patient.gender", "chief_complaint"], [], []
    )
    symptom_followup = generate_follow_up(
        ConsultationForm(), [], ["symptoms[].quality", "symptoms[].onset_time"], []
    )
    conditional_followup = generate_follow_up(
        ConsultationForm(), [], [], ["red_flags.dyspnea"]
    )
    empty_followup = generate_follow_up(ConsultationForm(), [], [], [])

    assert "已收集到以下信息" in global_followup["text"]
    assert global_followup["questions"][0]["field"] == "patient.gender"
    assert "性质" in symptom_followup["text"]
    assert conditional_followup["questions"][0]["field"] == "red_flags.dyspnea"
    assert empty_followup["questions"] == []

    report = generate_form_summary(form)
    for section in ["患者信息", "主诉", "症状详情", "生命体征", "药物过敏"]:
        assert section in report


def test_incremental_extractor_merges_every_supported_section():
    extracted = {
        "patient": {
            "age": 42,
            "age_unit": "岁",
            "weight_kg": 70,
            "gender": "男",
            "pregnant": "否",
            "gestational_weeks": 0,
            "breastfeeding": False,
        },
        "chief_complaint": "头痛两天",
        "symptoms": [
            {
                "location": "头部",
                "quality": "胀痛",
                "severity_0_10": 7,
                "onset_time": "两天前",
                "pattern": "持续",
                "trigger_factors": "熬夜",
                "relieving_factors": "休息",
                "accompanying_symptoms": ["恶心"],
            }
        ],
        "vital_signs": {
            "temperature_c": 38.2,
            "has_fever": "是",
            "fever_duration_days": 2,
            "blood_pressure_systolic": 130,
            "blood_pressure_diastolic": 85,
            "heart_rate_bpm": 90,
            "respiratory_rate": 18,
            "oxygen_saturation": 98,
            "skin_rash": "无",
            "rash_description": "无",
        },
        "medical_history": {
            "chronic_diseases": ["高血压"],
            "has_liver_disease": "否",
            "has_kidney_disease": "否",
            "has_peptic_ulcer": "否",
            "has_gi_bleeding": "否",
            "has_epilepsy": "否",
            "has_glaucoma": "否",
            "has_prostate_hyperplasia": "否",
            "has_thyroid_disease": "否",
            "has_heart_failure": "否",
            "has_arrhythmia": "否",
            "has_bleeding_disorder": "否",
            "recent_surgery": "否",
        },
        "current_medications": [{"medication_name": "阿司匹林", "dosage": "100mg"}],
        "self_medicated": [],
        "long_term_medications": [{"medication_name": "氨氯地平"}],
        "allergies": {
            "drug_allergies": ["青霉素"],
            "food_allergies": ["花生"],
            "excipient_allergies": [],
            "other_intolerances": ["乳糖"],
        },
        "social": {
            "occupation": "教师",
            "need_operate_machinery": False,
            "alcohol_use": "偶尔",
            "smoking_status": "不吸烟",
            "special_diet": "低盐",
        },
        "expectation": {
            "patient_goal": "止痛",
            "preferred_drug_type": "西药",
            "preferred_formulation": "片剂",
            "cost_constraint": "100元内",
        },
        "red_flags": {
            "high_fever": False,
            "severe_headache": True,
            "chest_pain": False,
            "dyspnea": False,
            "altered_mental": False,
            "bleeding": False,
            "anaphylaxis": False,
            "child_or_elderly_frail": False,
            "pregnancy_with_alarm": False,
            "other_red_flags": "无",
        },
    }
    client = MagicMock()
    client.chat.return_value = {
        "content": "```json\n" + json.dumps(extracted, ensure_ascii=False) + "\n```"
    }
    form = ConsultationForm()

    result = IncrementalExtractor(client).extract_and_merge(
        form,
        "男，42岁，70公斤，头痛两天，青霉素过敏，服用阿司匹林。",
    )

    assert result.patient.age == 42
    assert result.symptoms[0].relieving_factors == "休息"
    assert result.vital_signs.oxygen_saturation == 98
    assert result.medical_history.has_arrhythmia == "否"
    assert result.current_medications[0].medication_name == "阿司匹林"
    assert "self_medicated" in result.filled_fields
    assert result.allergies.food_allergies == ["花生"]
    assert result.social.occupation == "教师"
    assert result.expectation.cost_constraint == "100元内"
    assert result.red_flags.severe_headache is True


def test_incremental_extractor_parsing_validation_and_fallback(monkeypatch):
    extractor = IncrementalExtractor()
    form = ConsultationForm()

    assert extractor.extract_and_merge(form, " ") is form
    assert extractor._parse_json_response("") is None
    assert extractor._parse_json_response("not json") is None
    assert extractor._parse_json_response("{bad}") is None
    assert extractor._llm_extract("hello", form) is None

    form.patient.gender = "男"
    form.patient.age = 30
    form.patient.weight_kg = 70
    form.allergies.drug_allergies = ["青霉素"]
    fields = {
        "patient.gender",
        "patient.age",
        "patient.age_unit",
        "patient.weight_kg",
        "allergies.drug_allergies",
    }
    form.filled_fields.update(fields)
    extractor._validate_no_inference(form, "只是头痛", fields)
    assert form.patient.gender is None
    assert form.patient.age is None
    assert form.patient.weight_kg is None
    assert form.allergies.drug_allergies == []

    monkeypatch.setattr(extractor, "_llm_extract", MagicMock(side_effect=RuntimeError("bad llm")))
    fallback = ConsultationForm()
    extractor.extract_and_merge(
        fallback,
        "30岁男性，体重70kg，头痛，体温38C，心率90次，血压120/80mmHg",
    )
    assert fallback.patient.age == 30
    assert fallback.patient.gender == "男"
    assert fallback.symptoms
    assert fallback.vital_signs.temperature_c == 38
    assert fallback.vital_signs.blood_pressure_systolic == 120


@pytest.mark.parametrize(
    ("field", "message", "assertion"),
    [
        ("patient.gender", "男", lambda f: f.patient.gender == "男"),
        ("patient.gender", "女", lambda f: f.patient.gender == "女"),
        ("patient.gender", "不愿透露", lambda f: f.patient.gender == "不愿透露"),
        ("patient.age", "18月", lambda f: f.patient.age == 18 and f.patient.age_unit == "月"),
        ("patient.weight_kg", "140斤", lambda f: f.patient.weight_kg == 70),
        ("patient.weight_kg", "65.5kg", lambda f: f.patient.weight_kg == 65.5),
        (
            "allergies.drug_allergies",
            "青霉素、磺胺",
            lambda f: f.allergies.drug_allergies == ["青霉素", "磺胺"],
        ),
        (
            "allergies.drug_allergies",
            "无过敏",
            lambda f: f.allergies.drug_allergies == [],
        ),
        (
            "current_medications",
            "阿司匹林，氨氯地平",
            lambda f: [m.medication_name for m in f.current_medications]
            == ["阿司匹林", "氨氯地平"],
        ),
        ("current_medications", "没有用药", lambda f: f.current_medications == []),
    ],
)
def test_rule_extract_basics(field, message, assertion):
    form = ConsultationForm()
    rule_extract_basics(form, message, field)
    assert assertion(form)
    assert field in form.filled_fields


def test_rule_extract_basics_ignores_invalid_and_custom_values():
    form = ConsultationForm()
    for field, value in [
        ("patient.gender", "未知"),
        ("patient.age", "未知"),
        ("patient.weight_kg", "未知"),
        ("allergies.drug_allergies", "__custom__"),
        ("current_medications", "__custom__"),
        ("unknown", "value"),
    ]:
        rule_extract_basics(form, value, field)

    assert form.filled_fields == set()
