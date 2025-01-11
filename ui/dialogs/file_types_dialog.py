#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                           QLineEdit, QPushButton, QListWidget, QMessageBox,
                           QComboBox)
from PyQt5.QtCore import pyqtSignal
from config.constants import STANDARD_DATEITYPEN
from ui.style_helper import StyleHelper

class FileTypesDialog(QDialog):
    """Dialog für die Verwaltung der Dateitypen."""
    
    types_changed = pyqtSignal(list)  # Wird emittiert wenn sich die Typen ändern
    
    def __init__(self, current_types: list, parent=None):
        super().__init__(parent)
        self.current_types = current_types.copy()
        
        self.setWindowTitle("Dateitypen-Verwaltung")
        self.setup_ui()
        self.load_types()
        
    def setup_ui(self):
        """Richtet das UI des Dialogs ein."""
        layout = QVBoxLayout()
        
        # Dateityp-Auswahl
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Dateityp:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["AUDIO", "VIDEO", "IMAGE", "DOCUMENT"])
        StyleHelper.style_combobox(self.type_combo)
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)
        
        # Standard-Typen
        standard_group = QVBoxLayout()
        standard_group.addWidget(QLabel("Standard-Dateitypen:"))
        self.standard_list = QListWidget()
        self.standard_list.setSelectionMode(QListWidget.NoSelection)
        standard_group.addWidget(self.standard_list)
        layout.addLayout(standard_group)
        
        # Benutzerdefinierte Typen
        custom_group = QVBoxLayout()
        custom_group.addWidget(QLabel("Benutzerdefinierte Dateitypen:"))
        self.custom_list = QListWidget()
        custom_group.addWidget(self.custom_list)
        layout.addLayout(custom_group)
        
        # Eingabezeile
        input_layout = QHBoxLayout()
        self.type_input = QLineEdit()
        self.type_input.setPlaceholderText(".xyz")
        self.add_button = QPushButton("Hinzufügen")
        self.add_button.clicked.connect(self._on_add)
        input_layout.addWidget(self.type_input)
        input_layout.addWidget(self.add_button)
        layout.addLayout(input_layout)
        
        # Aktions-Buttons
        button_layout = QHBoxLayout()
        self.remove_button = QPushButton("Entfernen")
        self.remove_button.clicked.connect(self._on_remove)
        self.remove_button.setEnabled(False)
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Abbrechen")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.remove_button)
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Verbinde Signale
        self.custom_list.itemSelectionChanged.connect(self._on_selection_changed)
        
    def load_types(self):
        """Lädt die Dateitypen in die Listen."""
        # Standard-Typen
        self.standard_list.clear()
        for type_ in STANDARD_DATEITYPEN:
            self.standard_list.addItem(type_)
            
        # Benutzerdefinierte Typen
        self.custom_list.clear()
        custom_types = [t for t in self.current_types if t not in STANDARD_DATEITYPEN]
        for type_ in custom_types:
            self.custom_list.addItem(type_)
            
    def _on_add(self):
        """Fügt einen neuen Dateityp hinzu."""
        type_ = self.type_input.text().strip().lower()
        if not type_:
            return
            
        # Stelle sicher, dass der Typ mit einem Punkt beginnt
        if not type_.startswith('.'):
            type_ = '.' + type_
            
        # Prüfe ob der Typ bereits existiert
        if type_ in self.current_types:
            QMessageBox.warning(self, "Fehler", f"Dateityp {type_} existiert bereits.")
            return
            
        # Füge den Typ hinzu
        self.current_types.append(type_)
        self.custom_list.addItem(type_)
        self.type_input.clear()
        
        # Signalisiere Änderung
        self.types_changed.emit(self.current_types)
        
    def _on_remove(self):
        """Entfernt den ausgewählten Dateityp."""
        if not self.custom_list.currentItem():
            return
            
        type_ = self.custom_list.currentItem().text()
        self.current_types.remove(type_)
        self.load_types()
        
        # Signalisiere Änderung
        self.types_changed.emit(self.current_types)
        
    def _on_selection_changed(self):
        """Aktualisiert den Zustand des Entfernen-Buttons."""
        self.remove_button.setEnabled(len(self.custom_list.selectedItems()) > 0)
        
    def accept(self):
        """Handler für den OK-Button."""
        self.types_changed.emit(self.current_types)
        super().accept()
