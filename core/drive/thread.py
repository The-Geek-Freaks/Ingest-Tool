"""
Thread-basierte Laufwerksüberwachung.
"""
import os
import logging
import threading
from typing import Set, Dict, List
from PyQt5.QtCore import QThread, pyqtSignal

from .status import DriveStatus

class DriveMonitorThread(QThread):
    """Thread zur Überwachung von Laufwerken und Dateien."""
    
    # Signale für UI-Updates
    drive_connected = pyqtSignal(dict)  # Laufwerks-Dictionary
    drive_disconnected = pyqtSignal(dict)  # Laufwerks-Dictionary
    file_found = pyqtSignal(str)
    copy_progress = pyqtSignal(str, str, int, int)  # source, target, current, total
    file_moved = pyqtSignal(str, str)  # source, target
    duplicate_found = pyqtSignal(str, str)  # source, target
    transfer_failed = pyqtSignal(str)  # error message
    drive_status_changed = pyqtSignal(str, str)  # drive, status
    
    def __init__(self, watch_paths=None, file_types=None, delete_source=False):
        super().__init__()
        
        self.watch_paths = watch_paths or []
        self.file_types = [ext.lower() if not ext.startswith('.')
                          else ext[1:].lower() 
                          for ext in (file_types or [])]
        self.delete_source = delete_source
        
        self.running = True
        self._known_drives = set()  # Set von Pfaden
        self._known_files = set()
        self._drive_status = {}  # Pfad -> Status
        self._active_transfers = {}  # Pfad -> Liste von Transfers
        self._lock = threading.Lock()
        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
    def check_drives(self):
        """Prüft auf neue oder entfernte Laufwerke."""
        import wmi
        wmi_obj = wmi.WMI()
        
        current_drives = set()
        for drive in wmi_obj.Win32_LogicalDisk():
            if drive.DriveType in [2, 3]:  # Removable or Fixed disk
                drive_info = {
                    'letter': drive.DeviceID,
                    'name': drive.VolumeName or "Wechseldatenträger",
                    'size': int(drive.Size) if drive.Size else 0,
                    'free': int(drive.FreeSpace) if drive.FreeSpace else 0,
                    'type': 'removable' if drive.DriveType == 2 else 'fixed'
                }
                current_drives.add(drive.DeviceID)
                
                if drive.DeviceID not in self._known_drives:
                    self._known_drives.add(drive.DeviceID)
                    self.drive_connected.emit(drive_info)
                    self._drive_status[drive.DeviceID] = DriveStatus.BEREIT
                    self.drive_status_changed.emit(drive.DeviceID, DriveStatus.BEREIT)
                    
        # Prüfe auf entfernte Laufwerke
        for drive in list(self._known_drives):
            if drive not in current_drives:
                self._known_drives.remove(drive)
                self.drive_disconnected.emit({'letter': drive})
                if drive in self._drive_status:
                    del self._drive_status[drive]
                    
    def scan_drives(self):
        """Scannt Laufwerke nach neuen Dateien."""
        for drive in self._known_drives:
            if not os.path.exists(drive):
                continue
                
            if self._drive_status.get(drive) != DriveStatus.BEREIT:
                continue
                
            self._scan_drive(drive)
            
    def _scan_drive(self, drive_path):
        """Scannt ein einzelnes Laufwerk."""
        try:
            for root, _, files in os.walk(drive_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Prüfe Dateiendung
                    if not any(file.lower().endswith(f".{ext}")
                             for ext in self.file_types):
                        continue
                        
                    # Prüfe ob Datei bereits bekannt
                    if file_path in self._known_files:
                        continue
                        
                    self._known_files.add(file_path)
                    self.file_found.emit(file_path)
                    
        except Exception as e:
            self.logger.error(f"Fehler beim Scannen von {drive_path}: {e}")
            self._drive_status[drive_path] = DriveStatus.FEHLER
            self.drive_status_changed.emit(drive_path, DriveStatus.FEHLER)
            
    def run(self):
        """Hauptschleife des Threads."""
        while self.running:
            try:
                with self._lock:
                    self.check_drives()
                    self.scan_drives()
            except Exception as e:
                self.logger.error(f"Fehler in der Hauptschleife: {e}")
                
            self.msleep(1000)  # 1 Sekunde warten
            
    def stop(self):
        """Stoppt den Thread."""
        self.running = False
        
    def update_watch_paths(self, paths):
        """Aktualisiert die zu überwachenden Pfade."""
        with self._lock:
            self.watch_paths = paths
            
    def update_file_types(self, types):
        """Aktualisiert die zu überwachenden Dateitypen."""
        with self._lock:
            self.file_types = [ext.lower() if not ext.startswith('.')
                             else ext[1:].lower() 
                             for ext in types]
            
    def update_delete_source(self, delete):
        """Aktualisiert die Delete-Source-Option."""
        with self._lock:
            self.delete_source = delete
            
    def get_connected_drives(self) -> List[Dict]:
        """Gibt eine Liste der verbundenen Laufwerke zurück."""
        drives = []
        for drive in self._known_drives:
            status = self._drive_status.get(drive, DriveStatus.GETRENNT)
            if status != DriveStatus.GETRENNT:
                drives.append({
                    'letter': drive,
                    'name': os.path.splitdrive(drive)[0],
                    'status': status
                })
        return drives
