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
import time

class DriveProgress(QWidget):
    """Widget zur Anzeige des Fortschritts für ein einzelnes Laufwerk."""
    
    def __init__(self, drive_letter: str, drive_name: str, parent=None):
        super().__init__(parent)
        self.drive_letter = drive_letter
        self.drive_name = drive_name
        self._current_progress = 0
        self._current_speed = 0
        self._last_update = 0
        self._update_interval = 0.1  # 100ms minimales Update-Intervall
        self._setup_ui()
        
    def _setup_ui(self):
        """Erstellt das UI für das Widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 2, 3, 2)  # Etwas mehr horizontal
        layout.setSpacing(3)  # Mehr Zeilenabstand
        
        # Frame für besseres Aussehen
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        frame.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
            }
        """)
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(8, 4, 8, 4)  # Mehr Innenabstand
        frame_layout.setSpacing(3)  # Mehr Abstand zwischen Elementen
        
        # Obere Zeile: Laufwerk, Datei und Status
        top_row = QHBoxLayout()
        top_row.setSpacing(6)  # Mehr Abstand zwischen Elementen
        
        # Laufwerksicon und Name
        drive_layout = QHBoxLayout()
        drive_layout.setSpacing(4)
        
        drive_icon = QLabel("💾")
        drive_icon.setStyleSheet("font-size: 12px;")  # Größeres Icon
        drive_layout.addWidget(drive_icon)
        
        self.name_label = QLabel(self.drive_name)
        self.name_label.setStyleSheet("font-weight: bold; color: #ffffff; font-size: 11px;")
        drive_layout.addWidget(self.name_label)
        
        top_row.addLayout(drive_layout)
        
        # Dateiname
        self.file_label = QLabel()
        self.file_label.setStyleSheet("color: #aaaaaa; font-size: 11px;")  # Größere Schrift
        top_row.addWidget(self.file_label, stretch=1)
        
        # Größe und Geschwindigkeit
        info_layout = QHBoxLayout()
        info_layout.setSpacing(8)  # Mehr Abstand
        
        self.size_label = QLabel()
        self.size_label.setStyleSheet("color: #aaaaaa; font-size: 11px;")  # Größere Schrift
        self.size_label.setAlignment(Qt.AlignRight)
        info_layout.addWidget(self.size_label)
        
        self.speed_label = QLabel()
        self.speed_label.setStyleSheet("color: #aaaaaa; font-size: 11px;")  # Größere Schrift
        self.speed_label.setAlignment(Qt.AlignRight)
        info_layout.addWidget(self.speed_label)
        
        top_row.addLayout(info_layout)
        frame_layout.addLayout(top_row)
        
        # Untere Zeile: Fortschritt und ETA
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)
        
        # Fortschrittsbalken
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setFixedHeight(16)  # Höherer Fortschrittsbalken
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #555555;
                border-radius: 2px;
                background-color: #1e1e1e;
                color: white;
                text-align: center;
                font-size: 11px;
                margin: 0px;
                padding: 0px;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 1px;
            }
        """)
        bottom_row.addWidget(self.progress_bar, stretch=1)
        
        # ETA
        self.eta_label = QLabel()
        self.eta_label.setStyleSheet("color: #aaaaaa; font-size: 11px;")  # Größere Schrift
        self.eta_label.setAlignment(Qt.AlignRight)
        self.eta_label.setFixedWidth(90)  # Etwas mehr Platz für ETA
        bottom_row.addWidget(self.eta_label)
        
        frame_layout.addLayout(bottom_row)
        layout.addWidget(frame)
        
        # Setze maximale Höhe für das gesamte Widget
        self.setMaximumHeight(52)  # Etwas mehr Höhe
        
    def update_progress(self, filename: str, progress: float, speed: float):
        """Aktualisiert den Fortschritt."""
        try:
            # Rate-Limiting für Updates
            current_time = time.time()
            if current_time - self._last_update < self._update_interval:
                return
            
            # Speichere aktuelle Werte
            self._current_progress = progress
            self._current_speed = speed
            self._last_update = current_time
            
            # Aktualisiere UI
            # Kürze Dateinamen wenn zu lang
            max_length = 40
            if len(filename) > max_length:
                display_name = filename[:max_length-3] + "..."
            else:
                display_name = filename
            self.file_label.setText(display_name)
            
            # Aktualisiere Fortschrittsbalken
            self.progress_bar.setValue(int(progress))
            
            # Formatiere Geschwindigkeit (speed ist bereits in MB/s)
            if speed > 0:
                speed_text = f"🚀 {speed:.1f} MB/s"
            else:
                speed_text = "🚀 0 B/s"
            self.speed_label.setText(speed_text)
            
            # Berechne und zeige ETA
            if speed > 0 and progress < 100:
                remaining_percent = 100 - progress
                # Geschwindigkeit ist in MB/s, also multipliziere mit 1.024 für genauere Zeit
                remaining_time = (remaining_percent / speed) * 1.024
                
                if remaining_time < 60:
                    eta_text = f"⏱️ {int(remaining_time)}s"
                elif remaining_time < 3600:
                    eta_text = f"⏱️ {int(remaining_time/60)}min"
                else:
                    eta_text = f"⏱️ {remaining_time/3600:.1f}h"
            else:
                if progress >= 100:
                    eta_text = "⏱️ Fertig"
                else:
                    eta_text = "⏱️ Berechne..."
            self.eta_label.setText(eta_text)
            
        except Exception as e:
            logging.error(f"Fehler beim Aktualisieren des Fortschritts: {e}")


class ProgressWidget(QWidget):
    """Widget zur Anzeige des Gesamtfortschritts."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.drive_widgets = {}
        self.total_bytes = {}  
        self.transferred_bytes = {}  
        self.active_transfers = set()
        self._last_update = {}  # Zeitstempel des letzten Updates pro Laufwerk
        self._update_interval = 0.1  # Minimales Update-Intervall in Sekunden
        
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
        self.total_progress_bar = QProgressBar()
        self.total_progress_bar.setRange(0, 100)
        self.total_progress_bar.setValue(0)
        self.total_progress_bar.setStyleSheet("""
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
        header_layout.addWidget(self.total_progress_bar)
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
                    self.total_progress_bar.setValue(0)
                
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
            # Prüfe Update-Intervall
            current_time = time.time()
            if drive_letter in self._last_update:
                if current_time - self._last_update[drive_letter] < self._update_interval:
                    return  # Zu früh für ein Update
            
            # Aktualisiere Zeitstempel
            self._last_update[drive_letter] = current_time
            
            # Aktualisiere Bytes-Zähler
            if total_size is not None:
                self.total_bytes[drive_letter] = total_size
            if transferred is not None:
                self.transferred_bytes[drive_letter] = transferred
            
            # Hole oder erstelle Drive-Widget
            if drive_letter not in self.drive_widgets:
                self.add_drive(drive_letter)
            drive_widget = self.drive_widgets[drive_letter]
            
            # Aktualisiere aktive Transfers
            if progress < 100:
                self.active_transfers.add(drive_letter)
            else:
                self.active_transfers.discard(drive_letter)
            
            # Aktualisiere Drive-Widget
            drive_widget.update_progress(filename, progress, speed)
            
            # Aktualisiere Gesamtfortschritt
            self._update_total_progress()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren des Fortschritts: {e}")
            
    def _update_total_progress(self):
        """Aktualisiert den Gesamtfortschritt."""
        try:
            total_transferred = sum(self.transferred_bytes.values())
            total_size = sum(self.total_bytes.values())
            
            if total_size > 0:
                total_progress = (total_transferred / total_size) * 100
            else:
                total_progress = 0
                
            # Aktualisiere Gesamtfortschrittsanzeige
            if hasattr(self, 'total_progress_bar'):
                self.total_progress_bar.setValue(int(total_progress))
                
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren des Gesamtfortschritts: {e}")
