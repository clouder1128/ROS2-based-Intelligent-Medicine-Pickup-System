# 组件3：智能筛选系统

## 📖 简介

智能筛选系统是智能药品管理系统的核心组件之一，负责：

✅ **症状识别**：自动识别和标准化患者输入的症状
✅ **智能匹配**：基于症状和患者信息进行药品智能推荐
✅ **多维度筛选**：支持价格、类别、效能等多维度筛选
✅ **置信度评分**：为推荐结果提供科学的置信度评分
✅ **完整追踪**：记录所有筛选查询供后续分析

## 🎯 功能特性

### 核心功能

- **症状处理**
  - 自然语言症状文本标准化
  - 支持30+症状同义词映射
  - LLM增强的症状理解（可选）

- **智能筛选**
  - 基于症状的相似度匹配
  - 患者信息综合考虑（年龄、过敏等）
  - 多条件组合筛选

- **配置管理**
  - 灵活的系统参数配置
  - 支持多套配置方案
  - 版本管理和变更跟踪

- **历史追踪**
  - 完整的筛选查询历史
  - 用户行为分析
  - 数据导出功能

## 📊 技术栈

- **后端框架**: Flask
- **数据库**: SQLAlchemy ORM (支持 SQLite/MySQL/PostgreSQL)
- **缓存**: Python内置/Redis可选
- **测试**: unittest/pytest
- **文档**: OpenAPI/Swagger

## 📁 项目结构

```
screening/
├── models/                      # 数据模型层
│   ├── symptom_model.py         # 症状模型
│   ├── screening_history_model.py
│   └── screening_config_model.py
├── services/                    # 业务逻辑层
│   ├── symptom_service.py       # 症状处理
│   ├── screening_service.py     # 筛选查询
│   ├── config_service.py        # 配置管理
│   └── history_service.py       # 历史管理
├── routes/                      # API层
│   └── screening_routes.py      # REST API端点
├── SCREENING_API.md             # 完整API文档
├── GETTING_STARTED.md           # 快速开始指南
└── README.md                    # 本文件
```

## 🚀 快速开始

### 安装

```bash
# 克隆项目
git clone <repository>
cd agent_with_backend

# 安装依赖
pip install -r requirements.txt
```

### 使用

```python
from screening.services import ScreeningService, SymptomService

# 初始化服务
symptom_service = SymptomService()
screening_service = ScreeningService(symptom_service)

# 执行筛选
result = screening_service.screening_query(
    symptoms=['头痛', '发热'],
    patient_info={'age': 35},
    user_id=123
)

# 查看结果
for drug in result['results']:
    print(f\"{drug['drug_name']}: {drug['confidence_score']:.2%}\")
```

### 启动服务

```bash
# 开发模式
python main.py

# 生产模式
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

### API示例

```bash
# 症状标准化
curl -X POST http://localhost:5000/api/screening/symptoms/standardize \\
  -H \"Content-Type: application/json\" \\
  -d '{\"symptoms\": [\"头疼\", \"发烧\"]}'

# 执行筛选查询
curl -X POST http://localhost:5000/api/screening/query \\
  -H \"Content-Type: application/json\" \\
  -d '{\"symptoms\": [\"头痛\"], \"user_id\": 1}'

# 获取服务状态  
curl -X GET http://localhost:5000/api/screening/status
```

## 📚 API文档

完整的API文档见 [SCREENING_API.md](SCREENING_API.md)

### 主要端点

| HTTP | 端点 | 描述 |
|------|------|------|
| POST | `/api/screening/symptoms/standardize` | 症状标准化 |
| GET | `/api/screening/symptoms/synonyms` | 获取同义词 |
| POST | `/api/screening/query` | 执行筛选查询 |
| POST | `/api/screening/batch` | 批量筛选 |
| GET | `/api/screening/config` | 获取配置 |
| PUT | `/api/screening/config` | 更新配置 |
| GET | `/api/screening/history` | 查看历史 |
| GET | `/api/screening/history/{id}` | 查看历史详情 |
| GET | `/api/screening/status` | 获取服务状态 |

## 🧪 测试

```bash
# 运行所有测试
python -m unittest discover tests -v

