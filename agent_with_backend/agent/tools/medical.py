#!/usr/bin/env python3
"""
医疗工具模块 - 通过与后端API交互实现药品查询、过敏检查、剂量计算等功能
"""

import json
import logging
import random
from typing import Dict, List, Any, Optional
from datetime import datetime
import httpx

from common.config import Config

logger = logging.getLogger(__name__)

# ==================== 过敏检查映射 ====================

ALLERGY_MAPPING = {
    "青霉素": ["阿莫西林", "氨苄西林", "青霉素"],
    "头孢": ["头孢克肟", "头孢拉定", "头孢氨苄", "头孢"],
    "磺胺": ["磺胺嘧啶", "磺胺甲噁唑"],
    "阿司匹林": ["阿司匹林", "布洛芬"],
    "酒精": ["某些酊剂"],
}


def query_drug(query: str) -> str:
    """根据症状或药品名称查询相关药物信息"""
    logger.info(f"查询药物: {query}")

    try:
        from database.pharmacy_client import get_drugs_by_symptom_or_name

        # 优先按症状查询，再按名称查询
        drugs = get_drugs_by_symptom_or_name(query)
    except Exception as e:
        logger.error(f"查询药物失败: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"查询失败: {str(e)}",
            "drugs": [],
        }, ensure_ascii=False)

    if not drugs:
        return json.dumps({
            "status": "not_found",
            "message": f"未找到匹配 '{query}' 的药品",
            "drugs": [],
        }, ensure_ascii=False)

    formatted_drugs = []
    for drug in drugs:
        formatted_drug = {
            "name": drug.get("name", "未知"),
            "specification": "需从backend获取详细信息",
            "price": drug.get("retail_price", 0.0),
            "stock": drug.get("quantity", 0),
            "is_prescription": bool(drug.get("is_prescription", False)),
            "indications": drug.get("indications", ["需从backend获取适应症信息"]),
            "expiry_days": drug.get("expiry_date", 0),
            "location": f"货架{drug.get('shelve_id', 0)}-({drug.get('shelf_x', 0)},{drug.get('shelf_y', 0)})",
            "category": drug.get("category", ""),
        }
        formatted_drugs.append(formatted_drug)

    return json.dumps({
        "status": "success",
        "count": len(formatted_drugs),
        "query": query,
        "drugs": formatted_drugs,
    }, ensure_ascii=False, indent=2)


def check_allergy(patient_allergies: str, drug_name: str) -> str:
    """检查患者是否对某种药物过敏"""
    logger.info(f"检查过敏: 患者过敏史={patient_allergies}, 药物={drug_name}")
    drug_lower = drug_name.lower()
    allergy_found = False
    allergy_details = []
    allergies = [a.strip() for a in patient_allergies.split(",") if a.strip()]

    for allergy in allergies:
        allergy_lower = allergy.lower()
        for allergen, related_drugs in ALLERGY_MAPPING.items():
            if allergen in allergy_lower or allergy_lower in allergen.lower():
                for related in related_drugs:
                    if related.lower() in drug_lower or drug_lower in related.lower():
                        allergy_found = True
                        allergy_details.append({
                            "allergen": allergen,
                            "related_drug": related,
                            "patient_allergy": allergy,
                        })

    response = {
        "patient_allergies": patient_allergies,
        "drug_name": drug_name,
        "has_allergy": allergy_found,
        "allergy_details": allergy_details if allergy_found else [],
        "recommendation": "不建议使用该药物" if allergy_found else "未发现过敏风险",
        "timestamp": datetime.now().isoformat(),
        "note": "此为mock数据，实际使用需要专业的药物过敏数据库",
    }
    return json.dumps(response, ensure_ascii=False, indent=2)


