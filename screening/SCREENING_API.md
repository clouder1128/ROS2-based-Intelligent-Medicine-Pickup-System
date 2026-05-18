# 组件3：智能筛选系统 - API文档

## 📋 概述

本文档定义了智能筛选系统（组件3）的完整REST API接口，按照项目的架构接口清单规范编写。

**API基础信息：**
- 基础URL: `/api/screening`
- 版本: v1
- 认证: JWT Token（Bearer Token方式）
- 内容类型: `application/json`
- 响应格式: JSON

---

## 🔑 通用规范

### 请求格式

所有请求应包含以下HTTP头：

```
Content-Type: application/json
Authorization: Bearer {jwt_token}  # 如果需要认证的端点
```

### 响应格式

所有响应遵循统一的格式：

**成功响应 (200/201):**
```json
{
  "success": true,
  "data": {...},
  "message": "操作成功描述"  // 可选
}
```

**失败响应 (4xx/5xx):**
```json
{
  "success": false,
  "error": "错误简述",
  "message": "详细错误描述",  // 可选
  "error_code": "ERROR_001"  // 可选
}
```

### HTTP状态码

| 状态码 | 含义 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未认证或认证过期 |
| 403 | 无权限访问 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

### 分页规范

支持分页的端点使用以下参数：

```
page: 页码（从1开始）
limit: 每页返回数量（默认20，最大100）
offset: 偏移量（与page互斥）
```

---

## 🧬 症状处理接口

### 1. 标准化症状文本

**端点:** `POST /api/screening/symptoms/standardize`

**描述:** 将用户输入的症状文本转换为标准化的医学术语

**请求体:**

```json
{
  "symptoms": [
    "头疼",
    "发烧",
    "咳嗽"
  ],
  "language": "zh"  // 可选，默认中文
}
```

**请求参数说明:**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| symptoms | string[] | ✓ | 症状文本列表 |
| language | string | ✗ | 语言代码（默认'zh') |

**响应示例:**

```json
{
  "success": true,
  "data": {
    "standardized_symptoms": ["头痛", "发热", "咳嗽"],
    "unmatched": [],
    "confidence": 1.0,
    "input_count": 3,
    "matched_count": 3,
    "unmatched_count": 0
  }
}
```

**响应字段说明:**

| 字段 | 类型 | 描述 |
|------|------|------|
| standardized_symptoms | string[] | 标准化后的症状列表 |
| unmatched | string[] | 无法匹配的症状 |
| confidence | float | 匹配置信度（0-1） |
| input_count | int | 输入的症状数量 |
| matched_count | int | 成功匹配的症状数量 |
| unmatched_count | int | 未匹配的症状数量 |

**错误示例:**

```json
{
  "success": false,
  "error": "症状列表不能为空",
  "error_code": "INVALID_SYMPTOM_LIST"
}
```

---

### 2. 获取症状同义词

**端点:** `GET /api/screening/symptoms/synonyms`

**描述:** 获取指定症状的所有同义词表达

**查询参数:**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| symptom_name | string | ✓ | 标准症状名称 |

**请求示例:**

```
GET /api/screening/symptoms/synonyms?symptom_name=头痛
```

**响应示例:**

```json
{
  "success": true,
  "data": {
    "symptom_name": "头痛",
    "synonyms": ["头疼", "头痛", "偏头痛", "头部疼痛"]
  }
}
```

---

## 🔍 筛选查询接口

### 3. 症状筛选查询

**端点:** `POST /api/screening/query`

**描述:** 根据患者症状进行药品智能筛选

**请求体:**

```json
{
  "symptoms": ["头痛", "发热"],
  "patient_info": {
    "age": 35,
    "gender": "M",
    "allergies": ["青霉素"],
    "medical_history": ["高血压"]
  },
  "filters": {
    "max_results": 20,
    "price_range": [0, 100],
    "categories": ["感冒用药", "退烧用药"],
    "min_effectiveness": 0.7
  },
  "user_id": 123,
  "request_id": "req_20240520_001"  // 可选
}
```

**请求参数说明:**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| symptoms | string[] | ✓ | 标准化的症状列表 |
| patient_info | object | ✗ | 患者信息（年龄、性别等） |
| filters | object | ✗ | 筛选条件 |
| user_id | int | ✗ | 用户ID（用于历史记录） |
| request_id | string | ✗ | 请求追踪ID |

**filters对象字段:**

