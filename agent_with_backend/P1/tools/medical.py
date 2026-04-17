#!/usr/bin/env python3
"""
医疗工具模块 - P2负责的具体实现（当前为mock版本）
包含所有医疗相关的工具函数实现。
"""

import json
import logging
import random
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import httpx

from ..core.config import Config

logger = logging.getLogger(__name__)

# ==================== 药品数据（mock） ====================
DRUG_DATABASE = [
    {
        "name": "阿莫西林",
        "specification": "500mg/片",
        "price": 25.0,
        "stock": 100,
        "is_prescription": True,
        "indications": ["发热", "感冒", "呼吸道感染", "扁桃体炎", "中耳炎"],
        "contraindications": ["青霉素过敏"],
        "dosage_guide": "成人：500mg，每8小时一次；儿童：按体重计算",
    },
    {
        "name": "头孢克肟",
        "specification": "100mg/粒",
        "price": 35.0,
        "stock": 80,
        "is_prescription": True,
        "indications": ["呼吸道感染", "泌尿道感染", "皮肤软组织感染"],
        "contraindications": ["头孢菌素过敏"],
        "dosage_guide": "成人：100-200mg，每日两次；儿童：8mg/kg/日",
    },
    {
        "name": "布洛芬",
        "specification": "200mg/片",
        "price": 15.0,
        "stock": 150,
        "is_prescription": False,
        "indications": ["头痛", "牙痛", "关节痛", "痛经", "发热"],
        "contraindications": ["胃肠道溃疡", "严重肝肾功能不全"],
        "dosage_guide": "成人：200-400mg，每4-6小时一次；最大剂量：1200mg/日",
    },
    {
        "name": "对乙酰氨基酚",
        "specification": "500mg/片",
        "price": 10.0,
        "stock": 200,
        "is_prescription": False,
        "indications": ["发热", "头痛", "关节痛", "肌肉痛"],
        "contraindications": ["严重肝功能障碍", "酒精中毒"],
        "dosage_guide": "成人：500-1000mg，每4-6小时一次；最大剂量：4000mg/日",
    },
    {
        "name": "蒙脱石散",
        "specification": "3g/袋",
        "price": 20.0,
        "stock": 120,
        "is_prescription": False,
        "indications": ["腹泻", "肠胃不适"],
        "contraindications": ["肠梗阻"],
        "dosage_guide": "成人：1袋，每日3次；儿童：按年龄减量",
    },
    {
        "name": "氯雷他定",
        "specification": "10mg/片",
        "price": 30.0,
        "stock": 90,
        "is_prescription": False,
        "indications": ["过敏性鼻炎", "荨麻疹", "皮肤瘙痒"],
        "contraindications": ["严重肝功能不全"],
        "dosage_guide": "成人及12岁以上儿童：10mg，每日一次",
    },
]


# ==================== 药品查询工具 ====================
def query_drug(query: str) -> str:
    """
    根据症状或药品名称查询相关药物信息。

    Args:
        query: 症状关键词或药品名称

    Returns:
        药品信息JSON字符串
    """
    logger.info(f"查询药物: {query}")

    try:
        # Use pharmacy_client module for real queries
        from ..services.pharmacy_client import query_drugs_by_symptom, query_drug_by_name

        # 扩展症状关键词检测
        symptom_keywords = ["头痛", "头疼", "发热", "咳嗽", "疼痛", "fever", "pain", "cough"]
        is_symptom_query = any(keyword in query.lower() for keyword in symptom_keywords)

        if is_symptom_query:
            # Symptom query
            drugs = query_drugs_by_symptom(query)
        else:
            # Name query
            drug = query_drug_by_name(query)
            drugs = [drug] if drug else []

            # 症状映射回退机制
            if not drugs:
                symptom_mapping = {
                    "头疼": "布洛芬",
                    "头痛": "布洛芬",
                    "发热": "对乙酰氨基酚",
                    "咳嗽": "头孢克肟",
                    "过敏": "氯雷他定"
                }
                for symptom, default_drug in symptom_mapping.items():
                    if symptom in query:
                        drug = query_drug_by_name(default_drug)
                        if drug:
                            drugs = [drug]
                            logger.info(f"症状'{symptom}'映射到默认药品'{default_drug}'")
                        break

        if not drugs:
            return json.dumps(
                {
                    "status": "not_found",
                    "message": f"未找到匹配 '{query}' 的药品",
                    "drugs": [],
                },
                ensure_ascii=False,
            )

        # Format response
        formatted_drugs = []
        for drug in drugs:
            formatted_drug = {
                "name": drug.get("name", "未知"),
                "specification": "需从backend获取详细信息",
                "price": 0.0,  # Backend doesn't have price field yet
                "stock": drug.get("quantity", 0),
                "is_prescription": drug.get("name", "").lower()
                in ["amoxicillin", "azithromycin"],
                "indications": ["需从backend获取适应症信息"],
                "expiry_days": drug.get("expiry_date", 0),
                "location": f"货架{drug.get('shelve_id', 0)}-({drug.get('shelf_x', 0)},{drug.get('shelf_y', 0)})",
            }
            formatted_drugs.append(formatted_drug)

        return json.dumps(
            {
                "status": "success",
                "count": len(formatted_drugs),
                "query": query,
                "drugs": formatted_drugs,
            },
            ensure_ascii=False,
            indent=2,
        )

    except Exception as e:
        logger.error(f"查询药物失败: {str(e)}")
        return json.dumps(
            {"status": "error", "message": f"查询失败: {str(e)}", "drugs": []},
            ensure_ascii=False,
        )


