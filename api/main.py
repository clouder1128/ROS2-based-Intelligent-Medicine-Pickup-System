"""
FastAPI 后端主应用 - P4 后端API工程师负责
集成P1的MedicalAgent、P6的审批模块和P2的医疗工具
"""

import os
import logging
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# 导入P1的配置系统
import sys
import os
# 添加P1目录到Python路径，确保相对导入正常工作
P1_DIR = os.path.join(os.path.dirname(__file__), "..", "P1")
sys.path.insert(0, os.path.dirname(P1_DIR))  # 添加项目根目录
from P1.config import Config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 验证配置
try:
    Config.validate()
    logger.info("配置验证通过")
except Exception as e:
    logger.error(f"配置验证失败: {e}")
    raise RuntimeError(f"配置验证失败: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("启动FastAPI后端服务")
    logger.info(f"LLM提供商: {Config.LLM_PROVIDER}")
    logger.info(f"药房系统URL: {Config.PHARMACY_BASE_URL}")

    yield

    # 关闭时
    logger.info("关闭FastAPI后端服务")

# 创建FastAPI应用
app = FastAPI(
    title="AI开药助手后端API",
    description="基于FastAPI的后端服务，集成医疗Agent、审批系统和药房仿真",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入路由
from .routes import router as main_router
from .admin_routes import router as admin_router

# 注册路由
app.include_router(main_router, prefix="/api", tags=["主要API"])
app.include_router(admin_router, prefix="/api/admin", tags=["管理员API"])

@app.get("/")
async def root():
    """根端点，返回服务信息"""
    return {
        "service": "AI开药助手后端API",
        "version": "1.0.0",
        "status": "运行中",
        "modules": {
            "P1": "MedicalAgent集成",
            "P2": "医疗工具和药房集成",
            "P4": "后端API",
            "P6": "审批模块"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": "2026-04-15T12:00:00Z",  # TODO: 使用实际时间
        "config": {
            "llm_provider": Config.LLM_PROVIDER,
            "pharmacy_url": Config.PHARMACY_BASE_URL
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)