#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QSizePolicy
from PyQt5.QtCore import Qt
from .drive_list_item import DriveListItem
from ui.style_helper import StyleHelper

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
    
    def _get_drive_type_order(self, drive_type: str) -> int:
        """Gibt die Sortierreihenfolge für einen Laufwerkstyp zurück."""
        order = {
            'local': 0,
            'removable': 1,
            'remote': 2
        }
        return order.get(drive_type, 999)  # Unbekannte Typen ans Ende
    
    def addItem(self, item):
        """Fügt ein Laufwerk zur Liste hinzu und sortiert es nach Typ."""
        if isinstance(item, DriveListItem):
            # Finde die richtige Position basierend auf dem Laufwerkstyp
            drive_type = item.drive_type
            type_order = self._get_drive_type_order(drive_type)
            
            # Durchlaufe die Liste und finde die richtige Position
            for i in range(self.count()):
                current_item = self.item(i)
                if isinstance(current_item, DriveListItem):
                    current_type = current_item.drive_type
                    current_order = self._get_drive_type_order(current_type)
                    
                    # Wenn wir eine Position mit höherer Ordnung finden,
                    # fügen wir das neue Item davor ein
                    if current_order > type_order:
                        super().insertItem(i, item)
                        item.setSizeHint(item.widget.sizeHint())
                        self.setItemWidget(item, item.widget)
                        self.drive_items[item.drive_letter] = item
                        return
            
            # Wenn keine passende Position gefunden wurde, ans Ende anfügen
            super().addItem(item)
            item.setSizeHint(item.widget.sizeHint())
            self.setItemWidget(item, item.widget)
            self.drive_items[item.drive_letter] = item
        else:
            super().addItem(item)
            
    def remove_drive(self, drive_letter: str):
        """Entfernt ein Laufwerk aus der Liste."""
        if drive_letter in self.drive_items:
            item = self.drive_items[drive_letter]
            row = self.row(item)
            self.takeItem(row)
            del self.drive_items[drive_letter]
                
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
        drive_letters = list(self.drive_items.keys())
        logger.debug(f"Verfügbare Laufwerksbuchstaben: {drive_letters}")
        return drive_letters

    def get_drive_status(self, drive_letter: str) -> str:
        """Gibt den Status eines Laufwerks zurück."""
        if drive_letter in self.drive_items:
            drive_item = self.drive_items[drive_letter]
            status = drive_item.widget.get_status() if hasattr(drive_item, 'widget') else 'unknown'
            logger.debug(f"Status für Laufwerk {drive_letter}: {status}")
            return status
        logger.debug(f"Laufwerk {drive_letter} nicht in der Liste gefunden")
        return 'unknown'
        
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
