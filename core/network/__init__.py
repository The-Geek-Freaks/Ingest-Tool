"""
Netzwerkoperationen und -verwaltung.
"""

from .manager import NetworkManager
from .copy_manager import NetworkCopyManager
from .errors import (
    NetworkError,
    ConnectionError,
    TransferError,
    CopyAborted,
    CopyVerificationError
)
from .types import (
    NetworkPath,
    TransferStatus,
    QoSLevel,
    NetworkStats
)

__all__ = [
    'NetworkManager',
    'NetworkCopyManager',
    'NetworkError',
    'ConnectionError',
    'TransferError',
    'CopyAborted',
    'CopyVerificationError',
    'NetworkPath',
    'TransferStatus',
    'QoSLevel',
    'NetworkStats'
]
