# 测试覆盖缺口详细映射

## 模块覆盖状态矩阵

```
模块                 单元测试  集成测试  E2E测试  覆盖率   状态
═════════════════════════════════════════════════════════════════
配置管理             ✅✅✅    ✅        -       100%    ✨完备
数据库模型           ✅✅      ✅✅      -       70%     良好
API 控制器           ✅✅      ✅✅      ✅      60%     良好
认证授权             ✅        ✅        ✅      50%     待完善
─────────────────────────────────────────────────────────────────
Agent 引擎           ❌        ❌        ❌       0%     🔴关键
LLM 集成             ❌        ❌        ❌       0%     🔴关键
ROS2 集成            ❌        ❌        ❌       0%     🔴关键
子 Agent 系统         ❌        ❌        ❌       0%     🔴关键
─────────────────────────────────────────────────────────────────
记忆管理             ❌        ❌        -       0%     🟠重要
规划系统             ❌        ❌        -       0%     🟠重要
工具执行             ❌        ❌        -       0%     🟠重要
症状筛查             ⚠️        ❌        ❌      10%     🟠重要
─────────────────────────────────────────────────────────────────
会话管理             ❌        ❌        -       0%     中等
报告生成             ❌        ❌        -       0%     中等
审批流程             ❌        ✅        -       20%     中等
ROS 状态管理          ❌        ❌        -       0%     中等
─────────────────────────────────────────────────────────────────
错误处理             ❌        ✅        -       10%     低
性能优化             ❌        ❌        ❌       0%     低

图例:
✅✅✅ = 全面覆盖  ✅✅ = 良好覆盖  ✅ = 基础覆盖
⚠️  = 部分覆盖  ❌ = 无覆盖  - = 不适用
```

## 按优先级分类的缺口列表

### 🔴 P0 - 关键缺陷风险 (必须立即修复)

#### 1. Agent 推理引擎 (`agent/engine/medical_agent.py`)
**现状**: 0% 覆盖  
**风险**: Agent 错误的诊断直接影响患者安全  
**建议测试**:
```python
tests/unit/test_medical_agent.py  # ~150 行
- test_symptom_analysis()        # 解析症状
- test_diagnosis_generation()    # 生成诊断
- test_confidence_scoring()      # 信心度评分
- test_agent_error_handling()    # 错误处理
- test_concurrent_requests()     # 并发处理
```

#### 2. LLM 集成模块 (`agent/llm/client.py`)
**现状**: 0% 覆盖  
**风险**: LLM 调用失败导致整个系统崩溃  
**建议测试**:
```python
tests/unit/test_llm_client.py    # ~200 行
- test_claude_api_call()         # Claude 调用
- test_openai_api_call()         # OpenAI 调用
- test_retry_logic()             # 重试机制
- test_rate_limiting()           # 速率限制
- test_error_recovery()          # 错误恢复
- test_mock_llm_providers()      # Mock 供应商
```

#### 3. ROS2 集成 (`ros_integration/`)
**现状**: 0% 覆盖  
**风险**: 机器人不执行或错误执行任务  
**建议测试**:
```python
tests/integration/test_ros2_integration.py  # ~250 行
- test_message_publish()         # 消息发布
- test_message_subscribe()       # 消息订阅
- test_service_call()            # 服务调用
- test_robot_state_tracking()    # 机器人状态
- test_timeout_handling()        # 超时处理
- test_network_resilience()      # 网络恢复

tests/integration/test_robot_commands.py   # ~200 行
- test_pickup_medicine()         # 取药命令
- test_return_to_dock()          # 返回停靠
- test_emergency_stop()          # 紧急停止
- test_concurrent_robots()       # 多机器人
```

### 🟠 P1 - 主要功能缺陷 (1-2周内)

#### 4. Agent 工具系统 (`agent/tools/`)
**现状**: 0% 覆盖  
**建议测试**:
```python
tests/unit/test_tool_executor.py        # ~180 行
- test_tool_registry()
- test_tool_execution()
- test_tool_error_handling()
- test_medical_tools()
- test_inventory_tools()

tests/unit/test_report_generator.py     # ~150 行
- test_prescription_generation()
- test_report_formatting()
- test_export_formats()  # PDF, JSON 等
```

