# tests/test_session.py
import os
import tempfile
import pickle
import pytest
from unittest.mock import Mock, patch
from session.manager import SessionManager


class TestSessionManager:
    """测试SessionManager类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        # 创建临时目录用于测试
        self.temp_dir = tempfile.mkdtemp()
        self.manager = SessionManager(state_dir=self.temp_dir)

    def teardown_method(self):
        """每个测试方法后的清理"""
        # 删除临时目录
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_init(self):
        """测试初始化"""
        assert self.manager.state_dir == self.temp_dir
        assert os.path.exists(self.temp_dir)
        assert len(self.manager._sessions) == 0

    def test_get_agent_create_new_true(self):
        """测试get_agent方法，create_new=True（默认）"""
        patient_id = "test_patient_1"

        # 第一次调用应该创建新agent
        agent1 = self.manager.get_agent(patient_id)
        assert agent1 is not None
        assert patient_id in self.manager._sessions
        assert self.manager._sessions[patient_id] == agent1

        # 第二次调用应该返回同一个agent
        agent2 = self.manager.get_agent(patient_id)
        assert agent2 == agent1

    def test_get_agent_create_new_false(self):
        """测试get_agent方法，create_new=False"""
        patient_id = "test_patient_2"

        # 当会话不存在且create_new=False时，应该返回None
        agent = self.manager.get_agent(patient_id, create_new=False)
        assert agent is None
        assert patient_id not in self.manager._sessions

        # 先创建会话
        self.manager.create_agent(patient_id)

        # 现在get_agent应该能获取到
        agent = self.manager.get_agent(patient_id, create_new=False)
        assert agent is not None
        assert patient_id in self.manager._sessions

    def test_create_agent(self):
        """测试create_agent方法"""
        patient_id = "test_patient_3"

        # 创建新agent
        agent = self.manager.create_agent(patient_id)
        assert agent is not None
        assert patient_id in self.manager._sessions
        assert self.manager._sessions[patient_id] == agent

    def test_save_session(self):
        """测试save_session方法"""
        patient_id = "test_patient_4"

        # 创建agent
        agent = self.manager.create_agent(patient_id)

        # 模拟save_state方法
        with patch.object(agent, 'save_state') as mock_save:
            mock_save.return_value = True

            # 保存会话
            result = self.manager.save_session(patient_id)
            assert result is True
            mock_save.assert_called_once()

            # 检查文件路径
            expected_path = os.path.join(self.temp_dir, f"{patient_id}.pkl")
            mock_save.assert_called_with(expected_path)

    def test_save_session_not_found(self):
        """测试保存不存在的会话"""
        patient_id = "non_existent_patient"

        # 尝试保存不存在的会话
        result = self.manager.save_session(patient_id)
        assert result is False

    def test_delete_session(self):
        """测试delete_session方法"""
        patient_id = "test_patient_5"

        # 创建agent
        self.manager.create_agent(patient_id)
        assert patient_id in self.manager._sessions

        # 创建一个假的会话文件
        state_file = os.path.join(self.temp_dir, f"{patient_id}.pkl")
        with open(state_file, 'w') as f:
            f.write("dummy content")

        # 删除会话
        result = self.manager.delete_session(patient_id)
        assert result is True
        assert patient_id not in self.manager._sessions
        assert not os.path.exists(state_file)

    def test_delete_session_no_file(self):
        """测试删除没有文件的会话"""
        patient_id = "test_patient_6"

        # 创建agent但不创建文件
        self.manager.create_agent(patient_id)

        # 删除会话
        result = self.manager.delete_session(patient_id)
        assert result is False  # 文件不存在，返回False
        assert patient_id not in self.manager._sessions

    def test_list_sessions(self):
        """测试list_sessions方法"""
        # 初始为空
        assert self.manager.list_sessions() == []

        # 添加几个会话
        patient_ids = ["patient_a", "patient_b", "patient_c"]
        for pid in patient_ids:
            self.manager.create_agent(pid)

        # 检查列表
        sessions = self.manager.list_sessions()
        assert len(sessions) == 3
        assert set(sessions) == set(patient_ids)

    def test_get_active_count(self):
        """测试get_active_count方法"""
        # 初始为0
        assert self.manager.get_active_count() == 0

        # 添加会话
        self.manager.create_agent("patient_1")
        assert self.manager.get_active_count() == 1

        self.manager.create_agent("patient_2")
        assert self.manager.get_active_count() == 2

        # 删除一个会话
        self.manager.delete_session("patient_1")
        assert self.manager.get_active_count() == 1

    def test_save_all(self):
        """测试save_all方法"""
        # 创建多个agent
        patient_ids = ["patient_x", "patient_y", "patient_z"]
        agents = []

        for pid in patient_ids:
            agent = self.manager.create_agent(pid)
            agents.append(agent)

        # 模拟所有agent的save_state方法
        mock_saves = []
        for agent in agents:
            mock_save = Mock(return_value=True)
            agent.save_state = mock_save
            mock_saves.append(mock_save)

        # 保存所有会话
        self.manager.save_all()

        # 检查每个agent都被保存了
        for i, pid in enumerate(patient_ids):
            expected_path = os.path.join(self.temp_dir, f"{pid}.pkl")
            mock_saves[i].assert_called_with(expected_path)

    def test_cleanup_inactive(self):
        """测试cleanup_inactive方法（简化实现）"""
        # 这个方法当前是简化实现，只记录日志
        # 所以我们应该只检查它被调用且返回0
        result = self.manager.cleanup_inactive(max_age_hours=24)
        assert result == 0

        # 也可以测试不同的参数
        result = self.manager.cleanup_inactive(max_age_hours=48)
        assert result == 0

    def test_load_existing_session(self):
        """测试加载已存在的会话文件"""
        patient_id = "existing_patient"
        state_file = os.path.join(self.temp_dir, f"{patient_id}.pkl")

        # 创建一个假的会话文件
        dummy_data = {"test": "data"}
        with open(state_file, 'wb') as f:
            pickle.dump(dummy_data, f)

        # 模拟MedicalAgent的load_state方法
        with patch('session.manager.MedicalAgent') as MockAgent:
            mock_agent_instance = Mock()
            mock_agent_instance.load_state.return_value = True
            MockAgent.return_value = mock_agent_instance

            # 创建新的manager来测试加载
            new_manager = SessionManager(state_dir=self.temp_dir)
            agent = new_manager.get_agent(patient_id)

            # 检查是否尝试加载了状态
            mock_agent_instance.load_state.assert_called_once_with(state_file)
            assert patient_id in new_manager._sessions

    def test_load_failed_session(self):
        """测试加载失败的会话文件"""
        patient_id = "corrupted_patient"
        state_file = os.path.join(self.temp_dir, f"{patient_id}.pkl")

        # 创建一个损坏的文件
        with open(state_file, 'w') as f:
            f.write("corrupted data")

        # 模拟MedicalAgent的load_state方法返回False
        with patch('session.manager.MedicalAgent') as MockAgent:
            mock_agent_instance = Mock()
            mock_agent_instance.load_state.return_value = False
            MockAgent.return_value = mock_agent_instance

            # 创建新的manager来测试加载
            new_manager = SessionManager(state_dir=self.temp_dir)
            agent = new_manager.get_agent(patient_id)

            # 检查是否尝试加载了状态（但失败了）
            mock_agent_instance.load_state.assert_called_once_with(state_file)
            assert patient_id in new_manager._sessions  # 仍然应该创建新agent