"""
筛选系统种子数据脚本
为演示/测试场景提供完整的药品、适应症、症状同义词数据。
直接使用 common.utils.database 连接，与筛选服务使用同一数据源。

用法:
    cd agent_with_backend
    python3 scripts/seed_screening_data.py
"""

import json
import os
import sys

# 确保能导入 common 模块
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_script_dir, ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from common.utils.database import get_db_connection


def seed_symptom_synonyms(conn):
    """插入症状同义词数据"""
    synonyms = [
        # 头痛
        ("头痛", "头疼"),
        ("头痛", "头胀痛"),
        ("头痛", "偏头痛"),
        ("头痛", "太阳穴痛"),
        # 发热
        ("发热", "发烧"),
        ("发热", "高热"),
        ("发热", "低烧"),
        ("发热", "体温高"),
        # 咳嗽
        ("咳嗽", "干咳"),
        ("咳嗽", "咳痰"),
        ("咳嗽", "久咳"),
        ("咳嗽", "咽喉痒"),
        # 喉咙疼痛
        ("喉咙疼痛", "喉咙痛"),
        ("喉咙疼痛", "咽痛"),
        ("喉咙疼痛", "嗓子疼"),
        ("喉咙疼痛", "吞咽困难"),
        # 腹泻
        ("腹泻", "拉肚子"),
        ("腹泻", "水样便"),
        ("腹泻", "频繁排便"),
        # 便秘
        ("便秘", "排便困难"),
        ("便秘", "大便干燥"),
        ("便秘", "不通便"),
        # 恶心
        ("恶心", "想吐"),
        ("恶心", "反胃"),
        ("恶心", "胃部不适"),
        # 呕吐
        ("呕吐", "吐"),
        ("呕吐", "呕吐不止"),
        # 腹痛
        ("腹痛", "肚子疼"),
        ("腹痛", "胃痛"),
        ("腹痛", "腹部不适"),
        # 肌肉酸痛
        ("肌肉酸痛", "肌肉疼"),
        ("肌肉酸痛", "浑身酸痛"),
        ("肌肉酸痛", "身体疼"),
        ("肌肉酸痛", "四肢乏力"),
        # 皮疹
        ("皮疹", "长疹子"),
        ("皮疹", "出疹"),
        ("皮疹", "皮肤红疹"),
        # 瘙痒
        ("瘙痒", "痒"),
        ("瘙痒", "皮肤痒"),
        # 鼻塞
        ("鼻塞", "鼻子不通"),
        ("鼻塞", "呼吸不畅"),
        # 流鼻涕
        ("流鼻涕", "流清涕"),
        ("流鼻涕", "鼻涕多"),
        # 失眠
        ("失眠", "睡眠不好"),
        ("失眠", "难以入睡"),
        ("失眠", "多梦"),
        # 过敏
        ("过敏", "过敏反应"),
        ("过敏", "荨麻疹"),
        ("过敏", "过敏性鼻炎"),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO symptom_synonyms (standard_term, synonym, match_type) VALUES (?, ?, 'similar')",
        synonyms,
    )
    print(f"  ✓ 写入 {len(synonyms)} 条症状同义词")


def seed_drug_indications(conn, drug_id: int, indications: list):
    """为指定药品插入适应症"""
    rows = [(drug_id, ind) for ind in indications]
    conn.executemany(
        "INSERT OR IGNORE INTO drug_indications (drug_id, indication) VALUES (?, ?)",
        rows,
    )
    return len(rows)


