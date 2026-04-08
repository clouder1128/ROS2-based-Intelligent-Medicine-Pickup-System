# 医生审批系统 - approve_prescription.py 使用说明

## 概述

本文档介绍重构后的 `approve_prescription.py` 脚本功能和使用方法。该脚本现已升级为完整的交互式命令行界面，支持多次操作、添加医生建议、批准/拒绝审批单等功能。

## 主要功能

### 1. 交互式 CLI 界面
- 支持多次操作，无需重复启动脚本
- 提供丰富的命令系统
- 智能输入识别（支持审批ID、列表索引）

### 2. 医生建议支持
- 批准时可输入医生建议（可选）
- 建议将自动追加到原有用药建议末尾
- 格式：`\n[doctor] <建议内容>`
- 永久保存到审批记录中

### 3. 完整审批流程
- 列出待审批单
- 批准审批单（自动创建订单）
- 拒绝审批单（需输入理由）
- 查看审批单详情
- 检查订单状态

## 使用方式

### 启动交互模式
```bash
python approve_prescription.py
```

### 直接批准模式（向后兼容）
```bash
# 简单批准
python approve_prescription.py AP-20260408-XXXXXXX

# 带医生建议的批准
python approve_prescription.py AP-20260408-XXXXXXX --notes "饭后服用，多喝水" --doctor-id "doctor_001"
```

### 帮助信息
```bash
python approve_prescription.py -h
# 或
python approve_prescription.py --help
```

## 交互式命令参考

| 命令 | 功能 | 示例 |
|------|------|------|
| `/help` | 显示帮助信息 | `/help` |
| `/list` | 列出所有待审批单 | `/list` |
| `/approve [ID]` | 批准审批单（可输入医生建议） | `/approve 1` 或 `/approve AP-20260408-XXXXXXX` |
| `/reject [ID]` | 拒绝审批单（需输入拒绝理由） | `/reject 2` |
| `/view [ID]` | 查看审批单详细信息 | `/view AP-20260408-XXXXXXX` |
| `/status [ID]` | 检查审批单状态 | `/status AP-20260408-XXXXXXX` |
| `/orders` | 查看订单/库存扣减情况 | `/orders` |
| `/doctor [新ID]` | 更改医生ID | `/doctor doctor_001` |
| `/clear` | 清空屏幕 | `/clear` |
| `/exit`, `/quit` | 退出程序 | `/exit` |

## 操作流程示例

### 示例 1：批准审批单
```
[doctor_test_001]> /list
待审批的审批单 (42个):
1. ID: AP-20260407-89A2E1E1
   患者: Test Patient
   ...

[doctor_test_001]> /approve 1
正在批准审批单: AP-20260407-89A2E1E1

请输入医生建议（可选，直接按Enter跳过）: 饭后服用，避免饮酒

✅ 审批批准成功!
   审批ID: AP-20260407-89A2E1E1
   批准医生: doctor_test_001
   批准时间: 2026-04-08T17:37:02.282245
   医生建议: 饭后服用，避免饮酒...
   📦 订单创建: 成功
```

### 示例 2：拒绝审批单
```
[doctor_test_001]> /reject 2
正在拒绝审批单: AP-20260407-0C9491DC

请输入拒绝理由（必填）: 药品不适合该症状

✅ 审批拒绝成功!
   审批ID: AP-20260407-0C9491DC
   拒绝医生: doctor_test_001
   拒绝时间: 2026-04-08T17:38:15.123456
   拒绝理由: 药品不适合该症状...
```

## 技术实现

### 后端修改
1. **`backend/approval.py`** - `approve()` 方法
   - 新增 `notes` 参数
   - 将医生建议追加到原有 `advice` 字段
   - 格式：`new_advice = row['advice'] + '\n[doctor] ' + notes`

2. **`backend/app.py`** - `/api/approvals/{id}/approve` 端点
   - 接收 `notes` 字段（可选）
   - 传递给 `manager.approve()` 方法
   - 在响应中返回 `notes` 字段

### 前端 CLI 特性
1. **命令解析器** - 支持多种输入格式
2. **智能提示** - 自动识别审批ID和列表索引
3. **历史记录** - 使用 `readline` 支持命令历史
4. **错误处理** - 友好的错误提示和恢复

## 向后兼容性

### 旧版脚本仍可正常使用
```bash
# 这些命令仍然有效
python approve_prescription.py AP-20260408-XXXXXXX
python approve_prescription.py --help
```

### 新增功能不会破坏现有流程
- 医生建议字段可选，不影响原有审批逻辑
- 交互模式与直接模式并存
- API接口保持兼容

## 注意事项

1. **后端服务** - 确保后端服务正在运行：`make backend-start`
2. **医生建议格式** - 医生建议以 `[doctor]` 标记开头，便于识别
3. **订单创建** - 批准后自动创建订单并扣减库存
4. **数据验证** - 自动验证审批单状态、药品库存等

## 故障排除

### 常见问题
1. **无法连接到后端** - 运行 `make backend-start` 启动服务
2. **审批单不存在** - 检查审批ID是否正确
3. **库存不足** - 系统会显示错误信息，不会影响审批状态

### 调试命令
```bash
# 检查后端健康状态
curl http://localhost:8001/api/health

# 查看待审批单
curl http://localhost:8001/api/approvals/pending

# 查看订单
curl http://localhost:8001/api/orders
```

## 更新日志

### v2.0 (2026-04-08)
- 重构为交互式 CLI 界面
- 支持添加医生建议
- 新增 `/reject`、`/view`、`/orders` 等命令
- 保持向后兼容性

### v1.0 (早期版本)
- 简单的直接批准功能
- 支持交互式列表选择

---

**最后更新**: 2026年4月8日  
**版本**: 2.0  
**适用系统**: 智能药房P1+后端集成系统