#### 5. Agent 记忆系统 (`agent/memory/`)
**现状**: 0% 覆盖  
**建议测试**:
```python
tests/unit/test_memory_manager.py      # ~200 行
- test_memory_storage()
- test_memory_retrieval()
- test_compression()
- test_cache_invalidation()

tests/unit/test_memory_compressor.py   # ~100 行
- test_compression_ratio()
- test_compression_speed()
- test_fidelity_loss()
```

#### 6. 规划系统 (`agent/planner/`)
**现状**: 0% 覆盖  
**建议测试**:
```python
tests/unit/test_planner.py             # ~200 行
- test_plan_generation()
- test_plan_validation()
- test_step_sequencing()
- test_dependency_resolution()
- test_failure_recovery()
```

#### 7. 业务工作流端到端测试
**现状**: ~10% 覆盖  
**建议测试**:
```python
tests/e2e/test_symptom_screening_flow.py    # ~250 行
- test_user_symptom_input()
- test_ai_analysis()
- test_result_presentation()
- test_approval_request()

tests/e2e/test_medicine_pickup_flow.py      # ~300 行
- test_complete_flow()
  - 就医咨询 → 诊断 → 取药 → 完成
- test_flow_with_approval()
- test_flow_cancellation()
- test_multiple_users()
```

### 🟡 P2 - 重要功能完善 (2-3周内)

#### 8. 认证授权完善
```python
tests/unit/test_jwt_tokens.py           # ~150 行
- test_token_generation()
- test_token_validation()
- test_token_expiration()
- test_token_refresh()

tests/unit/test_permissions.py          # ~130 行
- test_role_permissions()
- test_permission_checking()
- test_permission_inheritance()
- test_admin_override()

tests/integration/test_auth_flow.py     # ~200 行
- test_login_logout_flow()
- test_session_management()
- test_concurrent_sessions()
- test_token_revocation()
```

#### 9. 症状筛查完善
```python
tests/unit/test_symptom_extraction.py   # ~180 行
- test_symptom_parsing()
- test_symptom_normalization()
- test_synonym_handling()
- test_invalid_symptoms()

tests/unit/test_screening_logic.py      # ~200 行
- test_screening_rules()
- test_condition_matching()
- test_severity_assessment()
```

#### 10. 性能与并发测试
```python
tests/performance/test_concurrent_requests.py  # ~200 行
- test_10_concurrent_users()
- test_100_concurrent_users()
- test_request_queue_handling()
- test_response_time_SLA()

tests/performance/test_database_performance.py # ~150 行
- test_bulk_insert_performance()
- test_query_performance()
- test_index_effectiveness()
```

### 🔵 P3 - 可选完善 (按需)

#### 11. 错误场景覆盖
```python
tests/test_error_scenarios.py           # ~250 行
- test_invalid_input()
- test_missing_fields()
- test_type_mismatches()
- test_out_of_range_values()
- test_database_connection_loss()
- test_external_api_timeout()
- test_network_disconnection()
```

#### 12. 安全测试
```python
tests/security/test_injection_attacks.py    # ~150 行
- test_sql_injection()
- test_xss_prevention()
- test_csrf_protection()

tests/security/test_access_control.py       # ~130 行
- test_unauthorized_access()
- test_data_isolation()
- test_privilege_escalation()
```

---

## 快速参考: 缺口总结

### 按代码行数统计

| 类别 | 已有 | 需要 | 总计 |
|-----|------|------|------|
| 配置与工具 | 135 | 100 | 235 |
| 数据库相关 | 100 | 250 | 350 |
| **API 与认证** | 460 | 400 | 860 |
| **Agent 相关** | 0 | 1,500 | 1,500 |
| **ROS2 相关** | 0 | 450 | 450 |
| **E2E 测试** | 400 | 700 | 1,100 |
| **性能测试** | 0 | 350 | 350 |
| **安全测试** | 0 | 280 | 280 |
| **错误处理** | 0 | 250 | 250 |
| **总计** | **1,095** | **4,280** | **5,375** |

### 工作量估计

