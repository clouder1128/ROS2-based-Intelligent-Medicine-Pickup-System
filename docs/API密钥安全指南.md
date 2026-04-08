# API密钥安全管理指南

**发送时间**: 2026年4月7日  
**发送人**: 项目安全负责人  
**重要性**: ⚠️ 高优先级  

---

## 🚨 重要安全通知

在最近的代码审查中，我们在`P1/DEEPSEEK_CONFIG.md`文件中发现了一个潜在的安全问题：**一个示例DeepSeek API密钥被硬编码在文档中**。

虽然这个密钥已确认为占位符（已修复），但此事件提醒我们所有人必须高度重视API密钥安全管理。

## 🔍 问题回顾

### 发现的问题
- **文件**: `P1/DEEPSEEK_CONFIG.md`
- **原始内容**: 
  ```bash
  export ANTHROPIC_AUTH_TOKEN="sk-fda9dd8c7d804a23aebd85c283e55e68"  # 您的DeepSeek API密钥
  ```
- **修复后内容**:
  ```bash
  export ANTHROPIC_AUTH_TOKEN="your_deepseek_api_key_here"  # 您的DeepSeek API密钥
  ```

### 安全风险评估
1. **如果是真实密钥**: 需要立即撤销并重新生成
2. **如果是占位符**: 需要确保所有文档中都使用占位符
3. **预防措施**: 需要建立API密钥管理规范

## 🔐 立即操作（全体成员）

### 1. 检查您使用的API密钥
```bash
# 检查是否使用了泄露的密钥
grep -r "sk-fda9dd8c7d804a23aebd85c283e55e68" /home/clouder/agent --include="*.py" --include="*.md" --include="*.txt" --include="*.sh"

# 检查.env文件（本地）
if [ -f ".env" ]; then
    echo "检查.env文件:"
    grep -n "ANTHROPIC_AUTH_TOKEN\|ANTHROPIC_API_KEY\|OPENAI_API_KEY" .env
fi
```

