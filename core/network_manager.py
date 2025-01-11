"""
Network Manager (Legacy-Import).
Bitte das neue Modul core.network verwenden.
"""

from .network import (
    NetworkManager,
    NetworkError,
    ConnectionError,
    TransferError,
    NetworkPath,
    NetworkStats,
    QoSLevel
)

__all__ = [
    'NetworkManager',
    'NetworkError',
    'ConnectionError',
    'TransferError',
    'NetworkPath',
    'NetworkStats',
    'QoSLevel'
]
