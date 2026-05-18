# tests/thought_logging/test_output.py
import os
import json
import tempfile
import shutil
from unittest.mock import Mock, patch
from agent_with_backend.P1.thought_logging.output import (
    OutputManager,
    JSONFileWriter,
    TextFileWriter,
    TerminalLogger
)
from agent_with_backend.P1.thought_logging.config import ThoughtLoggingConfig

def test_json_file_writer():
    """测试JSON文件写入器"""
    with tempfile.TemporaryDirectory() as temp_dir:
        writer = JSONFileWriter(temp_dir)

        # 测试写入单个记录
        thought = {
            "type": "test",
            "timestamp": 1234567890,
            "session_id": "test_session"
        }

        writer.write_thought(thought)

        # 验证文件存在
        session_dir = os.path.join(temp_dir, "test_session")
        json_file = os.path.join(session_dir, "thoughts.json")
        assert os.path.exists(json_file)

        # 验证JSON内容
        with open(json_file, 'r') as f:
            data = json.load(f)
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["type"] == "test"

def test_json_file_writer_append():
    """测试JSON文件追加写入"""
    with tempfile.TemporaryDirectory() as temp_dir:
        writer = JSONFileWriter(temp_dir)

        # 写入第一条记录
        thought1 = {"type": "first", "id": 1, "session_id": "test_session"}
        writer.write_thought(thought1)

        # 写入第二条记录
        thought2 = {"type": "second", "id": 2, "session_id": "test_session"}
        writer.write_thought(thought2)

        # 验证两条记录都在文件中
        session_dir = os.path.join(temp_dir, thought1["session_id"])
        json_file = os.path.join(session_dir, "thoughts.json")

        with open(json_file, 'r') as f:
            data = json.load(f)
            assert len(data) == 2
            assert data[0]["id"] == 1
            assert data[1]["id"] == 2

def test_text_file_writer():
    """测试文本文件写入器"""
    with tempfile.TemporaryDirectory() as temp_dir:
        writer = TextFileWriter(temp_dir)

        thought = {
            "type": "llm_call",
            "timestamp": 1234567890,
            "formatted_timestamp": "2026-04-17 09:44:11.858",
            "session_id": "test_session",
            "iteration": 1,
            "messages": [{"role": "user", "content": "测试"}],
            "response": {"content": "响应内容"}
        }

        writer.write_thought(thought)

        # 验证文件存在
        session_dir = os.path.join(temp_dir, "test_session")
        text_file = os.path.join(session_dir, "thoughts.log")
        assert os.path.exists(text_file)

        # 验证文本内容
        with open(text_file, 'r') as f:
            content = f.read()
            assert "LLM Call" in content
            assert "test_session" in content
            assert "迭代: 1" in content

def test_terminal_logger():
    """测试终端日志记录器"""
    with patch('builtins.print') as mock_print:
        logger = TerminalLogger(enabled=True)

        thought = {
            "type": "tool_decision",
            "tool_name": "query_drug",
            "iteration": 2
        }

        logger.log(thought)

        # 验证print被调用
        assert mock_print.called
        call_args = mock_print.call_args[0][0]
        assert "Tool Decision" in call_args
        assert "query_drug" in call_args

def test_output_manager():
    """测试OutputManager协调输出"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = ThoughtLoggingConfig(
            enabled=True,
            log_to_file=True,
            log_to_console=False,
            log_dir=temp_dir
        )

        manager = OutputManager(config)

        # 验证组件已初始化
        assert manager.config == config
        assert manager.json_writer is not None
        assert manager.text_writer is not None
        assert manager.terminal_logger is not None
        assert manager.terminal_logger.enabled == False  # 配置中log_to_console=False

        # 测试写入思考记录
        thought = {
            "type": "llm_call",
            "session_id": "test_session"
        }

        # Mock各个写入器的write_thought方法
        with patch.object(manager.json_writer, 'write_thought') as mock_json, \
             patch.object(manager.text_writer, 'write_thought') as mock_text, \
             patch.object(manager.terminal_logger, 'log') as mock_terminal:

            manager.write_thought(thought)

            # 验证所有写入器都被调用
            mock_json.assert_called_once_with(thought)
            mock_text.assert_called_once_with(thought)
            mock_terminal.assert_not_called()  # 终端日志禁用

def test_output_manager_with_console():
    """测试启用终端输出的OutputManager"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = ThoughtLoggingConfig(
            enabled=True,
            log_to_file=True,
            log_to_console=True,
            log_dir=temp_dir
        )

        manager = OutputManager(config)
        assert manager.terminal_logger.enabled == True

        thought = {"type": "test"}

        with patch.object(manager.json_writer, 'write_thought'), \
             patch.object(manager.text_writer, 'write_thought'), \
             patch.object(manager.terminal_logger, 'log') as mock_terminal:

            manager.write_thought(thought)
            mock_terminal.assert_called_once_with(thought)

def test_output_manager_file_only_formats():
    """测试仅文件格式的输出"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = ThoughtLoggingConfig(
            enabled=True,
            log_to_file=True,
            log_to_console=False,
            log_dir=temp_dir,
            log_formats=["json"]  # 仅JSON格式
        )

        manager = OutputManager(config)

        thought = {"type": "test", "session_id": "test_session"}

        # 验证只有JSON写入器被初始化
        assert manager.json_writer is not None
        assert manager.text_writer is None  # text格式未启用

        # 写入应该只调用JSON写入器
        session_dir = os.path.join(temp_dir, "test_session")
        json_file = os.path.join(session_dir, "thoughts.json")

        # 确保文件不存在
        if os.path.exists(json_file):
            os.remove(json_file)

        manager.write_thought(thought)

        # 验证JSON文件已创建
        assert os.path.exists(json_file)

        # 验证没有text文件
        text_file = os.path.join(session_dir, "thoughts.log")
        assert not os.path.exists(text_file)