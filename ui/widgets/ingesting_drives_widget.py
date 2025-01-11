#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, 
                            QProgressBar, QHBoxLayout, QFrame, QScrollArea, QGroupBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QColor

logger = logging.getLogger(__name__)

class IngestingDriveItem(QListWidgetItem):
    """Ein Listenelement für ein ingestierendes Laufwerk."""
    
    def __init__(self, drive_letter: str, drive_name: str = ""):
        super().__init__()
        self.drive_letter = drive_letter
        self.drive_name = drive_name
        self.current_file = ""
        self.transfer_speed = 0
        self.total_size = 0
        self.processed_size = 0
        self.progress = 0
        
        # Widget für das Item erstellen
        self.widget = QWidget()
        layout = QHBoxLayout(self.widget)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(12)
        
        # Linke Spalte: Laufwerksinfo
        drive_info = QWidget()
        drive_layout = QVBoxLayout(drive_info)
        drive_layout.setContentsMargins(0, 0, 0, 0)
        drive_layout.setSpacing(2)
        
        # Laufwerksname
        self.name_label = QLabel(f"{drive_letter}")
        if drive_name:
            self.name_label.setText(f"{drive_letter} ({drive_name})")
        self.name_label.setStyleSheet("font-weight: bold;")
        drive_layout.addWidget(self.name_label)
        
        # Aktueller Dateiname
        self.file_label = QLabel()
        self.file_label.setStyleSheet("color: #64748B; font-size: 11px;")
        drive_layout.addWidget(self.file_label)
        
        layout.addWidget(drive_info, stretch=2)
        
        # Mittlere Spalte: Transfer-Info
        transfer_info = QWidget()
        transfer_layout = QVBoxLayout(transfer_info)
        transfer_layout.setContentsMargins(0, 0, 0, 0)
        transfer_layout.setSpacing(2)
        
        # Geschwindigkeit
        self.speed_label = QLabel()
        self.speed_label.setStyleSheet("color: #64748B;")
        transfer_layout.addWidget(self.speed_label)
        
        # Größe
        self.size_label = QLabel()
        self.size_label.setStyleSheet("color: #64748B; font-size: 11px;")
        transfer_layout.addWidget(self.size_label)
        
        layout.addWidget(transfer_info, stretch=1)
        
        # Rechte Spalte: Fortschritt
        progress_container = QWidget()
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(4)
        
        # Prozent-Label
        self.percent_label = QLabel("0%")
        self.percent_label.setAlignment(Qt.AlignRight)
        self.percent_label.setStyleSheet("color: #64748B;")
        progress_layout.addWidget(self.percent_label)
        
        # Fortschrittsbalken
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #E2E8F0;
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #3B82F6;
                border-radius: 2px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(progress_container, stretch=1)
        
        # Setze die Größe des Items
        self.setSizeHint(self.widget.sizeHint())
        
    def update_transfer_progress(self, speed: float, total_size: int, processed_size: int, progress: float):
        """Aktualisiert die Transfer-Informationen."""
        self.transfer_speed = speed
        self.total_size = total_size
        self.processed_size = processed_size
        self.progress = progress
        
        # Aktualisiere Speed
        if speed < 1024:
            speed_text = f"{speed:.1f} KB/s"
        elif speed < 1024*1024:
            speed_text = f"{speed/1024:.1f} MB/s"
        else:
            speed_text = f"{speed/1024/1024:.1f} GB/s"
        self.speed_label.setText(speed_text)
        
        # Aktualisiere Größe
        if total_size < 1024*1024*1024:
            size_text = f"{processed_size/1024/1024:.1f}/{total_size/1024/1024:.1f} MB"
        else:
            size_text = f"{processed_size/1024/1024/1024:.1f}/{total_size/1024/1024/1024:.1f} GB"
        self.size_label.setText(size_text)
        
        # Aktualisiere Fortschritt
        self.progress_bar.setValue(int(progress * 100))
        self.percent_label.setText(f"{int(progress * 100)}%")
        
    def update_current_file(self, filename: str):
        """Aktualisiert den Namen der aktuellen Datei."""
        if filename:
            self.current_file = filename
            self.file_label.setText(os.path.basename(filename))
        else:
            self.current_file = ""
            self.file_label.setText("")
            
    def update_progress(self, speed: int, total_size: int, processed_size: int, progress: float, current_file: str):
        self.update_transfer_progress(speed, total_size, processed_size, progress)
        self.update_current_file(current_file)


