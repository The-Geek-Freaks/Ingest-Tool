"""
Hauptklasse für Metadaten-Verwaltung.
"""
import os
import logging
from pathlib import Path
from typing import Dict, Optional, Type

from .types import FileType, MetadataDict
from .cache import MetadataCache
from .rules import ValidationRules
from .handlers import (
    BaseHandler,
    ImageHandler,
    VideoHandler,
    AudioHandler,
    DocumentHandler
)
from utils.hasher import calculate_file_hash

class MetadataHandler:
    """Behandelt die Übertragung und Verwaltung von Datei-Metadaten."""
    
    def __init__(self):
        # Initialisiere Komponenten
        self._cache = MetadataCache()
        self._rules = ValidationRules()
        
        # Handler für verschiedene Dateitypen
        self._handlers: Dict[str, BaseHandler] = {
            FileType.IMAGE: ImageHandler(),
            FileType.VIDEO: VideoHandler(),
            FileType.AUDIO: AudioHandler(),
            FileType.DOCUMENT: DocumentHandler()
        }
        
    def get_file_metadata(self, filepath: str, force_refresh: bool = False) -> Optional[MetadataDict]:
        """Ermittelt die Metadaten einer Datei.
        
        Args:
            filepath: Pfad zur Datei
            force_refresh: Erzwingt eine Neuberechnung der Metadaten
            
        Returns:
            Dict mit Metadaten oder None bei Fehler
        """
        try:
            filepath = str(Path(filepath))
            
            # Prüfe Cache wenn nicht erzwungen
            if not force_refresh:
                cached = self._cache.get(filepath)
                if cached:
                    return cached
                    
            # Basis-Metadaten
            stat = os.stat(filepath)
            metadata: MetadataDict = {
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'created': stat.st_ctime,
                'quick_hash': self.get_quick_hash(filepath),
                'permissions': stat.st_mode
            }
            
            # Dateityp bestimmen
            ext = os.path.splitext(filepath)[1].lower()
            file_type = FileType.get_type(ext)
            
            # Erweiterte Metadaten über Handler
            if file_type and file_type in self._handlers:
                try:
                    extended = self._handlers[file_type].extract(filepath)
                    if extended:
                        metadata.update(extended)
                except Exception as e:
                    logging.warning(f"Fehler bei erweiterten Metadaten: {e}")
                    
            # Erweiterte Attribute
            try:
                import xattr
                attrs = xattr.listxattr(filepath)
                if attrs:
                    metadata['xattr'] = {
                        attr: xattr.getxattr(filepath, attr)
                        for attr in attrs
                    }
            except ImportError:
                pass
            except Exception as e:
                logging.warning(f"Fehler bei erweiterten Attributen: {e}")
                
            # Validiere Metadaten
            if file_type:
                self._rules.validate(metadata, file_type)
                
            # Speichere im Cache
            self._cache.add(filepath, metadata)
            
            return metadata
            
        except Exception as e:
            logging.error(f"Fehler beim Ermitteln der Metadaten: {e}")
            return None
            
    def add_custom_handler(self, file_type: str, handler: BaseHandler):
        """Fügt einen benutzerdefinierten Handler hinzu."""
        if not isinstance(handler, BaseHandler):
            raise TypeError("Handler muss von BaseHandler erben")
        self._handlers[file_type] = handler
        
    def add_validation_rule(self, file_type: str, rule: Dict):
        """Fügt eine neue Validierungsregel hinzu."""
        self._rules.add_rule(file_type, rule)
        
    def clear_cache(self):
        """Leert den Metadaten-Cache."""
        self._cache.clear()
        
    @staticmethod
    def get_full_hash(filepath: str) -> str:
        """Berechnet den vollständigen Hash der Datei."""
        result = calculate_file_hash(filepath, 'sha256')
        if result is None:
            raise RuntimeError(f"Konnte Hash nicht berechnen für: {filepath}")
        return result
    
    @staticmethod
    def get_quick_hash(filepath: str, sample_size: int = 65536) -> str:
        """Berechnet einen schnellen Hash der ersten und letzten Bytes."""
        try:
            size = os.path.getsize(filepath)
            if size == 0:
                return "empty"
                
            with open(filepath, 'rb') as f:
                # Lese Anfang
                start = f.read(min(sample_size, size))
                
                # Lese Ende wenn Datei groß genug
                if size > sample_size:
                    f.seek(max(0, size - sample_size))
                    end = f.read(sample_size)
                else:
                    end = b""
                    
                # Kombiniere Größe und Samples
                combined = f"{size}:{start}:{end}".encode('utf-8')
                return calculate_file_hash(combined, 'sha256')
                
        except Exception as e:
            logging.error(f"Fehler beim Quick-Hash von {filepath}: {e}")
            return ""
