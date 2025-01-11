#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
from PyQt5.QtWidgets import QListWidgetItem, QLabel, QWidget, QHBoxLayout, QSizePolicy, QFrame
from PyQt5.QtCore import QTimer, Qt, QPropertyAnimation, QRect, QThread
from PyQt5.QtGui import QPixmap, QPalette, QColor

logger = logging.getLogger(__name__)

# Status Icons mit Animation für Kopieren
ICON_READY = "🔵"        # Bereit für Transfer
ICON_COPYING = ["⬇️", "↙️", "⬅️", "↖️", "⬆️", "↗️", "➡️", "↘️"]  # Animation beim Kopieren
ICON_FAILED = "❌"       # Transfer fehlgeschlagen
ICON_ERROR = "⚠️"        # Fehler aufgetreten
ICON_DONE = "✅"         # Transfer abgeschlossen
ICON_EXCLUDED = "🚫"     # Ausgeschlossen
ICON_MAPPED = "🔗"       # Zugeordnet

# Status Farben
STATUS_COLORS = {
    "ready": "#4CAF50",      # Grün
    "copying": "#2196F3",    # Blau
    "failed": "#F44336",     # Rot
    "error": "#FF9800",      # Orange
    "done": "#4CAF50",       # Grün
    "excluded": "#9E9E9E",   # Grau
    "mapped": "#9C27B0"      # Lila
}

# Farben für Laufwerkstypen
DRIVE_TYPE_COLORS = {
    "removable": "#8B5CF6",  # Lila für Wechseldatenträger
    "local": "#4B5563",      # Dunkelgrau für lokale Laufwerke
    "remote": "#14B8A6"      # Türkis für Netzwerklaufwerke
}

