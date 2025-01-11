"""
Prioritätsverwaltung für Dateiübertragungen.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Any, Optional
from datetime import datetime

class TransferPriority(Enum):
    """Prioritätsstufen für Übertragungen."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3
    
@dataclass
class PriorityQueueItem:
    """Ein Element in der Prioritätswarteschlange."""
    priority: TransferPriority
    timestamp: datetime
    data: Any
    
    def __lt__(self, other):
        """Vergleichsoperator für die Prioritätswarteschlange."""
        if not isinstance(other, PriorityQueueItem):
            return NotImplemented
            
        # Vergleiche zuerst nach Priorität
        if self.priority != other.priority:
            return self.priority.value > other.priority.value
            
        # Bei gleicher Priorität nach Zeitstempel
        return self.timestamp < other.timestamp