### 2. 如果使用DeepSeek API
- **立即登录** [DeepSeek控制台](https://platform.deepseek.com/)
- **检查API使用记录**，确认是否有异常调用
- **如有疑问，撤销并重新生成API密钥**

### 3. 验证本地环境
```bash
# 查看当前环境变量
echo "ANTHROPIC_AUTH_TOKEN=$ANTHROPIC_AUTH_TOKEN"
echo "ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY"
echo "OPENAI_API_KEY=$OPENAI_API_KEY"
```

## 📋 API密钥安全规范

### 原则：永远不要提交真实密钥
- ✅ **使用占位符**: `your_api_key_here`, `sk-...`
- ✅ **环境变量管理**: 使用`.env`文件
- ❌ **禁止硬编码**: 不要在代码中写真实密钥
- ❌ **禁止提交**.env: `.env`必须在`.gitignore`中

### 正确的配置方法

#### 1. 环境变量文件结构
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

#### 2. 代码中的引用方式
```python
# ✅ 正确：从环境变量读取
import os
api_key = os.getenv("ANTHROPIC_AUTH_TOKEN")

# ❌ 错误：硬编码在代码中
api_key = "sk-fda9dd8c7d804a23aebd85c283e55e68"
```

#### 3. 测试中的密钥管理
```python
# ✅ 正确：使用测试专用密钥
os.environ["ANTHROPIC_API_KEY"] = "test_anthropic_key"
os.environ["OPENAI_API_KEY"] = "test_openai_key"

# ❌ 错误：使用真实密钥进行测试
os.environ["ANTHROPIC_API_KEY"] = "sk-real-key-123456"
```

### 4. 文档中的示例
```markdown
<!-- ✅ 正确：使用占位符 -->
```bash
export ANTHROPIC_AUTH_TOKEN="your_deepseek_api_key_here"
```

<!-- ❌ 错误：显示真实密钥 -->
```bash
export ANTHROPIC_AUTH_TOKEN="sk-fda9dd8c7d804a23aebd85c283e55e68"
```
```

## 🔧 安全配置检查清单

### 项目级检查
- [ ] `.gitignore`包含`.env*`文件
- [ ] `.env.example`只包含占位符
- [ ] 没有真实的`.env`文件提交到仓库
- [ ] 所有文档中的示例都是占位符

### 代码级检查
- [ ] 没有硬编码的API密钥
- [ ] 所有密钥都从环境变量读取
- [ ] 测试中使用模拟密钥
- [ ] 敏感信息在日志中被掩码

### 开发者级检查
- [ ] 本地`.env`文件已添加到`.gitignore`
- [ ] 使用了正确的API密钥占位符
- [ ] 定期检查API使用情况
- [ ] 不在公开场合分享密钥

## 🛡️ 应急响应流程

### 发现API密钥泄露
1. **立即撤销密钥**
   - 登录对应平台撤销泄露的密钥
   - 生成新的API密钥
2. **检查使用记录**
   - 查看API调用日志
   - 确认是否有未授权使用
3. **清理代码库**
   ```bash
   # 使用git filter-repo清理历史
   git filter-repo --force --replace-text <(echo "sk-leaked-key==>your_api_key_here")
   ```
4. **通知团队**
   - 立即通知所有团队成员
   - 要求更新本地环境变量

### 预防措施
1. **定期扫描**
   ```bash
   # 定期运行安全扫描
   grep -r "sk-[a-zA-Z0-9]\{20,\}" . --include="*.py" --include="*.md" --include="*.txt"
   ```
2. **预提交钩子**
   ```bash
   # 在.git/hooks/pre-commit中添加检查
   #!/bin/bash
   if grep -r "sk-[a-zA-Z0-9]\{20,\}" . --include="*.py" --include="*.md" --include="*.txt" --quiet; then
       echo "错误：检测到可能的API密钥泄露！"
       exit 1
   fi
   ```

## 📊 当前项目安全状态

| 文件 | 状态 | 检查结果 |
|------|------|----------|
| `P1/DEEPSEEK_CONFIG.md` | ✅ 已修复 | 真实密钥 → 占位符 |
| `P1/.env.example` | ✅ 安全 | 仅含占位符 |
| `P1/README.md` | ✅ 安全 | 仅含占位符 |
| `P1/config.py` | ✅ 安全 | 从环境变量读取 |
| `P1/tests/conftest.py` | ✅ 安全 | 测试专用密钥 |
| `.gitignore` | ✅ 已配置 | 排除.env文件 |

## 📚 各角色具体任务

### P1 (Agent核心工程师)
- 确保`config.py`只从环境变量读取密钥
- 验证测试中的模拟密钥都是安全的
- 检查所有示例代码使用占位符

### P2 (医疗工具与知识库工程师)
- 检查`tools/medical.py`中的`fill_prescription`函数
- 确保药房API调用没有硬编码密钥
- 验证数据库连接字符串管理

### P3 (规划与子代理工程师)
- 检查子代理配置中的外部API调用
- 确保规划器任务中没有敏感信息

### P4 (后端API工程师)
- 验证FastAPI配置中的密钥管理
- 检查`/approve`端点中的外部调用
- 确保响应中不包含敏感信息

### P5 (前端工程师)
- 检查前端代码中的硬编码URL或密钥
- 确保API调用使用环境变量
- 验证敏感信息不在前端暴露

### P6 (测试/审批/集成工程师)
- 检查测试配置中的密钥管理
- 验证审计日志不记录完整密钥
- 确保部署脚本安全处理密钥

## 🛠️ 工具和脚本

### 安全扫描脚本
```python
# security_scan.py
import os
import re
from pathlib import Path

def check_api_keys():
    """扫描项目中的API密钥泄露"""
    patterns = [
        r'sk-[a-zA-Z0-9_\-]{20,}',
        r'AKIA[0-9A-Z]{16}',
        r'gh[pousr]_[A-Za-z0-9_]{36,255}',
        r'eyJ[a-zA-Z0-9_\-]+\.eyJ[a-zA-Z0-9_\-]+\.',
    ]
    
    issues = []
    for file in Path('.').rglob('*'):
        if file.is_file() and not any(ignore in str(file) for ignore in ['.git', 'venv', '__pycache__']):
            try:
                content = file.read_text()
                for pattern in patterns:
                    if re.search(pattern, content):
                        issues.append((file, pattern))
            except:
                continue
    
    return issues

if __name__ == "__main__":
    issues = check_api_keys()
    if issues:
        print("⚠️ 发现潜在的安全问题:")
        for file, pattern in issues:
            print(f"  {file}: 匹配模式 {pattern}")
        exit(1)
    else:
        print("✅ 安全检查通过")
```

### 环境验证脚本
```bash
#!/bin/bash
# check_env.sh

echo "=== 环境变量安全检查 ==="

# 检查是否使用占位符
if [[ "$ANTHROPIC_AUTH_TOKEN" == *"your_deepseek_api_key_here"* ]]; then
    echo "❌ ANTHROPIC_AUTH_TOKEN仍为占位符，请替换为真实密钥"
fi

if [[ "$ANTHROPIC_AUTH_TOKEN" == *"sk-fda9dd8c7d804a23aebd85c283e55e68"* ]]; then
    echo "🚨 发现已泄露的密钥，请立即更换！"
fi

# 检查.env文件是否存在且不被提交
if [ -f ".env" ]; then
    if git check-ignore .env >/dev/null; then
        echo "✅ .env文件已在.gitignore中"
    else
        echo "❌ .env文件未在.gitignore中，请添加"
    fi
else
    echo "⚠️ 未找到.env文件，请从.env.example创建"
fi

echo "=== 检查完成 ==="
```

## 📞 联系和支持

### 遇到问题时的步骤
1. **立即暂停开发**，确认密钥安全
2. **联系安全负责人** (P1/P6)
3. **按照应急流程处理**
4. **更新团队文档**

### 资源链接
- [DeepSeek API密钥管理](https://platform.deepseek.com/api-keys)
- [OpenAI API安全最佳实践](https://platform.openai.com/docs/guides/safety-best-practices)
- [Anthropic API安全指南](https://docs.anthropic.com/claude/docs/safety-best-practices)
- [OWASP密钥管理指南](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)

## 🎯 总结与承诺

### 我们的承诺
- **永不**将真实API密钥提交到版本控制
- **始终**使用环境变量管理敏感信息
- **定期**进行安全扫描和审查
- **立即**响应任何潜在的安全问题

### 行动号召
请每位成员：
1. 立即检查本地开发环境
2. 确认使用正确的API密钥管理方法
3. 如有任何疑问，立即在团队群中提出

**安全是团队共同的责任，让我们共同努力维护项目安全！**

---
*本文档由Claude Code生成，如有问题请及时反馈。*