# P1医疗用药助手Agent系统

## 概述

P1医疗用药助手是一个基于大型语言模型的智能医疗助手系统，专门设计用于帮助医护人员和患者进行用药咨询、药物查询、剂量计算和用药建议生成。系统采用模块化架构，支持多种LLM提供商（Claude、OpenAI、DeepSeek等），并遵循严格的医疗工作流程。

**核心特性：**
- 🏥 **专业医疗工作流程**：严格遵循症状收集→药物查询→过敏检查→剂量计算→建议生成→医生审批流程
- 🔧 **模块化架构**：清晰的模块分离，便于维护和扩展
- 🤖 **多LLM提供商支持**：支持Claude、OpenAI、DeepSeek等主流LLM API
- 🛠️ **工具调用系统**：标准化工具调用接口，支持异步/同步执行
- 💾 **状态管理**：支持会话状态保存和恢复，工作流状态跟踪
- 🧪 **完整测试覆盖**：包含98个测试用例，确保系统稳定性
- 🔌 **可扩展性**：预留P3子代理集成接口，支持未来功能扩展

## 系统架构

### 模块结构

```
P1/
├── core/                    # 核心Agent和工作流管理
│   ├── agent.py            # MedicalAgent主类
│   ├── workflows.py        # 工作流管理器
│   └── __init__.py
├── llm/                    # LLM客户端和提供商
│   ├── client.py           # 统一LLM客户端
│   ├── providers/          # LLM提供商实现
│   │   ├── claude.py       # Claude/DeepSeek提供商
│   │   ├── openai.py       # OpenAI提供商
│   │   └── __init__.py
│   ├── schemas.py          # 数据模型
│   └── __init__.py
├── memory/                 # 消息和记忆管理
│   ├── manager.py          # 消息管理器
│   ├── compressor.py       # 消息压缩器
│   └── __init__.py
├── tools/                  # 工具系统
│   ├── base.py            # 工具基类
│   ├── executor.py        # 工具执行器
│   ├── registry.py        # 工具注册表
│   ├── inventory.py       # 库存管理工具
│   ├── medical.py         # 医疗工具
│   ├── report_generator.py # 报告生成工具
│   └── __init__.py
├── session/               # 会话管理
│   ├── manager.py         # 会话管理器
│   └── __init__.py
├── utils/                 # 工具函数
│   ├── http_client.py     # HTTP客户端工具
│   ├── json_tools.py      # JSON处理工具
│   ├── text_utils.py      # 文本处理工具
│   ├── validation.py      # 验证工具
│   ├── retry.py           # 重试机制
│   └── __init__.py
├── tests/                 # 测试套件
│   ├── conftest.py        # pytest配置
│   ├── integration/       # 集成测试目录
│   │   ├── test_backend_integration.py
│   │   └── test_mocked_integration.py
│   ├── test_core.py       # Agent核心测试（原test_agent.py）
│   ├── test_drug_db_simple.py    # 药品数据库简单测试
│   ├── test_drug_db_integration.py # 药品数据库集成测试
│   ├── test_http_client.py        # HTTP客户端测试
│   ├── test_inventory_integration.py # 库存集成测试
│   ├── test_llm.py        # LLM测试
│   ├── test_medical_integration.py # 医疗集成测试
│   ├── test_memory.py     # 内存测试
│   ├── test_session.py    # 会话管理测试
│   ├── test_tools.py      # 工具测试
│   └── test_utils.py      # 工具函数测试
├── sessions/              # 会话状态保存目录（自动创建）
├── cli.py                # 功能完整的交互式命令行界面
├── interactive.py        # 简单交互式命令行界面
├── example_usage.py      # 使用示例脚本
├── example_http_client.py # HTTP客户端示例
├── drug_db.py           # 药品数据库接口（HTTP客户端）
├── config.py             # 全局配置
├── exceptions.py         # 异常定义
├── run_tests.py         # 测试运行器（解决pytest插件冲突）
├── requirements.txt      # 依赖管理
├── pytest.ini           # pytest配置
├── .env.example         # 环境变量示例
├── DEEPSEEK_CONFIG.md   # DeepSeek API配置指南
├── test_deepseek_direct.py       # DeepSeek直接连接测试
└── test_deepseek_integration.py  # DeepSeek集成测试
```

