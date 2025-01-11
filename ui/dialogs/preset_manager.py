#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Dialog zur Verwaltung von Presets."""

import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
    QPushButton, QDialogButtonBox, QInputDialog,
    QLineEdit, QMessageBox
)

logger = logging.getLogger(__name__)

class PresetManagerDialog(QDialog):
    """Dialog zur Verwaltung von Presets."""
    
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.setWindowTitle(self.main_window.i18n.get("ui.manage_presets"))
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        """Erstellt die UI-Elemente."""
        layout = QVBoxLayout(self)
        
        # Liste der Presets
        self.list_widget = QListWidget(self)
        presets = self.main_window.settings.get('presets', {})
        for name in presets:
            self.list_widget.addItem(name)
        layout.addWidget(self.list_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton(self.main_window.i18n.get("ui.save_preset"))
        self.load_button = QPushButton(self.main_window.i18n.get("ui.load_preset"))
        self.delete_button = QPushButton(self.main_window.i18n.get("ui.delete_preset"))
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.delete_button)
        layout.addLayout(button_layout)
        
        # OK/Abbrechen
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Verbinde Buttons
        self.save_button.clicked.connect(self.on_save)
        self.load_button.clicked.connect(self.on_load)
        self.delete_button.clicked.connect(self.on_delete)
        
    def on_save(self):
        """Speichert die aktuellen Einstellungen als Preset."""
        try:
            # Hole die aktuellen Einstellungen
            current_settings = self.main_window.get_current_settings()
            
            if not current_settings.get('file_type') or not current_settings.get('target_path'):
                logger.warning("Bitte wählen Sie einen Dateityp und ein Zielverzeichnis aus")
                QMessageBox.warning(
                    self,
                    self.main_window.i18n.get("ui.warning"),
                    self.main_window.i18n.get("ui.select_filetype_and_target"),
                    QMessageBox.Ok
                )
                return
                
            # Hole den Preset-Namen
            name, ok = QInputDialog.getText(
                self,
                self.main_window.i18n.get("ui.save_preset"),
                self.main_window.i18n.get("ui.preset_name"),
                QLineEdit.Normal,
                ""
            )
            
            if ok and name:
                # Hole die aktuellen Presets
                presets = self.main_window.settings.get('presets', {})
                
                # Füge das neue Preset hinzu
                presets[name] = current_settings
                
                # Speichere die Presets
                self.main_window.settings['presets'] = presets
                self.main_window.settings_manager.save_settings(self.main_window.settings)
                
                # Aktualisiere die Preset-Liste
                self.list_widget.clear()
                self.list_widget.addItems(presets.keys())
                
                logger.info(f"Preset '{name}' gespeichert")
                
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Presets: {e}")
            QMessageBox.critical(
                self,
                self.main_window.i18n.get("ui.error"),
                str(e),
                QMessageBox.Ok
            )
            
    def on_load(self):
        """Lädt das ausgewählte Preset."""
        try:
            current = self.list_widget.currentItem()
            if current:
                name = current.text()
                presets = self.main_window.settings.get('presets', {})
                if name in presets:
                    preset = presets[name]
                    
                    # Aktualisiere die UI
                    if 'file_type' in preset:
                        self.main_window.filetype_combo.setCurrentText(preset['file_type'])
                    if 'target_path' in preset:
                        self.main_window.target_edit.setText(preset['target_path'])
                    if 'delete_source' in preset:
                        self.main_window.delete_source_checkbox.setChecked(preset['delete_source'])
                    
                    logger.info(f"Preset '{name}' geladen")
                    
        except Exception as e:
            logger.error(f"Fehler beim Laden des Presets: {e}")
            QMessageBox.critical(
                self,
                self.main_window.i18n.get("ui.error"),
                str(e),
                QMessageBox.Ok
            )
            
    def on_delete(self):
        """Löscht das ausgewählte Preset."""
        try:
            current = self.list_widget.currentItem()
            if current:
                name = current.text()
                # Verhindere das Löschen des Default-Presets
                if name == 'default':
                    logger.warning("Das Default-Preset kann nicht gelöscht werden")
                    QMessageBox.warning(
                        self,
                        self.main_window.i18n.get("ui.delete_preset"),
                        self.main_window.i18n.get("ui.cannot_delete_default"),
                        QMessageBox.Ok
                    )
                    return
                
                # Bestätigung einholen
                reply = QMessageBox.question(
                    self,
                    self.main_window.i18n.get("ui.delete_preset"),
                    self.main_window.i18n.get("ui.confirm_delete_preset").format(name=name),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    presets = self.main_window.settings.get('presets', {})
                    if name in presets:
                        del presets[name]
                        self.main_window.settings['presets'] = presets
                        self.main_window.settings_manager.save_settings(self.main_window.settings)
                        self.list_widget.takeItem(self.list_widget.row(current))
                        logger.info(f"Preset '{name}' gelöscht")
                    
        except Exception as e:
            logger.error(f"Fehler beim Löschen des Presets: {e}")
            QMessageBox.critical(
                self,
                self.main_window.i18n.get("ui.error"),
                str(e),
                QMessageBox.Ok
            )