def seed_drugs(conn):
    """插入带完整字段的药品数据"""
    drugs = [
        {
            "drug_id": 1,
            "name": "阿莫西林胶囊",
            "generic_name": "阿莫西林",
            "quantity": 200,
            "retail_price": 12.50,
            "category": "抗生素",
            "is_prescription": 1,
            "description": "广谱青霉素类抗生素，用于敏感菌所致感染",
            "manufacturer": "华北制药",
            "specification": "0.25g×24粒",
            "dosage_form": "胶囊剂",
            "unit": "盒",
            "contraindications": "青霉素过敏者禁用",
            "pregnancy_category": "B",
            "pediatric_caution": "儿童需按体重计算剂量",
            "age_restrictions": json.dumps({"min_age": 1, "max_age": 80}),
            "side_effects": "腹泻、皮疹、恶心",
            "interaction_warning": "与甲氨蝶呤合用增加毒性",
            "storage_condition": "密封，阴凉干燥处",
            "min_stock_level": 50,
            "max_stock_level": 500,
            "purchase_price": 8.00,
            "cost_price": 8.00,
            "supplier": "华北制药集团",
            "expiry_date": 730,
            "shelf_x": 1,
            "shelf_y": 1,
            "shelve_id": 1,
            "indications": ["喉咙疼痛", "咳嗽", "扁桃体炎", "支气管炎"],
        },
        {
            "drug_id": 2,
            "name": "布洛芬缓释胶囊",
            "generic_name": "布洛芬",
            "quantity": 150,
            "retail_price": 15.80,
            "category": "解热镇痛药",
            "is_prescription": 0,
            "description": "非甾体抗炎药，用于缓解轻至中度疼痛和退热",
            "manufacturer": "中美史克",
            "specification": "0.3g×20粒",
            "dosage_form": "缓释胶囊",
            "unit": "盒",
            "contraindications": "活动性消化性溃疡者禁用；对阿司匹林过敏者禁用",
            "pregnancy_category": "C",
            "pediatric_caution": "6个月以下婴儿慎用",
            "age_restrictions": json.dumps({"min_age": 0.5, "max_age": 80}),
            "side_effects": "胃肠道不适、恶心、头晕",
            "interaction_warning": "与抗凝药合用增加出血风险",
            "storage_condition": "密封保存",
            "min_stock_level": 30,
            "max_stock_level": 300,
            "purchase_price": 10.50,
            "cost_price": 10.50,
            "supplier": "中美史克制药",
            "expiry_date": 540,
            "shelf_x": 1,
            "shelf_y": 2,
            "shelve_id": 1,
            "indications": ["发热", "头痛", "肌肉酸痛", "牙痛", "痛经"],
        },
        {
            "drug_id": 3,
            "name": "对乙酰氨基酚片",
            "generic_name": "对乙酰氨基酚",
            "quantity": 300,
            "retail_price": 5.50,
            "category": "解热镇痛药",
            "is_prescription": 0,
            "description": "解热镇痛药，用于普通感冒引起的发热和头痛",
            "manufacturer": "白云山制药",
            "specification": "0.5g×10片",
            "dosage_form": "片剂",
            "unit": "盒",
            "contraindications": "严重肝肾功能不全者禁用",
            "pregnancy_category": "B",
            "pediatric_caution": "儿童按体重计算剂量",
            "age_restrictions": json.dumps({"min_age": 0.25, "max_age": 80}),
            "side_effects": "偶见皮疹、恶心",
            "interaction_warning": "饮酒增加肝毒性风险",
            "storage_condition": "密封保存",
            "min_stock_level": 50,
            "max_stock_level": 500,
            "purchase_price": 3.20,
            "cost_price": 3.20,
            "supplier": "白云山制药",
            "expiry_date": 720,
            "shelf_x": 2,
            "shelf_y": 1,
            "shelve_id": 1,
            "indications": ["发热", "头痛", "肌肉酸痛"],
        },
        {
            "drug_id": 4,
            "name": "氯雷他定片",
            "generic_name": "氯雷他定",
            "quantity": 80,
            "retail_price": 18.00,
            "category": "抗过敏药",
            "is_prescription": 0,
            "description": "三环类抗组胺药，用于过敏性鼻炎和荨麻疹",
            "manufacturer": "先灵葆雅",
            "specification": "10mg×6片",
            "dosage_form": "片剂",
            "unit": "盒",
            "contraindications": "对本品过敏者禁用",
            "pregnancy_category": "B",
            "pediatric_caution": "2岁以下儿童不宜使用",
            "age_restrictions": json.dumps({"min_age": 2, "max_age": 80}),
            "side_effects": "嗜睡、口干、乏力",
            "interaction_warning": "与酒精合用加重嗜睡",
            "storage_condition": "阴凉干燥处",
            "min_stock_level": 20,
            "max_stock_level": 200,
            "purchase_price": 12.00,
            "cost_price": 12.00,
            "supplier": "先灵葆雅制药",
            "expiry_date": 600,
            "shelf_x": 2,
            "shelf_y": 2,
            "shelve_id": 1,
            "indications": ["皮疹", "瘙痒", "过敏", "荨麻疹", "打喷嚏"],
        },
        {
            "drug_id": 5,
            "name": "蒙脱石散",
            "generic_name": "蒙脱石",
            "quantity": 120,
            "retail_price": 12.00,
            "category": "止泻药",
            "is_prescription": 0,
            "description": "天然止泻药，用于成人及儿童急慢性腹泻",
            "manufacturer": "博福-益普生",
            "specification": "3g×10袋",
            "dosage_form": "散剂",
            "unit": "盒",
            "contraindications": "肠梗阻者禁用",
            "pregnancy_category": "A",
            "pediatric_caution": "婴幼儿可用，按年龄减量",
            "age_restrictions": json.dumps({"min_age": 0, "max_age": 80}),
            "side_effects": "偶见便秘",
            "interaction_warning": "与其他药物间隔2小时服用",
            "storage_condition": "密封保存",
            "min_stock_level": 30,
            "max_stock_level": 200,
            "purchase_price": 7.50,
            "cost_price": 7.50,
            "supplier": "博福-益普生制药",
            "expiry_date": 540,
            "shelf_x": 3,
            "shelf_y": 1,
            "shelve_id": 2,
            "indications": ["腹泻", "水样便"],
        },
        {
            "drug_id": 6,
            "name": "盐酸氨溴索片",
            "generic_name": "氨溴索",
            "quantity": 90,
            "retail_price": 8.50,
            "category": "化痰药",
            "is_prescription": 0,
            "description": "黏液溶解剂，用于急慢性呼吸道疾病痰液黏稠",
            "manufacturer": "勃林格殷格翰",
            "specification": "30mg×20片",
            "dosage_form": "片剂",
            "unit": "盒",
            "contraindications": "对本品过敏者禁用",
            "pregnancy_category": "B",
            "pediatric_caution": "儿童可用",
            "age_restrictions": json.dumps({"min_age": 0, "max_age": 80}),
            "side_effects": "偶见胃肠道不适",
            "interaction_warning": "与抗生素合用增加肺部浓度",
            "storage_condition": "密封保存",
            "min_stock_level": 20,
            "max_stock_level": 200,
            "purchase_price": 5.00,
            "cost_price": 5.00,
            "supplier": "勃林格殷格翰",
            "expiry_date": 600,
            "shelf_x": 3,
            "shelf_y": 2,
            "shelve_id": 2,
            "indications": ["咳嗽", "咳痰", "痰多"],
        },
        {
            "drug_id": 7,
            "name": "藿香正气水",
            "generic_name": "藿香正气",
            "quantity": 60,
            "retail_price": 9.80,
            "category": "中成药",
            "is_prescription": 0,
            "description": "解表化湿、理气和中，用于暑湿感冒和胃肠不适",
            "manufacturer": "太极集团",
            "specification": "10ml×10支",
            "dosage_form": "口服液",
            "unit": "盒",
            "contraindications": "酒精过敏者慎用（含酒精）",
            "pregnancy_category": "C",
            "pediatric_caution": "儿童减量，需在医师指导下使用",
            "age_restrictions": json.dumps({"min_age": 3, "max_age": 80}),
            "side_effects": "偶见皮疹、头晕",
            "interaction_warning": "与头孢类抗生素合用可能引起双硫仑样反应",
            "storage_condition": "密封，阴凉处",
            "min_stock_level": 20,
            "max_stock_level": 150,
            "purchase_price": 6.00,
            "cost_price": 6.00,
            "supplier": "太极集团",
            "expiry_date": 720,
            "shelf_x": 4,
            "shelf_y": 1,
            "shelve_id": 2,
            "indications": ["腹泻", "恶心", "呕吐", "腹痛", "中暑"],
        },
        {
            "drug_id": 8,
            "name": "维生素C泡腾片",
            "generic_name": "维生素C",
            "quantity": 200,
            "retail_price": 25.00,
            "category": "维生素",
            "is_prescription": 0,
            "description": "补充维生素C，增强机体抵抗力",
            "manufacturer": "力度伸",
            "specification": "1g×20片",
            "dosage_form": "泡腾片",
            "unit": "瓶",
            "contraindications": "高草酸盐尿症者禁用",
            "pregnancy_category": "A",
            "pediatric_caution": "儿童可用",
            "age_restrictions": json.dumps({"min_age": 0, "max_age": 80}),
            "side_effects": "过量服用可引起腹泻",
            "interaction_warning": "",
            "storage_condition": "密封，防潮",
            "min_stock_level": 30,
            "max_stock_level": 300,
            "purchase_price": 16.00,
            "cost_price": 16.00,
            "supplier": "力度伸",
            "expiry_date": 900,
            "shelf_x": 4,
            "shelf_y": 2,
            "shelve_id": 2,
            "indications": ["预防", "免疫力低下", "口腔溃疡"],
        },
        {
            "drug_id": 9,
            "name": "板蓝根颗粒",
            "generic_name": "板蓝根",
            "quantity": 250,
            "retail_price": 6.50,
            "category": "中成药",
            "is_prescription": 0,
            "description": "清热解毒、凉血利咽，用于风热感冒和咽喉肿痛",
            "manufacturer": "同仁堂",
            "specification": "10g×20袋",
            "dosage_form": "颗粒剂",
            "unit": "包",
            "contraindications": "糖尿病患者慎用（含糖）",
            "pregnancy_category": "B",
            "pediatric_caution": "儿童减量",
            "age_restrictions": json.dumps({"min_age": 1, "max_age": 80}),
            "side_effects": "偶见过敏反应",
            "interaction_warning": "",
            "storage_condition": "密封，阴凉处",
            "min_stock_level": 50,
            "max_stock_level": 400,
            "purchase_price": 3.50,
            "cost_price": 3.50,
            "supplier": "同仁堂集团",
            "expiry_date": 600,
            "shelf_x": 5,
            "shelf_y": 1,
            "shelve_id": 3,
            "indications": ["喉咙疼痛", "发热", "风热感冒"],
        },
        {
            "drug_id": 10,
            "name": "酚麻美敏片",
            "generic_name": "酚麻美敏",
            "quantity": 100,
            "retail_price": 13.50,
            "category": "感冒药",
            "is_prescription": 0,
            "description": "复方感冒药，用于缓解普通感冒症状",
            "manufacturer": "强生",
            "specification": "12片",
            "dosage_form": "片剂",
            "unit": "盒",
            "contraindications": "严重高血压、冠心病者禁用",
            "pregnancy_category": "C",
            "pediatric_caution": "12岁以下儿童不宜使用",
            "age_restrictions": json.dumps({"min_age": 12, "max_age": 80}),
            "side_effects": "嗜睡、口干、偶见心悸",
            "interaction_warning": "与MAOI合用禁忌",
            "storage_condition": "密封保存",
            "min_stock_level": 30,
            "max_stock_level": 200,
            "purchase_price": 8.50,
            "cost_price": 8.50,
            "supplier": "强生制药",
            "expiry_date": 480,
            "shelf_x": 5,
            "shelf_y": 2,
            "shelve_id": 3,
            "indications": ["鼻塞", "流鼻涕", "发热", "头痛", "肌肉酸痛"],
        },
    ]

    conn.executemany(
        """
        INSERT OR REPLACE INTO inventory (
            drug_id, name, generic_name, quantity, retail_price,
            category, is_prescription, description, manufacturer,
            specification, dosage_form, unit, contraindications,
            pregnancy_category, pediatric_caution, age_restrictions,
            side_effects, interaction_warning, storage_condition,
            min_stock_level, max_stock_level, purchase_price, cost_price,
            supplier, expiry_date, shelf_x, shelf_y, shelve_id,
            is_deleted
        ) VALUES (
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?
        )
        """,
        [
            (
                d["drug_id"],
                d["name"],
                d["generic_name"],
                d["quantity"],
                d["retail_price"],
                d["category"],
                d["is_prescription"],
                d["description"],
                d["manufacturer"],
                d["specification"],
                d["dosage_form"],
                d["unit"],
                d["contraindications"],
                d["pregnancy_category"],
                d["pediatric_caution"],
                d["age_restrictions"],
                d["side_effects"],
                d["interaction_warning"],
                d["storage_condition"],
                d["min_stock_level"],
                d["max_stock_level"],
                d["purchase_price"],
                d["cost_price"],
                d["supplier"],
                d["expiry_date"],
                d["shelf_x"],
                d["shelf_y"],
                d["shelve_id"],
                0,
            )
            for d in drugs
        ],
    )

    # 写入适应症
    total_indications = 0
    for d in drugs:
        total_indications += seed_drug_indications(conn, d["drug_id"], d["indications"])

    print(f"  ✓ 写入 {len(drugs)} 种药品, {total_indications} 条适应症")