| 字段 | 类型 | 说明 |
|------|------|------|
| max_results | int | 最大返回结果数（默认20） |
| price_range | [min, max] | 价格范围 |
| categories | string[] | 药品分类过滤 |
| min_effectiveness | float | 最小药物效能（0-1） |

**响应示例:**

```json
{
  "success": true,
  "results": [
    {
      "drug_id": 1,
      "drug_name": "感冒灵",
      "category": "感冒用药",
      "matched_symptoms": ["头痛", "发热"],
      "match_ratio": 1.0,
      "effectiveness": 0.85,
      "price": 12.5,
      "confidence_score": 0.78
    },
    {
      "drug_id": 4,
      "drug_name": "退烧药",
      "category": "退烧用药",
      "matched_symptoms": ["发热"],
      "match_ratio": 0.5,
      "effectiveness": 0.95,
      "price": 3.5,
      "confidence_score": 0.65
    }
  ],
  "confidence_scores": {
    "1": 0.78,
    "4": 0.65
  },
  "total_count": 2,
  "request_id": "req_20240520_001",
  "execution_time": 0.234,
  "timestamp": "2024-05-20T10:30:00Z"
}
```

**置信度分数计算逻辑:**

分数 = 症状匹配度 × 0.5 + 药物效能 × 0.3 + 价格优势 × 0.2

- 症状匹配度：命中症状数 / 总症状数
- 药物效能：药品本身的效能评分（0-1）
- 价格优势：(100 - 价格) / 100

---

### 4. 批量筛选查询

**端点:** `POST /api/screening/batch`

**描述:** 一次性执行多个筛选查询

**请求体:**

```json
{
  "queries": [
    {
      "symptoms": ["头痛"],
      "patient_info": {"age": 35}
    },
    {
      "symptoms": ["腹泻", "腹痛"],
      "filters": {"max_results": 10}
    }
  ],
  "batch_id": "batch_20240520_001"  // 可选
}
```

**请求参数说明:**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| queries | object[] | ✓ | 查询列表 |
| batch_id | string | ✗ | 批处理ID（用于追踪） |

**响应示例:**

```json
{
  "success": true,
  "data": {
    "batch_id": "batch_20240520_001",
    "total_queries": 2,
    "successful_queries": 2,
    "failed_queries": 0,
    "results": [
      { /* 第一个查询结果，同screening/query */ },
      { /* 第二个查询结果，同screening/query */ }
    ],
    "errors": [],
    "timestamp": "2024-05-20T10:30:00Z"
  }
}
```

---

## ⚙️ 配置管理接口

### 5. 获取筛选配置

**端点:** `GET /api/screening/config`

**描述:** 获取当前活跃的筛选系统配置

**查询参数:**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| config_name | string | ✗ | 配置名称（默认'default'） |

**请求示例:**

```
GET /api/screening/config?config_name=default
```

