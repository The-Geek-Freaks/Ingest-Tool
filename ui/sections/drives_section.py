#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget
)
from PyQt5.QtCore import Qt
from core.drive_controller import DriveController
from .widgets.custom_list import CustomListWidget

class DrivesSection(QWidget):
    """Laufwerks-Sektion des Hauptfensters."""
    
    def __init__(self, drive_controller: DriveController, parent=None):
        super().__init__(parent)
        self.drive_controller = drive_controller
        self.setup_ui()
    
    def setup_ui(self):
        """Richtet das UI der Laufwerks-Sektion ein."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        drives_label = QLabel("Laufwerke")
        drives_label.setStyleSheet("color: white; font-size: 10pt;")
        layout.addWidget(drives_label)
        
        self.drives_list = CustomListWidget()
        layout.addWidget(self.drives_list)
