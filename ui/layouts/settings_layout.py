#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Layout für den Einstellungsbereich des Hauptfensters."""

from PyQt5.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QGroupBox, QLabel,
    QPushButton, QComboBox, QCheckBox
)
from ui.dialogs.advanced_settings import AdvancedSettingsDialog
from ui.components.dialogs import FileTypesDialog
from config.constants import STANDARD_DATEITYPEN

def create_settings_layout(main_window) -> QHBoxLayout:
    """Erstellt das Layout für den Einstellungsbereich."""
    settings_group = QGroupBox(main_window.i18n.get("ui.settings"))
    settings_group.setObjectName("settings_group")
    settings_layout = QVBoxLayout(settings_group)
    
    # Delete source files checkbox
    main_window.delete_source_files_checkbox = QCheckBox("Quelldateien löschen nach erfolgreichem Kopiervorgang")
    main_window.delete_source_files_checkbox.setChecked(main_window.settings.get('delete_source_files', False))
    main_window.delete_source_files_checkbox.stateChanged.connect(
        lambda state: main_window.settings_manager.save_settings({**main_window.settings, 'delete_source_files': bool(state)})
    )
    settings_layout.addWidget(main_window.delete_source_files_checkbox)
    
    # Vorhandene Einstellungen
    main_window.manage_presets_button = QPushButton("⚙️ " + main_window.i18n.get("ui.manage_presets"))
    main_window.manage_presets_button.clicked.connect(main_window.settings_handlers.show_preset_manager)
    settings_layout.addWidget(main_window.manage_presets_button)
    
    # Dateitypen verwalten Button
    main_window.manage_filetypes_button = QPushButton("📁 Dateitypen verwalten")
    main_window.manage_filetypes_button.clicked.connect(lambda: _show_filetypes_dialog(main_window))
    settings_layout.addWidget(main_window.manage_filetypes_button)
    
    # Erweiterte Einstellungen Button
    main_window.advanced_settings_button = QPushButton("🔧 " + main_window.i18n.get("ui.advanced_settings"))
    main_window.advanced_settings_button.clicked.connect(lambda: AdvancedSettingsDialog(main_window).exec_())
    settings_layout.addWidget(main_window.advanced_settings_button)
    
    return settings_group

def _show_filetypes_dialog(main_window):
    """Zeigt den Dialog zur Verwaltung der Dateitypen."""
    # Hole aktuelle Dateitypen aus den Einstellungen oder verwende Standards
    current_types = main_window.settings.get('file_types', STANDARD_DATEITYPEN)
    
    dialog = FileTypesDialog(main_window, current_types)
    if dialog.exec_():
        # Speichere die aktualisierten Dateitypen
        new_types = dialog.get_file_types()
        main_window.settings['file_types'] = new_types
        main_window.settings_manager.save_settings(main_window.settings)
