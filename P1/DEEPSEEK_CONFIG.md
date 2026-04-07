# DeepSeek API 配置指南

P1医疗用药助手Agent系统已支持通过DeepSeek API（兼容Anthropic API）作为LLM提供商。

## 配置步骤

### 1. 设置环境变量

创建 `.env` 文件或在系统中设置以下环境变量：

```bash
# DeepSeek API配置
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="your_deepseek_api_key_here"  # 您的DeepSeek API密钥
export ANTHROPIC_MODEL="deepseek-chat"  # 或使用其他支持的模型
export ANTHROPIC_SMALL_FAST_MODEL="deepseek-chat"  # 快速模型（可选）

# P1系统配置
export LLM_PROVIDER="claude"  # 使用Claude提供商（兼容DeepSeek）
export LLM_MAX_TOKENS="4096"
export LLM_TEMPERATURE="0.3"
export PHARMACY_BASE_URL="http://localhost:8001"  # 药房API地址
export LOG_LEVEL="INFO"
```

### 2. 安装依赖

确保已安装必要的依赖：

```bash
pip install anthropic openai python-dotenv
```

## 配置说明

### 环境变量映射

| 变量名 | 用途 | 示例值 |
|--------|------|--------|
| `ANTHROPIC_BASE_URL` | DeepSeek API端点 | `https://api.deepseek.com/anthropic` |
| `ANTHROPIC_AUTH_TOKEN` | DeepSeek API密钥 | `sk-...` |
| `ANTHROPIC_MODEL` | 使用的模型 | `deepseek-chat` |
| `LLM_PROVIDER` | LLM提供商 | `claude` |
| `LLM_MAX_TOKENS` | 最大输出tokens | `4096` |
| `LLM_TEMPERATURE` | 温度参数 | `0.3` |

### 代码修改

系统已进行以下修改以支持DeepSeek：

1. **config.py**: 添加对`ANTHROPIC_BASE_URL`、`ANTHROPIC_AUTH_TOKEN`和`ANTHROPIC_MODEL`的支持
2. **claude.py**: 更新`ClaudeProvider`以支持`base_url`参数
3. **client.py**: 传递`base_url`给`ClaudeProvider`

## 验证配置

### 方法1：运行测试

确保所有测试通过：

```bash
cd /home/clouder/agent/P1
python run_tests.py
```

### 方法2：手动验证

创建验证脚本：

```python
# test_deepseek.py
import os
os.environ.update({
    "ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "your_api_key_here",
    "ANTHROPIC_MODEL": "deepseek-chat",
    "LLM_PROVIDER": "claude"
})

from config import Config
from llm.client import LLMClient

print("配置验证:", Config.to_dict())
client = LLMClient()
print("LLM客户端初始化成功")
```

## 注意事项

1. **API密钥安全**：不要将API密钥提交到版本控制系统
2. **速率限制**：注意DeepSeek API的速率限制
3. **模型兼容性**：确保使用的模型与Anthropic API格式兼容
4. **测试环境**：测试时使用模拟API密钥，避免产生费用

## 故障排除

### 问题：API连接失败
- 检查`ANTHROPIC_BASE_URL`是否正确
- 验证`ANTHROPIC_AUTH_TOKEN`是否有效
- 确认网络连接正常

### 问题：模型不支持
- 检查`ANTHROPIC_MODEL`是否在DeepSeek支持的模型列表中
- 尝试使用`deepseek-chat`作为默认模型

### 问题：配置验证失败
- 检查`ANTHROPIC_API_KEY`或`ANTHROPIC_AUTH_TOKEN`是否已设置
- 确保`LLM_PROVIDER`设置为`claude`

## 支持的DeepSeek模型

DeepSeek通常支持以下模型（具体以官方文档为准）：
- `deepseek-chat`：通用聊天模型
- `deepseek-coder`：代码生成模型

使用前请查阅DeepSeek官方文档获取最新的模型列表和支持信息。