# 组件3：智能筛选系统 - 快速开始指南

## 🚀 快速开始

### 安装依赖

```bash
# 进入项目目录
cd agent_with_backend

# 安装所有依赖（已包含screening模块需要的库）
pip install -r requirements.txt
```

### 集成到主应用

在 `main.py` 或应用启动文件中注册screening蓝图：

```python
from flask import Flask
from screening.routes import create_screening_blueprint

app = Flask(__name__)

# 注册筛选系统蓝图
screening_bp = create_screening_blueprint()
app.register_blueprint(screening_bp)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

### 运行服务

```bash
# 方法1：直接运行
python main.py

# 方法2：使用make命令（如果配置了）
make run

# 方法3：使用gunicorn生产部署
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

### 测试API

通过浏览器或curl测试：

```bash
# 测试症状标准化
curl -X POST http://localhost:5000/api/screening/symptoms/standardize \\
  -H \"Content-Type: application/json\" \\
  -d '{\"symptoms\": [\"头疼\", \"发烧\"]}'

# 测试服务状态
curl -X GET http://localhost:5000/api/screening/status

# 测试筛选查询
curl -X POST http://localhost:5000/api/screening/query \\
  -H \"Content-Type: application/json\" \\
  -d '{\"symptoms\": [\"头痛\", \"发热\"], \"user_id\": 1}'
```

---

## 📁 项目结构

```
agent_with_backend/
├── screening/                          # 智能筛选系统
│   ├── __init__.py                    # 模块初始化
│   ├── models/                        # 数据模型
│   │   ├── __init__.py
│   │   ├── symptom_model.py           # 症状模型
│   │   ├── screening_history_model.py # 筛选历史模型
│   │   └── screening_config_model.py  # 配置模型
│   ├── services/                      # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── symptom_service.py         # 症状处理服务
│   │   ├── screening_service.py       # 筛选服务
│   │   ├── config_service.py          # 配置管理服务
│   │   └── history_service.py         # 历史管理服务
│   └── routes/                        # API路由层
│       ├── __init__.py
│       └── screening_routes.py        # 筛选API路由
├── tests/
│   ├── test_screening.py              # 单元测试
│   └── test_screening_integration.py  # 集成测试
├── screening/
│   └── SCREENING_API.md               # API文档
├── main.py                            # 应用入口
└── requirements.txt                   # 依赖列表
```

---

## 🏗️ 架构设计

### 分层架构

```
┌─────────────────────────────┐
│   API路由层 (routes)        │
│  - 请求验证和参数解析       │
│  - 错误处理和响应格式化     │
└──────────────┬──────────────┘
               │
┌──────────────▼──────────────┐
│   业务逻辑层 (services)     │
│  - SymptomService           │
│  - ScreeningService         │
│  - ConfigService            │
│  - HistoryService           │
└──────────────┬──────────────┘
               │
┌──────────────▼──────────────┐
│   数据模型层 (models)       │
│  - Symptom                  │
│  - ScreeningHistory         │
│  - ScreeningConfig          │
└──────────────┬──────────────┘
               │
┌──────────────▼──────────────┐
│   数据存储层 (Database)     │
│  - SQLite/MySQL             │
│  - 缓存系统 (Redis)         │
└─────────────────────────────┘
```

### 模块职责

#### 1. 症状处理服务 (SymptomService)

```python
# 主要方法
- standardize_symptom(text)        # 标准化单个症状
- standardize_symptoms(texts)      # 标准化多个症状
- get_synonyms(symptom_name)       # 获取同义词
- calculate_similarity(text1, text2) # 相似度计算
- expand_symptoms_with_synonyms()  # 同义词扩展
```

**使用示例：**

```python
from screening.services import SymptomService

service = SymptomService()

# 标准化症状
result = service.standardize_symptoms(['头疼', '发烧'])
# => {'standardized_symptoms': ['头痛', '发热'], ...}

# 获取同义词
synonyms = service.get_synonyms('头痛')
# => ['头疼', '头痛', '偏头痛']
```

#### 2. 筛选服务 (ScreeningService)

```python
# 主要方法
- screening_query(symptoms, patient_info, filters)
- batch_screening(queries, batch_id)
- get_service_status()
```

**筛选算法流程：**

