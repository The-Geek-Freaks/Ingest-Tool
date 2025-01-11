#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Layout für den oberen Bereich des Hauptfensters."""

from PyQt5.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QGroupBox,
    QListWidget, QPushButton
)
from ui.widgets.drive_list import DriveList

def create_top_layout(window):
    """Erstellt das obere Layout mit den Laufwerken."""
    layout = QHBoxLayout()
    
    # Verbundene Laufwerke
    connected_group = QGroupBox()
    connected_group.setTitle(" " + window.i18n.get("ui.connected_drives"))
    connected_layout = QVBoxLayout(connected_group)
    window.drives_list = DriveList(window)
    connected_layout.addWidget(window.drives_list)
    layout.addWidget(connected_group)
    
    return layout
