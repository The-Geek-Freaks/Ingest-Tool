#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Widget zur Anzeige des Kopierfortschritts."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QProgressBar, QScrollArea,
    QFrame
)
from PyQt5.QtCore import Qt
import logging

class DriveProgress(QWidget):
    """Widget zur Anzeige des Fortschritts für ein einzelnes Laufwerk."""
    
    def __init__(self, drive_letter: str, drive_name: str, parent=None):
        super().__init__(parent)
        self.drive_letter = drive_letter
        self.drive_name = drive_name
        self._setup_ui()
        
    def _setup_ui(self):
        """Erstellt das UI für das Widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Obere Zeile mit Laufwerksname und Geschwindigkeit
        top_row = QHBoxLayout()
        
        # Laufwerksname
        self.name_label = QLabel(self.drive_name)
        self.name_label.setStyleSheet("font-weight: bold;")
        top_row.addWidget(self.name_label)
        
        # Geschwindigkeit (rechtsbündig)
        self.speed_label = QLabel()
        self.speed_label.setAlignment(Qt.AlignRight)
        self.speed_label.setMinimumWidth(120)  # Fixed width for speed
        top_row.addWidget(self.speed_label)
        
        layout.addLayout(top_row)
        
        # Untere Zeile mit Fortschrittsbalken und Dateiname
        bottom_row = QHBoxLayout()
        
        # Fortschrittsbalken
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        bottom_row.addWidget(self.progress_bar, stretch=1)
        
        layout.addLayout(bottom_row)
        
        # Dateiname
        self.file_label = QLabel()
        self.file_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.file_label)
        
    def update_progress(self, filename: str, progress: float, speed: float):
        """Aktualisiert den Fortschritt."""
        try:
            # Update progress bar
            self.progress_bar.setValue(int(progress))
            
            # Format speed for display
            if speed >= 1024:  # More than 1024 MB/s
                speed_text = f"{speed/1024:.1f} GB/s"
            else:
                speed_text = f"{speed:.1f} MB/s"
            self.speed_label.setText(speed_text)
            
            # Update filename (truncate if too long)
            max_length = 50
            if len(filename) > max_length:
                display_name = filename[:max_length-3] + "..."
            else:
                display_name = filename
            self.file_label.setText(display_name)
            
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren des Fortschritts: {e}")


class ProgressWidget(QWidget):
    """Widget zur Anzeige des Gesamtfortschritts."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.drive_widgets = {}
        self.total_bytes = {}  # Track total bytes for each drive
        self.transferred_bytes = {}  # Track transferred bytes for each drive
        self.active_transfers = set()  # Track active transfers
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Erstellt die UI-Komponenten."""
        # Hauptlayout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Titel und Gesamtfortschritt
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(5)
        
        # Titel
        title = QLabel("Kopierfortschritt")
        title.setStyleSheet("""
            QLabel {
                color: #E5E7EB;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        header_layout.addWidget(title)
        
        # Gesamtfortschritt
        self.total_progress = QProgressBar()
        self.total_progress.setRange(0, 100)
        self.total_progress.setValue(0)
        self.total_progress.setStyleSheet("""
            QProgressBar {
                background-color: #374151;
                border: 1px solid #4B5563;
                border-radius: 4px;
                text-align: center;
                color: white;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #4B5563;
                border-radius: 3px;
            }
        """)
        header_layout.addWidget(self.total_progress)
        main_layout.addWidget(header_widget)
        
        # Container für die Laufwerke
        self.drives_container = QWidget()
        self.drives_layout = QVBoxLayout(self.drives_container)
        self.drives_layout.setContentsMargins(0, 0, 0, 0)
        self.drives_layout.setSpacing(10)
        
        # Platzhalter-Text
        self.placeholder_label = QLabel("Keine aktiven Kopiervorgänge")
        self.placeholder_label.setStyleSheet("""
            QLabel {
                color: #9CA3AF;
                font-style: italic;
                padding: 20px;
            }
        """)
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.drives_layout.addWidget(self.placeholder_label)
        
        # Scroll-Bereich
        scroll = QScrollArea()
        scroll.setWidget(self.drives_container)
        scroll.setWidgetResizable(True)
        scroll.setFrameStyle(QFrame.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #2D2D2D;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #4B5563;
                border-radius: 6px;
                min-height: 20px;
                margin: 2px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        # Container Styling
        self.drives_container.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
            QProgressBar {
                background-color: #374151;
                border: 1px solid #4B5563;
                border-radius: 4px;
                text-align: center;
                color: white;
                height: 16px;
            }
            QProgressBar::chunk {
                background-color: #4B5563;
                border-radius: 3px;
            }
            QLabel {
                color: #E5E7EB;
            }
        """)
        
        main_layout.addWidget(scroll)
        
    def add_drive(self, drive_letter: str, drive_name: str = None):
        """Fügt ein neues Laufwerk hinzu."""
        try:
            if drive_letter not in self.drive_widgets:
                # Platzhalter ausblenden beim ersten Laufwerk
                if len(self.drive_widgets) == 0:
                    self.placeholder_label.hide()
                
                # Neues DriveProgress Widget erstellen
                drive_widget = DriveProgress(drive_letter, drive_name, self)
                self.drives_layout.insertWidget(self.drives_layout.count() - 1, drive_widget)
                self.drive_widgets[drive_letter] = drive_widget
                
        except Exception as e:
            self.logger.error(f"Fehler beim Hinzufügen des Laufwerks: {str(e)}")
            
    def remove_drive(self, drive_letter: str):
        """Entfernt ein Laufwerk."""
        try:
            if drive_letter in self.drive_widgets:
                # Widget entfernen
                widget = self.drive_widgets.pop(drive_letter)
                self.drives_layout.removeWidget(widget)
                widget.deleteLater()
                
                # Tracking-Daten entfernen
                self.total_bytes.pop(drive_letter, None)
                self.transferred_bytes.pop(drive_letter, None)
                
                # Platzhalter anzeigen wenn keine Laufwerke mehr
                if len(self.drive_widgets) == 0:
                    self.placeholder_label.show()
                    self.total_progress.setValue(0)
                
        except Exception as e:
            self.logger.error(f"Fehler beim Entfernen des Laufwerks: {str(e)}")
            
    def update_drive_progress(self, drive_letter: str, filename: str,
                            progress: float, speed: float, total_size: int = None,
                            transferred: int = None):
        """Aktualisiert den Fortschritt eines Laufwerks.
        
        Args:
            drive_letter: Buchstabe des Laufwerks
            filename: Name der aktuellen Datei
            progress: Fortschritt in Prozent (0-100)
            speed: Kopiergeschwindigkeit in MB/s
            total_size: Gesamtgröße der zu übertragenden Dateien in Bytes
            transferred: Bereits übertragene Bytes
        """
        try:
            if drive_letter in self.drive_widgets:
                # Update drive widget
                self.drive_widgets[drive_letter].update_progress(
                    filename, progress, speed
                )
                
                # Update byte tracking if provided
                if total_size is not None:
                    self.total_bytes[drive_letter] = total_size
                if transferred is not None:
                    self.transferred_bytes[drive_letter] = transferred
                
                # Calculate total progress
                total_bytes_sum = sum(self.total_bytes.values())
                if total_bytes_sum > 0:
                    transferred_bytes_sum = sum(self.transferred_bytes.values())
                    total_progress = (transferred_bytes_sum / total_bytes_sum) * 100
                    self.total_progress.setValue(int(total_progress))
                
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren des Laufwerks: {str(e)}")
