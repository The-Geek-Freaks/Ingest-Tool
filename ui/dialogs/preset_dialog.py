#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                           QLineEdit, QPushButton, QListWidget, QMessageBox, QFileDialog, QShortcut, QGroupBox)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QKeySequence
from utils.settings import PresetManager

class PresetDialog(QDialog):
    """Dialog für die Preset-Verwaltung."""
    
    preset_selected = pyqtSignal(dict)  # Wird emittiert wenn ein Preset geladen wird
    
    def __init__(self, current_settings: dict, parent=None):
        super().__init__(parent)
        self.current_settings = current_settings
        self.preset_manager = PresetManager()
        
        self.setWindowTitle("Preset-Verwaltung")
        self.setup_ui()
        self.load_presets()
        
        # Prüfe auf Auto-Save
        if self.preset_manager.has_auto_save():
            self._show_auto_save_dialog()
        
    def setup_ui(self):
        """Richtet das UI des Dialogs ein."""
        layout = QVBoxLayout()
        
        # Letzte Presets
        recent_group = QGroupBox("Zuletzt verwendet")
        recent_layout = QHBoxLayout()
        self.recent_buttons = []
        
        for _ in range(self.preset_manager.MAX_RECENT_PRESETS):
            btn = QPushButton()
            btn.setVisible(False)
            btn.clicked.connect(lambda checked, b=btn: self._on_recent_clicked(b))
            self.recent_buttons.append(btn)
            recent_layout.addWidget(btn)
            
        recent_group.setLayout(recent_layout)
        layout.addWidget(recent_group)
        
        # Preset-Liste
        self.preset_list = QListWidget()
        self.preset_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.preset_list.setSortingEnabled(True)  # Aktiviere alphabetische Sortierung
        layout.addWidget(self.preset_list)
        
        # Name-Eingabe
        name_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        name_layout.addWidget(QLabel("Name:"))
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # Hauptbuttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton(" Speichern")
        self.save_button.clicked.connect(self._on_save)
        self.save_button.setToolTip("Aktuellen Stand als Preset speichern (Strg+S)")
        
        self.load_button = QPushButton(" Laden")
        self.load_button.clicked.connect(self._on_load)
        self.load_button.setEnabled(False)
        self.load_button.setToolTip("Ausgewähltes Preset laden (Enter)")
        
        self.delete_button = QPushButton(" Löschen")
        self.delete_button.clicked.connect(self._on_delete)
        self.delete_button.setEnabled(False)
        self.delete_button.setToolTip("Ausgewähltes Preset löschen (Entf)")
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.delete_button)
        
        layout.addLayout(button_layout)
        
        # Zusätzliche Aktionen
        action_layout = QHBoxLayout()
        
        self.rename_button = QPushButton(" Umbenennen")
        self.rename_button.clicked.connect(self._on_rename)
        self.rename_button.setEnabled(False)
        self.rename_button.setToolTip("Ausgewähltes Preset umbenennen (F2)")
        
        self.duplicate_button = QPushButton(" Duplizieren")
        self.duplicate_button.clicked.connect(self._on_duplicate)
        self.duplicate_button.setEnabled(False)
        self.duplicate_button.setToolTip("Ausgewähltes Preset duplizieren (Strg+D)")
        
        action_layout.addWidget(self.rename_button)
        action_layout.addWidget(self.duplicate_button)
        
        layout.addLayout(action_layout)
        
        # Import/Export
        import_export_layout = QHBoxLayout()
        
        self.import_button = QPushButton(" Importieren")
        self.import_button.clicked.connect(self._on_import)
        self.import_button.setToolTip("Presets aus Datei importieren")
        
        self.export_button = QPushButton(" Exportieren")
        self.export_button.clicked.connect(self._on_export)
        self.export_button.setEnabled(False)
        self.export_button.setToolTip("Ausgewählte Presets exportieren")
        
        import_export_layout.addWidget(self.import_button)
        import_export_layout.addWidget(self.export_button)
        
        layout.addLayout(import_export_layout)
        
        self.setLayout(layout)
        self.setup_shortcuts()
        self.update_recent_buttons()
        
    def setup_shortcuts(self):
        """Erstellt Keyboard-Shortcuts."""
        QShortcut(QKeySequence("Ctrl+S"), self, self._on_save)
        QShortcut(QKeySequence("Return"), self, self._on_load)
        QShortcut(QKeySequence("Delete"), self, self._on_delete)
        QShortcut(QKeySequence("F2"), self, self._on_rename)
        QShortcut(QKeySequence("Ctrl+D"), self, self._on_duplicate)
        
    def update_recent_buttons(self):
        """Aktualisiert die Buttons für die zuletzt verwendeten Presets."""
        recent_presets = self.preset_manager.get_recent_presets()
        
        for i, btn in enumerate(self.recent_buttons):
            if i < len(recent_presets):
                name = recent_presets[i]
                btn.setText(name)
                btn.setVisible(True)
                btn.setToolTip(f"Schnellzugriff auf '{name}'")
            else:
                btn.setVisible(False)
                
    def _show_auto_save_dialog(self):
        """Zeigt einen Dialog für nicht gespeicherte Änderungen."""
        reply = QMessageBox.question(
            self,
            "Nicht gespeicherte Änderungen",
            "Es gibt nicht gespeicherte Änderungen vom letzten Mal. Möchten Sie diese laden?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            settings = self.preset_manager.load_auto_save()
            self.preset_selected.emit(settings)
            
        self.preset_manager.clear_auto_save()
        
    def _on_recent_clicked(self, button):
        """Handler für Klicks auf die Recent-Buttons."""
        name = button.text()
        if name and self.preset_manager.preset_existiert(name):
            settings = self.preset_manager.preset_laden(name)
            self.preset_selected.emit(settings)
            self.preset_manager.add_to_recent(name)
            self.update_recent_buttons()
            
    def _on_save(self):
        """Speichert die aktuellen Einstellungen als Preset."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Fehler", "Bitte geben Sie einen Namen ein.")
            return
            
        if self.preset_manager.preset_existiert(name):
            reply = QMessageBox.question(
                self, "Überschreiben?",
                f"Preset '{name}' existiert bereits. Überschreiben?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
                
        self.preset_manager.preset_hinzufuegen(name, self.current_settings)
        self.preset_manager.add_to_recent(name)
        self.load_presets()
        self.update_recent_buttons()
        
    def _on_load(self):
        """Lädt das ausgewählte Preset."""
        if not self.preset_list.currentItem():
            return
            
        name = self.preset_list.currentItem().text()
        settings = self.preset_manager.preset_laden(name)
        if settings:
            self.preset_selected.emit(settings)
            self.accept()
        else:
            QMessageBox.warning(self, "Fehler", f"Preset '{name}' konnte nicht geladen werden.")
            
    def _on_delete(self):
        """Löscht das ausgewählte Preset."""
        if not self.preset_list.currentItem():
            return
            
        name = self.preset_list.currentItem().text()
        reply = QMessageBox.question(
            self, "Löschen bestätigen",
            f"Preset '{name}' wirklich löschen?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.preset_manager.preset_loeschen(name)
            self.load_presets()

    def load_presets(self):
        """Lädt die verfügbaren Presets in die Liste."""
        self.preset_list.clear()
        for preset_name in sorted(self.preset_manager.alle_presets()):  # Sortiere alphabetisch
            self.preset_list.addItem(preset_name)
            
    def _on_selection_changed(self):
        """Handler für Änderungen der Preset-Auswahl."""
        selected = len(self.preset_list.selectedItems()) > 0
        self.load_button.setEnabled(selected)
        self.delete_button.setEnabled(selected)
        self.rename_button.setEnabled(selected)
        self.duplicate_button.setEnabled(selected)
        self.export_button.setEnabled(selected)
        if selected:
            self.name_input.setText(self.preset_list.currentItem().text())
            
    def _on_rename(self):
        """Benennt das ausgewählte Preset um."""
        if not self.preset_list.currentItem():
            return
            
        old_name = self.preset_list.currentItem().text()
        new_name = self.name_input.text().strip()
        
        if not new_name:
            QMessageBox.warning(self, "Fehler", "Bitte geben Sie einen Namen ein.")
            return
            
        if new_name == old_name:
            return
            
        if self.preset_manager.preset_existiert(new_name):
            reply = QMessageBox.question(
                self, "Überschreiben?",
                f"Preset '{new_name}' existiert bereits. Überschreiben?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
                
        settings = self.preset_manager.preset_laden(old_name)
        self.preset_manager.preset_loeschen(old_name)
        self.preset_manager.preset_hinzufuegen(new_name, settings)
        self.load_presets()
        
    def _on_duplicate(self):
        """Dupliziert das ausgewählte Preset."""
        if not self.preset_list.currentItem():
            return
            
        old_name = self.preset_list.currentItem().text()
        new_name = f"{old_name} (Kopie)"
        i = 1
        
        while self.preset_manager.preset_existiert(new_name):
            new_name = f"{old_name} (Kopie {i})"
            i += 1
            
        settings = self.preset_manager.preset_laden(old_name)
        self.preset_manager.preset_hinzufuegen(new_name, settings)
        self.load_presets()
        
        # Wähle das neue Preset aus
        items = self.preset_list.findItems(new_name, Qt.MatchExactly)
        if items:
            self.preset_list.setCurrentItem(items[0])
            
    def _on_import(self):
        """Importiert Presets aus einer JSON-Datei."""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Presets importieren",
            "",
            "JSON-Dateien (*.json)"
        )
        if file_name:
            try:
                imported = self.preset_manager.import_presets(file_name)
                self.load_presets()
                QMessageBox.information(
                    self,
                    "Import erfolgreich",
                    f"{len(imported)} Presets wurden importiert."
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Fehler beim Import",
                    f"Die Presets konnten nicht importiert werden:\n{str(e)}"
                )
                
    def _on_export(self):
        """Exportiert ausgewählte Presets in eine JSON-Datei."""
        if not self.preset_list.selectedItems():
            return
            
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Presets exportieren",
            "",
            "JSON-Dateien (*.json)"
        )
        if file_name:
            try:
                presets_to_export = {}
                for item in self.preset_list.selectedItems():
                    name = item.text()
                    presets_to_export[name] = self.preset_manager.preset_laden(name)
                    
                self.preset_manager.export_presets(file_name, presets_to_export)
                QMessageBox.information(
                    self,
                    "Export erfolgreich",
                    f"{len(presets_to_export)} Presets wurden exportiert."
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Fehler beim Export",
                    f"Die Presets konnten nicht exportiert werden:\n{str(e)}"
                )
