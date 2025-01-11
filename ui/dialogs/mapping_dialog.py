#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QDialogButtonBox,
    QFileDialog
)
from ui.style_helper import StyleHelper

class MappingDialog(QDialog):
    """Dialog für das Hinzufügen einer neuer Zuordnungen."""
    
    def __init__(self, parent=None):
        """Initialisiert den Dialog."""
        super().__init__(parent)
        self.setWindowTitle("Neue Zuordnung")
        self.setup_ui()
        
    def setup_ui(self):
        """Richtet die Dialog-UI ein."""
        layout = QVBoxLayout(self)
        
        # Dateitype und Zielverzeichnis
        type_layout = QHBoxLayout()
        type_label = QLabel("Dateityp:")
        self.type_edit = QLineEdit()
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_edit)
        layout.addLayout(type_layout)
        
        path_layout = QHBoxLayout()
        path_label = QLabel("Zielverzeichnis:")
        self.path_edit = QLineEdit()
        browse_button = QPushButton("...")
        browse_button.clicked.connect(self._on_browse_clicked)
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_button)
        layout.addLayout(path_layout)
        
        # OK/Abbrechen Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def _on_browse_clicked(self):
        """Handler für Browse-Button."""
        path = QFileDialog.getExistingDirectory(
            self,
            "Zielverzeichnis auswählen",
            ""
        )
        if path:
            self.path_edit.setText(path)
            
    def get_values(self):
        """Gibt die eingegebenen Werte zurück."""
        return (
            self.type_edit.text(),
            self.path_edit.text()
        )