### 数据流和工作流程

```
用户输入 → MedicalAgent → 症状提取(P3) → LLM处理 → 工具调用 → 结果处理 → 回复用户
      ↑                                                                  |
      └─────────── 状态保存/恢复 ←─ 工作流跟踪 ←─ 工具执行结果 ←────────┘
```

**关键流程：**
1. **症状收集**：从用户输入中提取结构化症状信息（P3集成）
2. **药物查询**：通过query_drug工具查询相关药物
3. **过敏检查**：使用check_allergy工具验证患者过敏情况
4. **剂量计算**：根据年龄、体重计算合适剂量
5. **建议生成**：生成结构化用药建议
6. **医生审批**：提交给医生审批系统
7. **处方配药**：系统自动完成配药（需医生审批通过）

## 快速开始

### 环境要求

- Python 3.8+
- pip 20.0+

### 安装步骤

1. **克隆项目或进入P1目录**
   ```bash
   cd /path/to/P1
   ```

2. **创建虚拟环境（推荐）**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   venv\Scripts\activate  # Windows
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   
   # 根据选择的LLM提供商安装额外依赖
   pip install anthropic     # 如果使用Claude/DeepSeek
   # 或
   pip install openai        # 如果使用OpenAI
   ```

4. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑.env文件，设置您的API密钥和配置
   ```

### 基本使用示例

```python
from core.agent import MedicalAgent

# 创建医疗助手Agent
agent = MedicalAgent()

# 运行对话
response, steps = agent.run("患者头痛，请推荐药物")
print(f"助手回复: {response}")
print(f"执行步骤: {len(steps)}步")

# 查看工作流状态
workflow_state = agent.get_workflow_state()
print(f"工作流状态: {workflow_state}")

# 保存会话状态
agent.save_state("./sessions/patient_123.session")

# 重置会话（开始新对话）
agent.reset()
```

### 交互式示例脚本

我们还提供了一个交互式的示例脚本，演示系统的各种功能：

```bash
# 运行示例脚本
python example_usage.py

# 脚本提供以下演示选项：
# 1. 配置检查 - 验证环境变量和配置
# 2. LLM客户端演示 - 测试LLM连接
# 3. 完整MedicalAgent演示 - 完整的医疗咨询流程
# 4. 全部演示 - 运行所有演示
```

脚本会引导您逐步了解系统的各项功能，适合初次使用者。

### 交互式命令行界面

项目现在提供了两个交互式命令行界面，支持多轮对话：

#### 1. 功能完整的CLI (`cli.py`)

```bash
# 启动交互式CLI
python cli.py [患者ID] [--save-dir ./sessions]

# 示例
python cli.py patient_123
python cli.py --save-dir ./my_sessions
```

**主要功能：**
- 🗣️ **多轮对话**：持续与医疗助手对话
- 📝 **命令系统**：支持特殊命令（输入 `/help` 查看）
- 💾 **会话管理**：保存/加载会话状态
- 📊 **状态查询**：查看工作流状态、统计信息
- 🆔 **患者管理**：切换患者ID

**可用命令：**
- `/help` - 显示帮助信息
- `/reset` - 重置当前会话
- `/save [文件名]` - 保存会话状态
- `/load <文件名>` - 加载会话状态
- `/status` - 显示当前会话状态
- `/workflow` - 显示工作流状态
- `/stats` - 显示统计信息
- `/patient [新ID]` - 查看或更改患者ID
- `/exit` 或 `/quit` - 退出程序

#### 2. 简单交互模式 (`interactive.py`)