def calc_dosage(drug_name: str, age: int, weight_kg: float, condition_severity: str = "中") -> str:
    """根据患者年龄、体重、药品规格计算推荐剂量"""
    severity_mapping = {"轻度": "轻", "中度": "中", "重度": "重"}
    if condition_severity in severity_mapping:
        condition_severity = severity_mapping[condition_severity]
    logger.info(f"计算剂量: 药物={drug_name}, 年龄={age}, 体重={weight_kg}kg, 严重程度={condition_severity}")

    dosage_rules = {
        "阿莫西林": {"adult_dose": "500mg，每8小时一次", "child_dose_formula": "20-40mg/kg/日，分3次服用", "max_daily": "3000mg"},
        "头孢克肟": {"adult_dose": "100-200mg，每日两次", "child_dose_formula": "8mg/kg/日，分2次服用", "max_daily": "400mg"},
        "布洛芬": {"adult_dose": "200-400mg，每4-6小时一次", "child_dose_formula": "5-10mg/kg/次，每6-8小时一次", "max_daily": "1200mg"},
        "对乙酰氨基酚": {"adult_dose": "500-1000mg，每4-6小时一次", "child_dose_formula": "10-15mg/kg/次，每4-6小时一次", "max_daily": "4000mg"},
        "蒙脱石散": {"adult_dose": "1袋（3g），每日3次", "child_dose_formula": "按年龄调整：<1岁: 1/3袋/次, 1-2岁: 1/2袋/次, >2岁: 1袋/次", "max_daily": "9g"},
        "氯雷他定": {"adult_dose": "10mg，每日一次", "child_dose_formula": "2-12岁: 5mg/日，<2岁: 不推荐使用", "max_daily": "10mg"},
    }

    drug_rules = None
    for name, rules in dosage_rules.items():
        if name.lower() in drug_name.lower() or drug_name.lower() in name.lower():
            drug_rules = rules
            break
    if not drug_rules:
        drug_rules = {"adult_dose": "按说明书服用", "child_dose_formula": "按体重计算", "max_daily": "不超过最大推荐剂量"}

    is_child = age < 12
    if is_child and weight_kg > 0:
        if "布洛芬" in drug_name or "ibuprofen" in drug_name.lower():
            child_dose_mg = weight_kg * 7.5
            dosage_for_advice = f"儿童剂量：约{child_dose_mg:.0f}mg/次，每6-8小时一次"
        elif "对乙酰氨基酚" in drug_name or "paracetamol" in drug_name.lower():
            child_dose_mg = weight_kg * 12.5
            dosage_for_advice = f"儿童剂量：约{child_dose_mg:.0f}mg/次，每4-6小时一次"
        else:
            dosage_for_advice = f"儿童剂量：{drug_rules.get('child_dose_formula', '按体重计算')}"
    else:
        dosage_for_advice = f"成人剂量：{drug_rules.get('adult_dose', '按说明书服用')}"

    severity_multiplier = {"轻": 0.8, "中": 1.0, "重": 1.2}.get(condition_severity, 1.0)
    if severity_multiplier != 1.0:
        dosage_for_advice += f"（病情{condition_severity}，建议按{severity_multiplier}倍调整）"

    severity_to_quantity = {"轻": 1, "中": 2, "重": 3}
    estimated_quantity = severity_to_quantity.get(condition_severity, 1)
    if is_child:
        estimated_quantity = max(1, (estimated_quantity + 1) // 2)

    response = {
        "drug_name": drug_name,
        "age": age,
        "weight_kg": weight_kg,
        "condition_severity": condition_severity,
        "dosage": dosage_for_advice,
        "estimated_quantity": estimated_quantity,
        "next_step": "调用 generate_advice 工具，使用上面的 dosage 字段",
        "note": "请立即调用 generate_advice 工具，传递 drug_name 和 dosage 参数",
    }
    return json.dumps(response, ensure_ascii=False)


def generate_advice(drug_name: str, dosage: str, duration: str = None, notes: str = None) -> str:
    """生成结构化的用药建议文本"""
    logger.info(f"生成建议: 药物={drug_name}, 剂量={dosage}")
    if not duration:
        duration = "3-7天，根据病情调整"
    if not notes:
        notes = "饭后服用，避免饮酒，如有不适立即停药并就医"

    advice_text = f"""用药建议：
1. 药品名称：{drug_name}
2. 用法用量：{dosage}
3. 用药时长：{duration}
4. 注意事项：{notes}
5. 建议复查：症状缓解后如未完全康复，建议复查
6. 紧急情况：如出现严重过敏反应（呼吸困难、皮疹等），立即就医"""

    response = {
        "drug_name": drug_name,
        "dosage": dosage,
        "duration": duration,
        "notes": notes,
        "advice_text": advice_text,
        "structured_advice": {
            "medication": drug_name,
            "dosage_instruction": dosage,
            "duration": duration,
            "precautions": notes,
            "follow_up": "症状缓解后如未完全康复，建议复查",
            "emergency": "如出现严重过敏反应（呼吸困难、皮疹等），立即就医",
        },
        "timestamp": datetime.now().isoformat(),
        "note": "此建议仅供参考，最终用药需医生审批",
    }
    return json.dumps(response, ensure_ascii=False, indent=2)


def submit_approval(patient_name: str, advice: str, patient_age: int = None, patient_weight: float = None, symptoms: str = None, drug_name: str = None, drug_type: str = None, quantity: int = 1, **kwargs) -> str:
    """提交用药建议给医生审批"""
    logger.info(f"提交审批: patient={patient_name}, drug={drug_name}, quantity={quantity}")
    try:
        from common.utils.http_client import PharmacyHTTPClient

        client = PharmacyHTTPClient()
        approval_id = client.create_approval(
            patient_name=patient_name, advice=advice,
            patient_age=patient_age, patient_weight=patient_weight,
            symptoms=symptoms, drug_name=drug_name, drug_type=drug_type, quantity=quantity,
        )
        if approval_id:
            logger.info(f"审批提交成功: {approval_id}")
            return json.dumps({
                "status": "submitted",
                "approval_id": approval_id,
                "message": f"用药建议已提交审批，审批ID: {approval_id}",
                "instructions": "请等待医生审批。批准后，系统将自动配药。",
                "timestamp": datetime.now().isoformat(),
                "quantity": quantity,
            }, ensure_ascii=False)
        else:
            logger.error("审批提交失败: 未返回审批ID")
            mock_id = f"AP-{datetime.now().strftime('%Y%m%d')}-MOCK{random.randint(1000, 9999)}"
            return json.dumps({
                "status": "mock",
                "approval_id": mock_id,
                "message": f"审批提交失败，使用模拟审批ID: {mock_id}",
                "instructions": "此为模拟审批，用于测试。",
                "timestamp": datetime.now().isoformat(),
                "quantity": quantity,
            }, ensure_ascii=False)
    except Exception as e:
        logger.error(f"审批提交失败: {str(e)}")
        mock_id = f"AP-{datetime.now().strftime('%Y%m%d')}-MOCK{random.randint(1000, 9999)}"
        return json.dumps({
            "status": "error",
            "approval_id": mock_id,
            "message": f"审批提交过程中出错: {str(e)}",
            "instructions": "使用模拟审批ID继续测试。",
            "timestamp": datetime.now().isoformat(),
            "quantity": quantity,
        }, ensure_ascii=False)


async def _create_mock_response(prescription_id: str, patient_name: str, drugs: List[Dict]) -> Dict:
    import asyncio
    await asyncio.sleep(0.5)
    pickup_code = f"PICKUP-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
    return {
        "success": True, "prescription_id": prescription_id, "patient_name": patient_name,
        "pickup_code": pickup_code, "dispensed_at": datetime.now().isoformat(),
        "drugs_dispensed": drugs,
        "message": f"配药成功！取药码：{pickup_code}。请凭码到药房取药。",
        "pharmacy_note": "请在24小时内取药，过期作废",
        "mode": "mock",
    }


async def fill_prescription(prescription_id: str, patient_name: str, drugs: List[Dict]) -> str:
    """在医生审批通过后，将处方发送给药房系统进行配药"""
    logger.info(f"配药请求: 处方ID={prescription_id}, 患者={patient_name}, 药品数={len(drugs)}")
    try:
        pharmacy_url = Config.PHARMACY_BASE_URL
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                api_response = await client.post(
                    f"{pharmacy_url}/api/dispense",
                    json={"prescription_id": prescription_id, "patient_name": patient_name, "drugs": drugs},
                )
                if api_response.status_code == 200:
                    result = api_response.json()
                    response = {"success": True, "prescription_id": prescription_id, "patient_name": patient_name, **result, "mode": "real_api"}
                else:
                    response = await _create_mock_response(prescription_id, patient_name, drugs)
        except Exception:
            response = await _create_mock_response(prescription_id, patient_name, drugs)
    except Exception as e:
        logger.exception(f"配药过程中发生错误: {e}")
        response = {"success": False, "prescription_id": prescription_id, "patient_name": patient_name, "error": f"配药处理失败: {str(e)}", "mode": "exception"}
    return json.dumps(response, ensure_ascii=False, indent=2)


def fill_prescription_sync(prescription_id: str, patient_name: str, drugs: List[Dict]) -> str:
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(fill_prescription(prescription_id, patient_name, drugs))
    finally:
        loop.close()


def register_tools(executor):
    """将所有工具函数注册到执行器"""
    executor.register_handler("query_drug", query_drug)
    executor.register_handler("check_allergy", check_allergy)
    executor.register_handler("calc_dosage", calc_dosage)
    executor.register_handler("generate_advice", generate_advice)
    executor.register_handler("submit_approval", submit_approval)
    executor.register_handler("fill_prescription", fill_prescription_sync)
    logger.info("医疗工具已注册到执行器")
