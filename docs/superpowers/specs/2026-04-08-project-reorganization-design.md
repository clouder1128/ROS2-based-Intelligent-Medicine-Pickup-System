---
name: Project Reorganization and Code Formatting Design
description: 设计整理整个项目的文件夹结构、代码格式和文档组织，使其结构清晰、易于维护且功能不受影响
type: project
---

# 项目整理与代码格式化设计方案

## 1. 概述

### 1.1 项目背景
当前项目文件夹结构存在以下问题：
1. **目录结构混乱**：相关模块文件未归类，根目录文件过多
2. **代码格式不一致**：缩进、空行、行尾空格、注释排版不规范
3. **可读性有待提高**：文件组织不清晰，维护困难
4. **临时文件残留**：存在 `__pycache__/`、`.pytest_cache/`、`test/`（空目录）等未清理内容

### 1.2 设计目标
1. **结构清晰**：将相关模块文件归类到合理目录（如 `models/`、`controllers/`、`utils/`）
2. **格式规范**：统一Python代码格式（4空格缩进，删除多余空行和行尾空格）
3. **可维护性高**：项目逻辑不变，功能不受影响，易于后续开发和维护
4. **标准化命名**：文档和脚本文件使用标准化英文命名和清晰目录结构

### 1.3 核心约束
- ✅ **必须保留**：所有项目功能和业务逻辑
- ✅ **必须不变**：函数、类、变量命名和调用关系
- ✅ **必须更新**：所有导入路径以适应新目录结构
- ✅ **必须清理**：临时文件和缓存目录
- ⚠️ **不能修改**：业务逻辑、算法实现、API行为
- ⚠️ **保持原意**：注释内容仅做排版优化，不改变原意

## 2. 现状分析

### 2.1 当前项目结构问题

#### 2.1.1 根目录问题
- **文件混杂**：`approve_prescription.py/.md` 等文件在根目录
- **临时文件**：`__pycache__/`、`.pytest_cache/` 等缓存目录
- **遗留目录**：`test/` 目录为空或仅含已删除文件

#### 2.1.2 P1目录问题
- **根级别文件过多**：`cli.py`、`drug_db.py`、`config.py`、`exceptions.py`、`run_tests.py` 等混合存放
- **示例文件位置不当**：`example_usage.py`、`example_http_client.py` 在根目录
- **测试文件分散**：`test_deepseek_integration.py` 等不在标准测试目录

#### 2.1.3 Backend目录问题
- **单体应用**：`app.py` 包含所有路由、模型和业务逻辑（~350行）
- **缺乏模块化**：没有分离控制器、模型、工具函数
- **配置分散**：配置信息散布在代码中

#### 2.1.4 文档目录问题
- **中文文件名**：不利于跨平台协作和工具处理
- **结构扁平**：所有文档文件在同一层级，查找不便
- **命名不一致**：版本号、命名规范不统一

#### 2.1.5 代码格式问题
- **缩进不一致**：部分代码可能使用不同缩进风格
- **行尾空格**：存在多余空白字符
- **空行不规范**：函数、类之间的空行不一致
- **注释排版**：注释格式不统一

### 2.2 关键依赖关系分析

#### 2.2.1 P1导入关系
- **drug_db 广泛使用**：`tools/inventory.py`、`tools/medical.py`、多个测试文件导入
- **config 和 exceptions**：`core/agent.py` 等文件导入
- **cli.py 依赖**：`from core.agent import MedicalAgent`

#### 2.2.2 Backend导入关系
- **单文件结构**：目前所有功能在 `app.py` 中，无外部导入
- **测试依赖**：`tests/test_backend_config.py` 导入后端模块

#### 2.2.3 跨模块依赖
- **P1 → Backend**：`drug_db.py` 通过 HTTP 连接后端 API
- **集成测试**：`scripts/test-full-integration.py` 测试端到端流程

## 3. 方案设计

### 3.1 整体目录结构设计

