#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""DriveList-Widget für die Anzeige von Laufwerken."""

from PyQt5.QtWidgets import QListWidget, QListWidgetItem
from PyQt5.QtCore import QSize
from ui.widgets.drive_list_item import DriveListItem

class DriveList(QListWidget):
    """Liste der verbundenen Laufwerke."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setDragEnabled(False)
        self.setAcceptDrops(False)
        self.drive_items = {}
        
        # Setze die Größe der Items und entferne Einzug
        self.setStyleSheet("""
            QListWidget {
                background-color: #2b2b2b;
                show-decoration-selected: 0;
                spacing: 1px;  /* Verringere den Abstand zwischen Items */
            }
            QListWidget::item {
                min-height: 35px;  /* Reduziere die Mindesthöhe der Items */
                padding: 1px;  /* Verringere das Padding */
                padding-left: 6px;
                background-color: #333333;
                border: 1px solid #404040;
                border-radius: 3px;
            }
            QListWidget::item:selected {
                background-color: #404040;
                border: 1px solid #505050;
            }
            QListWidget::indicator,
            QListWidget::branch {
                width: 0px;
                border: none;
                background: none;
                margin: 0px;
                padding: 0px;
            }
        """)
        
    def addItem(self, item):
        """Fügt ein Laufwerk zur Liste hinzu."""
        if isinstance(item, DriveListItem):
            super().addItem(item)
            item.setSizeHint(QSize(self.viewport().width(), 35))  # Update size hint
            self.setItemWidget(item, item.widget)
            self.drive_items[item.drive_letter] = item
            self._update_height()
            
    def takeItem(self, row):
        """Entfernt ein Laufwerk aus der Liste."""
        item = super().takeItem(row)
        if item:
            self.removeItemWidget(item)
            self._update_height()
            self.update()
        return item
        
    def add_drive(self, drive_letter: str, drive_label: str = "") -> DriveListItem:
        """Fügt ein neues Laufwerk zur Liste hinzu."""
        if drive_letter not in self.drive_items:
            item = DriveListItem(drive_letter, drive_label)
            self.addItem(item)
            self.drive_items[drive_letter] = item
            return item
        return self.drive_items[drive_letter]
        
    def remove_drive(self, drive_letter: str):
        """Entfernt ein Laufwerk aus der Liste."""
        if drive_letter in self.drive_items:
            item = self.drive_items.pop(drive_letter)
            row = self.row(item)
            if row >= 0:
                self.takeItem(row)
                
    def get_drive_letters(self) -> list:
        """Gibt eine Liste aller Laufwerksbuchstaben zurück."""
        return list(self.drive_items.keys())
        
    def get_selected_drives(self) -> list:
        """Gibt eine Liste der ausgewählten Laufwerksbuchstaben zurück."""
        return [item.drive_letter for item in self.selectedItems() if isinstance(item, DriveListItem)]
        
    def clear(self):
        """Leert die Liste und das Dictionary."""
        super().clear()
        self.drive_items.clear()
        
    def resizeEvent(self, event):
        """Behandelt die Größenänderung der Liste."""
        super().resizeEvent(event)
        for i in range(self.count()):
            item = self.item(i)
            if isinstance(item, DriveListItem):
                item.setSizeHint(QSize(self.viewport().width(), 35))  # Update size hint
                
    def _update_height(self):
        """Aktualisiert die Höhe der Liste basierend auf der Anzahl der Items."""
        total_height = self.count() * 36 + 10  # 35px pro Item + 1px spacing + 10px Padding
        self.setFixedHeight(total_height)
