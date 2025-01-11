"""
Controller für Laufwerksüberwachung.
"""
import logging
from PyQt5.QtCore import QObject, pyqtSignal

from core.drive_monitor import DriveMonitorThread

class DriveController(QObject):
    """Controller für Laufwerksüberwachung."""
    
    # Signale
    on_drive_connected = pyqtSignal(str)  # drive_path
    on_drive_disconnected = pyqtSignal(str)  # drive_path
    on_file_found = pyqtSignal(str)  # file_path
    
    def __init__(self):
        super().__init__()
        self.monitor_thread = None
        self.watch_paths = []
        self.file_types = []
        self.excluded_drives = []
        
    def start_monitoring(self):
        """Startet die Laufwerksüberwachung."""
        try:
            if not self.monitor_thread:
                self.monitor_thread = DriveMonitorThread(
                    self.watch_paths,
                    self.file_types,
                    excluded_drives=self.excluded_drives
                )
                
                # Verbinde Signale
                self.monitor_thread.drive_status_changed.connect(
                    lambda path, connected: self._handle_drive_status(path, connected)
                )
                self.monitor_thread.file_found.connect(self.on_file_found.emit)
                
                # Starte Thread
                self.monitor_thread.start()
                logging.info("Laufwerksüberwachung gestartet")
                
        except Exception as e:
            logging.error(f"Fehler beim Starten der Laufwerksüberwachung: {str(e)}")
            
    def stop_monitoring(self):
        """Stoppt die Laufwerksüberwachung."""
        try:
            if self.monitor_thread:
                self.monitor_thread.stop()
                self.monitor_thread.wait()
                self.monitor_thread = None
                logging.info("Laufwerksüberwachung gestoppt")
                
        except Exception as e:
            logging.error(f"Fehler beim Stoppen der Laufwerksüberwachung: {str(e)}")
            
    def set_watch_paths(self, paths):
        """Setzt die zu überwachenden Pfade."""
        self.watch_paths = paths
        
    def set_file_types(self, types):
        """Setzt die zu überwachenden Dateitypen."""
        self.file_types = types
        
    def set_excluded_drives(self, drives):
        """Setzt die ausgeschlossenen Laufwerke."""
        self.excluded_drives = drives
        
    def _handle_drive_status(self, drive_path, connected):
        """Behandelt Laufwerksänderungen."""
        try:
            if connected:
                self.on_drive_connected.emit(drive_path)
            else:
                self.on_drive_disconnected.emit(drive_path)
                
        except Exception as e:
            logging.error(f"Fehler bei der Laufwerksstatusbehandlung: {str(e)}")
            
    def __del__(self):
        """Destruktor."""
        self.stop_monitoring()
