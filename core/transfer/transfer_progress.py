#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Klasse für das Tracking des Transfer-Fortschritts.
"""

import time
from typing import Optional
from collections import deque
import threading
from datetime import timedelta

class TransferProgress:
    """Thread-sichere Klasse zum Tracking von Dateitransfers."""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._start_time = time.time()
        self._last_update = self._start_time
        self._last_bytes = 0
        self._total_bytes = 0
        self._transferred_bytes = 0
        self._current_speed = 0.0
        self._speed_history = deque(maxlen=5)  # Für geglättete Geschwindigkeit
        self._progress = 0.0
        self._eta = timedelta(seconds=0)
        
    def update(self, transferred_bytes: int, total_bytes: int = None) -> float:
        """Aktualisiert den Fortschritt und berechnet die Geschwindigkeit.
        
        Args:
            transferred_bytes: Anzahl der übertragenen Bytes
            total_bytes: Gesamtgröße in Bytes (optional)
            
        Returns:
            float: Aktuelle Übertragungsgeschwindigkeit in Bytes/Sekunde
        """
        with self._lock:
            current_time = time.time()
            time_diff = current_time - self._last_update
            
            # Update nur alle 100ms
            if time_diff >= 0.1:
                if total_bytes is not None:
                    self._total_bytes = total_bytes
                
                self._transferred_bytes = transferred_bytes
                bytes_diff = transferred_bytes - self._last_bytes
                
                # Berechne Geschwindigkeit
                if time_diff > 0:
                    current_speed = bytes_diff / time_diff
                    self._speed_history.append(current_speed)
                    # Berechne geglättete Geschwindigkeit über die letzten 5 Messungen
                    self._current_speed = sum(self._speed_history) / len(self._speed_history)
                
                # Berechne Fortschritt
                if self._total_bytes > 0:
                    self._progress = (transferred_bytes / self._total_bytes) * 100
                    
                    # Berechne ETA
                    if self._current_speed > 0:
                        remaining_bytes = self._total_bytes - transferred_bytes
                        eta_seconds = remaining_bytes / self._current_speed
                        self._eta = timedelta(seconds=int(eta_seconds))
                
                self._last_bytes = transferred_bytes
                self._last_update = current_time
            
            return self._current_speed
            
    def get_progress(self) -> float:
        """Gibt den aktuellen Fortschritt zurück.
        
        Returns:
            float: Fortschritt in Prozent
        """
        with self._lock:
            return self._progress
            
    def get_speed(self) -> float:
        """Gibt die aktuelle Übertragungsgeschwindigkeit zurück.
        
        Returns:
            float: Geschwindigkeit in Bytes/Sekunde
        """
        with self._lock:
            return self._current_speed
            
    def get_eta(self) -> timedelta:
        """Gibt die geschätzte verbleibende Zeit zurück.
        
        Returns:
            timedelta: Geschätzte verbleibende Zeit
        """
        with self._lock:
            return self._eta
            
    def get_total_bytes(self) -> int:
        """Gibt die Gesamtgröße zurück.
        
        Returns:
            int: Gesamtgröße in Bytes
        """
        with self._lock:
            return self._total_bytes
            
    def get_transferred_bytes(self) -> int:
        """Gibt die Anzahl der übertragenen Bytes zurück.
        
        Returns:
            int: Übertragene Bytes
        """
        with self._lock:
            return self._transferred_bytes
            
    @property
    def elapsed_time(self) -> timedelta:
        """Gibt die verstrichene Zeit seit Start zurück."""
        with self._lock:
            return timedelta(seconds=int(time.time() - self._start_time))
