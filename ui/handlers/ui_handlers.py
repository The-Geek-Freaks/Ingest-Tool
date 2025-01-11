#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Handler für UI-Ereignisse.
"""

import os
import logging
from typing import Dict, Optional
from PyQt5.QtWidgets import QFileDialog, QMessageBox

logger = logging.getLogger(__name__)

class UIHandlers:
    """Handler für UI-Ereignisse."""
    
    def __init__(self, main_window):
        """Initialisiert die UI-Handler.
        
        Args:
            main_window: Referenz zum Hauptfenster
        """
        self.main_window = main_window
        
    def on_browse_clicked(self):
        """Öffnet einen Dialog zur Auswahl des Zielverzeichnisses."""
        try:
            directory = QFileDialog.getExistingDirectory(
                self.main_window,
                self.main_window.i18n.get("ui.select_target"),
                os.path.expanduser("~"),
                QFileDialog.ShowDirsOnly
            )
            
            if directory:
                self.main_window.target_path_edit.setText(directory)
                
        except Exception as e:
            logger.error(f"Fehler beim Öffnen des Verzeichnis-Dialogs: {e}")
            
    def on_add_mapping_clicked(self):
        """Fügt eine neue Zuordnung hinzu."""
        try:
            source = self.main_window.source_edit.text().strip()
            target = self.main_window.target_edit.text().strip()
            
            if not source or not target:
                self.show_warning(
                    self.main_window.i18n.get("general.warning"),
                    self.main_window.i18n.get("ui.invalid_mapping")
                )
                return
                
            self.main_window.add_mapping(source, target)
            
            # Leere Eingabefelder
            self.main_window.source_edit.clear()
            self.main_window.target_edit.clear()
            
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen der Zuordnung: {e}")
            
    def on_remove_mapping_clicked(self):
        """Entfernt die ausgewählte Zuordnung."""
        try:
            current_item = self.main_window.mappings_list.currentItem()
            if current_item:
                self.main_window.mappings_list.takeItem(
                    self.main_window.mappings_list.row(current_item)
                )
                
        except Exception as e:
            logger.error(f"Fehler beim Entfernen der Zuordnung: {e}")
            
    def on_add_excluded_path_clicked(self):
        """Öffnet einen Dialog zur Auswahl eines auszuschließenden Verzeichnisses."""
        try:
            directory = QFileDialog.getExistingDirectory(
                self.main_window,
                self.main_window.i18n.get("ui.select_excluded"),
                os.path.expanduser("~"),
                QFileDialog.ShowDirsOnly
            )
            
            if directory:
                self.main_window.excluded_list.addItem(directory)
                
        except Exception as e:
            logger.error(f"Fehler beim Öffnen des Verzeichnis-Dialogs: {e}")
            
    def on_remove_excluded_clicked(self):
        """Entfernt das ausgewählte ausgeschlossene Verzeichnis."""
        try:
            current_item = self.main_window.excluded_list.currentItem()
            if current_item:
                self.main_window.excluded_list.takeItem(
                    self.main_window.excluded_list.row(current_item)
                )
                
        except Exception as e:
            logger.error(f"Fehler beim Entfernen des ausgeschlossenen Verzeichnisses: {e}")
            
    def on_exclude_all_clicked(self):
        """Schließt alle verfügbaren Laufwerke aus."""
        try:
            for drive_letter in self.main_window.drive_items.keys():
                if not self.main_window.excluded_list.findItems(drive_letter, Qt.MatchExactly):
                    self.main_window.excluded_list.addItem(drive_letter)
                    
        except Exception as e:
            logger.error(f"Fehler beim Ausschließen aller Laufwerke: {e}")
            
    def show_warning(self, title: str, message: str):
        """Zeigt eine Warnung an."""
        QMessageBox.warning(self.main_window, title, message)
        
    def show_error(self, title: str, message: str):
        """Zeigt einen Fehler an."""
        QMessageBox.critical(self.main_window, title, message)
