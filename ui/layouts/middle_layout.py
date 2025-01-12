#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Layout für den mittleren Bereich des Hauptfensters."""

from PyQt5.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QGroupBox,
    QListWidget, QPushButton, QLabel,
    QComboBox, QLineEdit
)
from ui.style_helper import StyleHelper

def create_middle_layout(window):
    """Erstellt das mittlere Layout mit den Zuordnungen und ausgeschlossenen Laufwerken."""
    layout = QHBoxLayout()
    
    # Zuordnungen
    mappings_group = QGroupBox()
    mappings_group.setTitle("📁 " + window.i18n.get("ui.mappings"))
    mappings_layout = QVBoxLayout(mappings_group)
    
    # Dateityp und Zielverzeichnis
    mapping_input_layout = QHBoxLayout()
    filetype_label = QLabel(window.i18n.get("ui.file_type"))
    window.filetype_combo = QComboBox()
    window.filetype_combo.addItems(window.get_file_types())
    window.filetype_combo.setEditable(True)
    window.filetype_combo.setFixedWidth(200)  # Breite des Dateityp-Dropdowns anpassen
    StyleHelper.style_combobox(window.filetype_combo)  # Wende das Styling an
    mapping_input_layout.addWidget(filetype_label)
    mapping_input_layout.addWidget(window.filetype_combo)
    
    # Button für Zielverzeichnis
    window.browse_button = QPushButton("📂 " + window.i18n.get("ui.browse"))
    window.browse_button.clicked.connect(window.event_handlers.on_browse_clicked)
    mapping_input_layout.addWidget(window.browse_button)
    
    mappings_layout.addLayout(mapping_input_layout)
    
    # Liste der Zuordnungen
    window.mappings_list = QListWidget()
    mappings_layout.addWidget(window.mappings_list)
    
    # Mapping Buttons
    mapping_buttons = QHBoxLayout()
    window.add_mapping_button = QPushButton("➕ " + window.i18n.get("general.add"))
    window.remove_mapping_button = QPushButton("🗑️ " + window.i18n.get("general.remove"))
    window.add_mapping_button.clicked.connect(window._on_add_mapping_clicked)
    window.remove_mapping_button.clicked.connect(window._on_remove_mapping_clicked)
    mapping_buttons.addWidget(window.add_mapping_button)
    mapping_buttons.addWidget(window.remove_mapping_button)
    mappings_layout.addLayout(mapping_buttons)
    layout.addWidget(mappings_group)
    
    # Ausgeschlossene Laufwerke
    excluded_group = QGroupBox()
    excluded_group.setTitle("🚫 " + window.i18n.get("ui.excluded_drives"))
    excluded_layout = QVBoxLayout(excluded_group)
    window.excluded_list = QListWidget()
    excluded_layout.addWidget(window.excluded_list)
    
    # Excluded Buttons
    excluded_buttons = QHBoxLayout()
    window.add_excluded_button = QPushButton("🚫 " + window.i18n.get("general.add"))
    window.remove_excluded_button = QPushButton("✅ " + window.i18n.get("general.remove"))
    window.exclude_all_button = QPushButton("⛔ " + window.i18n.get("ui.exclude_all"))
    window.add_excluded_button.clicked.connect(window.event_handlers.on_add_excluded_path_clicked)
    window.remove_excluded_button.clicked.connect(window._on_remove_excluded_clicked)
    window.exclude_all_button.clicked.connect(window._on_exclude_all_clicked)
    excluded_buttons.addWidget(window.add_excluded_button)
    excluded_buttons.addWidget(window.remove_excluded_button)
    excluded_layout.addLayout(excluded_buttons)
    excluded_layout.addWidget(window.exclude_all_button)
    layout.addWidget(excluded_group)
    
    return layout
