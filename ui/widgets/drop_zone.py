#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""DropZone-Widget für Drag & Drop Dateitransfers."""

import os
import logging
from PyQt5.QtWidgets import QLabel, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDragEnterEvent, QDropEvent

logger = logging.getLogger(__name__)

class DropZone(QLabel):
    """Eine Drop-Zone für Dateien."""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()
        
    def setup_ui(self):
        """Initialisiert die UI."""
        self.setAlignment(Qt.AlignCenter)
        self.setText("📥 " + self.main_window.i18n.get("ui.drop_files"))
        self.setStyleSheet("""
            QLabel {
                background-color: #2d2d2d;
                border: 2px dashed #404040;
                border-radius: 5px;
                padding: 20px;
                color: #808080;
                font-size: 14px;
            }
            QLabel:hover {
                background-color: #353535;
                border-color: #505050;
            }
        """)
        self.setAcceptDrops(True)
        self.setMinimumHeight(100)
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Wird aufgerufen, wenn ein Drag über die Zone beginnt."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
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
        self.setup_ui()
        
    def dropEvent(self, event: QDropEvent):
        """Wird aufgerufen, wenn Dateien gedroppt werden."""
        try:
            urls = event.mimeData().urls()
            files = []
            file_types = set()
            
            # Sammle alle Dateien und ihre Typen
            for url in urls:
                file_path = url.toLocalFile()
                if os.path.isfile(file_path):
                    files.append(file_path)
                    _, ext = os.path.splitext(file_path)
                    if ext:
                        file_types.add(ext[1:].lower())  # Entferne den Punkt und konvertiere zu Kleinbuchstaben
            
            if not files:
                return
                
            # Prüfe für jeden Dateityp, ob eine Zuordnung existiert
            missing_types = []
            for file_type in file_types:
                if not self.main_window.get_mapping_for_type(file_type):
                    missing_types.append(file_type)
            
            if missing_types:
                # Zeige Warnung für fehlende Zuordnungen
                msg = self.main_window.i18n.get("ui.missing_mappings").format(
                    types=", ".join(missing_types)
                )
                QMessageBox.warning(
                    self,
                    self.main_window.i18n.get("ui.warning"),
                    msg,
                    QMessageBox.Ok
                )
                return
            
            # Starte den Kopiervorgang für alle Dateien
            self.main_window.start_copy_for_files(files)
            
        except Exception as e:
            logger.error(f"Fehler beim Verarbeiten der gedropten Dateien: {e}")
            QMessageBox.critical(
                self,
                self.main_window.i18n.get("ui.error"),
                str(e),
                QMessageBox.Ok
            )
        finally:
            self.setup_ui()
