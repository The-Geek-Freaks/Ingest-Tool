#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                           QComboBox, QPushButton, QFileDialog, QLineEdit)
from PyQt5.QtCore import Qt

class BatchJobDialog(QDialog):
    """Dialog zum Hinzufügen eines neuen Batch-Jobs."""
    
    def __init__(self, parent=None, drives=None, file_types=None):
        super().__init__(parent)
        self.drives = drives or []
        self.file_types = file_types or []
        self.target_path = ""
        self.setup_ui()
        
    def setup_ui(self):
        """Erstellt die UI-Elemente."""
        self.setWindowTitle("Batch-Job hinzufügen")
        layout = QVBoxLayout(self)
        
        # Quelllaufwerk
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("Quelllaufwerk:"))
        self.source_combo = QComboBox()
        self.source_combo.addItems([f"{d.letter} ({d.label})" if d.label else d.letter 
                                  for d in self.drives])
        source_layout.addWidget(self.source_combo)
        layout.addLayout(source_layout)
        
        # Dateityp
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Dateityp:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(self.file_types)
        self.type_combo.setMinimumWidth(200)  # Breiter für bessere Lesbarkeit
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)
        
        # Zielverzeichnis
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("Zielverzeichnis:"))
        self.target_edit = QLineEdit()
        self.target_edit.setReadOnly(True)
        target_layout.addWidget(self.target_edit)
        self.browse_button = QPushButton("...")
        self.browse_button.clicked.connect(self.browse_target)
        target_layout.addWidget(self.browse_button)
        layout.addLayout(target_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Hinzufügen")
        self.save_button.setEnabled(False)  # Deaktiviert bis Zielverzeichnis gewählt
        cancel_button = QPushButton("Abbrechen")
        self.save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
    def browse_target(self):
        """Öffnet einen Dialog zur Auswahl des Zielverzeichnisses."""
        directory = QFileDialog.getExistingDirectory(
            self, "Zielverzeichnis wählen",
            self.target_edit.text() or "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if directory:
            self.target_edit.setText(directory)
            self.target_path = directory
            self.save_button.setEnabled(True)
            
    def get_job_data(self):
        """Gibt die eingegebenen Daten zurück."""
        if not self.target_path:
            return None
            
        source = self.drives[self.source_combo.currentIndex()].letter
        return {
            "source_drive": source,
            "file_type": self.type_combo.currentText(),
            "target_path": self.target_path
        }