```bash
# 启动简单交互模式
python interactive.py [患者ID] [--verbose]

# 示例
python interactive.py
python interactive.py patient_456 --verbose
```

**特点：**
- 🚀 **快速启动**：简化的交互界面
- 🎯 **轻量级**：适合快速测试和对话
- 📋 **基本命令**：支持 `/reset`, `/exit`, `/help`

**使用示例：**
```bash
$ python interactive.py
P1医疗用药助手 - 简单交互模式
============================================================
输入您的症状或问题，Agent会进行处理
输入 '/reset' 重置对话
输入 '/exit' 或按 Ctrl+C 退出
============================================================

患者ID: default_patient
MedicalAgent已初始化，开始对话...

您: 患者头痛，需要用药建议
[处理中...]
助手: 请告诉我患者的年龄、体重和是否有药物过敏史...
```

#### 3. 直接使用MedicalAgent

对于程序化使用，可以直接调用MedicalAgent：

```python
from core.agent import MedicalAgent

agent = MedicalAgent()
response, steps = agent.run("患者头痛", patient_id="patient_123")
```

### 运行测试

```bash
# 运行所有测试（单元测试）
python run_tests.py

# 运行集成测试（需要后端运行）
python run_tests.py --integration

# 仅运行单元测试
python run_tests.py --unit

# 或直接使用pytest
pytest tests/ -v

# 运行特定测试模块
pytest tests/test_core.py -v  # Agent核心测试（原test_agent.py）
```

## 配置指南

### 环境变量配置

创建`.env`文件并设置以下变量：

```bash
# ==================== LLM配置 ====================
# LLM提供商：claude 或 openai
LLM_PROVIDER=claude

# DeepSeek API配置（兼容Anthropic API）
ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
ANTHROPIC_AUTH_TOKEN=sk-your-deepseek-api-key-here
ANTHROPIC_MODEL=deepseek-chat

# 传统Anthropic API配置（如果使用官方Anthropic API）
# ANTHROPIC_API_KEY=sk-ant-api03-...

# OpenAI API配置（如果使用OpenAI）
# OPENAI_API_KEY=sk-proj-...

# LLM参数
LLM_MAX_TOKENS=4096
LLM_TEMPERATURE=0.3

# ==================== 系统配置 ====================
# 药房API基础URL（P2模块）
PHARMACY_BASE_URL=http://localhost:8001

# 数据库连接
DATABASE_URL=sqlite:///./medical_assistant.db

# 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# 对话历史最大长度
MAX_HISTORY_LEN=20

# 最大迭代次数（工具调用循环）
MAX_ITERATIONS=10

# 会话状态保存目录
SESSION_STATE_DIR=./sessions

# ==================== 高级配置 ====================
# 启用异步处理（实验性）
ENABLE_ASYNC=false

# 最大并发会话数
MAX_CONCURRENT_SESSIONS=100

# API请求超时（秒）
REQUEST_TIMEOUT=30
```

### 支持的LLM提供商

#### 1. DeepSeek（推荐，兼容Anthropic API）
```bash
export LLM_PROVIDER=claude
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="sk-your-deepseek-api-key"
export ANTHROPIC_MODEL="deepseek-chat"
```

详细配置见：[DEEPSEEK_CONFIG.md](DEEPSEEK_CONFIG.md)

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

系统启动时会自动验证配置：
```python
from config import Config

# 手动验证配置
try:
    Config.validate()
    print("配置验证通过")
    
    # 查看配置摘要（不包含敏感信息）
    print(Config.to_dict())
except Exception as e:
    print(f"配置验证失败: {e}")
```

## 核心组件详解

### 1. MedicalAgent（核心代理）

MedicalAgent是系统的核心，负责协调所有组件：

