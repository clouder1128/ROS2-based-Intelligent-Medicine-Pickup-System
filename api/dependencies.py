"""
依赖注入模块 - 提供API依赖项，如数据库连接、配置、管理器等
"""

import logging
from typing import Optional, Generator
from contextlib import contextmanager
from fastapi import Depends, HTTPException, Header

# 导入项目配置
from P1.config import Config

logger = logging.getLogger(__name__)

# ==================== 配置依赖 ====================

def get_config():
    """获取配置实例"""
    return Config

# ==================== 数据库依赖 ====================

@contextmanager
def get_db_connection():
    """获取数据库连接（上下文管理器）"""
    import sqlite3
    # TODO: 根据Config.DATABASE_URL连接数据库
    # 当前使用固定路径
    db_path = "medical_assistant.db"
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        logger.debug(f"连接到数据库: {db_path}")
        yield conn
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        raise HTTPException(status_code=500, detail="数据库连接失败")
    finally:
        if conn:
            conn.close()
            logger.debug("数据库连接已关闭")

# ==================== 管理器依赖 ====================

def get_approval_manager():
    """获取审批管理器实例"""
    try:
        from test.backend.approval import get_approval_manager as get_manager
        manager = get_manager()
        logger.debug("审批管理器加载成功")
        return manager
    except ImportError:
        logger.warning("审批管理器不可用，返回Mock管理器")
        return MockApprovalManager()

class MockApprovalManager:
    """Mock审批管理器，当真实模块不可用时使用"""
    def list_pending(self, limit=100):
        return []

    def approve(self, approval_id, doctor_id):
        logger.info(f"[Mock] 审批通过: {approval_id} by {doctor_id}")
        return True

    def reject(self, approval_id, doctor_id, reason):
        logger.info(f"[Mock] 审批拒绝: {approval_id} by {doctor_id}, 原因: {reason}")
        return True

# ==================== MedicalAgent依赖 ====================

def get_medical_agent():
    """获取MedicalAgent实例（每次请求创建新实例）"""
    try:
        from P1.core.agent import MedicalAgent
        agent = MedicalAgent()
        logger.debug("MedicalAgent创建成功")
        return agent
    except ImportError:
        logger.warning("MedicalAgent不可用，返回Mock Agent")
        return MockMedicalAgent()

class MockMedicalAgent:
    """Mock MedicalAgent，当P1模块不可用时使用"""
    def run(self, message, patient_id=None):
        return f"[Mock] 收到消息: {message}", [{"step": 0, "type": "mock", "content": "使用Mock Agent"}]

    def get_approval_id(self):
        return "AP-MOCK-001"

# ==================== 药房工具依赖 ====================

def get_pharmacy_tool():
    """获取配药工具函数"""
    try:
        from P1.tools.medical import fill_prescription_sync
        logger.debug("配药工具加载成功")
        return fill_prescription_sync
    except ImportError:
        logger.warning("配药工具不可用，返回Mock函数")
        return mock_fill_prescription

def mock_fill_prescription(prescription_id, patient_name, drugs):
    """Mock配药函数"""
    logger.info(f"[Mock] 配药请求: {prescription_id} for {patient_name}")
    import json
    return json.dumps({
        "success": True,
        "prescription_id": prescription_id,
        "patient_name": patient_name,
        "pickup_code": "PICKUP-MOCK-123456",
        "message": "[Mock] 配药成功！取药码：PICKUP-MOCK-123456",
        "mode": "mock"
    })

# ==================== 身份验证依赖 ====================

def verify_admin_token(x_admin_token: Optional[str] = Header(None)):
    """验证管理员令牌（简单实现）"""
    if not x_admin_token:
        raise HTTPException(status_code=401, detail="缺少管理员令牌")

    # TODO: 实现真正的令牌验证
    # 目前简单检查是否为"admin-token-123"
    if x_admin_token != "admin-token-123":
        raise HTTPException(status_code=403, detail="无效的管理员令牌")

    return {"role": "admin", "user_id": "admin-001"}

def verify_doctor_token(x_doctor_token: Optional[str] = Header(None)):
    """验证医生令牌（简单实现）"""
    if not x_doctor_token:
        raise HTTPException(status_code=401, detail="缺少医生令牌")

    # TODO: 实现真正的令牌验证
    # 目前简单检查格式
    if not x_doctor_token.startswith("doctor-token-"):
        raise HTTPException(status_code=403, detail="无效的医生令牌")

    # 从令牌中提取医生ID（简单示例）
    doctor_id = x_doctor_token.replace("doctor-token-", "")
    return {"role": "doctor", "user_id": f"doctor-{doctor_id}"}

def get_current_user(
    x_admin_token: Optional[str] = Header(None),
    x_doctor_token: Optional[str] = Header(None)
):
    """获取当前用户（根据令牌类型）"""
    if x_admin_token:
        return verify_admin_token(x_admin_token)
    elif x_doctor_token:
        return verify_doctor_token(x_doctor_token)
    else:
        # 患者或其他用户，没有令牌
        return {"role": "patient", "user_id": "anonymous"}

# ==================== 速率限制依赖 ====================

class RateLimiter:
    """简单的速率限制器"""
    def __init__(self, calls_per_minute: int = 60):
        self.calls_per_minute = calls_per_minute
        self.calls = []

    async def __call__(self):
        import time
        current_time = time.time()

        # 清理一分钟前的记录
        self.calls = [call_time for call_time in self.calls
                     if current_time - call_time < 60]

        if len(self.calls) >= self.calls_per_minute:
            raise HTTPException(status_code=429, detail="请求过于频繁")

        self.calls.append(current_time)

# 创建不同端点的速率限制器
chat_rate_limiter = RateLimiter(calls_per_minute=30)  # 聊天端点：每分钟30次
approval_rate_limiter = RateLimiter(calls_per_minute=60)  # 审批端点：每分钟60次

# ==================== 请求验证依赖 ====================

def validate_patient_id(patient_id: str):
    """验证患者ID格式"""
    if not patient_id:
        return "anonymous"

    # 简单的格式检查
    if len(patient_id) > 100:
        raise HTTPException(status_code=400, detail="患者ID过长")

    # 检查是否包含非法字符
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', patient_id):
        raise HTTPException(status_code=400, detail="患者ID只能包含字母、数字、下划线和连字符")

    return patient_id

# ==================== 日志记录依赖 ====================

class RequestLogger:
    """请求日志记录器"""
    def __init__(self):
        self.logger = logging.getLogger("request")

    async def log_request(self, request, call_next):
        """记录请求信息"""
        import uuid
        import time

        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        # 记录请求开始
        self.logger.info(f"[{request_id}] {request.method} {request.url.path}")

        # 处理请求
        response = await call_next(request)

        # 记录请求完成
        duration = time.time() - start_time
        self.logger.info(f"[{request_id}] 完成 - 状态: {response.status_code}, 耗时: {duration:.3f}s")

        # 添加请求ID到响应头
        response.headers["X-Request-ID"] = request_id

        return response