```
agent/
├── backend/                    # 智能药房后端（模块化重组）
│   ├── main.py                # Flask应用入口（原app.py）
│   ├── init_db.py             # 数据库初始化
│   ├── requirements.txt       # 依赖文件
│   ├── README.md              # 后端说明
│   ├── pharmacy.db           # SQLite数据库
│   ├── controllers/           # API控制器
│   │   ├── health_controller.py
│   │   ├── drug_controller.py  
│   │   ├── order_controller.py
│   │   └── approval_controller.py
│   ├── models/                # 数据模型
│   │   ├── drug.py
│   │   ├── order.py
│   │   └── approval.py
│   ├── utils/                 # 工具函数
│   │   ├── database.py
│   │   ├── ros2_bridge.py
│   │   └── logger.py
│   ├── config/                # 配置管理
│   │   └── settings.py
│   └── tests/                 # 测试
│       ├── test_approval_api.py
│       └── test_drug_api.py
│
├── P1/                        # AI医疗助手（逻辑重组）
│   ├── cli/                   # 命令行界面
│   │   ├── __init__.py
│   │   ├── cli.py             # 主命令行
│   │   └── interactive.py     # 交互式界面
│   ├── services/              # 服务层
│   │   ├── __init__.py
│   │   └── pharmacy_client.py # 原drug_db.py重命名
│   ├── examples/              # 使用示例
│   │   ├── __init__.py
│   │   ├── example_usage.py
│   │   ├── example_http_client.py
│   │   ├── approve_prescription.py  # 从根目录移动
│   │   └── approve_prescription.md
│   ├── scripts/               # 工具脚本
│   │   ├── __init__.py
│   │   └── run_p1_tests.py    # 原run_tests.py重命名
│   ├── core/                  # 核心模块（扩展）
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── workflows.py
│   │   ├── config.py          # 从根目录移动
│   │   └── exceptions.py      # 从根目录移动
│   ├── llm/                   # LLM模块（保持不变）
│   ├── tools/                 # 工具系统（保持不变）
│   ├── utils/                 # 工具函数（保持不变）
│   ├── memory/                # 记忆管理（保持不变）
│   ├── session/               # 会话管理（保持不变）
│   ├── tests/                 # 测试（结构调整）
│   │   ├── integration/       # 集成测试
│   │   │   ├── test_backend_integration.py
│   │   │   ├── test_mocked_integration.py
│   │   │   ├── test_deepseek_integration.py    # 移动
│   │   │   └── test_deepseek_direct.py         # 移动
│   │   └── 其他测试文件...
│   └── requirements.txt       # P1依赖
│
├── docs/                      # 文档（标准化命名）
│   ├── guides/                # 使用指南
│   │   ├── quick-start.md     # 快速开始
│   │   ├── integration-guide.md
│   │   └── troubleshooting.md
│   ├── api/                   # API文档
│   │   ├── reference.md       # API参考
│   │   └── endpoints.md       # 端点列表
│   ├── team/                  # 团队文档
│   │   ├── project-description-v4.md  # 原AI开药助手文档
│   │   ├── team-notice.md     # 原团队通知
│   │   └── safety-guidelines.md  # 原API密钥安全指南
│   ├── analysis/              # 分析文档
│   │   └── backend-p1-integration-analysis.md
│   └── superpowers/           # 开发规划文档（保持不变）
│
├── scripts/                   # 项目脚本
│   ├── setup/                 # 环境设置
│   │   ├── quick-start.sh
│   │   └── environment-setup.sh
│   ├── testing/               # 测试脚本
│   │   ├── test-full-integration.py
│   │   └── run-backend-tests.sh
│   └── deployment/            # 部署脚本
│       ├── start-backend.sh
│       └── start-p1.sh
│
├── tests/                     # 根目录测试（保持不变）
├── sessions/                  # 会话数据（保持不变）
├── Makefile                   # 项目构建
├── README.md                  # 项目说明
└── .gitignore                 # Git忽略规则
```

### 3.2 P1目录重组详细设计

#### 3.2.1 文件移动与重命名映射表