```python
from core.agent import MedicalAgent

agent = MedicalAgent(
    llm_client=None,           # 可传入自定义LLM客户端
    message_manager=None       # 可传入自定义消息管理器
)

# 主要方法
response, steps = agent.run("患者症状", patient_id="123")

# 状态管理
agent.save_state("session.pkl")
agent.load_state("session.pkl")
agent.reset()  # 重置会话

# 工作流查询
state = agent.get_workflow_state("patient_123")
all_workflows = agent.get_all_workflows()
stats = agent.get_workflow_stats()
```

### 2. LLM客户端系统

统一LLM客户端支持多种提供商：

```python
from llm.client import LLMClient
from llm.schemas import LLMMessage

# 创建客户端
client = LLMClient()  # 使用Config中的配置
# 或指定提供商
client = LLMClient(provider="claude")

# 发送消息
messages = [
    {"role": "user", "content": "你好"}
]
response = client.chat(messages=messages, tools=tools_list)

# 查看统计
stats = LLMClient.get_stats()  # 请求次数、token估算
LLMClient.reset_stats()        # 重置统计
```

### 3. 工具系统

工具系统提供标准化接口：

```python
from tools.registry import TOOLS, execute_tool, register_tool
from tools.base import BaseTool

# 定义新工具
class MyTool(BaseTool):
    name = "my_tool"
    description = "工具描述"
    input_schema = {
        "type": "object",
        "properties": {
            "param": {"type": "string"}
        },
        "required": ["param"]
    }
    
    def execute(self, **kwargs):
        return {"result": f"处理参数: {kwargs['param']}"}

# 注册工具
register_tool(MyTool)

# 执行工具
result = execute_tool("my_tool", {"param": "value"})
```

### 4. 消息管理器

管理对话历史和消息压缩：

```python
from memory.manager import MessageManager

manager = MessageManager(
    system_prompt="系统提示",
    max_len=20,          # 最大历史长度
    compressor=None      # 自定义压缩器
)

# 添加消息
manager.add_message("user", "患者头痛")
manager.add_message("assistant", "建议服用...")
manager.add_tool_result("tool_id", "工具执行结果")

# 获取消息
messages = manager.get_full_messages()    # 完整消息
compressed = manager.get_messages()       # 压缩后消息

# 管理
manager.reset()                          # 重置（保留系统提示）
manager.trim_history()                   # 修剪历史
```

### 5. 工作流管理器

跟踪患者状态和工作流程：

```python
from core.workflows import WorkflowManager, WorkflowStep

workflow = WorkflowManager()

# 创建工作流
workflow.create_workflow("patient_123")

# 更新步骤
workflow.update_workflow_step(
    patient_id="patient_123",
    step=WorkflowStep.QUERY_DRUG,
    data={"drug": "布洛芬"}
)

# 查询状态
state = workflow.get_workflow("patient_123")
all_states = workflow.get_all_workflows()
stats = workflow.get_stats()
```

## API使用示例

### 基本医疗咨询

```python
from core.agent import MedicalAgent

agent = MedicalAgent()

# 简单症状咨询
response, steps = agent.run("患者头痛、发烧，需要用药建议")
print(f"回复: {response}")

# 查看执行详情
for step in steps:
    print(f"步骤 {step['step']}: {step['type']} - {step.get('tool', step.get('content', ''))[:50]}...")
```

### 多轮对话

```python
agent = MedicalAgent()

# 第一轮：症状描述
response1, _ = agent.run("我头痛、流鼻涕")

# 第二轮：提供更多信息
response2, _ = agent.run("我对青霉素过敏")

# 第三轮：询问具体药物
response3, _ = agent.run("可以吃什么药？")

# 保存会话状态
agent.save_state("./sessions/current_patient.session")
```

### 批量处理患者

