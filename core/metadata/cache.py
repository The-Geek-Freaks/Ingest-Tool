"""
Cache für Metadaten.
"""
import time
import threading
from typing import Dict, Optional
from .types import MetadataDict

class MetadataCache:
    """Cache für Metadaten mit Thread-Sicherheit."""
    
    def __init__(self, lifetime: int = 300, max_size: int = 1000):
        """
        Args:
            lifetime: Cache-Lebensdauer in Sekunden
            max_size: Maximale Anzahl an Cache-Einträgen
        """
        self._cache: Dict[str, tuple[MetadataDict, float]] = {}
        self._lock = threading.Lock()
        self._lifetime = lifetime
        self._max_size = max_size
        
    def get(self, filepath: str) -> Optional[MetadataDict]:
        """Holt Metadaten aus dem Cache."""
        with self._lock:
            if filepath not in self._cache:
                return None
                
            metadata, timestamp = self._cache[filepath]
            if time.time() - timestamp > self._lifetime:
                del self._cache[filepath]
                return None
                
            return metadata.copy()
            
    def add(self, filepath: str, metadata: MetadataDict):
        """Fügt Metadaten zum Cache hinzu."""
        with self._lock:
            # Entferne ältesten Eintrag wenn Cache voll
            if len(self._cache) >= self._max_size:
                oldest = min(self._cache.items(),
                           key=lambda x: x[1][1])
                del self._cache[oldest[0]]
                
            self._cache[filepath] = (metadata.copy(), time.time())
            
    def clear(self):
        """Leert den Cache."""
        with self._lock:
            self._cache.clear()
            
    def remove(self, filepath: str):
        """Entfernt einen Eintrag aus dem Cache."""
        with self._lock:
            if filepath in self._cache:
                del self._cache[filepath]