# ==================== 过敏检查工具 ====================
def check_allergy(patient_allergies: str, drug_name: str) -> str:
    """
    检查患者是否对某种药物过敏。

    Args:
        patient_allergies: 患者已知过敏史，如"青霉素, 头孢"
        drug_name: 要检查的药物名称

    Returns:
        过敏检查结果JSON字符串
    """
    logger.info(f"检查过敏: 患者过敏史={patient_allergies}, 药物={drug_name}")

    # 常见的过敏原映射
    allergy_mapping = {
        "青霉素": ["阿莫西林", "氨苄西林", "青霉素"],
        "头孢": ["头孢克肟", "头孢拉定", "头孢氨苄", "头孢"],
        "磺胺": ["磺胺嘧啶", "磺胺甲噁唑"],
        "阿司匹林": ["阿司匹林", "布洛芬"],
        "酒精": ["某些酊剂"],
    }

    # 检查药品是否在过敏原映射中
    drug_lower = drug_name.lower()
    allergy_found = False
    allergy_details = []

    # 解析患者过敏史
    allergies = [a.strip() for a in patient_allergies.split(",") if a.strip()]

    for allergy in allergies:
        allergy_lower = allergy.lower()
        # 检查过敏原映射
        for allergen, related_drugs in allergy_mapping.items():
            if allergen in allergy_lower or allergy_lower in allergen.lower():
                for related in related_drugs:
                    if related.lower() in drug_lower or drug_lower in related.lower():
                        allergy_found = True
                        allergy_details.append(
                            {
                                "allergen": allergen,
                                "related_drug": related,
                                "patient_allergy": allergy,
                            }
                        )

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