def seed_categories(conn):
    """插入药品分类"""
    categories = [
        ("抗生素", "抗感染类药物", None, 1),
        ("解热镇痛药", "退烧和止痛类药物", None, 2),
        ("感冒药", "感冒症状缓解类药物", None, 3),
        ("抗过敏药", "过敏症状缓解类药物", None, 4),
        ("止泻药", "腹泻治疗药物", None, 5),
        ("化痰药", "祛痰止咳类药物", None, 6),
        ("中成药", "中药制剂", None, 7),
        ("维生素", "维生素和营养补充剂", None, 8),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO categories (name, description, parent_id, sort_order) VALUES (?, ?, ?, ?)",
        categories,
    )
    print(f"  ✓ 写入 {len(categories)} 条药品分类")


def seed_screening_config(conn):
    """插入默认筛选配置"""
    config_json = json.dumps(
        {
            "description": "默认筛选配置",
            "algorithm_type": "similarity",
            "confidence_threshold": 0.5,
            "max_results": 20,
            "min_symptom_match_rate": 0.3,
            "enable_synonym_expansion": True,
            "enable_llm_synonym": False,
            "enable_cache": True,
            "cache_ttl": 3600,
            "timeout_seconds": 5.0,
            "batch_max_size": 100,
            "is_active": True,
            "version": 1,
        },
        ensure_ascii=False,
    )
    conn.execute(
        "INSERT OR IGNORE INTO screening_config (config_name, config_json, is_active, version) VALUES (?, ?, 1, 1)",
        ("default", config_json),
    )
    print("  ✓ 写入默认筛选配置")


def main():
    conn = get_db_connection()
    try:
        print("正在写入筛选系统种子数据...\n")
        seed_symptom_synonyms(conn)
        print()
        seed_drugs(conn)
        print()
        seed_categories(conn)
        print()
        seed_screening_config(conn)
        conn.commit()
        print("\n✓ 种子数据写入完成!")
    except Exception as e:
        conn.rollback()
        print(f"\n✗ 种子数据写入失败: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
