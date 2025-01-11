"""
Einfache Cache-Implementierung ohne externe Abhängigkeiten.
"""
import time
from typing import Dict, Any, Optional, Tuple

class SimpleCache:
    """Ein einfacher zeitbasierter Cache."""
    
    def __init__(self, ttl_seconds: int = 300):
        """Initialisiert den Cache.
        
        Args:
            ttl_seconds: Zeit in Sekunden, nach der ein Cache-Eintrag ungültig wird
        """
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._ttl = ttl_seconds
        
    def get(self, key: str) -> Optional[Any]:
        """Holt einen Wert aus dem Cache.
        
        Args:
            key: Schlüssel des Werts
            
        Returns:
            Den Wert wenn vorhanden und nicht abgelaufen, sonst None
        """
        if key not in self._cache:
            return None
            
        value, timestamp = self._cache[key]
        if time.time() - timestamp > self._ttl:
            del self._cache[key]
            return None
            
        return value
        
    def set(self, key: str, value: Any):
        """Speichert einen Wert im Cache.
        
        Args:
            key: Schlüssel unter dem der Wert gespeichert wird
            value: Zu speichernder Wert
        """
        self._cache[key] = (value, time.time())
        
    def clear(self):
        """Leert den Cache."""
        self._cache.clear()
