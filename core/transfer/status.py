"""Transfer-Status."""

from enum import Enum, auto

class TransferStatus(Enum):
    """Status eines Transfers."""
    
    QUEUED = auto()      # Transfer in der Warteschlange
    RUNNING = auto()     # Transfer läuft
    PAUSED = auto()      # Transfer pausiert
    COMPLETED = auto()   # Transfer abgeschlossen
    ERROR = auto()       # Fehler beim Transfer
    CANCELLED = auto()   # Transfer abgebrochen
