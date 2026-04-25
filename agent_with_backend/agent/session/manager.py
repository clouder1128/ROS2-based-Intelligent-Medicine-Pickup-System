import os
import pickle
import logging
from typing import Dict, Optional
from agent.engine import MedicalAgent
from common.config import Config

logger = logging.getLogger(__name__)


class SessionManager:
    """管理多个患者的Agent会话（P1职责：内存管理+持久化）"""

    def __init__(self, state_dir: str = None):
        self.state_dir = state_dir or Config.SESSION_STATE_DIR
        os.makedirs(self.state_dir, exist_ok=True)
        self._sessions: Dict[str, MedicalAgent] = {}

    def get_agent(self, patient_id: str, create_new: bool = True) -> MedicalAgent:
        """获取或创建患者的Agent实例"""
        if patient_id in self._sessions:
            return self._sessions[patient_id]

        if not create_new:
            return None

        # 尝试从磁盘加载
        agent = MedicalAgent()
        state_file = os.path.join(self.state_dir, f"{patient_id}.pkl")
        if os.path.exists(state_file):
            if agent.load_state(state_file):
                logger.info(f"Loaded session for {patient_id}")
            else:
                logger.warning(f"Failed to load session for {patient_id}, creating new")
        self._sessions[patient_id] = agent
        return agent

    def create_agent(self, patient_id: str) -> MedicalAgent:
        """创建新的Agent实例（不尝试加载）"""
        agent = MedicalAgent()
        self._sessions[patient_id] = agent
        logger.info(f"Created new session for {patient_id}")
        return agent

    def cleanup_inactive(self, max_age_hours: int = 24) -> int:
        """清理不活跃的会话（简化实现）"""
        logger.info(f"Session cleanup called with max_age_hours={max_age_hours}")
        return 0

    def save_all(self) -> None:
        """保存所有会话到磁盘"""
        for patient_id, agent in self._sessions.items():
            state_file = os.path.join(self.state_dir, f"{patient_id}.pkl")
            agent.save_state(state_file)
        logger.info(f"Saved {len(self._sessions)} sessions")

    def save_session(self, patient_id: str) -> bool:
        """保存单个会话"""
        if patient_id in self._sessions:
            state_file = os.path.join(self.state_dir, f"{patient_id}.pkl")
            self._sessions[patient_id].save_state(state_file)
            return True
        return False

    def delete_session(self, patient_id: str) -> bool:
        """删除会话（内存和磁盘）"""
        if patient_id in self._sessions:
            del self._sessions[patient_id]
        state_file = os.path.join(self.state_dir, f"{patient_id}.pkl")
        if os.path.exists(state_file):
            os.unlink(state_file)
            return True
        return False

    def list_sessions(self) -> list:
        """列出所有已加载的会话ID"""
        return list(self._sessions.keys())

    def get_active_count(self) -> int:
        """获取当前活跃会话数"""
        return len(self._sessions)