```
P0 (关键) - Agent + ROS2
├─ Agent 引擎: 150 行  (10-15 小时)
├─ LLM 集成: 200 行   (15-20 小时)
├─ ROS2 集成: 450 行  (30-40 小时)
└─ 工具系统: 330 行   (20-25 小时)
总计: 1,130 行 (75-100 小时) ⏱️ 2-3 周

P1 (主要) - 功能完善
├─ 记忆系统: 300 行   (15-20 小时)
├─ 规划系统: 200 行   (12-15 小时)
├─ 端到端测试: 550 行 (30-40 小时)
└─ 认证完善: 480 行   (25-30 小时)
总计: 1,530 行 (82-105 小时) ⏱️ 2-3 周

P2 (完善) - 品质提升
├─ 症状筛查: 380 行   (18-22 小时)
├─ 性能测试: 350 行   (20-25 小时)
└─ 并发测试: 200 行   (12-15 小时)
总计: 930 行 (50-62 小时) ⏱️ 1-2 周

P3 (可选) - 最佳实践
├─ 错误处理: 250 行   (12-15 小时)
├─ 安全测试: 280 行   (15-18 小时)
└─ 其他: 200 行      (10-12 小时)
总计: 730 行 (37-45 小时) ⏱️ 1 周

═══════════════════════════════════════════
总工作量: 4,320 行 (244-312 小时)
耗时: 7-10 周 (2-3 人或 1 人全职)
```

### 文件创建清单

```
新增测试文件结构:
tests/
├── unit/                                  # 单元测试
│   ├── test_medical_agent.py             ⭐ P0
│   ├── test_llm_client.py                ⭐ P0
│   ├── test_agent_tools.py               ⭐ P0
│   ├── test_memory_manager.py            ⭐ P1
│   ├── test_planner.py                   ⭐ P1
│   ├── test_jwt_tokens.py                🟠 P2
│   ├── test_permissions.py               🟠 P2
│   ├── test_symptom_extraction.py        🟠 P2
│   └── test_screening_logic.py           🟠 P2
│
├── integration/                           # 集成测试
│   ├── test_ros2_integration.py          ⭐ P0
│   ├── test_robot_commands.py            ⭐ P0
│   ├── test_auth_flow.py                 🟠 P2
│   ├── test_agent_with_database.py       🟠 P2
│   └── test_api_with_database.py         🟠 P2
│
├── e2e/                                   # 端到端测试
│   ├── test_symptom_screening_flow.py    🟠 P1
│   ├── test_medicine_pickup_flow.py      🟠 P1
│   └── test_approval_workflow.py         🟠 P2
│
├── performance/                           # 性能测试
│   ├── test_concurrent_requests.py       🟠 P2
│   ├── test_database_performance.py      🟠 P2
│   └── test_agent_response_time.py       🟠 P2
│
├── security/                              # 安全测试
│   ├── test_injection_attacks.py         🔵 P3
│   └── test_access_control.py            🔵 P3
│
├── test_error_scenarios.py               🔵 P3
├── test_timeout_handling.py              🔵 P3
├── test_network_failures.py              🔵 P3
├── fixtures/                              # 测试数据
│   ├── users.json
│   ├── medicines.json
│   └── conversations.json
├── mocks/                                 # Mock 对象
│   ├── mock_llm_client.py
│   ├── mock_ros_node.py
│   └── mock_database.py
└── conftest.py                            # 全局配置 (已有，需扩展)
```

---

## 执行计划时间表

### Week 1: 基础准备
- [ ] Mon: 搭建测试基础设施 (Mock, Fixture)
- [ ] Tue-Wed: P0 代码分析与设计
- [ ] Thu: 编写第一批单元测试 (Agent 引擎)
- [ ] Fri: 回顾与调整

### Week 2-3: 关键功能
- [ ] LLM 集成测试编写
- [ ] ROS2 集成测试编写
- [ ] Agent 工具系统测试

### Week 4: E2E 与集成
- [ ] 端到端测试设计
- [ ] 集成测试补充
- [ ] 覆盖率分析

### Week 5: 质量保证
- [ ] 认证授权完善
- [ ] 性能测试
- [ ] 文档编写

### Week 6+: 持续改进
- [ ] 代码审查
- [ ] CI/CD 集成
- [ ] 监控与维护

---

## 关键检查点

✅ **测试执行前检查**:
- [ ] Mock 库完整可用
- [ ] 数据库初始化脚本可用
- [ ] ROS2 模拟环境就绪
- [ ] API 文档最新

✅ **代码审查标准**:
- [ ] 覆盖率 >= 预期
- [ ] 无 Flaky 测试
- [ ] 性能 < 预期
- [ ] 代码风格一致

✅ **交付标准**:
- [ ] 所有 P0 测试通过
- [ ] 覆盖率 >= 50%
- [ ] CI/CD 绿色通过
- [ ] 文档完整

