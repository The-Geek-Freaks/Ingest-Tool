"""
VERALTET: Diese Datei ist veraltet und wird in einer zukünftigen Version entfernt.
Bitte verwenden Sie stattdessen core.drive_controller.
"""
import os
import time
import logging
import threading
from queue import Queue
from typing import Dict, List, Optional, Set, Callable
import warnings
warnings.warn(
    "Das Modul core.drive.monitor ist veraltet. "
    "Bitte verwenden Sie stattdessen core.drive_controller.",
    DeprecationWarning,
    stacklevel=2
)

class DriveMonitor:
    """Überwacht Laufwerke auf neue Dateien und Änderungen."""
    
    def __init__(self):
        self._watched_paths = set()
        self._excluded_paths = set()
        self._file_queue = Queue()
        
        # Filter
        self._file_filters = []
        self._size_limit = None
        self._age_limit = None
        
        # Cache für Laufwerksinformationen
        self._drive_cache = {}
        self._cache_lifetime = 300  # 5 Minuten
        self._last_cache_update = 0
        
        # Thread-Management
        self._monitor_threads = {}
        self._stop_event = threading.Event()
        
        # WMI-Client für Windows
        self._wmi_client = None
        try:
            import wmi
            self._wmi_client = wmi.WMI()
        except:
            logging.warning("WMI nicht verfügbar - eingeschränkte Laufwerkserkennung")
            
        # Callbacks
        self._new_file_callback = None
        self._removed_file_callback = None
        self._modified_file_callback = None
        self._error_callback = None
        
    def add_watch_path(self, path: str):
        """Fügt einen Pfad zur Überwachung hinzu."""
        if os.path.exists(path):
            self._watched_paths.add(os.path.abspath(path))
            self._start_monitoring(path)
            
    def remove_watch_path(self, path: str):
        """Entfernt einen überwachten Pfad."""
        abs_path = os.path.abspath(path)
        if abs_path in self._watched_paths:
            self._watched_paths.remove(abs_path)
            if abs_path in self._monitor_threads:
                self._monitor_threads[abs_path].stop()
                del self._monitor_threads[abs_path]
                
    def add_excluded_path(self, path: str):
        """Fügt einen Pfad zur Ausschlussliste hinzu."""
        self._excluded_paths.add(os.path.abspath(path))
        
    def remove_excluded_path(self, path: str):
        """Entfernt einen Pfad von der Ausschlussliste."""
        abs_path = os.path.abspath(path)
        if abs_path in self._excluded_paths:
            self._excluded_paths.remove(abs_path)
            
    def add_file_filter(self, pattern: str):
        """Fügt einen Dateifilter hinzu."""
        if pattern not in self._file_filters:
            self._file_filters.append(pattern)
            
    def set_size_limit(self, max_size: int):
        """Setzt Größenlimit für Dateien."""
        self._size_limit = max_size
        
    def set_age_limit(self, max_age: int):
        """Setzt Alterslimit für Dateien in Sekunden."""
        self._age_limit = max_age
        
    def _monitor_path(self, path: str):
        """Überwacht einen Pfad auf Änderungen."""
        last_scan = {}
        
        while not self._stop_event.is_set():
            try:
                current_scan = self._scan_directory(path)
                
                # Prüfe auf neue und geänderte Dateien
                for file_path, info in current_scan.items():
                    if file_path not in last_scan:
                        if self._new_file_callback:
                            self._new_file_callback(file_path, info)
                    elif info['mtime'] != last_scan[file_path]['mtime']:
                        if self._modified_file_callback:
                            self._modified_file_callback(file_path, info)
                            
                # Prüfe auf gelöschte Dateien
                for file_path in set(last_scan) - set(current_scan):
                    if self._removed_file_callback:
                        self._removed_file_callback(file_path, last_scan[file_path])
                        
                last_scan = current_scan
                time.sleep(1)
                
            except Exception as e:
                if self._error_callback:
                    self._error_callback(str(e))
                time.sleep(5)  # Warte länger bei Fehlern
                
    def _scan_directory(self, path: str) -> Dict:
        """Scannt ein Verzeichnis rekursiv.
        
        Returns:
            Dict mit Dateipfaden und Informationen
        """
        results = {}
        
        for root, _, files in os.walk(path):
            if root in self._excluded_paths:
                continue
                
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    stat = os.stat(file_path)
                    info = {
                        'size': stat.st_size,
                        'mtime': stat.st_mtime,
                        'ctime': stat.st_ctime
                    }
                    
                    if self._check_file_filters(file_path, info):
                        results[file_path] = info
                        
                except Exception as e:
                    if self._error_callback:
                        self._error_callback(f"Fehler beim Scannen von {file_path}: {e}")
                        
        return results
        
    def _check_file_filters(self, file_path: str, info: Dict) -> bool:
        """Prüft ob eine Datei die Filter erfüllt."""
        # Größenfilter
        if self._size_limit and info['size'] > self._size_limit:
            return False
            
        # Altersfilter
        if self._age_limit:
            age = time.time() - info['mtime']
            if age > self._age_limit:
                return False
                
        # Dateifilter
        if self._file_filters:
            import fnmatch
            return any(fnmatch.fnmatch(file_path, pattern)
                      for pattern in self._file_filters)
                      
        return True
        
    def get_available_drives(self) -> List[Dict]:
        """Ermittelt verfügbare Laufwerke.
        
        Returns:
            Liste mit Laufwerksinformationen
        """
        # Cache aktualisieren wenn nötig
        current_time = time.time()
        if (current_time - self._last_cache_update) > self._cache_lifetime:
            self._drive_cache = {}
            if self._wmi_client:
                for drive in self._wmi_client.Win32_LogicalDisk():
                    self._drive_cache[drive.DeviceID] = {
                        'letter': drive.DeviceID,
                        'label': drive.VolumeName or "Laufwerk",
                        'type': drive.DriveType,
                        'size': int(drive.Size) if drive.Size else 0,
                        'free': int(drive.FreeSpace) if drive.FreeSpace else 0
                    }
            self._last_cache_update = current_time
            
        return list(self._drive_cache.values())
        
    def get_removable_drives(self) -> List[Dict]:
        """Ermittelt nur Wechseldatenträger."""
        return [drive for drive in self.get_available_drives()
                if drive['type'] == 2]  # 2 = Removable
                
    def get_network_drives(self) -> List[Dict]:
        """Ermittelt nur Netzwerklaufwerke."""
        return [drive for drive in self.get_available_drives()
                if drive['type'] == 4]  # 4 = Network Drive
                
    def set_new_file_callback(self, callback: Callable):
        """Setzt Callback für neue Dateien."""
        self._new_file_callback = callback
        
    def set_removed_file_callback(self, callback: Callable):
        """Setzt Callback für gelöschte Dateien."""
        self._removed_file_callback = callback
        
    def set_modified_file_callback(self, callback: Callable):
        """Setzt Callback für geänderte Dateien."""
        self._modified_file_callback = callback
        
    def set_error_callback(self, callback: Callable):
        """Setzt Callback für Fehler."""
        self._error_callback = callback
        
    def get_next_file_event(self, timeout: Optional[float] = None):
        """Holt nächstes Dateiereignis aus der Queue.
        
        Args:
            timeout: Timeout in Sekunden oder None für unbegrenzt
            
        Returns:
            Tuple (event_type, file_path, info) oder None bei Timeout
        """
        try:
            return self._file_queue.get(timeout=timeout)
        except:
            return None
            
    def stop(self):
        """Stoppt alle Überwachungen."""
        self._stop_event.set()
        for thread in self._monitor_threads.values():
            thread.join()
        self._monitor_threads.clear()
        
    def clear_file_filters(self):
        """Löscht alle Dateifilter."""
        self._file_filters.clear()
        
    def get_watch_paths(self) -> Set[str]:
        """Liefert Liste der überwachten Pfade."""
        return self._watched_paths.copy()
        
    def get_excluded_paths(self) -> Set[str]:
        """Liefert Liste der ausgeschlossenen Pfade."""
        return self._excluded_paths.copy()
        
    def get_file_filters(self) -> List[str]:
        """Liefert Liste der Dateifilter."""
        return self._file_filters.copy()
