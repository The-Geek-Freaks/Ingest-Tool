#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Layout für den Einstellungsbereich des Hauptfensters."""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QCheckBox, QLabel, QComboBox
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from ui.style_helper import StyleHelper
from ui.dialogs.advanced_settings import AdvancedSettingsDialog
from ui.components.dialogs import FileTypesDialog
from config.constants import STANDARD_DATEITYPEN
import logging
logger = logging.getLogger(__name__)

def create_button(text: str, icon_name: str, bg_color: str, text_color: str, border_color: str) -> QPushButton:
    """Erstellt einen Button mit Icon und einheitlichem Styling."""
    button = QPushButton(text)
    button.setStyleSheet(f"""
        QPushButton {{
            background-color: {bg_color};
            color: {text_color};
            border: 1px solid {border_color};
            border-radius: 4px;
            padding: 8px 16px;
            text-align: left;
            font-size: 13px;
        }}
        QPushButton:hover {{
            background-color: {StyleHelper.SURFACE_LIGHT};
        }}
    """)
    
    # Icon aus der Resource-Datei laden
    try:
        icon = QIcon(f"resources/icons/{icon_name}.svg")
        if not icon.isNull():
            button.setIcon(icon)
            button.setIconSize(QSize(16, 16))
    except Exception as e:
        logger.error(f"Fehler beim Laden des Icons {icon_name}: {e}")
    
    return button

def create_settings_layout(main_window: QMainWindow) -> QWidget:
    """Erstellt das Layout für die Einstellungen."""
    # Container Widget
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    
    # Settings Widget
    settings_widget = QWidget()
    settings_layout = QVBoxLayout(settings_widget)
    settings_layout.setContentsMargins(8, 8, 8, 8)
    settings_layout.setSpacing(4)
    
    # Quelldatei nach Transfer löschen
    delete_source_checkbox = QCheckBox(main_window.i18n.get("Quelldatei nach Transfer löschen"))
    delete_source_checkbox.setObjectName("delete_source_checkbox")
    delete_source_checkbox.setChecked(main_window.settings.get('delete_source_files', False))
    delete_source_checkbox.stateChanged.connect(
        lambda state: main_window.settings_manager.save_settings({**main_window.settings, 'delete_source_files': bool(state)})
    )
    delete_source_checkbox.setStyleSheet(f"""
        QCheckBox {{
            color: {StyleHelper.TEXT};
            font-size: 13px;
            padding: 4px;
        }}
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border: 1px solid {StyleHelper.BORDER};
            border-radius: 2px;
            background: {StyleHelper.SURFACE};
        }}
        QCheckBox::indicator:checked {{
            background: {StyleHelper.PRIMARY};
            border-color: {StyleHelper.PRIMARY};
            image: url(resources/icons/check.svg);
        }}
    """)
    settings_layout.addWidget(delete_source_checkbox)
    
    # Voreinstellungen verwalten Button
    manage_presets_button = QPushButton("⚙️ " + main_window.i18n.get("Preset Manager"))
    manage_presets_button.setStyleSheet(f"""
        QPushButton {{
            background-color: {StyleHelper.SURFACE};
            color: {StyleHelper.TEXT};
            border: 1px solid {StyleHelper.BORDER};
            border-radius: 4px;
            padding: 8px 16px;
            text-align: left;
            font-size: 13px;
        }}
        QPushButton:hover {{
            background-color: {StyleHelper.SURFACE_LIGHT};
        }}
    """)
    manage_presets_button.clicked.connect(main_window.settings_handlers.show_preset_manager)
    settings_layout.addWidget(manage_presets_button)
    
    # Dateitypen verwalten Button
    manage_filetypes_button = QPushButton("📁 " + main_window.i18n.get("Dateitypen verwalten"))
    manage_filetypes_button.setStyleSheet(f"""
        QPushButton {{
            background-color: {StyleHelper.SURFACE};
            color: {StyleHelper.TEXT};
            border: 1px solid {StyleHelper.BORDER};
            border-radius: 4px;
            padding: 8px 16px;
            text-align: left;
            font-size: 13px;
        }}
        QPushButton:hover {{
            background-color: {StyleHelper.SURFACE_LIGHT};
        }}
    """)
    manage_filetypes_button.clicked.connect(lambda: _show_filetypes_dialog(main_window))
    settings_layout.addWidget(manage_filetypes_button)
    
    # Erweiterte Einstellungen Button
    advanced_settings_button = QPushButton("🛠️ " + main_window.i18n.get("Erweiterte Einstellungen"))
    advanced_settings_button.setStyleSheet(f"""
        QPushButton {{
            background-color: {StyleHelper.SURFACE};
            color: {StyleHelper.TEXT};
            border: 1px solid {StyleHelper.BORDER};
            border-radius: 4px;
            padding: 8px 16px;
            text-align: left;
            font-size: 13px;
        }}
        QPushButton:hover {{
            background-color: {StyleHelper.SURFACE_LIGHT};
        }}
    """)
    advanced_settings_button.clicked.connect(lambda: AdvancedSettingsDialog(main_window).exec_())
    settings_layout.addWidget(advanced_settings_button)
    
    settings_layout.addStretch()
    layout.addWidget(settings_widget)
    
    return container

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
