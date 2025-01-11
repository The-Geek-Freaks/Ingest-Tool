#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Event-Handler für das Hauptfenster."""

import logging
import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QMessageBox, QFileDialog
)
from PyQt5.QtCore import QThread, Qt, QMetaObject

logger = logging.getLogger(__name__)

class EventHandlers:
    """Verwaltet Event-Handler für das Hauptfenster."""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.logger = logging.getLogger(__name__)
        
    def connect_signals(self):
        """Verbindet alle UI-Signale mit ihren Handlern."""
        try:
            # Start/Stop Buttons
            self.main_window.start_button.clicked.connect(self.on_start_clicked)
            self.main_window.cancel_button.clicked.connect(self.on_stop_clicked)
            
            # Zuordnungen
            self.main_window.add_mapping_button.clicked.connect(self._on_add_mapping_clicked)
            self.main_window.remove_mapping_button.clicked.connect(self._on_remove_mapping_clicked)
            self.main_window.browse_button.clicked.connect(self._on_browse_clicked)
            
            # Ausgeschlossene Laufwerke
            self.main_window.add_excluded_button.clicked.connect(self._on_add_excluded_path_clicked)
            self.main_window.remove_excluded_button.clicked.connect(self._on_remove_excluded_clicked)
            self.main_window.exclude_all_button.clicked.connect(self._on_exclude_all_clicked)
            
            # Dateityp Combo
            self.main_window.filetype_combo.currentTextChanged.connect(self._on_filetype_changed)
            
            # Auto-Start Checkbox
            self.main_window.auto_start_checkbox.stateChanged.connect(self._on_auto_start_changed)
            
            self.logger.debug("UI Signale erfolgreich verbunden")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Verbinden der Signale: {e}", exc_info=True)
            
    def on_start_clicked(self):
        """Handler für Start-Button."""
        try:
            self.main_window.start_button.setEnabled(False)
            self.main_window.cancel_button.setEnabled(True)
            self.main_window.file_watcher_manager.start()
            self.logger.info("Dateiüberwachung gestartet")
        except Exception as e:
            self.logger.error(f"Fehler beim Starten der Überwachung: {e}", exc_info=True)
            
    def on_stop_clicked(self):
        """Handler für Stop-Button."""
        try:
            self.main_window.start_button.setEnabled(True)
            self.main_window.cancel_button.setEnabled(False)
            self.main_window.file_watcher_manager.stop()
            self.logger.info("Dateiüberwachung gestoppt")
        except Exception as e:
            self.logger.error(f"Fehler beim Stoppen der Überwachung: {e}", exc_info=True)
            
    def on_cancel_clicked(self):
        """Handler für Cancel-Button."""
        try:
            self.main_window.file_watcher_manager.stop_all_watchers()
            self.main_window.transfer_coordinator.cancel_all_transfers()
            self.main_window.cancel_button.setEnabled(False)
            self.main_window.start_button.setEnabled(True)
            
            # Setze Status aller Laufwerke zurück
            for drive_item in self.main_window.drive_items.values():
                drive_item.update_status("idle")
                
        except Exception as e:
            self.logger.error(f"Fehler beim Abbrechen des Kopiervorgangs: {e}")
            
    def on_browse_clicked(self):
        """Handler für Browse-Button."""
        try:
            directory = QFileDialog.getExistingDirectory(
                self.main_window,
                self.main_window.i18n.get("ui.select_target_directory"),
                os.path.expanduser("~")
            )
            if directory:
                self.main_window.target_path_edit.setText(directory)
                
        except Exception as e:
            self.logger.error(f"Fehler beim Öffnen des Datei-Dialogs: {e}")
            
    def on_add_mapping_clicked(self):
        """Handler für Add-Mapping-Button."""
        try:
            file_type = self.main_window.filetype_combo.currentText()
            target_path = self.main_window.target_path_edit.text()
            
            if not file_type or not target_path:
                self.main_window.ui_handlers.show_warning(
                    self.main_window.i18n.get("general.warning"),
                    self.main_window.i18n.get("ui.incomplete_mapping")
                )
                return
                
            # Normalisiere den Dateityp
            if not file_type.startswith('*'):
                file_type = '*' + file_type
                
            # Prüfe ob der Dateityp bereits existiert
            for i in range(self.main_window.mappings_list.count()):
                item_text = self.main_window.mappings_list.item(i).text()
                if item_text.startswith(file_type + " "):
                    self.main_window.ui_handlers.show_warning(
                        self.main_window.i18n.get("general.warning"),
                        self.main_window.i18n.get("ui.duplicate_mapping").format(file_type=file_type)
                    )
                    return
                    
            # Füge neue Zuordnung hinzu
            self.main_window.mappings_list.addItem(f"{file_type} ➔ {target_path}")
            self.main_window.save_settings()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Hinzufügen der Zuordnung: {e}")
            
    def on_remove_mapping_clicked(self):
        """Handler für Remove-Mapping-Button."""
        try:
            current_item = self.main_window.mappings_list.currentItem()
            if current_item:
                self.main_window.mappings_list.takeItem(
                    self.main_window.mappings_list.row(current_item)
                )
                self.main_window.save_settings()
                
        except Exception as e:
            self.logger.error(f"Fehler beim Entfernen der Zuordnung: {e}")
            
    def on_add_excluded_path_clicked(self):
        """Handler für Add-Excluded-Button."""
        try:
            directory = QFileDialog.getExistingDirectory(
                self.main_window,
                self.main_window.i18n.get("ui.select_directory"),
                os.path.expanduser("~")
            )
            if directory:
                # Prüfe ob das Verzeichnis bereits ausgeschlossen ist
                for i in range(self.main_window.excluded_list.count()):
                    if self.main_window.excluded_list.item(i).text() == directory:
                        self.main_window.ui_handlers.show_warning(
                            self.main_window.i18n.get("general.warning"),
                            self.main_window.i18n.get("ui.duplicate_excluded").format(directory=directory)
                        )
                        return
                
                self.main_window.excluded_list.addItem(directory)
                self.main_window.save_settings()
                
        except Exception as e:
            self.logger.error(f"Fehler beim Ausschließen des Verzeichnisses: {e}")
            
    def on_remove_excluded_clicked(self):
        """Handler für Remove-Excluded-Button."""
        try:
            current_item = self.main_window.excluded_list.currentItem()
            if current_item:
                self.main_window.excluded_list.takeItem(
                    self.main_window.excluded_list.row(current_item)
                )
                self.main_window.save_settings()
                
        except Exception as e:
            self.logger.error(f"Fehler beim Entfernen des ausgeschlossenen Verzeichnisses: {e}")
            
    def on_exclude_all_clicked(self):
        """Handler für Exclude-All-Button."""
        try:
            # Hole alle verfügbaren Laufwerke
            available_drives = []
            for drive_letter, drive_item in self.main_window.drive_items.items():
                if not drive_item.is_excluded:
                    available_drives.append(drive_letter)
            
            # Füge sie zur Ausschlussliste hinzu
            for drive_letter in available_drives:
                # Prüfe ob das Laufwerk bereits ausgeschlossen ist
                already_excluded = False
                for i in range(self.main_window.excluded_list.count()):
                    if self.main_window.excluded_list.item(i).text() == drive_letter:
                        already_excluded = True
                        break
                
                if not already_excluded:
                    self.main_window.excluded_list.addItem(drive_letter)
            
            self.main_window.save_settings()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Ausschließen aller Laufwerke: {e}")
            
    def on_file_detected(self, file_path: str):
        """Callback wenn eine neue Datei erkannt wurde."""
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            target_path = self.main_window.transfer_handlers.get_mapping_for_type(file_ext)
            if target_path:
                self.main_window.transfer_coordinator.start_copy_for_files([file_path], target_path)
                self.logger.info(f"Neue Datei erkannt und Kopiervorgang gestartet: {file_path}")
                
        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten der erkannten Datei {file_path}: {e}")

    def _on_add_mapping_clicked(self):
        """Handler für den 'Hinzufügen' Button bei Zuordnungen."""
        try:
            filetype = self.main_window.filetype_combo.currentText()
            target_path = self.main_window.target_path_edit.text()
            
            if not filetype or not target_path:
                self.main_window.ui_handlers.show_warning(
                    "Warnung",
                    "Bitte wählen Sie einen Dateityp und Zielordner aus."
                )
                return
                
            # Füge Zuordnung zur Liste hinzu
            item_text = f"{filetype} -> {target_path}"
            self.main_window.mappings_list.addItem(item_text)
            
            # Speichere Einstellungen
            self.main_window.save_settings()
            
            self.logger.debug(f"Neue Zuordnung hinzugefügt: {item_text}")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Hinzufügen der Zuordnung: {e}", exc_info=True)
            
    def _on_remove_mapping_clicked(self):
        """Handler für den 'Entfernen' Button bei Zuordnungen."""
        try:
            current_item = self.main_window.mappings_list.currentItem()
            if current_item:
                self.main_window.mappings_list.takeItem(
                    self.main_window.mappings_list.row(current_item)
                )
                self.main_window.save_settings()
                self.logger.debug(f"Zuordnung entfernt: {current_item.text()}")
                
        except Exception as e:
            self.logger.error(f"Fehler beim Entfernen der Zuordnung: {e}", exc_info=True)
            
    def _on_browse_clicked(self):
        """Handler für den 'Durchsuchen' Button."""
        try:
            folder = QFileDialog.getExistingDirectory(
                self.main_window,
                "Zielordner auswählen",
                os.path.expanduser("~"),
                QFileDialog.ShowDirsOnly
            )
            
            if folder:
                self.main_window.target_path_edit.setText(folder)
                self.logger.debug(f"Zielordner ausgewählt: {folder}")
                
        except Exception as e:
            self.logger.error(f"Fehler beim Auswählen des Ordners: {e}", exc_info=True)
            
    def _on_add_excluded_path_clicked(self):
        """Handler für den 'Ausschließen' Button bei Laufwerken."""
        try:
            current_item = self.main_window.drives_list.currentItem()
            if current_item:
                drive_path = current_item.text()
                self.main_window.excluded_list.addItem(drive_path)
                self.main_window.save_settings()
                self.logger.debug(f"Laufwerk ausgeschlossen: {drive_path}")
                
        except Exception as e:
            self.logger.error(f"Fehler beim Ausschließen des Laufwerks: {e}", exc_info=True)
            
    def _on_remove_excluded_clicked(self):
        """Handler für den 'Entfernen' Button bei ausgeschlossenen Laufwerken."""
        try:
            current_item = self.main_window.excluded_list.currentItem()
            if current_item:
                self.main_window.excluded_list.takeItem(
                    self.main_window.excluded_list.row(current_item)
                )
                self.main_window.save_settings()
                self.logger.debug(f"Ausgeschlossenes Laufwerk entfernt: {current_item.text()}")
                
        except Exception as e:
            self.logger.error(f"Fehler beim Entfernen des ausgeschlossenen Laufwerks: {e}", exc_info=True)
            
    def _on_exclude_all_clicked(self):
        """Handler für den 'Alle ausschließen' Button."""
        try:
            # Füge alle Laufwerke zur Ausschlussliste hinzu
            for i in range(self.main_window.drives_list.count()):
                drive_path = self.main_window.drives_list.item(i).text()
                # Prüfe ob das Laufwerk bereits ausgeschlossen ist
                items = self.main_window.excluded_list.findItems(
                    drive_path, Qt.MatchExactly
                )
                if not items:
                    self.main_window.excluded_list.addItem(drive_path)
                    
            self.main_window.save_settings()
            self.logger.debug("Alle Laufwerke ausgeschlossen")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Ausschließen aller Laufwerke: {e}", exc_info=True)
            
    def _on_filetype_changed(self, text):
        """Handler für Änderungen in der Dateityp-Combobox."""
        try:
            self.logger.debug(f"Dateityp geändert zu: {text}")
        except Exception as e:
            self.logger.error(f"Fehler bei Dateityp-Änderung: {e}", exc_info=True)
            
    def _on_auto_start_changed(self, state):
        """Handler für Änderungen der Auto-Start Checkbox."""
        try:
            is_checked = state == Qt.Checked
            self.logger.debug(f"Auto-Start geändert zu: {is_checked}")
            self.main_window.save_settings()
        except Exception as e:
            self.logger.error(f"Fehler bei Auto-Start-Änderung: {e}", exc_info=True)
