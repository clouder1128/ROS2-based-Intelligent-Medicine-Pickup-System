# P1医疗助手系统

![Python 3.12](https://img.shields.io/badge/Python-3.12-blue)
![LLM Support](https://img.shields.io/badge/LLM-Claude%2FOpenAI%2FDeepSeek-green)

基于大型语言模型的智能医疗助手，提供症状分析、药品推荐、剂量计算等医疗咨询服务，与智能药房后端集成实现完整的电子审批工作流。

## 📖 目录
- [项目简介](#项目简介)
- [核心特性](#核心特性)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [API使用示例](#api使用示例)
- [配置指南](#配置指南)
- [测试说明](#测试说明)

## 🧪 项目简介

P1医疗助手是一个模块化的AI医疗咨询系统，基于LLM技术为医护人员和患者提供专业的用药建议。系统支持多种LLM提供商，包含完整的工具调用系统和工作流管理，与智能药房后端紧密集成。

**主要功能**：
- 症状分析和药品推荐
- 剂量计算和过敏检查
- 电子审批流程集成
- 多轮对话和会话管理

## ⚡ 核心特性

### 智能医疗咨询
- **专业工作流**：症状收集 → 药物查询 → 过敏检查 → 剂量计算 → 建议生成 → 医生审批
- **多LLM支持**：Claude、OpenAI、DeepSeek等主流LLM API
- **工具调用系统**：标准化工具接口，支持异步/同步执行

### 系统管理
- **模块化架构**：清晰的模块分离，便于维护和扩展
- **状态管理**：会话状态保存/恢复，工作流状态跟踪
- **内存管理**：对话历史压缩和持久化

### 后端集成
- **药房API集成**：实时药品查询和库存管理
- **审批流程**：与后端审批系统无缝对接
- **测试覆盖**：完整的单元测试和集成测试套件

## 🏗️ 系统架构

```
用户输入
    │
    ▼
┌─────────────────┐
│  MedicalAgent   │ ← 核心协调器
├─────────────────┤
│  • 消息管理器   │ ← 对话历史管理
│  • LLM客户端    │ ← 多提供商支持
│  • 工具执行器   │ ← 标准化工具调用
│  • 工作流管理器 │ ← 状态跟踪
└────────┬────────┘
         │
         ▼
   工具调用结果
         │
         ▼
   生成医疗建议
         │
         ▼
   后端API集成
         │
         ▼
   用户回复/审批提交
```

**核心模块**：
1. **MedicalAgent** - 主协调器，管理整个咨询流程
2. **LLM客户端** - 统一接口支持多种LLM提供商
3. **工具系统** - 标准化工具调用和执行
4. **消息管理** - 对话历史压缩和持久化
5. **工作流管理** - 患者状态跟踪和工作流程控制

## 🚀 快速开始

### 环境要求
- Python 3.8+
- LLM API密钥（DeepSeek/Claude/OpenAI）
- 智能药房后端运行（端口8001）

### 安装步骤
```bash
# 1. 进入P1目录
cd P1

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑.env文件，设置API密钥和PHARMACY_BASE_URL

# 4. 测试连接
python -c "from services.pharmacy_client import health_check; print(health_check())"
```

### 启动方式

#### 医生CLI（推荐）
```bash
python cli/doctor_cli.py
```

#### 患者CLI
```bash
python cli/patient_cli.py
```

#### 简单交互模式
```bash
python cli/interactive.py
```

#### 程序化使用
```python
from core.agent import MedicalAgent

agent = MedicalAgent()
response, steps = agent.run("患者头痛，请推荐药物", patient_id="patient_123")
print(f"回复: {response}")
```

## 📁 项目结构

```
P1/
├── core/                    # 核心模块
│   ├── agent.py            # MedicalAgent主类
│   ├── workflows.py        # 工作流管理器
│   ├── config.py           # 配置管理
│   └── exceptions.py       # 异常定义
│
├── llm/                    # LLM客户端
│   ├── client.py           # 统一LLM客户端
│   ├── schemas.py          # 数据模型
│   └── providers/          # LLM提供商实现
│       ├── claude.py       # Claude/DeepSeek提供商
│       └── openai.py       # OpenAI提供商
│
├── tools/                  # 工具系统
│   ├── registry.py         # 工具注册表
│   ├── base.py             # 工具基类
│   ├── medical.py          # 医疗工具
│   ├── inventory.py        # 库存工具
│   └── report_generator.py # 报告生成工具
│
├── memory/                 # 消息管理
│   ├── manager.py          # 消息管理器
│   └── compressor.py       # 消息压缩器
│
├── services/               # 服务模块
│   └── pharmacy_client.py  # 后端HTTP客户端
│
├── cli/                    # 命令行界面
│   ├── doctor_cli.py       # 医生CLI
│   ├── patient_cli.py      # 患者CLI
│   ├── interactive.py      # 交互式界面
│   └── cli.py              # 功能完整CLI
│
├── utils/                  # 工具函数
│   ├── http_client.py      # HTTP客户端
│   ├── json_tools.py       # JSON处理
│   ├── text_utils.py       # 文本处理
│   ├── validation.py       # 验证工具
│   └── retry.py            # 重试机制
│
└── tests/                  # 测试套件
    ├── test_core.py        # Agent核心测试
    ├── test_llm.py         # LLM测试
    ├── test_tools.py       # 工具测试
    └── integration/        # 集成测试
```

## 📚 API使用示例

### 基本医疗咨询
```python
from core.agent import MedicalAgent

# 创建医疗助手
agent = MedicalAgent()

# 简单症状咨询
response, steps = agent.run("患者头痛、发烧，需要用药建议")
print(f"回复: {response}")

# 查看执行步骤
for step in steps:
    print(f"步骤: {step['step']} - {step['type']}")
```

### 多轮对话
```python
agent = MedicalAgent()

# 第一轮：症状描述
response1, _ = agent.run("我头痛、流鼻涕")

# 第二轮：提供过敏信息
response2, _ = agent.run("我对青霉素过敏")

# 第三轮：询问具体药物
response3, _ = agent.run("可以吃什么药？")

# 保存会话状态
agent.save_state("./sessions/current_patient.session")
```

### 工具调用监控
```python
def log_tool_calls(steps):
    """记录工具调用详情"""
    tool_calls = [s for s in steps if s['type'] == 'tool_call']
    for tc in tool_calls:
        print(f"工具: {tc['tool']}")
        print(f"输入: {tc.get('input', {})}")
        print(f"结果: {tc.get('result', '无结果')[:100]}...")

response, steps = agent.run("患者头痛，请推荐药物")
log_tool_calls(steps)
```

### 工作流状态查询
```python
# 获取患者工作流状态
state = agent.get_workflow_state("patient_123")
print(f"当前步骤: {state['current_step']}")
print(f"历史记录: {state['history']}")

# 获取所有工作流统计
stats = agent.get_workflow_stats()
print(f"总患者数: {stats['total_patients']}")
print(f"平均步骤数: {stats['avg_steps']}")
```

## 🔧 配置指南

### 环境变量配置
```bash
# LLM提供商配置
LLM_PROVIDER=claude                    # claude或openai
ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic  # DeepSeek API地址
ANTHROPIC_AUTH_TOKEN=sk-your-api-key  # API密钥

# 后端集成配置
PHARMACY_BASE_URL=http://localhost:8001 # 智能药房后端地址

# 系统配置
LOG_LEVEL=INFO                         # 日志级别
MAX_HISTORY_LEN=20                     # 最大对话历史长度
MAX_ITERATIONS=10                      # 最大工具调用迭代次数
SESSION_STATE_DIR=./sessions           # 会话状态保存目录
```

### 支持的LLM提供商

#### 1. DeepSeek（推荐，兼容Anthropic API）
```bash
export LLM_PROVIDER=claude
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="sk-your-deepseek-api-key"
export ANTHROPIC_MODEL="deepseek-chat"
```

#### 2. Anthropic Claude
```bash
export LLM_PROVIDER=claude
export ANTHROPIC_API_KEY="sk-ant-api03-..."
export ANTHROPIC_MODEL="claude-3-sonnet-20240229"
```

#### 3. OpenAI
```bash
export LLM_PROVIDER=openai
export OPENAI_API_KEY="sk-proj-..."
export LLM_MODEL="gpt-4-turbo-preview"
```

### 配置验证
```python
from core.config import Config

try:
    Config.validate()
    print("配置验证通过")
    print(Config.to_dict())  # 查看配置摘要（不包含敏感信息）
except Exception as e:
    print(f"配置验证失败: {e}")
```

## 🧪 测试说明

### 测试运行
```bash
# 运行所有测试（单元测试）
cd P1 && pytest tests/

# 运行集成测试（需要后端运行）
export PHARMACY_BASE_URL=http://localhost:8001
RUN_INTEGRATION_TESTS=1 pytest tests/integration/

# 运行特定测试模块
pytest tests/test_core.py -v        # Agent核心测试
pytest tests/test_llm.py -v         # LLM测试
pytest tests/test_tools.py -v       # 工具测试
```

### 测试覆盖率
```bash
# 生成覆盖率报告
pytest tests/ --cov=. --cov-report=html

# 查看覆盖率摘要
pytest tests/ --cov=. --cov-report=term-missing
```

### 测试策略
- **单元测试**：测试单个函数或类（tools、utils、llm模块）
- **集成测试**：测试模块间交互（Agent完整流程测试）
- **端到端测试**：测试完整API调用（需要后端服务）

## 🔄 开发工作流

### 日常开发
```bash
# 设置开发环境
export PHARMACY_BASE_URL=http://localhost:8001
export LOG_LEVEL=DEBUG

# 运行测试确保功能正常
pytest tests/

# 启动交互式CLI进行测试
python cli/doctor_cli.py
```

### 代码规范
- 遵循PEP 8编码规范
- 使用类型注解提高代码可读性
- 为公共API添加docstring文档
- 保持模块单一职责原则

### 调试技巧
```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 查看LLM调用统计
from llm.client import LLMClient
print("LLM统计:", LLMClient.get_stats())

# 调试工具调用
from tools.registry import TOOLS
print("可用工具:", list(TOOLS.keys()))
```

---

*最后更新：2026年4月15日*  
*项目状态：开发中 - 核心功能已实现，测试覆盖完整*