```python
from core.agent import MedicalAgent

patients = [
    {"id": "p001", "symptom": "头痛"},
    {"id": "p002", "symptom": "咳嗽"},
    {"id": "p003", "symptom": "发烧"}
]

for patient in patients:
    agent = MedicalAgent()
    response, steps = agent.run(
        f"患者症状：{patient['symptom']}",
        patient_id=patient['id']
    )
    
    # 记录工作流状态
    state = agent.get_workflow_state(patient['id'])
    print(f"患者 {patient['id']} 处理完成，状态: {state['current_step']}")
    
    # 保存会话
    agent.save_state(f"./sessions/{patient['id']}.session")
```

### 工具调用监控

```python
from core.agent import MedicalAgent
import json

agent = MedicalAgent()

def log_tool_calls(steps):
    """记录工具调用详情"""
    tool_calls = [s for s in steps if s['type'] == 'tool_call']
    for tc in tool_calls:
        print(f"工具: {tc['tool']}")
        print(f"输入: {tc.get('input', {})}")
        print(f"结果: {tc.get('result', '无结果')[:100]}...")
        print(f"耗时: {tc['duration_ms']}ms")
        print("-" * 50)

response, steps = agent.run("患者头痛，请推荐药物")
log_tool_calls(steps)
```

## 高级功能

### 异步处理

系统支持异步工具调用（实验性功能）：

```python
from config import Config

# 启用异步模式
os.environ["ENABLE_ASYNC"] = "true"

# 异步执行
import asyncio
from core.agent import MedicalAgent

async def async_demo():
    agent = MedicalAgent()
    # 注意：run方法目前是同步的，异步支持在工具层面
    response, steps = agent.run("患者症状")
    return response

# 运行异步函数
response = asyncio.run(async_demo())
```

### 自定义LLM提供商

实现自定义LLM提供商：

```python
from llm.schemas import LLMMessage, LLMResponse
from exceptions import LLMError

class CustomProvider:
    def __init__(self, api_key: str, model: str, **kwargs):
        self.api_key = api_key
        self.model = model
        # 初始化客户端
        
    def chat(self, messages: List[LLMMessage], tools=None, temperature=None, max_tokens=None) -> LLMResponse:
        # 实现聊天接口
        # 返回LLMResponse对象
        pass

# 在client.py中集成自定义提供商
```

### 消息压缩策略

自定义消息压缩策略：

```python
from memory.compressor import MessageCompressor

class CustomCompressor(MessageCompressor):
    def compress(self, messages: List[Dict]) -> List[Dict]:
        """自定义压缩逻辑"""
        # 实现压缩算法
        return compressed_messages

# 使用自定义压缩器
from memory.manager import MessageManager
manager = MessageManager(compressor=CustomCompressor())
```

## 测试和开发

### 测试套件

项目包含完整的测试套件：

```bash
# 运行所有测试（98个测试用例）
python run_tests.py

# 测试覆盖率报告
pytest tests/ --cov=. --cov-report=html

# 运行特定测试类别
pytest tests/test_agent.py -v       # Agent测试
pytest tests/test_llm.py -v         # LLM测试
pytest tests/test_tools.py -v       # 工具测试
pytest tests/test_memory.py -v      # 内存测试
```

### 开发指南

1. **代码规范**
   - 使用Black进行代码格式化：`black .`
   - 使用Flake8进行代码检查：`flake8 .`
   - 使用MyPy进行类型检查：`mypy .`

2. **添加新功能**
   - 新工具：继承`BaseTool`，在`tools/`目录实现
   - 新LLM提供商：在`llm/providers/`目录实现
   - 新工具函数：在`utils/`目录添加

3. **测试新功能**
   - 为每个新功能添加测试用例
   - 确保测试覆盖率不降低
   - 运行完整测试套件验证

### 调试技巧

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 查看配置
from config import Config
print("配置:", Config.to_dict())

# 监控LLM调用
from llm.client import LLMClient
print("LLM统计:", LLMClient.get_stats())