# 运行特定测试
python -m unittest tests.test_screening -v

# 覆盖率
coverage run -m unittest discover tests
coverage report
```

## ⚙️ 配置

### 默认配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `confidence_threshold` | 0.5 | 置信度阈值 |
| `max_results` | 20 | 最大返回结果数 |
| `cache_ttl` | 3600 | 缓存过期时间（秒） |
| `timeout_seconds` | 5.0 | 查询超时时间（秒） |

### 获取当前配置

```python
from screening.services import ConfigService

config_service = ConfigService()
config = config_service.get_active_config()
print(config)
```

### 更新配置

```python
result = config_service.update_config(
    'default',
    {'max_results': 30, 'confidence_threshold': 0.6}
)
```

## 🔄 集成指南

### 与组件2（药品管理）的集成

组件3需要从组件2获取药品数据：

```python
# 在screening_service.py中
import requests

def _fetch_drugs_from_component2(self):
    \"\"\"获取药品列表\"\"\"
    response = requests.get(
        'http://component2-host/api/drugs',
        headers={'Authorization': f'Bearer {token}'}
    )
    return response.json()['data']
```

### 与组件4（权限认证）的集成

所有API都应该进行认证：

```python
# 在screening_routes.py中
from auth.middleware import require_auth

@bp.route('/query', methods=['POST'])
@require_auth(roles=['doctor', 'pharmacist', 'admin'])
def screening_query():
    # ...
```

### 与组件1（数据库）的集成

使用ORM定义模型并迁移到数据库：

```python
# 运行迁移
flask db upgrade

# 或者直接初始化
from common.config import db
from screening.models import Symptom, ScreeningHistory, ScreeningConfig

db.create_all()
```

## 📈 性能指标

| 指标 | 目标 | 实际 |
|------|------|------|
| 症状标准化 | < 100ms | - |
| 单次筛选查询 | < 500ms | - |
| 批量筛选 | < 2s | - |
| 吞吐量 | 100 req/s | - |

## 🔐 安全性

- ✅ JWT认证
- ✅ 基于角色的访问控制(RBAC)
- ✅ 参数验证和防注入
- ✅ 速率限制
- ✅ 审计日志记录

## 📝 诊断和故障排查

### 常见问题

**Q1: 症状无法识别**

A: 检查症状是否在同义词库中
```python
symptom_service.get_synonyms('头痛')  # 查看支持的同义词
```

**Q2: 筛选结果为空**

A: 检查是否满足置信度阈值
```python
# 调低置信度阈值重试
config_service.update_config('default', {'confidence_threshold': 0.3})
```

**Q3: 性能下降**

A: 检查缓存和数据库
```python
# 查看服务状态
screening_service.get_service_status()
```

### 日志和监控

```python
import logging

logger = logging.getLogger('screening')
logger.setLevel(logging.DEBUG)

# 查看详细日志
tail -f logs/screening.log
```

## 🚀 部署

### Docker部署

```dockerfile
FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD [\"gunicorn\", \"-w\", \"4\", \"-b\", \"0.0.0.0:5000\", \"main:app\"]
```

### Kubernetes部署

见 [deployment.yaml](deployment.yaml)

## 📚 文档

- [API详细文档](SCREENING_API.md)
- [快速开始指南](GETTING_STARTED.md)
- [项目架构设计](../按架构组件分工/智能药品管理系统架构组件接口清单.md)

## 🤝 贡献指南

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启PR审查

## 📋 开发计划

- [ ] 集成真实数据库
- [ ] 连接组件2的药品API
- [ ] 集成组件4的权限认证
- [ ] 实现ML-based筛选算法
- [ ] 性能基准测试
- [ ] 安全审计
- [ ] 生产部署
- [ ] 监控和告警配置

## 📞 联系方式

- 开发团队：智能筛选小组
- 技术问题：创建Issue
- 反馈建议：提交讨论

## 📄 许可证

本项目采用 MIT 许可证

---

**项目版本**: 1.0.0  
**最后更新**: 2024-05-20  
**维护者**: 组件3开发团队
