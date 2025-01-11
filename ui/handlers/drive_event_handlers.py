#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Handler für Drive-bezogene Events."""

import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class DriveEventHandlers:
    """Verwaltet Drive-bezogene Events."""
    
    def __init__(self, main_window):
        self.main_window = main_window
        
    def connect_signals(self):
        """Verbindet Drive-bezogene Signale."""
        self.main_window.drive_controller.drive_connected.connect(self.on_drive_connected)
        self.main_window.drive_controller.drive_disconnected.connect(self.on_drive_disconnected)
        
    def on_drive_connected(self, drive_letter: str, drive_label: str = "", drive_type: str = "local"):
        """Handler für neue Laufwerksverbindung."""
        try:
            # Prüfe ob das Laufwerk ausgeschlossen ist
            excluded_drives = [
                self.main_window.excluded_list.item(i).text()
                for i in range(self.main_window.excluded_list.count())
            ]
            
            if drive_letter not in excluded_drives:
                # Automatischer Start wenn aktiviert
                if self.main_window.auto_start_checkbox.isChecked():
                    source_files = self.main_window.transfer_handlers.get_source_files(drive_letter)
                    if source_files:
                        # Nutze hohe Priorität für Auto-Start
                        for source_file in source_files:
                            target_file = os.path.join(
                                self.main_window.target_path_edit.text(),
                                os.path.basename(source_file)
                            )
                            self.main_window.transfer_coordinator.start_copy_for_files([source_file], target_file)
            
            # UI Update
            self.main_window.drive_handlers.on_drive_connected(drive_letter, drive_label, drive_type)
            
        except Exception as e:
            logger.error(f"Fehler beim Verarbeiten der Laufwerksverbindung: {e}")
            
    def on_drive_disconnected(self, drive_letter: str):
        """Handler für getrennte Laufwerksverbindung."""
        try:
            # UI Update
            self.main_window.drive_handlers.on_drive_disconnected(drive_letter)
            
            # Stoppe den Watcher für dieses Laufwerk
            if hasattr(self.main_window, 'file_watcher_manager'):
                self.main_window.file_watcher_manager.stop_watcher(drive_letter)
            
        except Exception as e:
            logger.error(f"Fehler beim Verarbeiten der Laufwerkstrennung: {e}")
            
    def update_drive_status(self, drive_letter: str, status: str, current_file: str = None):
        """Aktualisiert den Status eines Laufwerks.
        
        Args:
            drive_letter: Laufwerksbuchstabe
            status: Neuer Status
            current_file: Aktuelle Datei (optional)
        """
        try:
            if drive_letter in self.main_window.drive_items:
                self.main_window.drive_items[drive_letter].update_status(status, current_file)
                
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren des Laufwerksstatus: {e}")
            
    def get_drive_status(self, drive_letter: str) -> str:
        """Gibt den Status eines Laufwerks zurück.
        
        Args:
            drive_letter: Laufwerksbuchstabe
            
        Returns:
            Status des Laufwerks
        """
        try:
            if drive_letter in self.main_window.drive_items:
                return self.main_window.drive_items[drive_letter].get_status()
            return "unknown"
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Laufwerksstatus: {e}")
            return "error"
            
    def on_file_found(self, file_path: str):
        """Event-Handler für gefundene Dateien."""
        try:
            # UI-Update über den Drive-Handler
            self.main_window.drive_handlers.on_file_found(file_path)
            
        except Exception as e:
            logger.error(f"Fehler im File-Found Event Handler: {e}")
