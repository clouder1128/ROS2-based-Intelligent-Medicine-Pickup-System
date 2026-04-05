try:
    from .registry import TOOLS, register_tool_handler, execute_tool, get_registered_tools, is_tool_registered
    from .base import BaseTool
    from .executor import ToolExecutor
except ImportError:
    TOOLS = []
    register_tool_handler = None
    execute_tool = None
    get_registered_tools = None
    is_tool_registered = None
    BaseTool = None
    ToolExecutor = None

__all__ = ['TOOLS', 'register_tool_handler', 'execute_tool', 'get_registered_tools', 'is_tool_registered', 'BaseTool', 'ToolExecutor']