| 原路径 | 新路径 | 变更说明 | 导入更新 |
|--------|--------|----------|----------|
| `P1/cli.py` | `P1/cli/cli.py` | 移动到cli子目录 | 保持原导入方式 |
| `P1/interactive.py` | `P1/cli/interactive.py` | 移动到cli子目录 | 保持原导入方式 |
| `P1/drug_db.py` | `P1/services/pharmacy_client.py` | 重命名，更准确反映功能 | `import drug_db` → `from services.pharmacy_client import ...` |
| `P1/config.py` | `P1/core/config.py` | 移动到core目录 | `from config import ...` → `from core.config import ...` |
| `P1/exceptions.py` | `P1/core/exceptions.py` | 移动到core目录 | `from exceptions import ...` → `from core.exceptions import ...` |
| `P1/run_tests.py` | `P1/scripts/run_p1_tests.py` | 重命名并移动 | 仅脚本，无导入依赖 |
| `P1/example_usage.py` | `P1/examples/example_usage.py` | 移动到examples目录 | 仅示例，无导入依赖 |
| `P1/example_http_client.py` | `P1/examples/example_http_client.py` | 移动到examples目录 | 仅示例，无导入依赖 |
| `P1/test_deepseek_integration.py` | `P1/tests/integration/test_deepseek_integration.py` | 移动到集成测试目录 | 测试文件，导入路径需更新 |
| `P1/test_deepseek_direct.py` | `P1/tests/integration/test_deepseek_direct.py` | 移动到集成测试目录 | 测试文件，导入路径需更新 |
| `根目录/approve_prescription.py` | `P1/examples/approve_prescription.py` | 移动到P1示例目录 | 需要更新内部导入 |
| `根目录/approve_prescription.md` | `P1/examples/approve_prescription.md` | 移动到P1示例目录 | 文档，无导入依赖 |

#### 3.2.2 导入路径批量更新策略

1. **查找所有导入语句**：
   ```bash
   grep -r "import drug_db" P1/
   grep -r "from drug_db" P1/
   grep -r "from config import" P1/
   grep -r "from exceptions import" P1/
   ```

2. **替换模式**：
   - `import drug_db` → `from services.pharmacy_client import PharmacyHTTPClient, ...`
   - `from drug_db import ...` → `from services.pharmacy_client import ...`
   - `from config import ...` → `from core.config import ...`
   - `from exceptions import ...` → `from core.exceptions import ...`

3. **更新 __init__.py 文件**：
   - 在每个新目录创建 `__init__.py` 文件
   - 在 `P1/__init__.py` 中添加必要导入以便向后兼容

#### 3.2.3 代码格式规范化
- **缩进**：统一为4空格，使用 `reindent` 工具
- **行尾空格**：使用 `sed -i 's/[[:space:]]*$//' *.py` 删除
- **空行**：函数之间2空行，类方法之间1空行
- **注释**：统一为 `# 注释` 格式，中文注释保持原样

### 3.3 Backend目录模块化详细设计

#### 3.3.1 app.py 拆分策略

**按功能域拆分为4个控制器：**

1. **health_controller.py** - 健康检查相关
   - `GET /api/health` - 健康检查（含ROS2状态）

2. **drug_controller.py** - 药品管理相关  
   - `GET /api/drugs` - 获取所有药品（支持名称过滤）
   - `GET /api/drugs/{id}` - 获取特定药品

3. **order_controller.py** - 订单管理相关
   - `GET /api/orders` - 查看取药记录（最近50条）
   - `POST /api/order` - 批量取药（库存扣减+ROS2任务）
   - `POST /api/pickup` - 单条取药（兼容旧接口）

4. **approval_controller.py** - 审批管理相关
   - `POST /api/approvals` - 创建医生审批单
   - `GET /api/approvals/{id}` - 查询审批单
   - `GET /api/approvals/pending` - 获取待审批列表
   - `POST /api/approvals/{id}/approve` - 批准审批单
   - `POST /api/approvals/{id}/reject` - 拒绝审批单

#### 3.3.2 数据模型提取

从 `app.py` 提取以下类到 `models/` 目录：

1. **drug.py** - `Drug` 类（药品模型）
   - 字段：`id`, `name`, `description`, `stock`, `shelf_location`, `expiry_date`
   - 方法：`to_dict()`, `from_dict()`

2. **order.py** - `Order` 类（订单模型）
   - 字段：`id`, `patient_id`, `drug_id`, `quantity`, `status`, `created_at`
   - 方法：`to_dict()`, `from_dict()`

3. **approval.py** - `Approval` 类（审批模型）
   - 字段：`id`, `patient_id`, `drug_name`, `dosage`, `duration`, `status`, `doctor_notes`, `created_at`, `processed_at`
   - 方法：`to_dict()`, `from_dict()`, `approve()`, `reject()`

#### 3.3.3 工具函数提取

1. **database.py** - 数据库操作
   - `get_db_connection()` - 获取数据库连接
   - `init_database()` - 初始化数据库表
   - 查询和更新辅助函数

