"""
Event-Definitionen für Laufwerke und Dateien.
"""
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class DriveEvent:
    """Event für Laufwerksänderungen."""
    drive: Dict
    connected: bool
    status: Optional[str] = None

@dataclass
class FileEvent:
    """Event für Dateiänderungen."""
    path: str
    event_type: str  # 'new', 'modified', 'deleted'
    info: Optional[Dict] = None
