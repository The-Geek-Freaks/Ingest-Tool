#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QSizePolicy
from PyQt5.QtCore import Qt
from .drive_list_item import DriveListItem
from ..style_helper import StyleHelper

logger = logging.getLogger(__name__)

class DriveList(QListWidget):
    """Liste der verbundenen Laufwerke."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.drive_items = {}
        self._setup_ui()
        
    def _setup_ui(self):
        """Konfiguriert das Aussehen der Liste."""
        # Grundlegende Eigenschaften
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.setSpacing(2)
        
        # Style
        self.setStyleSheet(StyleHelper.get_list_style())
        
        # Widget soll sich in beide Richtungen ausdehnen
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
    def addItem(self, item):
        """Fügt ein Laufwerk zur Liste hinzu."""
        if isinstance(item, DriveListItem):
            super().addItem(item)
            item.setSizeHint(item.widget.sizeHint())
            self.setItemWidget(item, item.widget)
            self.drive_items[item.drive_letter] = item
            
    def remove_drive(self, drive_letter: str):
        """Entfernt ein Laufwerk aus der Liste."""
        if drive_letter in self.drive_items:
            item = self.drive_items.pop(drive_letter)
            row = self.row(item)
            if row >= 0:
                self.takeItem(row)
                
    def get_selected_drives(self) -> list:
        """Gibt eine Liste der ausgewählten Laufwerksbuchstaben zurück."""
        selected_drives = []
        for i in range(self.count()):
            item = self.item(i)
            if item.isSelected():
                selected_drives.append(item.drive_letter)
        return selected_drives
        
    def get_drive_letters(self) -> list:
        """Gibt eine Liste aller Laufwerksbuchstaben in der Liste zurück."""
        return list(self.drive_items.keys())
        
    def clear(self):
        """Leert die Liste."""
        super().clear()
        self.drive_items.clear()
        
    def resizeEvent(self, event):
        """Aktualisiert die Größe der Items beim Resize."""
        super().resizeEvent(event)
        for i in range(self.count()):
            item = self.item(i)
            if item and hasattr(item, 'widget'):
                item.setSizeHint(item.widget.sizeHint())
