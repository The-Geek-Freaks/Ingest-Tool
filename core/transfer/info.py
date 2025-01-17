"""Transfer-Informationen."""

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Optional, Dict, Any

from .status import TransferStatus

@dataclass
class TransferInfo:
    """Informationen über einen Transfer."""
    
    id: str
    source: str
    target: str
    status: TransferStatus = TransferStatus.QUEUED
    progress: float = 0.0
    speed: float = 0.0
    eta: timedelta = field(default_factory=timedelta)
    total_size: int = 0
    copied_size: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other: 'TransferInfo') -> bool:
        """Vergleicht zwei Transfers für die PriorityQueue."""
        # Da wir ein Tupel (priority, transfer_info) in die Queue legen,
        # wird diese Methode nie aufgerufen. Wir implementieren sie trotzdem
        # der Vollständigkeit halber.
        return False
