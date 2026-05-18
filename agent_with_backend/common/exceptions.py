class ConfigurationError(Exception):
    pass


class AgentError(Exception):
    """Base exception for Agent related errors."""
    def __init__(self, message: str = "Agent error occurred") -> None:
        super().__init__(message)


class LLMError(AgentError):
    """Raised when LLM API call fails."""
    def __init__(self, message: str = "LLM error occurred") -> None:
        super().__init__(message)


class ToolExecutionError(AgentError):
    """Raised when a tool execution fails."""
    def __init__(self, message: str = "Tool execution error") -> None:
        super().__init__(message)


class ValidationError(AgentError):
    """Raised when input validation fails."""
    def __init__(self, message: str = "Validation error occurred") -> None:
        super().__init__(message)


class DatabaseError(Exception):
    """Raised when database operation fails."""
    def __init__(self, message: str = "Database error occurred") -> None:
        super().__init__(message)
