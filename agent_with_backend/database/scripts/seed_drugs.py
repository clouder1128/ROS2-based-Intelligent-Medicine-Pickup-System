"""
批量药品种子数据生成脚本
生成 100+ 种涵盖 12 大类的药品，每种药附带适应症信息。
幂等执行：每次运行先清空再重新写入。

用法：python3 -m database.scripts.seed_drugs
"""

import sqlite3
import random
import itertools
from datetime import date
from common.config import Config

DB_PATH = Config.DATABASE_PATH

# ==================== 药品数据定义 ====================

DRUG_CATEGORIES = [
    {
        "category": "解热镇痛抗炎药",
        "drugs": [
            {
                "name": "布洛芬",
                "indications": ["头痛","头疼","偏头痛","牙痛","关节痛","痛经","发热","发烧","肌肉痛"],
                "is_prescription": False, "price": 15.0,
                "min_stock": 50, "max_stock": 200,
            },
            {
                "name": "对乙酰氨基酚",
                "indications": ["发热","发烧","头痛","头疼","关节痛","肌肉痛","感冒"],
                "is_prescription": False, "price": 10.0,
                "min_stock": 80, "max_stock": 300,
            },
            {
                "name": "阿司匹林",
                "indications": ["发热","发烧","头痛","关节痛","心血管疾病","预防血栓"],
                "is_prescription": True, "price": 8.0,
                "min_stock": 60, "max_stock": 200,
            },
            {
                "name": "双氯芬酸",
                "indications": ["关节痛","肌肉痛","腰痛","关节炎","扭伤","痛风"],
                "is_prescription": True, "price": 18.0,
                "min_stock": 30, "max_stock": 100,
            },
            {
                "name": "塞来昔布",
                "indications": ["关节炎","关节痛","腰痛","骨关节炎","强直性脊柱炎"],
                "is_prescription": True, "price": 45.0,
                "min_stock": 20, "max_stock": 80,
            },
            {
                "name": "洛索洛芬",
                "indications": ["头痛","牙痛","关节痛","肌肉痛","腰痛","手术后疼痛"],
                "is_prescription": True, "price": 22.0,
                "min_stock": 30, "max_stock": 100,
            },
            {
                "name": "依托考昔",
                "indications": ["关节炎","关节痛","痛风","腰痛","骨关节炎"],
                "is_prescription": True, "price": 50.0,
                "min_stock": 15, "max_stock": 60,
            },
            {
                "name": "萘普生",
                "indications": ["头痛","牙痛","关节痛","肌肉痛","痛经","发热"],
                "is_prescription": False, "price": 12.0,
                "min_stock": 40, "max_stock": 150,
            },
            {
                "name": "美洛昔康",
                "indications": ["关节炎","关节痛","腰痛","骨关节炎","类风湿关节炎"],
                "is_prescription": True, "price": 28.0,
                "min_stock": 20, "max_stock": 80,
            },
            {
                "name": "吲哚美辛",
                "indications": ["关节炎","痛风","腰痛","强直性脊柱炎","关节痛"],
                "is_prescription": True, "price": 10.0,
                "min_stock": 25, "max_stock": 90,
            },
        ],
    },
    {
        "category": "抗生素抗感染药",
        "drugs": [
            {
                "name": "阿莫西林",
                "indications": ["感冒","发热","发烧","呼吸道感染","扁桃体炎","中耳炎","鼻窦炎"],
                "is_prescription": True, "price": 12.0,
                "min_stock": 40, "max_stock": 150,
            },
            {
                "name": "头孢克肟",
                "indications": ["呼吸道感染","泌尿道感染","皮肤感染","扁桃体炎","中耳炎"],
                "is_prescription": True, "price": 35.0,
                "min_stock": 30, "max_stock": 100,
            },
            {
                "name": "头孢拉定",
                "indications": ["呼吸道感染","泌尿道感染","皮肤感染","扁桃体炎"],
                "is_prescription": True, "price": 20.0,
                "min_stock": 30, "max_stock": 100,
            },
            {
                "name": "头孢氨苄",
                "indications": ["呼吸道感染","皮肤感染","泌尿道感染","扁桃体炎"],
                "is_prescription": True, "price": 15.0,
                "min_stock": 35, "max_stock": 120,
            },
            {
                "name": "阿奇霉素",
                "indications": ["呼吸道感染","肺炎","支气管炎","咽炎","皮肤感染"],
                "is_prescription": True, "price": 40.0,
                "min_stock": 20, "max_stock": 80,
            },
            {
                "name": "左氧氟沙星",
                "indications": ["呼吸道感染","泌尿道感染","肠道感染","前列腺炎","皮肤感染"],
                "is_prescription": True, "price": 30.0,
                "min_stock": 25, "max_stock": 90,
            },
            {
                "name": "克拉霉素",
                "indications": ["呼吸道感染","支气管炎","肺炎","鼻窦炎","皮肤感染"],
                "is_prescription": True, "price": 35.0,
                "min_stock": 20, "max_stock": 80,
            },
            {
                "name": "甲硝唑",
                "indications": ["牙痛","牙周炎","牙龈炎","肠道感染","阴道感染"],
                "is_prescription": True, "price": 8.0,
                "min_stock": 40, "max_stock": 150,
            },
            {
                "name": "诺氟沙星",
                "indications": ["腹泻","肠道感染","泌尿道感染","细菌性痢疾"],
                "is_prescription": True, "price": 10.0,
                "min_stock": 30, "max_stock": 120,
            },
            {
                "name": "克林霉素",
                "indications": ["皮肤感染","呼吸道感染","骨感染","牙周感染"],
                "is_prescription": True, "price": 25.0,
                "min_stock": 20, "max_stock": 80,
            },
            {
                "name": "罗红霉素",
                "indications": ["呼吸道感染","支气管炎","肺炎","咽炎","皮肤感染"],
                "is_prescription": True, "price": 28.0,
                "min_stock": 20, "max_stock": 80,
            },
            {
                "name": "头孢呋辛",
                "indications": ["呼吸道感染","泌尿道感染","皮肤感染","中耳炎","鼻窦炎"],
                "is_prescription": True, "price": 32.0,
                "min_stock": 20, "max_stock": 70,
            },
            {
                "name": "阿莫西林克拉维酸",
                "indications": ["呼吸道感染","鼻窦炎","中耳炎","皮肤感染","泌尿道感染"],
                "is_prescription": True, "price": 45.0,
                "min_stock": 15, "max_stock": 60,
            },
            {
                "name": "呋喃妥因",
                "indications": ["泌尿道感染","膀胱炎","尿路感染"],
                "is_prescription": True, "price": 12.0,
                "min_stock": 25, "max_stock": 90,
            },
            {
                "name": "磷霉素",
                "indications": ["肠道感染","泌尿道感染","细菌性痢疾","腹泻"],
                "is_prescription": True, "price": 18.0,
                "min_stock": 20, "max_stock": 70,
            },
        ],
    },
    {
        "category": "消化系统药",
        "drugs": [
            {
                "name": "蒙脱石散",
                "indications": ["腹泻","拉肚子","拉稀","肠胃不适","急性胃肠炎"],
                "is_prescription": False, "price": 20.0,
                "min_stock": 40, "max_stock": 150,
            },
            {
                "name": "奥美拉唑",
                "indications": ["胃痛","胃酸","反酸","胃食管反流","胃炎","胃溃疡"],
                "is_prescription": False, "price": 25.0,
                "min_stock": 40, "max_stock": 150,
            },
            {
                "name": "多潘立酮",
                "indications": ["恶心","想吐","呕吐","腹胀","消化不良","胃胀"],
                "is_prescription": False, "price": 15.0,
                "min_stock": 30, "max_stock": 120,
            },
            {
                "name": "铝碳酸镁",
                "indications": ["胃痛","胃酸","反酸","胃灼热","胃炎","消化不良"],
                "is_prescription": False, "price": 18.0,
                "min_stock": 30, "max_stock": 100,
            },
            {
                "name": "雷贝拉唑",
                "indications": ["胃痛","胃酸","反酸","胃食管反流","胃炎","胃溃疡"],
                "is_prescription": True, "price": 38.0,
                "min_stock": 20, "max_stock": 80,
            },
            {
                "name": "枸橼酸铋钾",
                "indications": ["胃痛","胃炎","胃溃疡","胃酸","消化不良"],
                "is_prescription": False, "price": 22.0,
                "min_stock": 20, "max_stock": 80,
            },
            {
                "name": "莫沙必利",
                "indications": ["腹胀","消化不良","胃胀","便秘","恶心","食欲不振"],
                "is_prescription": True, "price": 28.0,
                "min_stock": 20, "max_stock": 70,
            },
            {
                "name": "双歧杆菌",
                "indications": ["腹泻","便秘","腹胀","消化不良","肠胃不适","肠道菌群失调"],
                "is_prescription": False, "price": 35.0,
                "min_stock": 25, "max_stock": 80,
            },
            {
                "name": "乳果糖",
                "indications": ["便秘","排便困难","老年便秘","习惯性便秘"],
                "is_prescription": False, "price": 30.0,
                "min_stock": 30, "max_stock": 100,
            },
            {
                "name": "开塞露",
                "indications": ["便秘","排便困难","大便干结"],
                "is_prescription": False, "price": 5.0,
                "min_stock": 50, "max_stock": 200,
            },
            {
                "name": "泮托拉唑",
                "indications": ["胃痛","胃酸","胃溃疡","胃食管反流","胃炎"],
                "is_prescription": True, "price": 35.0,
                "min_stock": 20, "max_stock": 80,
            },
            {
                "name": "复方消化酶",
                "indications": ["消化不良","腹胀","食欲不振","胃胀","肠胃不适"],
                "is_prescription": False, "price": 25.0,
                "min_stock": 20, "max_stock": 70,
            },
        ],
    },
    {
        "category": "呼吸系统药",
        "drugs": [
            {
                "name": "氨溴索",
                "indications": ["咳嗽","咳痰","痰多","支气管炎","咽喉痛","呼吸道感染"],
                "is_prescription": False, "price": 12.0,
                "min_stock": 40, "max_stock": 150,
            },
            {
                "name": "右美沙芬",
                "indications": ["咳嗽","干咳","感冒咳嗽","咽炎"],
                "is_prescription": False, "price": 15.0,
                "min_stock": 30, "max_stock": 120,
            },
            {
                "name": "沙丁胺醇",
                "indications": ["哮喘","气喘","呼吸困难","支气管痉挛","咳嗽","胸闷"],
                "is_prescription": True, "price": 25.0,
                "min_stock": 20, "max_stock": 80,
            },
            {
                "name": "复方甘草片",
                "indications": ["咳嗽","咳痰","咽喉痛","支气管炎","感冒咳嗽"],
                "is_prescription": False, "price": 8.0,
                "min_stock": 40, "max_stock": 200,
            },
            {
                "name": "孟鲁司特",
                "indications": ["哮喘","过敏性鼻炎","咳嗽","气喘","呼吸困难"],
                "is_prescription": True, "price": 40.0,
                "min_stock": 15, "max_stock": 60,
            },
            {
                "name": "茶碱",
                "indications": ["哮喘","气喘","支气管炎","呼吸困难","慢性阻塞性肺病"],
                "is_prescription": True, "price": 18.0,
                "min_stock": 20, "max_stock": 80,
            },
            {
                "name": "异丙托溴铵",
                "indications": ["哮喘","气喘","呼吸困难","支气管炎","慢性阻塞性肺病"],
                "is_prescription": True, "price": 30.0,
                "min_stock": 15, "max_stock": 60,
            },
            {
                "name": "乙酰半胱氨酸",
                "indications": ["咳嗽","咳痰","痰多","支气管炎","呼吸道感染"],
                "is_prescription": False, "price": 22.0,
                "min_stock": 20, "max_stock": 80,
            },
            {
                "name": "福莫特罗",
                "indications": ["哮喘","气喘","呼吸困难","支气管痉挛","慢性阻塞性肺病"],
                "is_prescription": True, "price": 55.0,
                "min_stock": 10, "max_stock": 50,
            },
            {
                "name": "布地奈德",
                "indications": ["哮喘","过敏性鼻炎","气喘","呼吸困难","慢性阻塞性肺病"],
                "is_prescription": True, "price": 60.0,
                "min_stock": 10, "max_stock": 50,
            },
        ],
    },
    {
        "category": "抗过敏药",
        "drugs": [
            {
                "name": "氯雷他定",
                "indications": ["过敏性鼻炎","荨麻疹","皮肤瘙痒","过敏","皮肤过敏","皮疹","打喷嚏","流鼻涕"],
                "is_prescription": False, "price": 20.0,
                "min_stock": 40, "max_stock": 150,
            },
            {
                "name": "西替利嗪",
                "indications": ["过敏性鼻炎","荨麻疹","皮肤瘙痒","过敏","皮肤过敏","皮疹"],
                "is_prescription": False, "price": 18.0,
                "min_stock": 30, "max_stock": 120,
            },
            {
                "name": "扑尔敏",
                "indications": ["过敏性鼻炎","荨麻疹","皮肤瘙痒","过敏","打喷嚏","流鼻涕","感冒"],
                "is_prescription": False, "price": 5.0,
                "min_stock": 50, "max_stock": 200,
            },
            {
                "name": "依巴斯汀",
                "indications": ["过敏性鼻炎","荨麻疹","皮肤瘙痒","过敏","皮肤过敏"],
                "is_prescription": False, "price": 25.0,
                "min_stock": 20, "max_stock": 80,
            },
            {
                "name": "非索非那定",
                "indications": ["过敏性鼻炎","荨麻疹","皮肤瘙痒","过敏","打喷嚏","流鼻涕"],
                "is_prescription": False, "price": 30.0,
                "min_stock": 20, "max_stock": 70,
            },
            {
                "name": "酮替芬",
                "indications": ["过敏性鼻炎","荨麻疹","皮肤瘙痒","过敏","哮喘","咳嗽"],
                "is_prescription": True, "price": 12.0,
                "min_stock": 25, "max_stock": 90,
            },
        ],
    },
    {
        "category": "心血管药",
        "drugs": [
            {
                "name": "硝苯地平",
                "indications": ["高血压","血压高","心绞痛","冠心病"],
                "is_prescription": True, "price": 15.0,
                "min_stock": 40, "max_stock": 150,
            },
            {
                "name": "厄贝沙坦",
                "indications": ["高血压","血压高","肾病","糖尿病肾病"],
                "is_prescription": True, "price": 28.0,
                "min_stock": 30, "max_stock": 100,
            },
            {
                "name": "美托洛尔",
                "indications": ["高血压","血压高","心绞痛","心力衰竭","心律失常","心悸"],
                "is_prescription": True, "price": 18.0,
                "min_stock": 30, "max_stock": 120,
            },
            {
                "name": "氨氯地平",
                "indications": ["高血压","血压高","心绞痛","冠心病"],
                "is_prescription": True, "price": 25.0,
                "min_stock": 35, "max_stock": 120,
            },
            {
                "name": "缬沙坦",
                "indications": ["高血压","血压高","心力衰竭","肾病"],
                "is_prescription": True, "price": 30.0,
                "min_stock": 25, "max_stock": 100,
            },
            {
                "name": "卡托普利",
                "indications": ["高血压","血压高","心力衰竭","肾病"],
                "is_prescription": True, "price": 12.0,
                "min_stock": 30, "max_stock": 100,
            },
            {
                "name": "氯沙坦",
                "indications": ["高血压","血压高","肾病","糖尿病肾病"],
                "is_prescription": True, "price": 32.0,
                "min_stock": 25, "max_stock": 90,
            },
            {
                "name": "阿托伐他汀",
                "indications": ["高血脂","高胆固醇","冠心病","动脉粥样硬化","心血管疾病"],
                "is_prescription": True, "price": 45.0,
                "min_stock": 30, "max_stock": 100,
            },
            {
                "name": "辛伐他汀",
                "indications": ["高血脂","高胆固醇","冠心病","动脉粥样硬化"],
                "is_prescription": True, "price": 20.0,
                "min_stock": 30, "max_stock": 100,
            },
            {
                "name": "非洛地平",
                "indications": ["高血压","血压高","心绞痛"],
                "is_prescription": True, "price": 22.0,
                "min_stock": 20, "max_stock": 80,
            },
            {
                "name": "普伐他汀",
                "indications": ["高血脂","高胆固醇","冠心病","动脉粥样硬化"],
                "is_prescription": True, "price": 35.0,
                "min_stock": 20, "max_stock": 80,
            },
            {
                "name": "比索洛尔",
                "indications": ["高血压","血压高","心绞痛","心力衰竭","心律失常","心悸"],
                "is_prescription": True, "price": 28.0,
                "min_stock": 20, "max_stock": 80,
            },
        ],
    },
    {
        "category": "内分泌代谢药",
        "drugs": [
            {
                "name": "二甲双胍",
                "indications": ["糖尿病","血糖高","2型糖尿病","多囊卵巢综合征"],
                "is_prescription": True, "price": 10.0,
                "min_stock": 50, "max_stock": 200,
            },
            {
                "name": "格列美脲",
                "indications": ["糖尿病","血糖高","2型糖尿病"],
                "is_prescription": True, "price": 25.0,
                "min_stock": 20, "max_stock": 80,
            },
            {
                "name": "左甲状腺素",
                "indications": ["甲状腺功能减退","甲减","甲状腺肿大"],
                "is_prescription": True, "price": 20.0,
                "min_stock": 25, "max_stock": 90,
            },
            {
                "name": "阿卡波糖",
                "indications": ["糖尿病","血糖高","2型糖尿病","餐后血糖高"],
                "is_prescription": True, "price": 35.0,
                "min_stock": 15, "max_stock": 60,
            },
            {
                "name": "格列齐特",
                "indications": ["糖尿病","血糖高","2型糖尿病"],
                "is_prescription": True, "price": 22.0,
                "min_stock": 20, "max_stock": 80,
            },
            {
                "name": "瑞格列奈",
                "indications": ["糖尿病","血糖高","2型糖尿病","餐后血糖高"],
                "is_prescription": True, "price": 30.0,
                "min_stock": 15, "max_stock": 60,
            },
            {
                "name": "西格列汀",
                "indications": ["糖尿病","血糖高","2型糖尿病"],
                "is_prescription": True, "price": 55.0,
                "min_stock": 10, "max_stock": 50,
            },
            {
                "name": "吡格列酮",
                "indications": ["糖尿病","血糖高","2型糖尿病"],
                "is_prescription": True, "price": 40.0,
                "min_stock": 15, "max_stock": 60,
            },
        ],
    },
    {
        "category": "神经系统药",
        "drugs": [
            {
                "name": "艾司唑仑",
                "indications": ["失眠","睡不着","入睡困难","焦虑","睡眠障碍"],
                "is_prescription": True, "price": 12.0,
                "min_stock": 20, "max_stock": 80,
            },
            {
                "name": "地西泮",
                "indications": ["焦虑","失眠","紧张","惊厥","肌肉痉挛","烦躁"],
                "is_prescription": True, "price": 8.0,
                "min_stock": 20, "max_stock": 80,
            },
            {
                "name": "阿普唑仑",
                "indications": ["焦虑","紧张","失眠","惊恐","烦躁"],
                "is_prescription": True, "price": 15.0,
                "min_stock": 15, "max_stock": 60,
            },
            {
                "name": "氟桂利嗪",
                "indications": ["偏头痛","头痛","眩晕","头晕","耳鸣"],
                "is_prescription": True, "price": 20.0,
                "min_stock": 20, "max_stock": 80,
            },
            {
                "name": "谷维素",
                "indications": ["失眠","焦虑","神经衰弱","植物神经紊乱","头痛","头晕"],
                "is_prescription": False, "price": 8.0,
                "min_stock": 40, "max_stock": 150,
            },
            {
                "name": "甲钴胺",
                "indications": ["神经痛","神经炎","麻木","周围神经病变","贫血"],
                "is_prescription": False, "price": 15.0,
                "min_stock": 30, "max_stock": 120,
            },
            {
                "name": "维生素B1",
                "indications": ["神经炎","神经痛","麻木","食欲不振","疲劳","脚气病"],
                "is_prescription": False, "price": 5.0,
                "min_stock": 50, "max_stock": 200,
            },
            {
                "name": "帕罗西汀",
                "indications": ["抑郁","焦虑","强迫症","惊恐","社交焦虑"],
                "is_prescription": True, "price": 55.0,
                "min_stock": 15, "max_stock": 50,
            },
        ],
    },
    {
        "category": "维生素矿物质",
        "drugs": [
            {
                "name": "维生素C",
                "indications": ["免疫力低下","坏血病","口腔溃疡","感冒","疲劳","牙龈出血"],
                "is_prescription": False, "price": 5.0,
                "min_stock": 100, "max_stock": 500,
            },
            {
                "name": "维生素D",
                "indications": ["骨质疏松","钙缺乏","佝偻病","免疫力低下","骨折"],
                "is_prescription": False, "price": 15.0,
                "min_stock": 60, "max_stock": 300,
            },
            {
                "name": "维生素B6",
                "indications": ["呕吐","孕吐","神经炎","皮肤炎症","贫血","恶心"],
                "is_prescription": False, "price": 5.0,
                "min_stock": 50, "max_stock": 200,
            },
            {
                "name": "维生素B12",
                "indications": ["贫血","疲劳","神经炎","神经痛","麻木","口腔溃疡"],
                "is_prescription": False, "price": 8.0,
                "min_stock": 40, "max_stock": 180,
            },
            {
                "name": "钙片",
                "indications": ["骨质疏松","钙缺乏","骨折","抽筋","佝偻病","关节痛"],
                "is_prescription": False, "price": 30.0,
                "min_stock": 50, "max_stock": 200,
            },
            {
                "name": "复合维生素",
                "indications": ["疲劳","免疫力低下","食欲不振","营养不良","维生素缺乏"],
                "is_prescription": False, "price": 45.0,
                "min_stock": 30, "max_stock": 150,
            },
            {
                "name": "铁剂",
                "indications": ["贫血","缺铁性贫血","头晕","疲劳","面色苍白"],
                "is_prescription": False, "price": 25.0,
                "min_stock": 30, "max_stock": 120,
            },
            {
                "name": "锌剂",
                "indications": ["口腔溃疡","免疫力低下","食欲不振","生长发育迟缓","腹泻"],
                "is_prescription": False, "price": 20.0,
                "min_stock": 30, "max_stock": 120,
            },
            {
                "name": "叶酸",
                "indications": ["贫血","备孕","孕期保健","胎儿神经管畸形预防","巨幼细胞性贫血"],
                "is_prescription": False, "price": 10.0,
                "min_stock": 40, "max_stock": 200,
            },
            {
                "name": "维生素E",
                "indications": ["皮肤干燥","抗氧化","不孕不育","习惯性流产","肌肉萎缩"],
                "is_prescription": False, "price": 12.0,
                "min_stock": 30, "max_stock": 150,
            },
        ],
    },
    {
        "category": "外用药皮肤科",
        "drugs": [
            {
                "name": "莫匹罗星软膏",
                "indications": ["皮肤感染","毛囊炎","疖子","皮肤破损","湿疹感染","脓疱疮"],
                "is_prescription": False, "price": 18.0,
                "min_stock": 30, "max_stock": 100,
            },
            {
                "name": "酮康唑乳膏",
                "indications": ["皮肤癣","脚气","体癣","股癣","花斑癣","真菌感染"],
                "is_prescription": False, "price": 15.0,
                "min_stock": 30, "max_stock": 100,
            },
            {
                "name": "氢化可的松软膏",
                "indications": ["皮肤瘙痒","湿疹","皮炎","过敏","皮疹","皮肤红肿"],
                "is_prescription": False, "price": 10.0,
                "min_stock": 30, "max_stock": 120,
            },
            {
                "name": "红霉素软膏",
                "indications": ["皮肤感染","毛囊炎","疖子","烧伤感染","皮肤破损","痤疮"],
                "is_prescription": False, "price": 8.0,
                "min_stock": 40, "max_stock": 150,
            },
            {
                "name": "阿昔洛韦软膏",
                "indications": ["带状疱疹","单纯疱疹","水痘","病毒性皮肤病","唇疱疹"],
                "is_prescription": False, "price": 12.0,
                "min_stock": 25, "max_stock": 90,
            },
            {
                "name": "特比萘芬乳膏",
                "indications": ["脚气","体癣","股癣","手癣","真菌感染","皮肤癣"],
                "is_prescription": False, "price": 20.0,
                "min_stock": 20, "max_stock": 80,
            },
            {
                "name": "炉甘石洗剂",
                "indications": ["皮肤瘙痒","皮疹","荨麻疹","蚊虫叮咬","湿疹","过敏"],
                "is_prescription": False, "price": 8.0,
                "min_stock": 30, "max_stock": 120,
            },
            {
                "name": "复方醋酸地塞米松乳膏",
                "indications": ["湿疹","皮炎","皮肤瘙痒","过敏","皮疹","神经性皮炎"],
                "is_prescription": False, "price": 10.0,
                "min_stock": 30, "max_stock": 100,
            },
            {
                "name": "尿素软膏",
                "indications": ["皮肤干燥","手足皲裂","皮肤粗糙","鱼鳞病","角质增生"],
                "is_prescription": False, "price": 6.0,
                "min_stock": 30, "max_stock": 120,
            },
            {
                "name": "克霉唑乳膏",
                "indications": ["真菌感染","脚气","体癣","股癣","阴道感染","皮肤癣"],
                "is_prescription": False, "price": 10.0,
                "min_stock": 25, "max_stock": 100,
            },
        ],
    },
    {
        "category": "中成药感冒类",
        "drugs": [
            {
                "name": "板蓝根颗粒",
                "indications": ["感冒","咽喉痛","喉咙痛","发热","扁桃体炎"],
                "is_prescription": False, "price": 12.0,
                "min_stock": 60, "max_stock": 300,
            },
            {
                "name": "连花清瘟胶囊",
                "indications": ["感冒","流感","发热","咳嗽","咽喉痛","头痛","肌肉痛"],
                "is_prescription": False, "price": 25.0,
                "min_stock": 50, "max_stock": 200,
            },
            {
                "name": "感冒灵颗粒",
                "indications": ["感冒","发热","头痛","咳嗽","流鼻涕","鼻塞","咽喉痛"],
                "is_prescription": False, "price": 15.0,
                "min_stock": 50, "max_stock": 200,
            },
            {
                "name": "蒲地蓝消炎口服液",
                "indications": ["咽喉痛","扁桃体炎","腮腺炎","感冒","发热"],
                "is_prescription": False, "price": 30.0,
                "min_stock": 30, "max_stock": 120,
            },
            {
                "name": "藿香正气水",
                "indications": ["中暑","肠胃不适","腹泻","恶心","呕吐","感冒","腹胀"],
                "is_prescription": False, "price": 10.0,
                "min_stock": 40, "max_stock": 150,
            },
            {
                "name": "六味地黄丸",
                "indications": ["肾虚","腰膝酸软","头晕","耳鸣","盗汗","疲劳"],
                "is_prescription": False, "price": 25.0,
                "min_stock": 30, "max_stock": 120,
            },
            {
                "name": "牛黄解毒片",
                "indications": ["咽喉痛","口腔溃疡","牙龈炎","便秘","上火","牙痛"],
                "is_prescription": False, "price": 8.0,
                "min_stock": 50, "max_stock": 200,
            },
            {
                "name": "云南白药",
                "indications": ["跌打损伤","扭伤","瘀伤","肌肉痛","关节痛","出血"],
                "is_prescription": False, "price": 35.0,
                "min_stock": 25, "max_stock": 100,
            },
            {
                "name": "清开灵颗粒",
                "indications": ["感冒","发热","咽喉痛","咳嗽","扁桃体炎"],
                "is_prescription": False, "price": 18.0,
                "min_stock": 30, "max_stock": 120,
            },
            {
                "name": "小柴胡颗粒",
                "indications": ["感冒","发热","恶心","食欲不振","咽喉痛","头痛"],
                "is_prescription": False, "price": 15.0,
                "min_stock": 30, "max_stock": 120,
            },
        ],
    },
    {
        "category": "其他专科药",
        "drugs": [
            {
                "name": "黄体酮",
                "indications": ["月经不调","保胎","更年期综合征","功能性子宫出血"],
                "is_prescription": True, "price": 40.0,
                "min_stock": 15, "max_stock": 60,
            },
            {
                "name": "碳酸钙",
                "indications": ["骨质疏松","钙缺乏","抽筋","胃酸过多","骨折"],
                "is_prescription": False, "price": 20.0,
                "min_stock": 40, "max_stock": 150,
            },
            {
                "name": "硫糖铝",
                "indications": ["胃痛","胃酸","胃溃疡","胃炎","胃食管反流"],
                "is_prescription": False, "price": 12.0,
                "min_stock": 30, "max_stock": 100,
            },
            {
                "name": "环孢素",
                "indications": ["移植排斥","类风湿关节炎","肾病综合征","银屑病","皮炎"],
                "is_prescription": True, "price": 120.0,
                "min_stock": 5, "max_stock": 20,
            },
            {
                "name": "秋水仙碱",
                "indications": ["痛风","关节痛","急性痛风发作","痛风性关节炎"],
                "is_prescription": True, "price": 15.0,
                "min_stock": 15, "max_stock": 60,
            },
        ],
    },
]


