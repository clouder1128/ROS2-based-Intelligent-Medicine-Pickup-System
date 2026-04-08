try:
    from .manager import MessageManager
    from .compressor import (
        compress_messages_by_tokens,
        compress_messages_by_count,
        smart_compress,
    )
except ImportError:
    MessageManager = None
    compress_messages_by_tokens = None
    compress_messages_by_count = None
    smart_compress = None

__all__ = [
    "MessageManager",
    "compress_messages_by_tokens",
    "compress_messages_by_count",
    "smart_compress",
]
