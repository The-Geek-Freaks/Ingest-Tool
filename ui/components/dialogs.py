"""
Benutzerdefinierte Dialoge.
"""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QMessageBox, QDialogButtonBox, QGroupBox, QComboBox
)
from ui.style_helper import StyleHelper

class PresetDialog(QDialog):
    """Dialog zur Verwaltung von Presets."""
    
    def __init__(self, parent=None, presets=None):
        super().__init__(parent)
        self.presets = presets or []
        self.setup_ui()
        
    def setup_ui(self):
        """Richtet das UI des Dialogs ein."""
        self.setWindowTitle("Presets verwalten")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Preset Liste
        self.preset_list = QListWidget()
        for preset in self.presets:
            item = QListWidgetItem(preset['name'])
            item.setData(Qt.UserRole, preset)
            self.preset_list.addItem(item)
        layout.addWidget(self.preset_list)
        
        # Neues Preset
        input_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholder("Preset Name")
        input_layout.addWidget(self.name_input)
        
        add_button = QPushButton("Hinzufügen")
        add_button.clicked.connect(self.add_preset)
        input_layout.addWidget(add_button)
        layout.addLayout(input_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        remove_button = QPushButton("Entfernen")
        remove_button.clicked.connect(self.remove_preset)
        button_layout.addWidget(remove_button)
        
        button_layout.addStretch()
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)
        
        cancel_button = QPushButton("Abbrechen")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def add_preset(self):
        """Fügt ein neues Preset hinzu."""
        name = self.name_input.text().strip()
        if name:
            preset = {'name': name}
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, preset)
            self.preset_list.addItem(item)
            self.name_input.clear()
            
    def remove_preset(self):
        """Entfernt das ausgewählte Preset."""
        current = self.preset_list.currentItem()
        if current:
            self.preset_list.takeItem(self.preset_list.row(current))
            
    def get_presets(self):
        """Gibt die Liste der Presets zurück."""
        presets = []
        for i in range(self.preset_list.count()):
            item = self.preset_list.item(i)
            presets.append(item.data(Qt.UserRole))
        return presets

class FileTypesDialog(QDialog):
    """Dialog zur Verwaltung von Dateitypen."""
    
    def __init__(self, parent=None, file_types=None):
        super().__init__(parent)
        self.file_types = file_types or {}
        self.setup_ui()
        
    def setup_ui(self):
        """Richtet das UI des Dialogs ein."""
        self.setWindowTitle("Dateitypen verwalten")
        self.setMinimumWidth(400)
        layout = QVBoxLayout()
        
        # Dateityp-Auswahl
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Dateityp:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(sorted(self.file_types.keys()))
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        StyleHelper.style_combobox(self.type_combo)  # Wende das neue Styling an
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)
        
        # Liste der Erweiterungen
        extensions_group = QGroupBox("Erweiterungen")
        extensions_layout = QVBoxLayout()
        
        self.extensions_list = QListWidget()
        self._update_extensions_list()
        extensions_layout.addWidget(self.extensions_list)
        
        # Buttons für Erweiterungen
        ext_buttons_layout = QHBoxLayout()
        
        self.add_ext_edit = QLineEdit()
        self.add_ext_edit.setPlaceholderText(".xyz")
        ext_buttons_layout.addWidget(self.add_ext_edit)
        
        add_ext_btn = QPushButton("+")
        add_ext_btn.clicked.connect(self._add_extension)
        ext_buttons_layout.addWidget(add_ext_btn)
        
        remove_ext_btn = QPushButton("-")
        remove_ext_btn.clicked.connect(self._remove_extension)
        ext_buttons_layout.addWidget(remove_ext_btn)
        
        extensions_layout.addLayout(ext_buttons_layout)
        extensions_group.setLayout(extensions_layout)
        layout.addWidget(extensions_group)
        
        # Dialog-Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
    def _update_extensions_list(self):
        """Aktualisiert die Liste der Erweiterungen."""
        self.extensions_list.clear()
        current_type = self.type_combo.currentText()
        if current_type in self.file_types:
            self.extensions_list.addItems(sorted(self.file_types[current_type]))
            
    def _on_type_changed(self, type_name):
        """Handler für Änderungen des ausgewählten Dateityps."""
        self._update_extensions_list()
        
    def _add_extension(self):
        """Fügt eine neue Erweiterung hinzu."""
        ext = self.add_ext_edit.text().strip().lower()
        if not ext:
            return
            
        # Stelle sicher, dass die Erweiterung mit einem Punkt beginnt
        if not ext.startswith('.'):
            ext = '.' + ext
            
        current_type = self.type_combo.currentText()
        if current_type in self.file_types:
            if ext not in self.file_types[current_type]:
                self.file_types[current_type].append(ext)
                self._update_extensions_list()
                self.add_ext_edit.clear()
            else:
                QMessageBox.warning(
                    self,
                    "Fehler",
                    f"Die Erweiterung {ext} existiert bereits."
                )
                
    def _remove_extension(self):
        """Entfernt die ausgewählte Erweiterung."""
        current_item = self.extensions_list.currentItem()
        if not current_item:
            return
            
        ext = current_item.text()
        current_type = self.type_combo.currentText()
        
        if current_type in self.file_types:
            self.file_types[current_type].remove(ext)
            self._update_extensions_list()
            
    def get_file_types(self):
        """Gibt das aktualisierte Dictionary der Dateitypen zurück."""
        return self.file_types
