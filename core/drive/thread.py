#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Thread für die Laufwerksüberwachung.
"""

import os
import time
import logging
import threading
from typing import Dict, List, Optional
from PyQt5.QtCore import QObject, pyqtSignal
from .status import DriveStatus
from .events import DriveEvent

logger = logging.getLogger(__name__)

class DriveMonitorThread(QObject):
    """Thread zur Überwachung von Laufwerksänderungen."""
    
    drive_changed = pyqtSignal(DriveEvent)  # Signal für Laufwerksänderungen
    
    def __init__(self, poll_interval: float = 2.0):
        """Initialisiert den DriveMonitorThread.
        
        Args:
            poll_interval: Zeit zwischen Polls in Sekunden (Standard: 2.0)
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self._poll_interval = poll_interval
        self._running = False
        self._thread = None
        self._known_drives: Dict[str, DriveStatus] = {}
        
    def start(self):
        """Startet die Laufwerksüberwachung."""
        if self._thread is None or not self._thread.is_alive():
            self._running = True
            self._thread = threading.Thread(target=self._monitor_drives)
            self._thread.daemon = True
            self._thread.start()
            self.logger.info("Laufwerksüberwachung gestartet")
            
    def stop(self):
        """Stoppt die Laufwerksüberwachung."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
        self.logger.info("Laufwerksüberwachung gestoppt")
        
    def _monitor_drives(self):
        """Überwacht Änderungen an Laufwerken."""
        while self._running:
            try:
                # Hole aktuelle Laufwerke
                current_drives = self._get_drives()
                
                # Prüfe auf neue Laufwerke
                for drive, status in current_drives.items():
                    if drive not in self._known_drives:
                        # Neues Laufwerk gefunden
                        self.logger.info(f"Neues Laufwerk gefunden: {drive} ({status.label}) - Typ: {status.type}")
                        self.drive_changed.emit(DriveEvent(drive, status, 'added'))
                        
                # Prüfe auf entfernte Laufwerke
                for drive in list(self._known_drives.keys()):
                    if drive not in current_drives:
                        # Laufwerk wurde entfernt
                        status = self._known_drives[drive]
                        self.logger.info(f"Laufwerk entfernt: {drive} ({status.label})")
                        self.drive_changed.emit(DriveEvent(drive, status, 'removed'))
                        
                # Aktualisiere bekannte Laufwerke
                self._known_drives = current_drives
                
                # Warte bis zum nächsten Poll
                time.sleep(self._poll_interval)
                
            except Exception as e:
                self.logger.error(f"Fehler bei Laufwerksüberwachung: {str(e)}", exc_info=True)
                time.sleep(1.0)  # Kurze Pause bei Fehler
                
    def _get_drives(self) -> Dict[str, DriveStatus]:
        """Ermittelt alle verfügbaren Laufwerke.
        
        Returns:
            Dict[str, DriveStatus]: Dictionary mit Laufwerksbuchstaben als Schlüssel
                                  und DriveStatus als Wert
        """
        drives = {}
        try:
            # Windows: Prüfe alle möglichen Laufwerksbuchstaben
            for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                drive_path = f"{letter}:\\"
                if os.path.exists(drive_path):
                    try:
                        # Hole Laufwerksinformationen
                        label = self._get_drive_label(drive_path)
                        drive_type = self._get_drive_type(drive_path)
                        
                        # Erstelle DriveStatus
                        status = DriveStatus(
                            letter=letter,
                            label=label,
                            type=drive_type,
                            path=drive_path
                        )
                        drives[letter] = status
                        
                    except Exception as e:
                        self.logger.error(f"Fehler beim Lesen von Laufwerk {letter}: {str(e)}")
                        
        except Exception as e:
            self.logger.error(f"Fehler beim Ermitteln der Laufwerke: {str(e)}", exc_info=True)
            
        return drives
        
    def _get_drive_label(self, path: str) -> str:
        """Ermittelt die Bezeichnung eines Laufwerks.
        
        Args:
            path: Pfad zum Laufwerk (z.B. "C:\\")
            
        Returns:
            str: Laufwerksbezeichnung oder leerer String
        """
        try:
            import win32api
            label = win32api.GetVolumeInformation(path)[0]
            return label if label else ""
        except:
            return ""
            
    def _get_drive_type(self, path: str) -> str:
        """Ermittelt den Typ eines Laufwerks.
        
        Args:
            path: Pfad zum Laufwerk (z.B. "C:\\")
            
        Returns:
            str: Laufwerkstyp ('local', 'removable', 'remote', 'cdrom', 'ramdisk')
        """
        try:
            import win32file
            drive_type = win32file.GetDriveType(path)
            
            # Mapping von Windows Drive Types
            type_map = {
                win32file.DRIVE_FIXED: 'local',
                win32file.DRIVE_REMOVABLE: 'removable',
                win32file.DRIVE_REMOTE: 'remote',
                win32file.DRIVE_CDROM: 'cdrom',
                win32file.DRIVE_RAMDISK: 'ramdisk'
            }
            
            return type_map.get(drive_type, 'unknown')
            
        except:
            return 'unknown'
