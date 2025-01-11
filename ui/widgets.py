#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QListWidgetItem, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QProgressBar, QListWidget,
    QSpacerItem, QSizePolicy, QFrame
)
from PyQt5.QtGui import QColor, QFont, QIcon, QPainter, QPen
from PyQt5.QtCore import Qt, QSize
from utils.helpers import format_size, get_drive_space
from .style_helper import StyleHelper

class ZuordnungsListItem(QListWidgetItem):
    """Erweitertes ListWidgetItem für Datei-Zuordnungen mit Speicherplatzanzeige."""
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.update_space()

    def update_space(self):
        """Aktualisiert die Speicherplatzanzeige."""
        try:
            # Extrahiere Zielordner aus dem Text
            ziel_ordner = self.text().split(" -> ")[1]
            free_space = get_drive_space(ziel_ordner)

            if free_space is not None:
                formatted_space = format_size(free_space)
                self.setText(f"{self.text()} [Frei: {formatted_space}]")

                # Setze Farbe basierend auf verfügbarem Speicher
                if free_space < 1024 * 1024 * 1024:  # Weniger als 1 GB
                    self.setForeground(QColor("#f44336"))  # Rot
                elif free_space < 10 * 1024 * 1024 * 1024:  # Weniger als 10 GB
                    self.setForeground(QColor("#ff9800"))  # Orange
                else:
                    self.setForeground(QColor("#4caf50"))  # Grün
        except Exception:
            pass

class TransferWidget(QWidget):
    """Widget zur Anzeige eines aktiven Transfers."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        StyleHelper.apply_dark_theme(self)

    def init_ui(self):
        """Initialisiert die UI-Komponenten."""
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)

        # Obere Zeile mit Dateinamen und Status
        top_layout = QHBoxLayout()
        self.file_label = QLabel()
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignRight)
        top_layout.addWidget(self.file_label)
        top_layout.addWidget(self.status_label)
        layout.addLayout(top_layout)

        # Fortschrittsbalken
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% - %v / %m MB")
        StyleHelper.style_progress_bar(self.progress_bar)
        layout.addWidget(self.progress_bar)

    def update_transfer(self, datei: str, status: str, fortschritt: float, groesse: int):
        """Aktualisiert die Anzeige des Transfers.
        
        Args:
            datei: Dateiname
            status: Aktueller Status
            fortschritt: Fortschritt in Prozent
            groesse: Dateigröße in Bytes
        """
        self.file_label.setText(datei)
        self.status_label.setText(status)
        self.progress_bar.setValue(int(fortschritt))
        
        # Setze Maximum in MB
        max_mb = groesse / (1024 * 1024)
        current_mb = (groesse * fortschritt / 100) / (1024 * 1024)
        self.progress_bar.setMaximum(int(max_mb))
        self.progress_bar.setValue(int(current_mb))

class DriveWidget(QWidget):
    """Widget zur Anzeige eines Laufwerks."""
    
    def __init__(self, laufwerk: str, parent=None):
        super().__init__(parent)
        self.laufwerk = laufwerk
        self.init_ui()
        StyleHelper.apply_dark_theme(self)

    def init_ui(self):
        """Initialisiert die UI-Komponenten."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(32, 32)
        layout.addWidget(self.icon_label)
        
        # Info Layout
        info_layout = QVBoxLayout()
        
        # Laufwerksname
        self.name_label = QLabel(self.laufwerk)
        font = QFont()
        font.setBold(True)
        self.name_label.setFont(font)
        info_layout.addWidget(self.name_label)
        
        # Status und Fortschritt
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Bereit")
        status_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(100)
        StyleHelper.style_progress_bar(self.progress_bar)
        status_layout.addWidget(self.progress_bar)
        
        info_layout.addLayout(status_layout)
        layout.addLayout(info_layout)
        
        # Spacer
        layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )

    def update_status(self, status: str, progress: int = 0):
        """Aktualisiert den Status und Fortschritt."""
        self.status_label.setText(status)
        self.progress_bar.setValue(progress)

class ZuordnungsListWidget(QWidget):
    """Widget für die Anzeige einer Zuordnungsliste."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        StyleHelper.apply_dark_theme(self)

    def init_ui(self):
        """Initialisiert die UI-Komponenten."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Liste
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

class StyleHelper:
    """Hilfsklasse für einheitliches Styling der UI-Komponenten."""
    
    @staticmethod
    def style_button(button: QPushButton):
        """Wendet einheitliches Styling auf einen Button an."""
        button.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 4px;
                color: white;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
            QPushButton:pressed {
                background-color: #1d1d1d;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #808080;
                border-color: #404040;
            }
        """)

    @staticmethod
    def style_progress_bar(progress_bar: QProgressBar):
        """Wendet einheitliches Styling auf eine Fortschrittsanzeige an."""
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #404040;
                border-radius: 4px;
                text-align: center;
                background-color: #2d2d2d;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
            }
        """)

    @staticmethod
    def style_list_widget(list_widget: QListWidget):
        """Wendet einheitliches Styling auf eine ListWidget an."""
        list_widget.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 4px;
                color: #ffffff;
            }
            QListWidget::item {
                padding: 4px;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #333333;
            }
            QListWidget::item:alternate {
                background-color: #262626;
            }
        """)

    @staticmethod
    def apply_dark_theme(widget: QWidget):
        """Wendet einheitliches dunkles Design auf ein Widget an."""
        widget.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
        """)