2. **ros2_bridge.py** - ROS2集成
   - `init_ros2()` - 初始化ROS2
   - `publish_task()` - 发布任务到ROS2
   - `check_ros2_status()` - 检查ROS2状态

3. **logger.py** - 日志配置
   - 统一日志格式和级别配置
   - 文件日志和终端日志处理

#### 3.3.4 配置管理

创建 `config/settings.py`：
```python
import os

class Config:
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'pharmacy.db')
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8001))
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    ENABLE_ROS2 = os.getenv('ENABLE_ROS2', 'true').lower() == 'true'
```

#### 3.3.5 main.py（应用入口）

```python
from flask import Flask
from controllers.health_controller import health_bp
from controllers.drug_controller import drug_bp
from controllers.order_controller import order_bp
from controllers.approval_controller import approval_bp
from config.settings import Config

app = Flask(__name__)
app.register_blueprint(health_bp)
app.register_blueprint(drug_bp)
app.register_blueprint(order_bp)
app.register_blueprint(approval_bp)

if __name__ == '__main__':
    app.run(host=Config.HOST, port=Config.PORT, debug=True)
```

### 3.4 文档目录标准化设计

#### 3.4.1 文件重命名映射表

| 原文件名 | 新文件名 | 新路径 | 说明 |
|----------|----------|--------|------|
| `AI 开药助手 —— 团队项目说明文档 ver 4.0.md` | `project-description-v4.md` | `docs/team/` | 团队项目说明 |
| `团队通知.md` | `team-notice.md` | `docs/team/` | 团队开发通知 |
| `API密钥安全指南.md` | `safety-guidelines.md` | `docs/team/` | API安全指南 |
| `技术参考手册.md` | `reference-manual.md` | `docs/guides/` | 综合技术参考 |
| `backend-to-p1-integration-analysis.md` | `backend-p1-integration-analysis.md` | `docs/analysis/` | 集成分析文档 |

#### 3.4.2 文档内容更新
- **内部链接更新**：更新所有文档间的交叉引用
- **版本信息更新**：在文档开头添加更新说明
- **目录结构调整**：为长文档添加详细目录

### 3.5 脚本目录整理设计