**响应示例:**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "config_name": "default",
    "description": "默认筛选配置",
    "algorithm_type": "similarity",
    "confidence_threshold": 0.5,
    "max_results": 20,
    "min_symptom_match_rate": 0.3,
    "enable_synonym_expansion": true,
    "enable_llm_synonym": false,
    "max_synonym_attempts": 3,
    "enable_cache": true,
    "cache_ttl": 3600,
    "cache_strategy": "lru",
    "timeout_seconds": 5.0,
    "batch_max_size": 100,
    "is_active": true,
    "version": 1,
    "created_at": "2024-05-20T08:00:00Z",
    "updated_at": "2024-05-20T10:00:00Z"
  }
}
```

**配置字段说明:**

| 字段 | 类型 | 说明 |
|------|------|------|
| algorithm_type | string | 匹配算法（similarity/ml/hybrid） |
| confidence_threshold | float | 置信度阈值（0-1） |
| max_results | int | 最大返回结果数 |
| enable_synonym_expansion | bool | 是否启用同义词扩展 |
| enable_llm_synonym | bool | 是否启用LLM同义词 |
| cache_ttl | int | 缓存时间（秒） |
| cache_strategy | string | 缓存策略（lru/lfu/fifo） |
| timeout_seconds | float | 查询超时时间（秒） |
| batch_max_size | int | 批处理最大查询数 |

---

### 6. 更新筛选配置

**端点:** `PUT /api/screening/config`

**描述:** 更新筛选系统配置（需要管理员权限）

**请求体:**

```json
{
  "config_name": "default",
  "confidence_threshold": 0.6,
  "max_results": 25,
  "enable_llm_synonym": true,
  "cache_ttl": 7200
}
```

**权限要求:** 仅管理员和配置管理员可更新

**响应示例:**

```json
{
  "success": true,
  "config": { /* 更新后的完整配置 */ },
  "message": "配置 default 更新成功"
}
```

**错误示例:**

```json
{
  "success": false,
  "error": "置信度阈值必须在0-1之间",
  "error_code": "INVALID_CONFIG_VALUE"
}
```

---

## 📜 历史管理接口

### 7. 获取筛选历史

**端点:** `GET /api/screening/history`

**描述:** 获取用户的筛选查询历史记录

**查询参数:**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| user_id | int | ✓ | 用户ID |
| limit | int | ✗ | 返回数量（默认20，最大100） |
| offset | int | ✗ | 分页偏移（默认0） |
| start_date | string | ✗ | 开始日期（ISO 8601格式） |
| end_date | string | ✗ | 结束日期（ISO 8601格式） |

**请求示例:**

```
GET /api/screening/history?user_id=123&limit=20&offset=0&start_date=2024-05-01&end_date=2024-05-31
```

**响应示例:**

```json
{
  "success": true,
  "user_id": 123,
  "total": 50,
  "limit": 20,
  "offset": 0,
  "count": 20,
  "history": [
    {
      "id": 1001,
      "user_id": 123,
      "input_symptoms": ["头痛", "发热"],
      "result_count": 2,
      "result_drugs": [
        {"id": 1, "name": "感冒灵"},
        {"id": 4, "name": "退烧药"}
      ],
      "confidence_scores": {"1": 0.78, "4": 0.65},
      "execution_time": 0.234,
      "status": "success",
      "request_id": "req_20240520_001",
      "created_at": "2024-05-20T10:30:00Z"
    },
    {
      "id": 1000,
      "user_id": 123,
      "input_symptoms": ["腹泻"],
      "result_count": 1,
      "result_drugs": [{"id": 3, "name": "止泻药"}],
      "confidence_scores": {"3": 0.85},
      "execution_time": 0.156,
      "status": "success",
      "request_id": "req_20240520_000",
      "created_at": "2024-05-19T15:20:00Z"
    }
  ],
  "timestamp": "2024-05-20T10:35:00Z"
}
```

---

### 8. 获取历史详情

**端点:** `GET /api/screening/history/{id}`

**描述:** 获取单条历史记录的详细信息

**路径参数:**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | int | ✓ | 历史记录ID |

**请求示例:**

```
GET /api/screening/history/1001
```

**响应示例:**

```json
{
  "success": true,
  "detail": {
    "id": 1001,
    "user_id": 123,
    "input_symptoms": ["头痛", "发热"],
    "input_text": "我头疼，并且发烧了",
    "patient_info": {
      "age": 35,
      "gender": "M"
    },
    "filters": {
      "max_results": 20
    },
    "result_drugs": [
      {
        "drug_id": 1,
        "drug_name": "感冒灵",
        "category": "感冒用药",
        "price": 12.5,
        "effectiveness": 0.85
      },
      {
        "drug_id": 4,
        "drug_name": "退烧药",
        "category": "退烧用药",
        "price": 3.5,
        "effectiveness": 0.95
      }
    ],
    "result_count": 2,
    "confidence_scores": {"1": 0.78, "4": 0.65},
    "execution_time": 0.234,
    "status": "success",
    "request_id": "req_20240520_001",
    "created_at": "2024-05-20T10:30:00Z"
  },
  "timestamp": "2024-05-20T10:35:00Z"
}
```

---

## 📊 状态监控接口

### 9. 获取服务状态

**端点:** `GET /api/screening/status`

**描述:** 获取筛选服务的运行状态和性能指标

**请求示例:**

```
GET /api/screening/status
```

**响应示例:**

```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "service_name": "ScreeningService",
    "version": "1.0.0",
    "timestamp": "2024-05-20T10:35:00Z",
    "metrics": {
      "available_drugs": 116,
      "cache_size": 256,
      "uptime_seconds": 86400,
      "total_queries_today": 1523,
      "average_response_time": 0.245,
      "p95_response_time": 0.512,
      "p99_response_time": 1.023,
      "error_rate": 0.02
    }
  }
}
```

**服务状态值:**

| 状态 | 含义 |
|------|------|
| healthy | 服务正常 |
| degraded | 服务性能下降 |
| unhealthy | 服务异常 |
| unavailable | 服务不可用 |

---

## 🔐 安全与认证

### JWT认证

所有需要认证的端点都需要在请求头中包含JWT Token：

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 权限控制

不同角色的权限：

| 操作 | 医生 | 药剂师 | 管理员 | 普通用户 |
|------|------|--------|--------|---------|
| 症状筛选 | ✓ | ✓ | ✓ | ✓ |
| 查看历史 | 仅自己 | ✓ | ✓ | 仅自己 |
| 更新配置 | ✗ | ✗ | ✓ | ✗ |
| 查看统计 | ✗ | ✓ | ✓ | ✗ |

---

## 🧪 测试示例

### cURL请求

```bash
# 1. 症状标准化
curl -X POST http://localhost:5000/api/screening/symptoms/standardize \\
  -H \"Content-Type: application/json\" \\
  -d '{\"symptoms\": [\"头疼\", \"发烧\"]}'

