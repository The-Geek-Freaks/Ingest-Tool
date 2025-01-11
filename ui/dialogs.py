#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QFileDialog, QMessageBox,
    QCheckBox, QComboBox, QSpinBox, QGroupBox
)
from PyQt5.QtCore import Qt

from utils.settings import SettingsManager
from .widgets import StyleHelper

class ZielverzeichnisDialog(QDialog):
    """Dialog zum Hinzufügen oder Bearbeiten eines Zielverzeichnisses."""
    
    def __init__(self, parent=None, verzeichnis: str = None):
        super().__init__(parent)
        self.verzeichnis = verzeichnis
        self.init_ui()

    def init_ui(self):
        """Initialisiert die UI-Komponenten."""
        self.setWindowTitle("Zielverzeichnis" if not self.verzeichnis else "Verzeichnis bearbeiten")
        layout = QVBoxLayout(self)

        # Verzeichnispfad
        pfad_layout = QHBoxLayout()
        self.pfad_edit = QLineEdit(self.verzeichnis if self.verzeichnis else "")
        self.pfad_edit.setReadOnly(True)
        pfad_layout.addWidget(self.pfad_edit)

        # Durchsuchen-Button
        self.browse_button = QPushButton("Durchsuchen...")
        StyleHelper.style_button(self.browse_button)
        self.browse_button.clicked.connect(self.browse_directory)
        pfad_layout.addWidget(self.browse_button)

        layout.addLayout(pfad_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Abbrechen")
        StyleHelper.style_button(self.ok_button)
        StyleHelper.style_button(self.cancel_button)
        
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

    def browse_directory(self):
        """Öffnet den Verzeichnis-Auswahldialog."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Zielverzeichnis auswählen",
            self.pfad_edit.text()
        )
        if directory:
            self.pfad_edit.setText(directory)

    def get_directory(self) -> str:
        """Gibt das ausgewählte Verzeichnis zurück."""
        return self.pfad_edit.text()

class EinstellungenDialog(QDialog):
    """Dialog für Programmeinstellungen."""
    
    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.init_ui()

    def init_ui(self):
        """Initialisiert die UI-Komponenten."""
        self.setWindowTitle("Einstellungen")
        layout = QVBoxLayout(self)

        # Allgemeine Einstellungen
        allgemein_group = QGroupBox("Allgemein")
        allgemein_layout = QVBoxLayout()

        # Sprache
        sprach_layout = QHBoxLayout()
        sprach_layout.addWidget(QLabel("Sprache:"))
        self.sprach_combo = QComboBox()
        self.sprach_combo.addItems(["Deutsch", "English"])
        sprach_layout.addWidget(self.sprach_combo)
        allgemein_layout.addLayout(sprach_layout)

        # Dark Mode
        self.dark_mode_check = QCheckBox("Dark Mode")
        allgemein_layout.addWidget(self.dark_mode_check)

        # Benachrichtigungen
        self.notifications_check = QCheckBox("Benachrichtigungen anzeigen")
        allgemein_layout.addWidget(self.notifications_check)

        allgemein_group.setLayout(allgemein_layout)
        layout.addWidget(allgemein_group)

        # Transfer-Einstellungen
        transfer_group = QGroupBox("Transfer")
        transfer_layout = QVBoxLayout()

        # Quelldateien löschen
        self.delete_source_check = QCheckBox(
            "Quelldateien nach erfolgreicher Übertragung löschen"
        )
        transfer_layout.addWidget(self.delete_source_check)

        # Automatischer Start
        self.auto_start_check = QCheckBox("Automatisch mit Transfer beginnen")
        transfer_layout.addWidget(self.auto_start_check)

        transfer_group.setLayout(transfer_layout)
        layout.addWidget(transfer_group)

        # Log-Einstellungen
        log_group = QGroupBox("Protokoll")
        log_layout = QVBoxLayout()

        # Maximale Log-Einträge
        log_entries_layout = QHBoxLayout()
        log_entries_layout.addWidget(QLabel("Maximale Log-Einträge:"))
        self.log_entries_spin = QSpinBox()
        self.log_entries_spin.setRange(100, 10000)
        self.log_entries_spin.setSingleStep(100)
        log_entries_layout.addWidget(self.log_entries_spin)
        log_layout.addLayout(log_entries_layout)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Abbrechen")
        StyleHelper.style_button(self.ok_button)
        StyleHelper.style_button(self.cancel_button)
        
        self.ok_button.clicked.connect(self.save_settings)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        # Lade aktuelle Einstellungen
        self.load_settings()

    def load_settings(self):
        """Lädt die aktuellen Einstellungen."""
        settings = self.settings_manager.einstellungen
        
        # Allgemein
        self.sprach_combo.setCurrentText(
            "English" if settings.get("sprache") == "en" else "Deutsch"
        )
        self.dark_mode_check.setChecked(settings.get("dark_mode", True))
        self.notifications_check.setChecked(settings.get("benachrichtigungen", True))
        
        # Transfer
        self.delete_source_check.setChecked(settings.get("quelldateien_loeschen", False))
        self.auto_start_check.setChecked(settings.get("auto_start", False))
        
        # Log
        self.log_entries_spin.setValue(settings.get("max_log_eintraege", 1000))

    def save_settings(self):
        """Speichert die Einstellungen."""
        # Allgemein
        self.settings_manager.set_einstellung(
            "sprache",
            "en" if self.sprach_combo.currentText() == "English" else "de"
        )
        self.settings_manager.set_einstellung("dark_mode", self.dark_mode_check.isChecked())
        self.settings_manager.set_einstellung("benachrichtigungen", self.notifications_check.isChecked())
        
        # Transfer
        self.settings_manager.set_einstellung("quelldateien_loeschen", self.delete_source_check.isChecked())
        self.settings_manager.set_einstellung("auto_start", self.auto_start_check.isChecked())
        
        # Log
        self.settings_manager.set_einstellung("max_log_eintraege", self.log_entries_spin.value())
        
        self.accept()