```
1. 症状验证 → 2. 药品匹配 → 3. 应用筛选 → 4. 患者信息过滤
    ↓              ↓            ↓               ↓
  检查空值    按症状相似度   价格、分类等   年龄、过敏等
    ↓              ↓            ↓               ↓
5. 结果排序 → 6. 置信度计算 → 7. 返回结果
```

**置信度计算：**

```
confidence_score = 
  症状匹配度 × 0.5 +      # 50% 权重
  药物效能 × 0.3 +        # 30% 权重  
  价格优势 × 0.2          # 20% 权重
```

#### 3. 配置管理服务 (ConfigService)

```python
# 主要方法
- get_config(config_name)          # 获取配置
- get_active_config()              # 获取活跃配置
- create_config(config_data)       # 创建配置
- update_config(name, updates)     # 更新配置
- delete_config(config_name)       # 删除配置
```

**配置参数：**

| 参数 | 默认值 | 范围 | 说明 |
|------|--------|------|------|
| confidence_threshold | 0.5 | 0-1 | 置信度阈值 |
| max_results | 20 | 1-1000 | 最大结果数 |
| cache_ttl | 3600 | 0-86400 | 缓存时间(秒) |
| timeout_seconds | 5.0 | 0-60 | 查询超时(秒) |

#### 4. 历史管理服务 (HistoryService)

```python
# 主要方法
- save_history(history_data)                    # 保存历史
- get_history(user_id, limit, offset, date_range)  # 获取历史
- get_history_detail(history_id)               # 获取详情
- get_user_statistics(user_id)                 # 获取统计
- clear_old_history(days)                      # 清理旧记录
```

---

## 🔄 调用流程

### 完整的筛选查询流程

```
用户请求
    ↓
API路由接收 (/api/screening/query)
    ↓
症状标准化 (SymptomService.standardize_symptoms)
    ↓
药品筛选 (ScreeningService.screening_query)
    ├─→ 匹配相关药品
    ├─→ 应用筛选条件
    ├─→ 考虑患者信息
    └─→ 排序和计算置信度
    ↓
保存历史记录 (HistoryService.save_history)
    ↓
返回结果给用户
```

### 代码示例

```python
# 直接使用服务层
from screening.services import (
    SymptomService,
    ScreeningService,
    HistoryService
)

# 初始化服务
symptom_service = SymptomService()
screening_service = ScreeningService(symptom_service)
history_service = HistoryService()

# 执行筛选
symptoms = ['头疼', '发烧']
result = screening_service.screening_query(
    symptoms=symptoms,
    patient_info={'age': 35},
    filters={'max_results': 20},
    user_id=123
)

# 检查结果
if result['success']:
    print(f\"找到 {result['total_count']} 个推荐药品\")
    for drug in result['results']:
        print(f\"  - {drug['drug_name']}: {drug['confidence_score']:.2%}\")
    
    # 保存历史
    history_service.save_history({
        'user_id': 123,
        'input_symptoms': symptoms,
        'result_drugs': result['results'],
        'result_count': result['total_count'],
        'status': 'success'
    })
```

---

## 🧪 测试

### 运行单元测试

```bash
# 运行所有测试
python -m unittest discover tests

# 运行特定测试文件
python -m unittest tests.test_screening

# 运行特定测试类
python -m unittest tests.test_screening.TestSymptomService

# 运行特定测试方法
python -m unittest tests.test_screening.TestSymptomService.test_standardize_symptom_exact_match

# 带详细输出
python -m unittest tests.test_screening -v
```

### 运行集成测试

```bash
# 运行API集成测试
python -m unittest tests.test_screening_integration -v
```

### 测试覆盖率

```bash
# 安装coverage工具
pip install coverage

# 运行覆盖率检查
coverage run -m unittest discover tests
coverage report
coverage html  # 生成HTML报告
```

### 手动测试清单

- [ ] 症状标准化：验证同义词正确识别
- [ ] 筛选查询：验证返回的药品相关性
- [ ] 置信度：验证置信度计算正确
- [ ] 性能：验证查询响应时间 < 500ms
- [ ] 历史记录：验证历史保存和查询
- [ ] 配置管理：验证配置的创建、更新、删除
- [ ] 错误处理：验证异常情况的处理

---

## 📊 性能优化

### 缓存策略

```python
# 症状标准化结果缓存
symptom_cache = {}

# 药品匹配结果缓存
drug_match_cache = {}

# 缓存过期时间：3600秒（1小时）
CACHE_TTL = 3600
```

### 数据库查询优化