# 调试工具调用
from tools.registry import TOOLS
print("可用工具:", list(TOOLS.keys()))
```

## 故障排除

### 常见问题

1. **LLM API连接失败**
   ```
   错误：Claude API error: 401
   解决：检查API密钥是否正确，是否有访问权限
   ```

2. **工具调用失败**
   ```
   错误：Tool execution error: Tool not found
   解决：确保工具已正确注册在tools/registry.py中
   ```

3. **测试运行失败**
   ```
   错误：pytest插件冲突
   解决：使用python run_tests.py替代直接pytest命令
   ```

4. **内存不足**
   ```
   错误：MemoryError or excessive token usage
   解决：调整MAX_HISTORY_LEN，启用消息压缩
   ```

### 调试步骤

1. **验证配置**
   ```python
   python -c "from config import Config; Config.validate(); print('OK')"
   ```

2. **测试LLM连接**
   ```python
   python test_deepseek_direct.py  # 或对应提供商测试
   ```

3. **检查工具注册**
   ```python
   python -c "from tools.registry import TOOLS; print('Tools:', list(TOOLS.keys()))"
   ```

4. **运行基础测试**
   ```bash
   python run_tests.py --simple
   ```

### 获取帮助

1. **查看日志**
   ```bash
   export LOG_LEVEL=DEBUG
   python your_script.py
   ```

2. **检查环境变量**
   ```bash
   printenv | grep -E "(ANTHROPIC|OPENAI|LLM)"
   ```

3. **验证依赖**
   ```bash
   pip list | grep -E "(anthropic|openai|pytest)"
   ```

## 部署和生产

### 性能优化建议

1. **LLM配置优化**
   - 调整`LLM_TEMPERATURE`：降低随机性，提高一致性
   - 设置`LLM_MAX_TOKENS`：根据实际需要调整，减少token使用
   - 启用缓存：如果LLM提供商支持响应缓存

2. **系统配置优化**
   - 调整`MAX_ITERATIONS`：限制最大工具调用次数
   - 设置`MAX_HISTORY_LEN`：控制对话历史长度
   - 启用消息压缩：减少token使用

3. **资源管理**
   - 监控`LLMClient.get_stats()`：跟踪API使用情况
   - 设置`MAX_CONCURRENT_SESSIONS`：限制并发会话数
   - 配置`REQUEST_TIMEOUT`：设置合理的超时时间

### 安全注意事项

1. **API密钥安全**
   - 永远不要将API密钥提交到版本控制系统
   - 使用环境变量或密钥管理服务
   - 定期轮换API密钥

2. **患者数据保护**
   - 会话状态文件可能包含敏感信息，妥善保管
   - 考虑加密存储会话状态
   - 遵守相关医疗数据保护法规

3. **输入验证**
   - 所有用户输入都应经过验证
   - 工具调用参数需要严格验证
   - 防止注入攻击

### 监控和日志

建议的监控指标：
- LLM API调用次数和token使用量
- 工具调用成功率
- 平均响应时间
- 工作流完成率
- 错误率和异常类型

## 开发者指南

本部分为后续开发者提供深入的技术细节和扩展指南，帮助理解项目架构和进行定制开发。

### 开发环境设置

#### 1. 本地开发环境
```bash
# 1. 克隆项目
git clone <repository-url>
cd P1

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 3. 安装开发依赖
pip install -r requirements.txt
pip install anthropic  # 或 openai，根据使用的LLM提供商

# 4. 安装开发工具
pip install black flake8 mypy pytest-cov pytest-mock

# 5. 配置环境变量
cp .env.example .env
# 编辑.env文件设置API密钥
```

#### 2. IDE配置建议
- **VS Code**：安装Python扩展，配置格式化器为Black
- **PyCharm**：启用类型检查，配置代码样式
- **通用设置**：设置`.env`文件支持，启用自动导入

#### 3. 预提交检查
建议设置Git钩子或CI检查：
```bash
# 代码格式化
black .

# 代码检查
flake8 .

# 类型检查
mypy .