def seed_database():
    """清空旧数据，重新生成 100+ 种药品"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 清空旧数据（先删子表，再删主表）
    c.execute("DELETE FROM drug_indications")
    c.execute("DELETE FROM inventory")

    # 预生成货位坐标（最多 1000 个组合）
    shelf_positions = list(itertools.product(range(10), range(10), range(10)))

    drug_id = 0
    total_drugs = 0

    for category_info in DRUG_CATEGORIES:
        category = category_info["category"]
        for drug in category_info["drugs"]:
            drug_id += 1
            x, y, z = shelf_positions[(drug_id - 1) % len(shelf_positions)]

            quantity = random.randint(drug["min_stock"], drug["max_stock"])
            expiry_date = random.randint(365, 800)  # 一年以上有效期
            is_prescription = 1 if drug["is_prescription"] else 0

            c.execute("""
                INSERT INTO inventory
                    (drug_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id,
                     category, is_prescription, retail_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                drug_id, drug["name"], quantity, expiry_date,
                x, y, z, category, is_prescription, drug["price"],
            ))

            for indication in drug["indications"]:
                c.execute("""
                    INSERT INTO drug_indications (drug_id, indication) VALUES (?, ?)
                """, (drug_id, indication))

            total_drugs += 1

    conn.commit()
    conn.close()
    print(f"Seeding complete: {total_drugs} drugs inserted across {len(DRUG_CATEGORIES)} categories.")


if __name__ == "__main__":
    seed_database()