# ==================== 剂量计算工具 ====================
def calc_dosage(
    drug_name: str, age: int, weight_kg: float, condition_severity: str = "中"
) -> str:
    """
    根据患者年龄、体重、药品规格计算推荐剂量。

    Args:
        drug_name: 药品名称
        age: 年龄（岁）
        weight_kg: 体重（公斤）
        condition_severity: 病情严重程度（轻、中、重）

    Returns:
        剂量计算结果JSON字符串
    """
    # 统一严重程度格式：将"轻度"转为"轻"，"重度"转为"重"
    severity_mapping = {"轻度": "轻", "中度": "中", "重度": "重"}
    if condition_severity in severity_mapping:
        condition_severity = severity_mapping[condition_severity]

    logger.info(
        f"计算剂量: 药物={drug_name}, 年龄={age}, 体重={weight_kg}kg, 严重程度={condition_severity}"
    )

    # 剂量计算规则（mock）
    dosage_rules = {
        "阿莫西林": {
            "adult_dose": "500mg，每8小时一次",
            "child_dose_formula": "20-40mg/kg/日，分3次服用",
            "max_daily": "3000mg",
        },
        "头孢克肟": {
            "adult_dose": "100-200mg，每日两次",
            "child_dose_formula": "8mg/kg/日，分2次服用",
            "max_daily": "400mg",
        },
        "布洛芬": {
            "adult_dose": "200-400mg，每4-6小时一次",
            "child_dose_formula": "5-10mg/kg/次，每6-8小时一次",
            "max_daily": "1200mg",
        },
        "对乙酰氨基酚": {
            "adult_dose": "500-1000mg，每4-6小时一次",
            "child_dose_formula": "10-15mg/kg/次，每4-6小时一次",
            "max_daily": "4000mg",
        },
        "蒙脱石散": {
            "adult_dose": "1袋（3g），每日3次",
            "child_dose_formula": "按年龄调整：<1岁: 1/3袋/次, 1-2岁: 1/2袋/次, >2岁: 1袋/次",
            "max_daily": "9g",
        },
        "氯雷他定": {
            "adult_dose": "10mg，每日一次",
            "child_dose_formula": "2-12岁: 5mg/日，<2岁: 不推荐使用",
            "max_daily": "10mg",
        },
    }

    # 获取药品规则
    drug_rules = None
    for name, rules in dosage_rules.items():
        if name.lower() in drug_name.lower() or drug_name.lower() in name.lower():
            drug_rules = rules
            break

    if not drug_rules:
        # 默认规则
        drug_rules = {
            "adult_dose": "按说明书服用",
            "child_dose_formula": "按体重计算",
            "max_daily": "不超过最大推荐剂量",
        }

    # 计算推荐剂量
    is_child = age < 12
    recommended_dose = ""

    if is_child:
        if weight_kg > 0:
            # 模拟按体重计算
            if "布洛芬" in drug_name or "ibuprofen" in drug_name.lower():
                child_dose_mg = weight_kg * 7.5  # 7.5mg/kg
                recommended_dose = f"儿童（{age}岁，{weight_kg}kg）：约{child_dose_mg:.1f}mg/次，每6-8小时一次"
            elif "对乙酰氨基酚" in drug_name or "paracetamol" in drug_name.lower():
                child_dose_mg = weight_kg * 12.5  # 12.5mg/kg
                recommended_dose = f"儿童（{age}岁，{weight_kg}kg）：约{child_dose_mg:.1f}mg/次，每4-6小时一次"
            else:
                recommended_dose = f"儿童（{age}岁，{weight_kg}kg）：{drug_rules['child_dose_formula']}"
        else:
            recommended_dose = f"儿童剂量：{drug_rules['child_dose_formula']}"
    else:
        recommended_dose = f"成人剂量：{drug_rules['adult_dose']}"

    # 根据病情严重程度调整
    severity_multiplier = {"轻": 0.8, "中": 1.0, "重": 1.2}.get(condition_severity, 1.0)

    if severity_multiplier != 1.0:
        recommended_dose += (
            f"（病情{condition_severity}，建议按{severity_multiplier}倍调整）"
        )

    # 生成简洁的剂量描述，供generate_advice使用
    if is_child:
        if "布洛芬" in drug_name or "ibuprofen" in drug_name.lower():
            child_dose_mg = weight_kg * 7.5
            dosage_for_advice = f"儿童剂量：约{child_dose_mg:.0f}mg/次，每6-8小时一次"
        elif "对乙酰氨基酚" in drug_name or "paracetamol" in drug_name.lower():
            child_dose_mg = weight_kg * 12.5
            dosage_for_advice = f"儿童剂量：约{child_dose_mg:.0f}mg/次，每4-6小时一次"
        else:
            dosage_for_advice = (
                f"儿童剂量：{drug_rules.get('child_dose_formula', '按体重计算')}"
            )
    else:
        dosage_for_advice = f"成人剂量：{drug_rules.get('adult_dose', '按说明书服用')}"

    # 根据严重程度估算药品数量
    severity_to_quantity = {"轻": 1, "中": 2, "重": 3}
    estimated_quantity = severity_to_quantity.get(condition_severity, 1)
    # 如果是儿童，数量减半（向上取整）
    if is_child:
        estimated_quantity = max(1, (estimated_quantity + 1) // 2)  # 向上取整的减半

    # 构建核心响应，仅包含必要字段
    response = {
        "drug_name": drug_name,
        "age": age,
        "weight_kg": weight_kg,
        "condition_severity": condition_severity,
        "dosage": dosage_for_advice,  # 关键字段：供generate_advice使用
        "estimated_quantity": estimated_quantity,  # 关键字段：供submit_approval使用
        "next_step": "调用 generate_advice 工具，使用上面的 dosage 字段",
        "note": "请立即调用 generate_advice 工具，传递 drug_name 和 dosage 参数",
    }

    return json.dumps(response, ensure_ascii=False)


# ==================== 建议生成工具 ====================
def generate_advice(
    drug_name: str, dosage: str, duration: str = None, notes: str = None
) -> str:
    """
    生成结构化的用药建议文本，供医生审批参考。

    Args:
        drug_name: 药品名称
        dosage: 剂量说明
        duration: 用药时长（可选）
        notes: 注意事项（可选）

    Returns:
        建议文本JSON字符串
    """
    logger.info(f"生成建议: 药物={drug_name}, 剂量={dosage}")

    # 如果没有提供用药时长，生成默认值
    if not duration:
        duration = "3-7天，根据病情调整"

    # 如果没有提供注意事项，生成默认值
    if not notes:
        notes = "饭后服用，避免饮酒，如有不适立即停药并就医"

    # 生成建议文本
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


# ==================== 审批提交工具 ====================
def submit_approval(
    patient_name: str,
    advice: str,
    patient_age: int = None,
    patient_weight: float = None,
    symptoms: str = None,
    drug_name: str = None,
    drug_type: str = None,
    quantity: int = 1,
    **kwargs,
) -> str:
    """
    提交用药建议给医生审批

    Args:
        patient_name: 患者姓名
        advice: 用药建议
        patient_age: 患者年龄（可选）
        patient_weight: 患者体重（可选）
        symptoms: 症状描述（可选）
        drug_name: 药品名称（可选）
        drug_type: 药品类型（可选）
        quantity: 药品数量，默认为1

    Returns:
        审批单ID，格式如 "AP-20260407-ABCD1234"
    """
    logger.info(
        f"提交审批: patient={patient_name}, drug={drug_name}, quantity={quantity}"
    )

    try:
        # Import HTTP client
        from ..utils.http_client import PharmacyHTTPClient

        client = PharmacyHTTPClient()
        approval_id = client.create_approval(
            patient_name=patient_name,
            advice=advice,
            patient_age=patient_age,
            patient_weight=patient_weight,
            symptoms=symptoms,
            drug_name=drug_name,
            drug_type=drug_type,
            quantity=quantity,
        )

        if approval_id:
            logger.info(f"审批提交成功: {approval_id}")
            # 返回JSON格式，包含审批ID和状态信息
            return json.dumps(
                {
                    "status": "submitted",
                    "approval_id": approval_id,
                    "message": f"用药建议已提交审批，审批ID: {approval_id}",
                    "instructions": "请等待医生审批。批准后，系统将自动配药。您也可以手动检查状态：python approve_prescription.py",
                    "timestamp": datetime.now().isoformat(),
                    "quantity": quantity,
                },
                ensure_ascii=False,
            )
        else:
            logger.error("审批提交失败: 未返回审批ID")
            # Fallback to mock for compatibility
            mock_id = f"AP-{datetime.now().strftime('%Y%m%d')}-MOCK{random.randint(1000, 9999)}"
            return json.dumps(
                {
                    "status": "mock",
                    "approval_id": mock_id,
                    "message": f"审批提交失败，使用模拟审批ID: {mock_id}",
                    "instructions": "此为模拟审批，用于测试。实际使用时需要真实后端。",
                    "timestamp": datetime.now().isoformat(),
                    "quantity": quantity,
                },
                ensure_ascii=False,
            )

    except Exception as e:
        logger.error(f"审批提交失败: {str(e)}")
        # Fallback to mock for compatibility
        mock_id = (
            f"AP-{datetime.now().strftime('%Y%m%d')}-MOCK{random.randint(1000, 9999)}"
        )
        return json.dumps(
            {
                "status": "error",
                "approval_id": mock_id,
                "message": f"审批提交过程中出错: {str(e)}",
                "instructions": "使用模拟审批ID继续测试。",
                "timestamp": datetime.now().isoformat(),
                "quantity": quantity,
            },
            ensure_ascii=False,
        )


# ==================== 处方配药工具 ====================
async def _create_mock_response(
    prescription_id: str, patient_name: str, drugs: List[Dict]
) -> Dict:
    """创建mock响应（回退用）"""
    import asyncio

    await asyncio.sleep(0.5)  # 模拟网络延迟

    # 生成取药码
    pickup_code = (
        f"PICKUP-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
    )

    return {
        "success": True,
        "prescription_id": prescription_id,
        "patient_name": patient_name,
        "pickup_code": pickup_code,
        "dispensed_at": datetime.now().isoformat(),
        "drugs_dispensed": drugs,
        "message": f"配药成功！取药码：{pickup_code}。请凭码到药房取药。",
        "pharmacy_note": "请在24小时内取药，过期作废",
        "mode": "mock",
    }


async def fill_prescription(
    prescription_id: str, patient_name: str, drugs: List[Dict]
) -> str:
    """
    在医生审批通过后，调用此工具将处方发送给药房系统进行配药。

    Args:
        prescription_id: 处方ID
        patient_name: 患者姓名
        drugs: 药品列表，每个药品包含name、dosage、quantity

    Returns:
        配药结果JSON字符串
    """
    logger.info(
        f"配药请求: 处方ID={prescription_id}, 患者={patient_name}, 药品数={len(drugs)}"
    )

    try:
        # 检查药房系统是否可用
        pharmacy_url = Config.PHARMACY_BASE_URL

        if pharmacy_url == "http://localhost:8001":
            # 尝试调用真实API（本地开发环境）
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    api_response = await client.post(
                        f"{pharmacy_url}/api/dispense",
                        json={
                            "prescription_id": prescription_id,
                            "patient_name": patient_name,
                            "drugs": drugs,
                        },
                    )

                    if api_response.status_code == 200:
                        result = api_response.json()
                        response = {
                            "success": True,
                            "prescription_id": prescription_id,
                            "patient_name": patient_name,
                            **result,
                            "mode": "real_api",
                        }
                    else:
                        # API调用失败，回退到mock模式
                        logger.warning(
                            f"API调用失败 {api_response.status_code}，使用mock模式"
                        )
                        response = await _create_mock_response(
                            prescription_id, patient_name, drugs
                        )
            except Exception as e:
                # 网络错误，回退到mock模式
                logger.warning(f"API调用异常: {str(e)}，使用mock模式")
                response = await _create_mock_response(
                    prescription_id, patient_name, drugs
                )
        else:
            # 真实模式：调用药房系统API
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    api_response = await client.post(
                        f"{pharmacy_url}/api/dispense",
                        json={
                            "prescription_id": prescription_id,
                            "patient_name": patient_name,
                            "drugs": drugs,
                        },
                    )

                    if api_response.status_code == 200:
                        result = api_response.json()
                        response = {
                            "success": True,
                            "prescription_id": prescription_id,
                            "patient_name": patient_name,
                            **result,
                            "mode": "real_api",
                        }
                    else:
                        response = {
                            "success": False,
                            "prescription_id": prescription_id,
                            "patient_name": patient_name,
                            "error": f"药房系统返回错误: {api_response.status_code}",
                            "error_details": (
                                api_response.text[:200] if api_response.text else ""
                            ),
                            "mode": "real_api_failed",
                        }
            except Exception as e:
                response = {
                    "success": False,
                    "prescription_id": prescription_id,
                    "patient_name": patient_name,
                    "error": f"调用药房系统失败: {str(e)}",
                    "mode": "real_api_error",
                }

    except Exception as e:
        logger.exception(f"配药过程中发生错误: {e}")
        response = {
            "success": False,
            "prescription_id": prescription_id,
            "patient_name": patient_name,
            "error": f"配药处理失败: {str(e)}",
            "mode": "exception",
        }

    return json.dumps(response, ensure_ascii=False, indent=2)


# ==================== 同步版本（用于非异步环境） ====================
def fill_prescription_sync(
    prescription_id: str, patient_name: str, drugs: List[Dict]
) -> str:
    """
    fill_prescription的同步版本，用于不支持异步的环境。
    """
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(
            fill_prescription(prescription_id, patient_name, drugs)
        )
        return result
    finally:
        loop.close()


# ==================== 工具注册函数 ====================
def register_tools(executor):
    """
    将所有工具函数注册到执行器。

    Args:
        executor: ToolExecutor实例
    """
    executor.register_handler("query_drug", query_drug)
    executor.register_handler("check_allergy", check_allergy)
    executor.register_handler("calc_dosage", calc_dosage)
    executor.register_handler("generate_advice", generate_advice)
    executor.register_handler("submit_approval", submit_approval)
    executor.register_handler(
        "fill_prescription", fill_prescription_sync
    )  # 使用同步版本

    logger.info("医疗工具已注册到执行器")