# 运行测试
python run_tests.py
```

### 项目架构深入理解

#### 1. 核心设计模式
- **Provider模式**：LLM提供商抽象，便于切换不同AI服务
- **工具调用模式**：标准化工具接口，支持异步/同步执行
- **工作流模式**：状态机跟踪患者咨询流程
- **消息管理**：对话历史压缩和持久化

#### 2. 关键数据流
```
用户输入 → MedicalAgent → 消息管理器 → LLM客户端 → 工具调用 → 结果处理
      ↑                      ↓              ↓           ↓          ↓
      └── 状态保存 ←── 工作流跟踪 ←── 响应解析 ←── 工具注册表
```

#### 3. 模块依赖关系
```
config.py (配置中心)
    ↓
core/agent.py (主入口)
    ├── llm/client.py (LLM通信)
    ├── memory/manager.py (消息管理)
    ├── tools/registry.py (工具调用)
    └── core/workflows.py (工作流跟踪)
```

### 扩展点和定制开发

#### 1. 添加新的LLM提供商
1. 在`llm/providers/`目录创建新文件，如`myprovider.py`
2. 实现`chat()`方法，返回`LLMResponse`对象
3. 在`llm/providers/__init__.py`中注册提供商
4. 更新`config.py`支持新提供商的配置

示例模板：
```python
# llm/providers/myprovider.py
from llm.schemas import LLMMessage, LLMResponse

class MyProvider:
    def __init__(self, api_key: str, model: str, **kwargs):
        self.api_key = api_key
        self.model = model
        
    def chat(self, messages: List[LLMMessage], tools=None, **kwargs) -> LLMResponse:
        # 实现与您的LLM API的通信
        pass
```

#### 2. 添加新的工具
1. 在`tools/`目录或新模块中创建工具类
2. 继承`BaseTool`并实现`execute()`方法
3. 在`tools/registry.py`中注册工具
4. 更新工具描述和输入模式

示例：
```python
from tools.base import BaseTool

class NewTool(BaseTool):
    name = "new_tool"
    description = "新工具的描述"
    input_schema = {
        "type": "object",
        "properties": {
            "param1": {"type": "string"}
        },
        "required": ["param1"]
    }
    
    def execute(self, **kwargs):
        # 工具逻辑
        return {"result": "执行成功"}
```

#### 3. 自定义消息压缩策略
1. 继承`MessageCompressor`类
2. 实现`compress()`方法
3. 在创建`MessageManager`时传入自定义压缩器

#### 4. 集成外部系统（P2/P3/P4）
- **P2（药房系统）**：通过`PHARMACY_BASE_URL`环境变量配置
- **P3（子代理）**：通过条件导入实现，参见`core/agent.py`中的占位实现
- **P4（其他工具）**：通过工具注册系统集成

### 测试策略

#### 1. 测试层次结构
- **单元测试**：测试单个函数或类（`tests/test_*.py`）
- **集成测试**：测试模块间交互（`tests/test_agent.py`中的完整流程测试）
- **端到端测试**：测试完整API调用（`test_deepseek_*.py`）

#### 2. 测试工具
- **pytest**：主测试框架
- **pytest-mock**：模拟外部依赖
- **pytest-cov**：测试覆盖率
- **pytest-asyncio**：异步测试支持

#### 3. 模拟策略
- **LLM API**：使用`unittest.mock`模拟API调用
- **工具执行**：模拟外部服务调用
- **文件系统**：使用临时目录测试文件操作

#### 4. 运行测试的注意事项
```bash
# 使用项目提供的测试运行器（解决ROS插件冲突）
python run_tests.py

