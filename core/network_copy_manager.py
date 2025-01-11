"""
Network Copy Manager (Legacy-Import).
Bitte das neue Modul core.network verwenden.
"""

from .network import (
    NetworkCopyManager,
    CopyAborted,
    CopyVerificationError,
    TransferStatus,
    QoSLevel
)

__all__ = [
    'NetworkCopyManager',
    'CopyAborted',
    'CopyVerificationError',
    'TransferStatus',
    'QoSLevel'
]
