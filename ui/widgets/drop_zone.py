#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""DropZone-Widget für Drag & Drop Dateitransfers."""

import os
import logging
from PyQt5.QtWidgets import QLabel, QMessageBox, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDragEnterEvent, QDropEvent

logger = logging.getLogger(__name__)

class DropZone(QLabel):
    """Eine Drop-Zone für Dateien."""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._setup_ui()
        
    def _setup_ui(self):
        """Initialisiert die UI-Komponenten."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Label für Drag & Drop Hinweis
        self.label = QLabel("📥 Dateien hier ablegen\noder klicken zum Auswählen")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setStyleSheet("""
            QLabel {
                color: #9CA3AF;
                font-size: 14px;
                border: 2px dashed #4B5563;
                border-radius: 8px;
                padding: 20px;
                background: #2D2D2D;
            }
        """)
        layout.addWidget(self.label)
        self.setAcceptDrops(True)
        self.setMinimumHeight(100)
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Wird aufgerufen, wenn ein Drag über die Zone beginnt."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.label.setStyleSheet("""
                QLabel {
                    background-color: #353535;
                    border: 2px dashed #606060;
                    border-radius: 5px;
                    padding: 20px;
                    color: #a0a0a0;
                }
            """)
            
    def dragLeaveEvent(self, event):
        """Wird aufgerufen, wenn ein Drag die Zone verlässt."""
        self._setup_ui()
        
    def dropEvent(self, event: QDropEvent):
        """Wird aufgerufen, wenn Dateien gedroppt werden."""
        try:
            urls = event.mimeData().urls()
            files = []
            
            # Sammle alle Dateien
            for url in urls:
                file_path = url.toLocalFile()
                if os.path.isfile(file_path):
                    files.append(file_path)
            
            if not files:
                return
                
            # Übergebe die Dateien an die bestehende Funktion
            self.main_window.start_copy_for_files(files)
            
            # Setze die UI zurück
            self._setup_ui()
            
        except Exception as e:
            logger.error(f"Fehler beim Verarbeiten der gedropten Dateien: {str(e)}")
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler beim Verarbeiten der Dateien:\n{str(e)}",
                QMessageBox.Ok
            )
