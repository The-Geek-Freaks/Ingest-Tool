#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VERALTET: Diese Datei ist veraltet und wird in einer zukünftigen Version entfernt.
Bitte verwenden Sie stattdessen core.transfer.manager.
"""

import warnings
warnings.warn(
    "Das Modul core.transfer_manager ist veraltet. "
    "Bitte verwenden Sie stattdessen core.transfer.manager.",
    DeprecationWarning,
    stacklevel=2
)

"""Manager für Datei-Transfers."""

import os
import time
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class TransferManager:
    """Manager für Datei-Transfers."""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.active_copies = {}
        self.transfer_start_time = None
        
    def start_copy(self, source_drive: str, target_path: str):
        """Startet den Kopiervorgang."""
        try:
            source_files = self.get_source_files(source_drive)
            if not source_files:
                return
                
            for source_file in source_files:
                target_file = os.path.join(target_path, os.path.basename(source_file))
                
                # Prüfe ob Datei bereits existiert
                if os.path.exists(target_file):
                    base, ext = os.path.splitext(target_file)
                    counter = 1
                    while os.path.exists(target_file):
                        target_file = f"{base}_{counter}{ext}"
                        counter += 1
                
                # Erstelle Task ID und füge zur Warteschlange hinzu
                task_id = f"{source_file}->{target_file}"
                
                # Füge Fortschrittsanzeige hinzu
                self.main_window.progress_widget.add_copy_task(task_id, os.path.basename(source_file))
                
                # Starte Transfer
                self.main_window.transfer_controller.start_transfer(source_file, target_file)
                self.active_copies[task_id] = {
                    "source_drive": source_drive,
                    "source_file": source_file,
                    "target_file": target_file,
                    "progress": 0.0,
                    "speed": 0.0
                }
                
            # Speichere Startzeit für Geschwindigkeitsberechnung
            self.transfer_start_time = time.time()
            
            # Aktualisiere UI
            self.main_window.progress_label.setText(self.main_window.i18n.get("ui.starting_transfer"))
            self.main_window.speed_label.setText(self.main_window.i18n.get("ui.speed_format", speed="0 B/s"))
            
        except Exception as e:
            logger.error(f"Fehler beim Starten des Kopiervorgangs: {e}")
            self.main_window.show_error("Fehler beim Starten des Kopiervorgangs", str(e))
            
    def get_source_files(self, source_drive: str) -> List[str]:
        """Gibt eine Liste der zu kopierenden Dateien zurück."""
        try:
            # Prüfe ob Laufwerk existiert
            if not os.path.exists(source_drive + ":\\"):
                self.main_window.show_warning(
                    "Fehler",
                    f"Laufwerk {source_drive} nicht gefunden."
                )
                return []

            # Hole Dateitypen
            file_types = self.main_window.get_file_types()
            if not file_types:
                self.main_window.show_warning(
                    "Fehler",
                    "Keine Dateitypen ausgewählt."
                )
                return []

            # Suche Dateien
            source_files = []
            for root, _, files in os.walk(source_drive + ":\\"):
                for file in files:
                    file_path = os.path.join(root, file)
                    if any(file.lower().endswith(ext.lower().replace("*", "")) for ext in file_types):
                        source_files.append(file_path)

            if not source_files:
                self.main_window.show_warning(
                    "Keine Dateien gefunden",
                    f"Keine passenden Dateien auf Laufwerk {source_drive} gefunden."
                )

            return source_files

        except Exception as e:
            logger.error(f"Fehler beim Suchen der Quelldateien: {e}")
            self.main_window.show_error(
                "Fehler",
                f"Fehler beim Suchen der Quelldateien: {e}"
            )
            return []