#### 3.5.1 脚本分类
1. **setup/** - 环境设置脚本
   - `quick-start.sh` - 一键启动脚本
   - `environment-setup.sh` - 环境配置脚本

2. **testing/** - 测试脚本
   - `test-full-integration.py` - 完整集成测试
   - `run-backend-tests.sh` - 后端测试脚本
   - `run-p1-tests.sh` - P1测试脚本

3. **deployment/** - 部署脚本
   - `start-backend.sh` - 启动后端服务
   - `start-p1.sh` - 启动P1服务

### 3.6 根目录清理设计

#### 3.6.1 删除内容
- `test/` 目录（已为空或仅含已删除文件）
- 所有 `__pycache__/` 目录（递归删除）
- 所有 `.pytest_cache/` 目录
- 其他临时文件：`.DS_Store`、`*.pyc`、`*.log`（非必要）

#### 3.6.2 保留内容
- `.venv/` - Python虚拟环境
- `.git/` - Git仓库数据
- `.worktrees/` - Git工作树
- `.claude/` - Claude配置
- `sessions/` - 用户会话数据

## 4. 实施步骤

### 阶段一：备份与准备（预计时间：10分钟）
1. **创建备份**：`git stash` 或 `git commit -m "备份: 整理前状态"`
2. **验证当前状态**：运行所有测试确保基线正常
3. **记录关键信息**：记录重要导入关系和文件位置

### 阶段二：P1目录重组（预计时间：45分钟）
1. **创建目录结构**：创建 `cli/`, `services/`, `examples/`, `scripts/` 目录
2. **移动和重命名文件**：按照映射表移动文件
3. **更新导入路径**：批量更新所有Python文件中的导入语句
4. **验证P1功能**：运行P1测试确保功能正常

### 阶段三：Backend目录重组（预计时间：30分钟）
1. **创建模块目录**：创建 `controllers/`, `models/`, `utils/`, `config/`
2. **拆分app.py**：按功能域拆分为4个控制器
3. **提取数据模型**：创建 `drug.py`, `order.py`, `approval.py`
4. **提取工具函数**：创建 `database.py`, `ros2_bridge.py`, `logger.py`
5. **创建配置模块**：创建 `config/settings.py`
6. **验证后端功能**：运行后端测试确保API正常

### 阶段四：文档整理（预计时间：20分钟）
1. **创建文档目录**：创建 `guides/`, `api/`, `team/`, `analysis/`
2. **移动和重命名文档**：按照映射表移动文档文件
3. **更新文档链接**：更新所有内部交叉引用
4. **验证文档可读性**：检查文档渲染和链接正确性

### 阶段五：脚本整理（预计时间：15分钟）
1. **创建脚本目录**：创建 `setup/`, `testing/`, `deployment/`
2. **移动脚本文件**：分类移动脚本文件
3. **更新脚本路径**：更新脚本中的文件引用
4. **验证脚本功能**：运行关键脚本确保正常

### 阶段六：根目录清理（预计时间：10分钟）
1. **删除临时目录**：递归删除所有 `__pycache__/`, `.pytest_cache/`
2. **清理空目录**：删除 `test/` 等空目录
3. **移动根目录文件**：移动 `approve_prescription.*` 到P1示例目录
4. **验证清理效果**：检查根目录整洁度

### 阶段七：最终验证（预计时间：15分钟）
1. **完整测试套件**：运行 `pytest tests/` 和 `make test-integration`
2. **服务启动测试**：`make backend-start` 和 `python P1/cli/cli.py`
3. **导入路径检查**：检查所有Python文件无导入错误
4. **代码格式验证**：使用 `black --check` 或类似工具验证格式

## 5. 风险控制

### 5.1 主要风险及应对

| 风险 | 可能性 | 影响 | 应对措施 |
|------|--------|------|----------|
| 导入路径错误 | 高 | 中 | 1. 使用自动化脚本更新导入<br>2. 分阶段验证导入正确性<br>3. 保留回滚能力 |
| 功能破坏 | 中 | 高 | 1. 每个阶段后运行测试验证<br>2. 保持git可回退状态<br>3. 对比重构前后输出结果 |
| 文件丢失 | 低 | 高 | 1. 操作前备份重要文件<br>2. 使用git跟踪所有变更<br>3. 分阶段实施，及时提交 |
| 性能影响 | 低 | 低 | 1. 仅改变结构和格式，不改变算法<br>2. 验证关键接口响应时间 |

### 5.2 验证策略
1. **自动化测试**：每个阶段后运行相关测试套件
2. **手动验证**：关键功能手动测试验证
3. **对比验证**：重构前后输出结果对比
4. **回归测试**：完整集成测试验证端到端流程

## 6. 成功标准

### 6.1 功能标准
1. ✅ **所有测试通过**：`pytest tests/` 通过率100%
2. ✅ **后端服务正常**：`make backend-start` 成功启动，API端点可访问
3. ✅ **P1 CLI正常**：`python P1/cli/cli.py` 可正常交互
4. ✅ **集成测试通过**：`make test-integration` 完整流程测试通过
5. ✅ **无语法错误**：所有Python文件无语法错误

### 6.2 质量标准
1. ✅ **代码格式统一**：所有Python文件使用4空格缩进，无尾随空格
2. ✅ **目录结构清晰**：按功能模块组织，符合Python最佳实践
3. ✅ **文件命名规范**：英文命名，清晰表达文件用途
4. ✅ **导入路径正确**：无`ModuleNotFoundError`或导入错误
5. ✅ **文档链接有效**：所有文档内部链接正确有效

### 6.3 维护标准
1. ✅ **易于扩展**：新功能可添加到相应模块目录
2. ✅ **易于理解**：新开发者能快速理解项目结构
3. ✅ **易于测试**：测试文件与源码对应清晰
4. ✅ **版本可控**：所有变更通过git管理，可追溯

## 7. 后续建议

### 7.1 持续维护
1. **代码格式检查**：在CI/CD中添加代码格式检查（black, isort）
2. **导入排序**：定期检查并规范化导入语句
3. **目录结构审查**：每季度审查目录结构合理性

### 7.2 文档更新
1. **保持同步**：代码变更时同步更新相关文档
2. **版本管理**：文档使用语义化版本控制
3. **定期审查**：每季度审查文档准确性和完整性

### 7.3 自动化工具
1. **格式化脚本**：添加代码自动格式化脚本
2. **导入检查**：添加导入路径自动检查工具
3. **结构验证**：添加目录结构验证脚本

---

*设计完成时间：2026年4月8日*  
*设计版本：v1.0*  
*设计目标：项目整理与代码格式化，功能不变，结构优化*