import asyncio
import logging
from typing import Any, Dict, Callable
from common.exceptions import ToolExecutionError

logger = logging.getLogger(__name__)


class ToolExecutor:
    """工具执行器，统一管理工具调用"""

    def __init__(self):
        self._handlers: Dict[str, Callable] = {}

    def register_handler(self, name: str, handler: Callable) -> None:
        self._handlers[name] = handler
        logger.info(f"Registered tool handler: {name}")

    def execute(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        if tool_name not in self._handlers:
            raise ToolExecutionError(f"Unknown tool: {tool_name}")

        handler = self._handlers[tool_name]
        try:
            if asyncio.iscoroutinefunction(handler):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(handler(**tool_input))
                loop.close()
            else:
                result = handler(**tool_input)
            return str(result)
        except Exception as e:
            logger.exception(f"Tool {tool_name} execution failed")
            raise ToolExecutionError(f"Tool {tool_name} failed: {str(e)}")

    def get_registered_tools(self) -> list:
        return list(self._handlers.keys())

    def is_registered(self, name: str) -> bool:
        return name in self._handlers
