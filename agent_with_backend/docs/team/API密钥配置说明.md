# API密钥配置说明

## 1. 环境变量文件结构
```bash
# .env.example (提交到仓库)
ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
ANTHROPIC_AUTH_TOKEN="your_deepseek_api_key_here"
ANTHROPIC_MODEL="deepseek-chat"
LLM_PROVIDER="claude"

# .env (本地使用，不提交)
ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
ANTHROPIC_AUTH_TOKEN="sk-your-real-api-key-123456"
ANTHROPIC_MODEL="deepseek-chat"
LLM_PROVIDER="claude"
```

## 2. 代码中的引用方式
```python
# ✅ 正确：从环境变量读取
import os
api_key = os.getenv("ANTHROPIC_AUTH_TOKEN")

# ❌ 错误：硬编码在代码中
api_key = "sk-xx"
```