# 2. 获取同义词
curl -X GET 'http://localhost:5000/api/screening/symptoms/synonyms?symptom_name=头痛'

# 3. 执行筛选查询
curl -X POST http://localhost:5000/api/screening/query \\
  -H \"Content-Type: application/json\" \\
  -d '{\"symptoms\": [\"头痛\", \"发热\"], \"user_id\": 123}'

# 4. 获取历史
curl -X GET 'http://localhost:5000/api/screening/history?user_id=123&limit=10'

# 5. 获取服务状态
curl -X GET http://localhost:5000/api/screening/status
```

### Python请求示例

```python
import requests
import json

# 症状筛选查询
url = 'http://localhost:5000/api/screening/query'
payload = {
    'symptoms': ['头痛', '发热'],
    'patient_info': {'age': 35},
    'user_id': 123
}
headers = {
    'Content-Type': 'application/json'
}

response = requests.post(url, json=payload, headers=headers)
result = response.json()

if result['success']:
    print(f\"找到 {result['total_count']} 个药品推荐\")
    for drug in result['results']:
        print(f\"  - {drug['drug_name']}: 置信度 {drug['confidence_score']:.2%}\")
else:
    print(f\"错误: {result['error']}\")
```

---

## ⚠️ 错误处理

### 常见错误码

| 错误码 | HTTP状态 | 描述 |
|--------|----------|------|
| INVALID_SYMPTOM_LIST | 400 | 症状列表为空或格式错误 |
| SYMPTOM_NOT_FOUND | 404 | 指定的症状不存在 |
| INVALID_CONFIG_VALUE | 400 | 配置值超出允许范围 |
| CONFIG_NOT_FOUND | 404 | 指定的配置不存在 |
| HISTORY_NOT_FOUND | 404 | 指定的历史记录不存在 |
| UNAUTHORIZED | 401 | 未认证或认证过期 |
| FORBIDDEN | 403 | 没有权限执行此操作 |
| SERVICE_UNAVAILABLE | 503 | 服务不可用 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |

### 错误响应示例

```json
{
  "success": false,
  "error": "症状列表不能为空",
  "error_code": "INVALID_SYMPTOM_LIST",
  "message": "请提供至少一个症状",
  "timestamp": "2024-05-20T10:35:00Z"
}
```

---

## 📈 性能指标

### 响应时间要求

| 端点类型 | 目标响应时间 | P95 | P99 |
|----------|-------------|-----|-----|
| 症状标准化 | < 100ms | < 200ms | < 500ms |
| 单个筛选查询 | < 500ms | < 1s | < 2s |
| 批量筛选 | < 2s | < 5s | < 10s |
| 历史查询 | < 200ms | < 500ms | < 1s |
| 配置查询 | < 50ms | < 100ms | < 200ms |

### 吞吐量要求

- 症状筛选：≥ 100 req/s
- 批量筛选：≥ 10 batch/s
- 历史查询：≥ 200 req/s

---

## 📚 扩展阅读

- [数据库架构（组件1）](../按架构组件分工/智能药品管理系统架构组件接口清单.md#组件1数据库与基础架构开发)
- [药品管理API（组件2）](../按架构组件分工/智能药品管理系统架构组件接口清单.md#组件2药品管理api开发)
- [权限认证系统（组件4）](../按架构组件分工/智能药品管理系统架构组件接口清单.md#组件4权限认证系统开发)
- [前端界面（组件5）](../按架构组件分工/智能药品管理系统架构组件接口清单.md#组件5前端界面开发)

---

**文档版本:** 1.0  
**最后更新:** 2024-05-20  
**作者:** 组件3开发团队
