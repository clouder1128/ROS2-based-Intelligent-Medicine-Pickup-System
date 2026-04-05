try:
    from .manager import SessionManager
except ImportError:
    SessionManager = None

__all__ = ['SessionManager']