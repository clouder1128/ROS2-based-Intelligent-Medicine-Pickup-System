# 测试环境预配置
# 该文件用于在 pytest 运行时，将 agent_with_backend 目录加入 sys.path，
# 以便测试文件能够直接导入项目模块（例如 auth.tokens、api.drug_controller、screening.services）。

import os
import sys

ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "agent_with_backend")
)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
