"""Transfer-Einstellungen."""

from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class TransferSettings:
    """Einstellungen für Dateiübertragungen."""
    
    # Thread-Pool Einstellungen
    max_workers: int = 4
    
    # Datei-Übertragung
    chunk_size: int = 8192  # 8KB
    buffer_size: int = 65536  # 64KB
    
    # Fehlerbehandlung
    retry_count: int = 3
    retry_delay: float = 1.0
    timeout: float = 30.0
    
    # UI-Updates
    progress_update_interval: int = 100  # ms
    
    # Verzeichnis-Einstellungen
    create_target_dirs: bool = True  # Erstelle Zielverzeichnisse automatisch
    preserve_timestamps: bool = True  # Behalte Zeitstempel bei
    
    # Zusätzliche Einstellungen
    metadata: Dict[str, Any] = field(default_factory=dict)