```python
# 使用索引加速查询
# symptom表：按standard_name建立索引
# screening_history表：按user_id, created_at建立组合索引

CREATE INDEX idx_symptom_name ON symptoms(standard_name);
CREATE INDEX idx_history_user_date ON screening_history(user_id, created_at DESC);
```

### 批量操作

```python
# 批量查询使用IN语句而不是多个单独查询
# 批量插入使用insertMany降低数据库往返次数
```

---

## 🔗 与其他组件的集成

### 与组件2（药品管理API）的集成

```python
# 调用组件2的API获取药品信息
import requests

def fetch_drugs_from_component2():
    \"\"\"从组件2获取药品数据\"\"\"
    response = requests.get(
        'http://localhost:5000/api/drugs',
        params={'limit': 1000},
        headers={'Authorization': f'Bearer {jwt_token}'}
    )
    return response.json()
```

### 与组件4（权限认证）的集成

```python
# 所有API都需要认证
from functools import wraps
from flask import request

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return {'success': False, 'error': '缺少认证令牌'}, 401
        # 验证token...
        return f(*args, **kwargs)
    return decorated

@bp.route('/query', methods=['POST'])
@require_auth
def screening_query():
    # ...
```

---

## 🐛 常见问题

### Q1: 为什么症状无法识别？

**A:** 症状可能不在标准症状库中，或拼写有误。可以：
1. 检查症状名称是否正确
2. 查询同义词列表
3. 添加新的症状同义词映射

### Q2: 筛选结果为空？

**A:** 可能原因：
1. 症状太特殊，没有匹配的药品
2. 置信度阈值过高，调低阈值重试
3. 应用了过严格的筛选条件，放宽条件重试

### Q3: API响应很慢？

**A:** 可以进行以下优化：
1. 检查缓存是否启用
2. 检查数据库连接池配置
3. 减少返回结果数量（max_results）
4. 增加更新缓存TTL时间

### Q4: 历史记录无法保存？

**A:** 检查数据库连接和表是否存在：
```python
# 确保创建了必要的表
# 可运行数据库迁移脚本
python database/scripts/init_db.py
```

---

## 📚 进阶开发

### 自定义症状库

```python
# 1. 创建自定义症状服务
class CustomSymptomService(SymptomService):
    def __init__(self, db_session):
        super().__init__(db_session)
        self._load_custom_symptoms()
    
    def _load_custom_symptoms(self):
        \"\"\"从数据库加载自定义症状\"\"\"
        # 从数据库查询症状表
        symptoms = db_session.query(Symptom).all()
        for symptom in symptoms:
            self.STANDARD_SYMPTOMS[symptom.standard_name] = (
                [s.synonym_name for s in symptom.synonyms]
            )
```

### 自定义筛选算法

```python
# 实现ML-based筛选
class MLScreeningService(ScreeningService):
    def __init__(self, symptom_service, model):
        super().__init__(symptom_service)
        self.model = model  # ML模型
    
    def _rank_results(self, candidates, symptoms):
        \"\"\"使用ML模型对结果排序\"\"\"
        # 使用ML模型给每个候选药品打分
        for candidate in candidates:
            features = self._extract_features(candidate, symptoms)
            score = self.model.predict(features)
            candidate['confidence_score'] = score
        
        return sorted(candidates, key=lambda x: x['confidence_score'], reverse=True)
```

---

## 📋 检查清单

**开发完成检查：**

- [x] 数据模型定义完成
- [x] 业务逻辑实现完成
- [x] API路由定义完成
- [x] 单元测试编写完成
- [x] 集成测试编写完成
- [x] API文档编写完成
- [ ] 数据库迁移脚本编写
- [ ] 生产部署配置编写
- [ ] 性能基准测试完成
- [ ] 安全审计完成

**部署前检查：**

- [ ] 所有测试通过
- [ ] 代码审查完成
- [ ] 安全扫描完成
- [ ] 性能测试通过
- [ ] 文档更新完成
- [ ] 部署计划制定
- [ ] 回滚方案准备
- [ ] 监控告警配置

---

## 🚀 下一步

1. **集成数据库**：将内存存储改为真实数据库存储
2. **连接组件2**：集成药品管理API，获取真实药品数据
3. **完善权限**：集成组件4的权限认证系统
4. **性能测试**：压测和优化以满足性能指标
5. **前端集成**：与组件5的前端联调

---

**最后更新:** 2024-05-20  
**维护者:** 组件3开发团队