class IngestingDrivesWidget(QWidget):
    """Widget zur Anzeige der ingestierenden Laufwerke."""
    
    # Signale für Thread-sichere Updates
    drive_added = pyqtSignal(str, str)  # drive_letter, drive_name
    drive_removed = pyqtSignal(str)  # drive_letter
    drive_progress_updated = pyqtSignal(str, float, int, int, float, str)  # drive_letter, speed, total_size, processed_size, progress, current_file
    drive_cleared = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.drive_items = {}
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """Initialisiert die UI-Komponenten."""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Scrollbereich für Laufwerke
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Container für Laufwerke
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(0)
        self.scroll_layout.addStretch()
        
        self.scroll_area.setWidget(self.scroll_widget)
        self.layout.addWidget(self.scroll_area)
        
        # Laufwerks-Gruppe
        drives_group = QGroupBox("💾 Verfügbare Laufwerke")
        drives_group.setMinimumWidth(250)  # Minimale Breite festlegen
        self.layout.addWidget(drives_group)
        
    def _connect_signals(self):
        """Verbindet die Signale mit den Slots."""
        # Verwende Qt.QueuedConnection für Thread-sichere Updates
        self.drive_added.connect(self._add_drive_internal, Qt.QueuedConnection)
        self.drive_removed.connect(self._remove_drive_internal, Qt.QueuedConnection)
        self.drive_progress_updated.connect(self._update_drive_progress_internal, Qt.QueuedConnection)
        self.drive_cleared.connect(self._clear_internal, Qt.QueuedConnection)
        
    def add_drive(self, drive_letter: str, drive_name: str):
        """Fügt ein Laufwerk hinzu (Thread-sicher)."""
        self.drive_added.emit(drive_letter, drive_name)
        
    def _add_drive_internal(self, drive_letter: str, drive_name: str):
        """Interner Slot zum Hinzufügen eines Laufwerks."""
        if drive_letter not in self.drive_items:
            drive_item = IngestingDriveItem(drive_letter, drive_name)
            self.drive_items[drive_letter] = drive_item
            self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, drive_item.widget)
            
    def remove_drive(self, drive_letter: str):
        """Entfernt ein Laufwerk (Thread-sicher)."""
        self.drive_removed.emit(drive_letter)
        
    def _remove_drive_internal(self, drive_letter: str):
        """Interner Slot zum Entfernen eines Laufwerks."""
        if drive_letter in self.drive_items:
            drive_item = self.drive_items.pop(drive_letter)
            self.scroll_layout.removeWidget(drive_item.widget)
            drive_item.widget.deleteLater()
            
    def update_drive_progress(self, drive_letter: str, speed: int, total_size: int,
                            processed_size: int, progress: float, current_file: str):
        """Aktualisiert den Fortschritt eines Laufwerks (Thread-sicher)."""
        self.drive_progress_updated.emit(drive_letter, speed, total_size,
                                       processed_size, progress, current_file)
        
    def _update_drive_progress_internal(self, drive_letter: str, speed: int,
                                      total_size: int, processed_size: int,
                                      progress: float, current_file: str):
        """Interner Slot zum Aktualisieren des Fortschritts."""
        if drive_letter in self.drive_items:
            self.drive_items[drive_letter].update_progress(
                speed, total_size, processed_size, progress, current_file
            )
            
    def clear(self):
        """Entfernt alle Laufwerke (Thread-sicher)."""
        self.drive_cleared.emit()
        
    def _clear_internal(self):
        """Interner Slot zum Entfernen aller Laufwerke."""
        for drive_letter in list(self.drive_items.keys()):
            self._remove_drive_internal(drive_letter)
