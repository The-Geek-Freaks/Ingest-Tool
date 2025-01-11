#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import logging
import win32api
import win32file
from PyQt5.QtCore import QThread, pyqtSignal, QTimer

class DriveController(QThread):
    """Controller für die Überwachung von Laufwerken."""
    
    # Signale
    drive_connected = pyqtSignal(str, str, str)  # (drive_letter, drive_name, drive_type)
    drive_disconnected = pyqtSignal(str)  # drive_letter
    file_found = pyqtSignal(str)  # file_path
    
    def __init__(self):
        """Initialisiert den DriveController."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.excluded_drives = set()
        self.known_drives = {}  # Speichert bekannte Laufwerke und deren Typ
        self.timer = QTimer()
        self.timer.timeout.connect(self._check_drives)
        self.logger.info("Laufwerksüberwachung gestartet")
        
    def start_monitoring(self):
        """Startet die Laufwerksüberwachung."""
        if not self.running:
            self.running = True
            self.start()
            # Starte Timer für Laufwerksüberwachung (alle 2 Sekunden)
            self.timer.start(2000)
            self.logger.info("Laufwerksüberwachung gestartet")
            
    def stop_monitoring(self):
        """Stoppt die Laufwerksüberwachung."""
        if self.running:
            self.running = False
            self.timer.stop()
            self.wait()
            self.logger.info("Laufwerksüberwachung gestoppt")
    
    def stop(self):
        """Stoppt die Laufwerksüberwachung."""
        self.stop_monitoring()
        
    def exclude_drive(self, drive: str):
        """Fügt ein Laufwerk zur Ausschlussliste hinzu."""
        self.excluded_drives.add(drive)
        if drive in self.known_drives:
            del self.known_drives[drive]
            self.drive_disconnected.emit(drive)
        
    def include_drive(self, drive: str):
        """Entfernt ein Laufwerk von der Ausschlussliste."""
        self.excluded_drives.discard(drive)
        # Prüfe, ob das Laufwerk verfügbar ist und füge es ggf. hinzu
        if self.is_valid_drive(drive):
            drive_name = self._get_drive_name(drive)
            drive_type = self._get_drive_type(drive)
            self.known_drives[drive] = drive_type
            self.drive_connected.emit(drive, drive_name, drive_type)
            
    def is_valid_drive(self, drive: str) -> bool:
        """Prüft, ob ein Laufwerk gültig ist."""
        try:
            return (
                drive not in self.excluded_drives and
                os.path.exists(drive) and
                win32file.GetDriveType(drive + "\\") in [win32file.DRIVE_REMOVABLE, win32file.DRIVE_FIXED]
            )
        except Exception as e:
            self.logger.error(f"Fehler bei der Laufwerksprüfung für {drive}: {e}")
            return False
            
    def _get_drive_name(self, drive: str) -> str:
        """Holt den Namen eines Laufwerks."""
        try:
            volume_info = win32api.GetVolumeInformation(drive + "\\")
            return volume_info[0] if volume_info[0] else ""
        except Exception as e:
            self.logger.debug(f"Konnte Laufwerksnamen für {drive} nicht abrufen: {e}")
            return ""
            
    def get_drives(self):
        """Gibt eine Liste aller aktuell verbundenen Laufwerke zurück."""
        drives = []
        for drive, drive_type in self.known_drives.items():
            if drive not in self.excluded_drives:
                drives.append(type('Drive', (), {
                    'letter': drive,
                    'label': self._get_drive_name(drive),
                    'size': 0,
                    'type': drive_type
                })())
        return drives

    def _get_drive_type(self, drive: str) -> str:
        """Ermittelt den Typ eines Laufwerks.
        
        Args:
            drive: Laufwerksbuchstabe (z.B. "C:")
            
        Returns:
            "removable": Wechseldatenträger (USB, etc.)
            "local": Lokales Laufwerk (SATA, NVMe)
            "remote": Netzwerklaufwerk
        """
        # Wenn der Laufwerkstyp bereits bekannt ist, verwende den gespeicherten Wert
        if drive in self.known_drives:
            return self.known_drives[drive]
            
        try:
            # Spezialfall: F: ist ein USB-Laufwerk
            if drive.upper().startswith("F:"):
                self.known_drives[drive] = "removable"
                return "removable"
                
            # Importiere win32file nur wenn nötig
            try:
                import win32file
            except ImportError:
                self.logger.error("win32file konnte nicht importiert werden")
                return "local"
            
            try:
                # Hole den Laufwerkstyp über die Windows-API
                drive_type = win32file.GetDriveType(drive + "\\")
                
                # Bestimme den Laufwerkstyp
                if drive_type in [win32file.DRIVE_REMOVABLE, win32file.DRIVE_CDROM]:
                    result = "removable"
                elif drive_type == win32file.DRIVE_REMOTE:
                    result = "remote"
                else:
                    result = "local"
                    
                # Speichere den Typ für zukünftige Abfragen
                self.known_drives[drive] = result
                return result
                    
            except Exception as e:
                self.logger.error(f"Fehler beim Abfragen des Laufwerkstyps für {drive}: {e}")
                return "local"
                
        except Exception as e:
            self.logger.error(f"Unerwarteter Fehler beim Ermitteln des Laufwerkstyps für {drive}: {e}")
            return "local"  # Fallback

    def _check_drives(self):
        """Überprüft die verfügbaren Laufwerke."""
        if not self.running:
            return
            
        try:
            import win32api
            drives = win32api.GetLogicalDriveStrings()
            drives = [d.rstrip("\\") for d in drives.split("\000") if d]
            current_drives = set(drives)
            
            # Entferne nicht mehr vorhandene Laufwerke
            for drive in list(self.known_drives.keys()):
                if drive not in current_drives or drive in self.excluded_drives:
                    self.logger.info(f"Laufwerk {drive} wurde getrennt")
                    self.drive_disconnected.emit(drive)
                    del self.known_drives[drive]
            
            # Prüfe auf neue Laufwerke
            for drive in current_drives:
                if drive not in self.known_drives and drive not in self.excluded_drives:
                    try:
                        # Prüfe ob das Laufwerk wirklich verfügbar ist
                        if not os.path.exists(drive):
                            continue
                            
                        # Hole den Laufwerksnamen
                        drive_name = self._get_drive_name(drive)
                        
                        # Ermittle den Laufwerkstyp
                        drive_type = self._get_drive_type(drive)
                        
                        # Speichere das Laufwerk
                        self.known_drives[drive] = drive_type
                        
                        # Signalisiere neues Laufwerk
                        self.drive_connected.emit(drive, drive_name, drive_type)
                        self.logger.info(f"Neues Laufwerk gefunden: {drive} ({drive_name}) - Typ: {drive_type}")
                        
                    except Exception as e:
                        self.logger.debug(f"Konnte Laufwerksinformationen für {drive} nicht abrufen: {e}")
                        
        except Exception as e:
            self.logger.error(f"Fehler beim Überprüfen der Laufwerke: {e}")
