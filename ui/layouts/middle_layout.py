#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Layout für den mittleren Bereich des Hauptfensters."""

from PyQt5.QtWidgets import (
    QHBoxLayout, QVBoxLayout,
    QListWidget, QPushButton,
    QLabel, QComboBox, QLineEdit,
    QWidget
)

from ui.style_helper import StyleHelper
from ui.widgets.header_widget import HeaderWidget
from config.constants import STANDARD_DATEITYPEN

def create_middle_layout(window):
    """Erstellt das Layout für den mittleren Bereich."""
    layout = QHBoxLayout()
    layout.setSpacing(20)  # Abstand zwischen den Hauptspalten
    
    # Linke Spalte: Zuordnungen
    left_column = QVBoxLayout()
    
    # Zuordnungen Header und Content
    mappings_widget = HeaderWidget(" 🔄 " + window.i18n.get("ui.mappings"))
    
    # Container für Eingabefelder mit definiertem Spacing
    input_container = QWidget()
    mapping_input_layout = QHBoxLayout(input_container)
    mapping_input_layout.setContentsMargins(0, 0, 0, 0)
    mapping_input_layout.setSpacing(10)
    
    # Dateityp
    filetype_combo_container = QWidget()
    filetype_combo_layout = QHBoxLayout(filetype_combo_container)
    filetype_combo_layout.setContentsMargins(0, 0, 0, 0)
    filetype_combo_layout.setSpacing(5)
    
    filetype_label = QLabel(window.i18n.get("ui.file_type"))
    filetype_label.setStyleSheet(f"color: {StyleHelper.TEXT};")
    filetype_combo_layout.addWidget(filetype_label)
    
    window.filetype_combo = QComboBox()
    window.filetype_combo.setEditable(True)
    window.filetype_combo.setStyleSheet(StyleHelper.get_combo_box_style())
    
    # Alle Dateitypen aus den Standardeinstellungen laden
    all_extensions = []
    for category in STANDARD_DATEITYPEN.values():
        all_extensions.extend([f"*{ext}" for ext in category])
    window.filetype_combo.addItems(sorted(all_extensions))
    
    filetype_combo_layout.addWidget(window.filetype_combo)
    
    mapping_input_layout.addWidget(filetype_combo_container)
    
    # Button für Zielverzeichnis
    window.browse_button = QPushButton("📂 " + window.i18n.get("ui.browse"))
    window.browse_button.clicked.connect(window.event_handlers.on_browse_clicked)
    window.browse_button.setStyleSheet(StyleHelper.get_button_style())
    mapping_input_layout.addWidget(window.browse_button)
    
    mappings_widget.add_widget(input_container)
    
    # Liste der Zuordnungen
    window.mappings_list = QListWidget()
    window.mappings_list.setStyleSheet(StyleHelper.get_list_widget_style())
    mappings_widget.add_widget(window.mappings_list)
    
    # Container für Buttons mit definiertem Spacing
    button_container = QWidget()
    mapping_buttons = QHBoxLayout(button_container)
    mapping_buttons.setContentsMargins(0, 0, 0, 0)
    mapping_buttons.setSpacing(10)
    
    window.add_mapping_button = QPushButton("➕ " + window.i18n.get("general.add"))
    window.remove_mapping_button = QPushButton("🗑️ " + window.i18n.get("general.remove"))
    window.add_mapping_button.setStyleSheet(StyleHelper.get_button_style())
    window.remove_mapping_button.setStyleSheet(StyleHelper.get_button_style())
    window.add_mapping_button.clicked.connect(window._on_add_mapping_clicked)
    window.remove_mapping_button.clicked.connect(window._on_remove_mapping_clicked)
    
    mapping_buttons.addWidget(window.add_mapping_button)
    mapping_buttons.addWidget(window.remove_mapping_button)
    
    mappings_widget.add_widget(button_container)
    
    left_column.addWidget(mappings_widget)
    layout.addLayout(left_column)
    
    # Rechte Spalte: Ausgeschlossene Laufwerke
    right_column = QVBoxLayout()
    
    # Ausgeschlossene Laufwerke Header und Content
    excluded_widget = HeaderWidget(" 🚫 " + window.i18n.get("ui.excluded_drives"))
    
    window.excluded_list = QListWidget()
    window.excluded_list.setStyleSheet(StyleHelper.get_list_widget_style())
    excluded_widget.add_widget(window.excluded_list)
    
    # Container für Exclude-Buttons
    exclude_button_container = QWidget()
    exclude_buttons = QHBoxLayout(exclude_button_container)
    exclude_buttons.setContentsMargins(0, 0, 0, 0)
    exclude_buttons.setSpacing(10)
    
    window.exclude_button = QPushButton("🚫 " + window.i18n.get("general.add"))
    window.include_button = QPushButton("✅ " + window.i18n.get("general.remove"))
    window.exclude_all_button = QPushButton("⛔ " + window.i18n.get("ui.exclude_all"))
    
    for button in [window.exclude_button, window.include_button, window.exclude_all_button]:
        button.setStyleSheet(StyleHelper.get_button_style())
        exclude_buttons.addWidget(button)
    
    window.exclude_button.clicked.connect(window.event_handlers.on_add_excluded_path_clicked)
    window.include_button.clicked.connect(window._on_remove_excluded_clicked)
    window.exclude_all_button.clicked.connect(window._on_exclude_all_clicked)
    
    excluded_widget.add_widget(exclude_button_container)
    
    right_column.addWidget(excluded_widget)
    layout.addLayout(right_column)
    
    return layout
