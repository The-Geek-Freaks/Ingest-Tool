"""
Statusdefinitionen für Laufwerke und deren Überwachung.
"""
from enum import Enum, auto

class DriveStatus(Enum):
    """Status eines Laufwerks oder Verzeichnisses."""
    
    # Laufwerk ist bereit und wird überwacht
    READY = auto()
    
    # Laufwerk wird gerade initialisiert
    INITIALIZING = auto()
    
    # Laufwerk ist nicht verfügbar oder nicht eingebunden
    UNAVAILABLE = auto()
    
    # Laufwerk ist voll
    FULL = auto()
    
    # Laufwerk ist schreibgeschützt
    READ_ONLY = auto()
    
    # Laufwerk wird gerade gescannt
    SCANNING = auto()
    
    # Fehler beim Zugriff auf das Laufwerk
    ERROR = auto()
    
    # Laufwerk ist pausiert (keine Überwachung)
    PAUSED = auto()
    
    # Laufwerk wird gerade entfernt
    REMOVING = auto()
    
    def is_active(self) -> bool:
        """Prüft ob das Laufwerk aktiv überwacht wird."""
        return self in (
            DriveStatus.READY,
            DriveStatus.SCANNING,
            DriveStatus.INITIALIZING
        )
        
    def can_write(self) -> bool:
        """Prüft ob auf das Laufwerk geschrieben werden kann."""
        return self in (
            DriveStatus.READY,
            DriveStatus.SCANNING,
            DriveStatus.INITIALIZING
        )
        
    def is_error(self) -> bool:
        """Prüft ob ein Fehlerzustand vorliegt."""
        return self in (
            DriveStatus.ERROR,
            DriveStatus.UNAVAILABLE,
            DriveStatus.FULL,
            DriveStatus.READ_ONLY
        )
        
    @property
    def description(self) -> str:
        """Liefert eine menschenlesbare Beschreibung des Status."""
        descriptions = {
            DriveStatus.READY: "Bereit",
            DriveStatus.INITIALIZING: "Wird initialisiert",
            DriveStatus.UNAVAILABLE: "Nicht verfügbar",
            DriveStatus.FULL: "Laufwerk voll",
            DriveStatus.READ_ONLY: "Schreibgeschützt",
            DriveStatus.SCANNING: "Wird gescannt",
            DriveStatus.ERROR: "Fehler",
            DriveStatus.PAUSED: "Pausiert",
            DriveStatus.REMOVING: "Wird entfernt"
        }
        return descriptions.get(self, "Unbekannt")