class StatusLabel(QLabel):
    """Ein Label mit Hintergrundfarbe für Status-Anzeigen."""
    def __init__(self, text="", color="#4CAF50"):
        super().__init__(text)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                border-radius: 4px;
                padding: 2px 8px;
                margin: 2px;
            }}
        """)
        self.setMinimumHeight(24)

class DriveListItem(QListWidgetItem):
    """Ein Listenelement für ein verbundenes Laufwerk."""
    
    def __init__(self, drive_letter: str, drive_name: str = "", drive_type: str = "local"):
        """Initialisiert das DriveListItem.
        
        Args:
            drive_letter: Laufwerksbuchstabe (z.B. "D:")
            drive_name: Optionale Bezeichnung des Laufwerks
            drive_type: Typ des Laufwerks ("removable", "local", "remote")
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self._current_thread = None
        self.drive_letter = drive_letter
        self.drive_name = drive_name
        self.drive_type = drive_type
        self.status = "ready"
        self.current_file = ""
        self.is_excluded = False
        self.is_mapped = False
        
        # Debug-Ausgabe für Laufwerksnamen
        logger.debug(f"DriveListItem erstellt - Buchstabe: {drive_letter}, Name: {drive_name}, Typ: {drive_type}")
        
        # Entferne den vertikalen Strich durch Setzen der Textausrichtung
        self.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        self.animation_index = 0
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._update_animation)
        self.animation_timer.setInterval(100)  # 100ms zwischen Frames für flüssigere Animation
        
        self._setup_ui()
        
    def _setup_ui(self):
        try:
            self._current_thread = QThread.currentThread()
            self.logger.debug(f"DriveListItem._setup_ui() aufgerufen in Thread: {self._current_thread}")
            
            # Erstelle Widget für das Item
            self.widget = QWidget()
            layout = QHBoxLayout(self.widget)
            layout.setContentsMargins(6, 2, 10, 2)
            layout.setSpacing(10)
            
            # Status-Icon (links)
            self.status_label = QLabel(ICON_READY)
            self.status_label.setFixedWidth(30)
            layout.addWidget(self.status_label)
            
            # Container für Laufwerksname mit Hintergrundfarbe
            self.drive_container = QWidget()
            self.drive_container.setStyleSheet(f"""
                QWidget {{
                    background-color: {DRIVE_TYPE_COLORS.get(self.drive_type, DRIVE_TYPE_COLORS["local"])};
                    border-radius: 4px;
                    padding: 2px 8px;
                    margin: 2px;
                }}
            """)
            container_layout = QHBoxLayout(self.drive_container)
            container_layout.setContentsMargins(8, 2, 8, 2)
            container_layout.setSpacing(0)
            
            # Laufwerksname (Mitte)
            self.drive_label = QLabel()
            self.drive_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
            self.drive_label.setMinimumWidth(150)  # Mindestbreite für Laufwerksnamen
            self.drive_label.setStyleSheet("""
                QLabel {
                    color: white;
                    font-weight: bold;
                }
            """)
            container_layout.addWidget(self.drive_label)
            
            layout.addWidget(self.drive_container)
            
            # Status-Text (rechts)
            self.status_text = StatusLabel()
            layout.addWidget(self.status_text)
            
            # Aktualisiere die Anzeige
            self._update_display()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen des DriveListItems: {e}", exc_info=True)
        
    def _update_animation(self):
        """Aktualisiert den Animationsframe."""
        if self.status == "copying":
            self.animation_index = (self.animation_index + 1) % len(ICON_COPYING)
            self._update_display()
            
    def _update_display(self):
        """Aktualisiert die Anzeige des Items."""
        try:
            # Laufwerksname
            display_name = f"{self.drive_letter}"
            if hasattr(self, 'drive_name') and self.drive_name and len(self.drive_name.strip()) > 0:
                display_name += f" ({self.drive_name})"
            self.drive_label.setText(display_name)
            
            # Setze Status-Icon
            if self.status == "copying":
                if not self.animation_timer.isActive():
                    self.animation_timer.start()
                self.status_label.setText(ICON_COPYING[self.animation_index])
            else:
                if self.animation_timer.isActive():
                    self.animation_timer.stop()
                    
                if self.status == "ready":
                    self.status_label.setText(ICON_READY)
                elif self.status == "failed":
                    self.status_label.setText(ICON_FAILED)
                elif self.status == "error":
                    self.status_label.setText(ICON_ERROR)
                elif self.status == "done":
                    self.status_label.setText(ICON_DONE)
                    
            # Setze Hintergrundfarbe basierend auf Status
            color = STATUS_COLORS.get(self.status, STATUS_COLORS["ready"])
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {color};
                    color: white;
                    border-radius: 4px;
                    padding: 2px 8px;
                    margin: 2px;
                }}
            """)
            
            # Aktualisiere Laufwerksname und Status
            if self.is_excluded:
                self.status_label.setText(ICON_EXCLUDED)
                self.drive_container.setStyleSheet(f"""
                    QWidget {{
                        background-color: {STATUS_COLORS["excluded"]};
                        border-radius: 4px;
                        padding: 4px;
                    }}
                """)
            elif self.is_mapped:
                self.drive_container.setStyleSheet(f"""
                    QWidget {{
                        background-color: {STATUS_COLORS["mapped"]};
                        border-radius: 4px;
                        padding: 4px;
                    }}
                """)
            else:
                self.drive_container.setStyleSheet(f"""
                    QWidget {{
                        background-color: {DRIVE_TYPE_COLORS.get(self.drive_type, DRIVE_TYPE_COLORS["local"])};
                        border-radius: 4px;
                        padding: 4px;
                    }}
                """)
                
            # Aktualisiere die Größe
            self.widget.adjustSize()
            self.setSizeHint(self.widget.sizeHint())
            
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der Anzeige: {e}")
        
    def update_status(self, status: str):
        """Aktualisiert den Status des Laufwerks."""
        self.status = status
        self._update_display()
        
    def set_excluded(self, excluded: bool):
        """Setzt den Ausschluss-Status des Laufwerks."""
        self.is_excluded = excluded
        self._update_display()
        
    def set_mapped(self, mapped: bool):
        """Setzt den Zuordnungs-Status des Laufwerks."""
        self.is_mapped = mapped
        self._update_display()
        
    def set_parallel_copy_info(self, count: int, total_speed: str = ""):
        """Setzt Informationen für parallele Kopiervorgänge."""
        self.parallel_count = count
        self.total_speed = total_speed
        self._update_display()
