"""
Worker-Pool für parallele Dateiübertragungen.
"""

import logging
import threading
import queue
from typing import Callable, Dict, Optional
from datetime import datetime

class WorkerPool:
    """Verwaltet einen Pool von Worker-Threads für Dateiübertragungen."""
    
    def __init__(self, max_workers: int = 4):
        self._max_workers = max_workers
        self._active_workers = 0
        self._worker_lock = threading.Lock()
        self._worker_threads = []
        self._stop_event = threading.Event()
        
        # Callback für Worker-Funktion
        self._worker_callback: Optional[Callable] = None
        
    def start(self, worker_callback: Callable):
        """Startet den Worker-Pool."""
        self._worker_callback = worker_callback
        for _ in range(self._max_workers):
            self._start_worker()
            
    def _start_worker(self):
        """Startet einen einzelnen Worker-Thread."""
        thread = threading.Thread(target=self._worker_loop)
        thread.daemon = True
        thread.start()
        self._worker_threads.append(thread)
        
    def _worker_loop(self):
        """Hauptschleife eines Worker-Threads."""
        while not self._stop_event.is_set():
            try:
                with self._worker_lock:
                    self._active_workers += 1
                try:
                    # Rufe Worker-Callback auf
                    if self._worker_callback:
                        self._worker_callback()
                finally:
                    with self._worker_lock:
                        self._active_workers -= 1
            except Exception as e:
                logging.error(f"Worker-Fehler: {e}")
                
    def adjust_workers(self, new_max_workers: int):
        """Passt die Anzahl der Worker-Threads an."""
        with self._worker_lock:
            self._max_workers = max(1, new_max_workers)
            
            # Starte neue Worker wenn nötig
            while (
                len(self._worker_threads) < self._max_workers and 
                not self._stop_event.is_set()
            ):
                self._start_worker()
                
    def get_active_workers(self) -> int:
        """Gibt die Anzahl aktiver Worker zurück."""
        return self._active_workers
        
    def shutdown(self, wait: bool = True):
        """Fährt den Worker-Pool herunter."""
        self._stop_event.set()
        
        if wait:
            for thread in self._worker_threads:
                thread.join()
                
        self._worker_threads.clear()
