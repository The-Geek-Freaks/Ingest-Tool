"""
VERALTET: Diese Datei ist veraltet und wird in einer zukünftigen Version entfernt.
Bitte verwenden Sie stattdessen core.drive_controller.
"""

import warnings

warnings.warn(
    "Das Modul drive_monitor ist veraltet. "
    "Bitte verwenden Sie stattdessen core.drive_controller.",
    DeprecationWarning,
    stacklevel=2
)

from .drive import (
    DriveMonitor,
    DriveStatus,
    DriveEvent,
    FileEvent
)
import os
import sys
import string
import ctypes
import logging
from pathlib import Path
from PyQt5.QtCore import QThread, pyqtSignal

class DriveMonitorThread(QThread):
    """Thread zur Überwachung von Laufwerken auf neue Dateien."""
    
    file_found = pyqtSignal(str)  # Signal für gefundene Datei
    drive_status_changed = pyqtSignal(str, bool)  # Signal für Laufwerksänderungen
    neues_laufwerk = pyqtSignal(str, float)  # Signal für neue Laufwerke (Pfad, Zeitstempel)
    log_eintrag = pyqtSignal(str)  # Signal für Log-Einträge
    kopiere_fortschritt = pyqtSignal(str, str, int, int)  # Signal für Kopierfortschritt
    verschoben = pyqtSignal(str, str)  # Signal für verschobene Dateien
    transfer_abgebrochen = pyqtSignal(str)  # Signal für abgebrochene Transfers
    duplicate_found = pyqtSignal(str, str)  # Signal für Duplikate
    fehlgeschlagen = pyqtSignal(str)  # Signal für fehlgeschlagene Operationen
    
    def __init__(self, watch_paths, file_types, delete_source=False, excluded_drives=None):
        super().__init__()
        self.watch_paths = watch_paths
        self.file_types = [ext.lower() if not ext.startswith('.') else ext[1:].lower() 
                          for ext in file_types]
        self.delete_source = delete_source
        self.excluded_drives = excluded_drives or []
        self.running = True
        self.aktive_laufwerke = set()
        self.bekannte_dateien = set()
        
    def run(self):
        """Hauptschleife des Monitor-Threads."""
        while self.running:
            try:
                # Hole aktuelle Laufwerke
                aktuelle_laufwerke = self.get_mounted_drives()
                
                # Prüfe auf neue und entfernte Laufwerke
                neue_laufwerke = aktuelle_laufwerke - self.aktive_laufwerke
                entfernte_laufwerke = self.aktive_laufwerke - aktuelle_laufwerke
                
                # Behandle neue Laufwerke
                for laufwerk in neue_laufwerke:
                    if not self.is_drive_excluded(laufwerk):
                        self.aktive_laufwerke.add(laufwerk)
                        self.drive_status_changed.emit(laufwerk, True)
                        self.log_eintrag.emit(f"Neues Laufwerk gefunden: {laufwerk}")
                        self._scan_drive(laufwerk)
                
                # Behandle entfernte Laufwerke
                for laufwerk in entfernte_laufwerke:
                    self.aktive_laufwerke.remove(laufwerk)
                    self.drive_status_changed.emit(laufwerk, False)
                    self.log_eintrag.emit(f"Laufwerk entfernt: {laufwerk}")
                
                # Scanne aktive Laufwerke
                for laufwerk in self.aktive_laufwerke:
                    if not self.running:
                        break
                    self._scan_drive(laufwerk)
                
                self.msleep(1000)  # Warte 1 Sekunde
                
            except Exception as e:
                self.log_eintrag.emit(f"Fehler im Monitor-Thread: {str(e)}")
                self.msleep(5000)  # Warte 5 Sekunden bei Fehler
    
    def get_mounted_drives(self):
        """Ermittelt alle eingehängten Laufwerke."""
        try:
            if sys.platform == 'win32':
                drives = set()
                bitmask = ctypes.windll.kernel32.GetLogicalDrives()
                for letter in string.ascii_uppercase:
                    if bitmask & 1:
                        drive = f"{letter}:\\"
                        if os.path.exists(drive):
                            drives.add(drive)
                    bitmask >>= 1
                return drives
            else:
                # Für Linux/Mac
                return {'/'}  # Dummy-Implementation
                
        except Exception as e:
            self.log_eintrag.emit(f"Fehler beim Abrufen der Laufwerke: {str(e)}")
            return set()
            
    def is_drive_excluded(self, drive_path):
        """Prüft, ob ein Laufwerk ausgeschlossen ist."""
        return any(drive_path.startswith(excluded) for excluded in self.excluded_drives)
        
    def _scan_drive(self, laufwerk):
        """Scannt ein Laufwerk nach neuen Dateien."""
        try:
            if self.is_drive_excluded(laufwerk):
                return
                
            for root, _, files in os.walk(laufwerk):
                if not self.running:
                    break
                    
                if self.is_drive_excluded(root):
                    continue
                    
                for filename in files:
                    if not self.running:
                        break
                        
                    filepath = os.path.join(root, filename)
                    
                    if self.is_drive_excluded(filepath):
                        continue
                        
                    if filepath in self.bekannte_dateien:
                        continue
                        
                    # Prüfe Dateityp
                    _, ext = os.path.splitext(filename)
                    ext = ext[1:].lower() if ext.startswith('.') else ext.lower()
                    if ext not in self.file_types:
                        continue
                        
                    # Datei gefunden
                    self.bekannte_dateien.add(filepath)
                    self.file_found.emit(filepath)
                    self.log_eintrag.emit(f"Neue Datei gefunden: {filepath}")
                    
        except Exception as e:
            error_msg = f"Fehler beim Scannen von {laufwerk}: {str(e)}"
            self.log_eintrag.emit(error_msg)
            self.fehlgeschlagen.emit(error_msg)
            
    def stop(self):
        """Stoppt den Monitor-Thread."""
        self.running = False

__all__ = [
    'DriveMonitor',
    'DriveMonitorThread',
    'DriveStatus',
    'DriveEvent',
    'FileEvent'
]
