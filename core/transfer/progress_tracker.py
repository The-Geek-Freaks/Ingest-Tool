"""Verwaltet die Fortschrittsverfolgung von Transfers."""

import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

class TransferProgress:
    """Tracker für Transfer-Fortschritt mit ETA-Berechnung."""
    
    def __init__(self):
        """Initialisiert den TransferProgress Tracker."""
        self.total_bytes = 0
        self.transferred_bytes = 0
        self.start_time = time.time()
        
        # Tracking für Geschwindigkeitsberechnung
        self.last_update_time = self.start_time
        self.last_bytes = 0
        self.current_speed = 0.0  # Aktuelle Geschwindigkeit in Bytes/s
        
        # Minimale Zeit zwischen Updates für stabile Geschwindigkeit
        self.min_update_interval = 0.1  # 100ms
        
    def _calculate_speed(self, current_time: float, current_bytes: int) -> float:
        """Berechnet die aktuelle Übertragungsgeschwindigkeit.
        
        Args:
            current_time: Aktuelle Zeit in Sekunden
            current_bytes: Aktuell übertragene Bytes
            
        Returns:
            float: Geschwindigkeit in Bytes/s
        """
        time_diff = current_time - self.last_update_time
        bytes_diff = current_bytes - self.last_bytes
        
        # Nur aktualisieren wenn genug Zeit vergangen ist
        if time_diff >= self.min_update_interval:
            if time_diff > 0 and bytes_diff >= 0:
                # Berechne neue Geschwindigkeit
                instant_speed = bytes_diff / time_diff
                
                if self.current_speed > 0:
                    # Sanftere Angleichung (90% neu, 10% alt)
                    self.current_speed = (instant_speed * 0.9) + (self.current_speed * 0.1)
                else:
                    # Erste Messung direkt übernehmen
                    self.current_speed = instant_speed
                
            # Aktualisiere Tracking-Werte
            self.last_update_time = current_time
            self.last_bytes = current_bytes
            
        return max(0.1, self.current_speed)  # Mindestens 0.1 Bytes/s um Division durch 0 zu vermeiden
        
    def update(self, transferred_bytes: int, total_bytes: int) -> float:
        """Aktualisiert den Fortschritt und berechnet die aktuelle Geschwindigkeit.
        
        Args:
            transferred_bytes: Übertragene Bytes
            total_bytes: Gesamtgröße in Bytes
            
        Returns:
            float: Aktuelle Geschwindigkeit in MB/s
        """
        # Speichere alte Werte
        old_transferred = self.transferred_bytes
        
        # Aktualisiere Gesamtwerte
        self.total_bytes = total_bytes
        self.transferred_bytes = transferred_bytes
        
        # Berechne aktuelle Geschwindigkeit in Bytes/s
        current_time = time.time()
        speed = self._calculate_speed(current_time, transferred_bytes)
        
        # Debug-Logging
        bytes_diff = transferred_bytes - old_transferred
        time_diff = current_time - self.last_update_time
        if time_diff > 0:
            instant_speed = bytes_diff / time_diff
            logger.debug(f"Speed calculation: bytes_diff={bytes_diff}, time_diff={time_diff:.3f}s, " 
                      f"instant_speed={instant_speed/1024/1024:.2f}MB/s, smoothed_speed={speed/1024/1024:.2f}MB/s")
        
        # Konvertiere zu MB/s für die Anzeige
        return speed / (1024 * 1024)
        
    def get_progress(self) -> float:
        """Ermittelt den aktuellen Fortschritt in Prozent.
        
        Returns:
            float: Fortschritt (0-100)
        """
        if self.total_bytes == 0:
            return 0
        return (self.transferred_bytes / self.total_bytes) * 100
        
    def get_average_speed(self) -> float:
        """Ermittelt die aktuelle Übertragungsgeschwindigkeit.
        
        Returns:
            float: Geschwindigkeit in MB/s
        """
        return max(0.1, self.current_speed) / (1024 * 1024)
        
    def get_eta(self) -> Optional[float]:
        """Berechnet die geschätzte verbleibende Zeit.
        
        Returns:
            Optional[float]: Geschätzte verbleibende Zeit in Sekunden oder None
        """
        if self.current_speed <= 0:
            return None
            
        remaining_bytes = self.total_bytes - self.transferred_bytes
        if remaining_bytes <= 0:
            return 0
            
        return remaining_bytes / max(0.1, self.current_speed)

    @staticmethod
    def format_time(seconds: Optional[float]) -> str:
        """Formatiert Sekunden in lesbare Zeit.
        
        Args:
            seconds: Zeit in Sekunden
            
        Returns:
            str: Formatierte Zeit
        """
        if seconds is None:
            return "Berechne..."
            
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        return f"{secs}s"