# 或配置pytest跳过冲突插件
pytest tests/ -p no:warnings  # 跳过警告插件
```

### 调试和故障排除

#### 1. 常见调试场景
- **LLM API连接失败**：检查API密钥、网络连接、服务状态
- **工具调用失败**：检查工具注册、输入参数、依赖服务
- **会话状态问题**：检查文件权限、序列化格式
- **工作流状态异常**：检查步骤更新逻辑

#### 2. 调试工具
- **日志系统**：设置`LOG_LEVEL=DEBUG`获取详细日志
- **交互式调试**：使用`cli.py`进行实时测试
- **状态检查**：使用`/status`、`/workflow`等CLI命令

#### 3. 性能分析
```python
from utils.text_utils import log_duration
import logging

logger = logging.getLogger(__name__)

# 使用装饰器记录函数执行时间
@log_duration(logger, "函数执行")
def my_function():
    pass

# 或在代码中手动计时
import time
start = time.time()
# ... 代码执行 ...
elapsed = time.time() - start
logger.info(f"执行时间: {elapsed:.2f}秒")
```

### 代码质量保证

#### 1. 静态分析
- **类型检查**：使用MyPy确保类型安全
- **代码风格**：使用Black统一代码格式
- **代码质量**：使用Flake8检查潜在问题

#### 2. 动态检查
- **测试覆盖率**：确保新代码有相应测试
- **性能基准**：监控关键路径的执行时间
- **内存使用**：检查是否存在内存泄漏

#### 3. 文档要求
- **API文档**：为公共函数和类添加docstring
- **类型注解**：为所有函数参数和返回值添加类型提示
- **示例代码**：为复杂功能提供使用示例

### 升级和迁移指南

#### 1. 版本兼容性
- **向后兼容**：保持现有API不变，新增功能通过扩展实现
- **配置迁移**：提供配置转换脚本（如需要）
- **数据迁移**：提供会话状态转换工具（如格式变更）

#### 2. 破坏性变更处理
如果必须进行破坏性变更：
1. 提供详细的迁移指南
2. 提供兼容性过渡期
3. 更新所有示例和文档
4. 更新测试用例

#### 3. 依赖更新
- 定期更新依赖版本
- 测试新版本兼容性
- 记录版本变更的影响

### 最佳实践

#### 1. 代码组织
- 保持模块单一职责
- 使用清晰的导入结构
- 避免循环依赖

#### 2. 错误处理
- 使用项目定义的异常类
- 提供有意义的错误信息
- 记录错误上下文

#### 3. 配置管理
- 所有配置通过环境变量或配置文件
- 提供默认值和验证逻辑
- 敏感信息不硬编码

#### 4. 性能考虑
- 合理使用缓存
- 避免不必要的API调用
- 监控资源使用情况

## 贡献指南

### 开发流程

1. Fork项目
2. 创建功能分支
3. 实现功能并添加测试
4. 运行测试确保通过
5. 提交Pull Request

### 代码规范

- 遵循PEP 8编码规范
- 使用类型注解
- 添加适当的文档字符串
- 为公共API提供使用示例

### 测试要求

- 新功能必须包含测试用例
- 测试覆盖率不应降低
- 边缘情况和错误处理需要测试

## Backend Integration
P1 now integrates with the smart pharmacy backend for real drug data and approval management.

### Configuration
Set `PHARMACY_BASE_URL` environment variable:
```bash
export PHARMACY_BASE_URL=http://localhost:8001
```

### Integrated Modules
- `drug_db.py` - Real drug queries from backend
- `tools/medical.py` - Real approval submission
- `tools/inventory.py` - Real inventory operations

### Testing
```bash
# Unit tests (mocked)
pytest tests/

# Integration tests (requires backend running)
RUN_INTEGRATION_TESTS=1 pytest tests/integration/
```

See [Integration Guide](docs/integration-guide.md) for details.

## 许可证

本项目采用MIT许可证。详见LICENSE文件。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 项目Issue：提交GitHub Issue
- 邮件：项目维护者邮箱
- 文档改进：提交Pull Request

---

**最后更新：2026年4月7日**

*注意：本系统为医疗辅助工具，不能替代专业医疗建议。所有用药建议都需要医生审批。*