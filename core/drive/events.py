"""
Event-Definitionen für die Laufwerksüberwachung.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from .status import DriveStatus

@dataclass
class DriveEvent:
    """Event für Laufwerksänderungen."""
    
    # Pfad zum Laufwerk
    drive_path: str
    
    # Alter Status
    old_status: Optional[DriveStatus]
    
    # Neuer Status
    new_status: DriveStatus
    
    # Zeitstempel des Events
    timestamp: datetime = datetime.now()
    
    # Optionale Fehlermeldung
    error_message: Optional[str] = None

@dataclass
class FileEvent:
    """Event für Dateiänderungen."""
    
    # Pfad zur Datei
    file_path: str
    
    # Art des Events (new, modified, deleted)
    event_type: str
    
    # Dateigröße in Bytes
    file_size: int
    
    # Zeitstempel des Events
    timestamp: datetime = datetime.now()
    
    # Optionale Metadaten
    metadata: Optional[dict] = None
