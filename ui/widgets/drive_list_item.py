#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from PyQt5.QtWidgets import (QListWidgetItem, QLabel, QWidget, QHBoxLayout, 
                            QSizePolicy, QApplication)
from PyQt5.QtCore import QTimer, Qt, QSize
from PyQt5.QtGui import QIcon, QColor
from PyQt5.Qt import QStyle

logger = logging.getLogger(__name__)

class DriveListItem(QListWidgetItem):
    """Ein ListWidget-Item für ein Laufwerk."""
    
    # Icons für verschiedene Laufwerkstypen
    DRIVE_ICONS = {
        "fixed": QStyle.SP_DriveHDIcon,
        "removable": QStyle.SP_DriveFDIcon,
        "cdrom": QStyle.SP_DriveCDIcon,
        "remote": QStyle.SP_DriveNetIcon,
        "unknown": QStyle.SP_DriveHDIcon
    }

    # Status Icons
    STATUS_ICONS = {
        "ready": "✅",
        "copying": "🔄",
        "excluded": "🚫",
        "failed": "❌",
        "error": "⚠️",
        "done": "✅",
        "mapped": "➡️"
    }

    # Farben für Laufwerkstypen
    DRIVE_COLORS = {
        "removable": "#8B5CF6",  # Lila für Wechseldatenträger
        "local": "#374151",      # Dunkelgrau für lokale Laufwerke
        "remote": "#14B8A6",     # Türkis für Netzwerklaufwerke
        "cd": "#4B5563",         # Grau für CD/DVD
        "unknown": "#4B5563"     # Grau für unbekannte Typen
    }

    # Status Farben
    STATUS_COLORS = {
        "ready": "#4CAF50",      # Grün
        "copying": "#2196F3",    # Blau
        "excluded": "#9E9E9E",   # Grau
        "failed": "#F44336",     # Rot
        "error": "#FF9800",      # Orange
        "done": "#4CAF50",       # Grün
        "mapped": "#9C27B0"      # Lila
    }

    # Status Texte
    STATUS_TEXT = {
        "ready": "Bereit",
        "copying": "Kopiere...",
        "excluded": "Ausgeschlossen",
        "failed": "Fehlgeschlagen",
        "error": "Fehler",
        "done": "Fertig",
        "mapped": "Zugeordnet"
    }
    
    def __init__(self, drive_letter: str, drive_name: str = "", drive_type: str = "local"):
        """Initialisiert das DriveListItem.
        
        Args:
            drive_letter: Laufwerksbuchstabe
            drive_name: Name des Laufwerks
            drive_type: Typ des Laufwerks (removable, local, remote, cd, unknown)
        """
        super().__init__()
        self.drive_letter = drive_letter
        self.drive_name = drive_name
        self.drive_type = drive_type
        self.status = "ready"
        self.is_excluded = False
        self.is_mapped = False
        self.transfer_complete = False
        self.animation_index = 0
        
        # Animation Timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._update_animation)
        self.animation_timer.setInterval(100)
        
        # Style für Icons
        self.style = QApplication.style()
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Erstellt das UI für das DriveListItem."""
        # Container Widget
        self.widget = QWidget()
        
        # Layout
        layout = QHBoxLayout(self.widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Icon Label
        self.icon_label = QLabel()
        icon = QIcon(self.style.standardPixmap(self.DRIVE_ICONS.get(self.drive_type, self.DRIVE_ICONS["unknown"])))
        pixmap = icon.pixmap(32, 32)
        self.icon_label.setPixmap(pixmap)
        self.icon_label.setFixedSize(32, 32)
        layout.addWidget(self.icon_label)
        
        # Drive Label Container
        self.drive_container = QWidget()
        self.drive_container.setStyleSheet(f"""
            QWidget {{
                background-color: {self.DRIVE_COLORS.get(self.drive_type, self.DRIVE_COLORS["unknown"])};
                border-radius: 4px;
                padding: 4px 8px;
            }}
        """)
        
        drive_layout = QHBoxLayout(self.drive_container)
        drive_layout.setContentsMargins(4, 2, 4, 2)
        
        # Laufwerksname
        self.drive_label = QLabel(f"{self.drive_letter}")
        if self.drive_name:
            self.drive_label.setText(f"{self.drive_letter} ({self.drive_name})")
        self.drive_label.setStyleSheet("color: white;")
        drive_layout.addWidget(self.drive_label)
        
        layout.addWidget(self.drive_container)
        
        # Status Label
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.status_label.setMinimumWidth(100)  # Minimale Breite für Status
        self.status_label.setStyleSheet("""
            QLabel {
                color: white;
                padding: 2px 6px;
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.status_label)
        
        # Kein Stretch mehr hier, damit der Status rechts bleibt
        # layout.addStretch()
        
        # Setze Widget
        self.setSizeHint(self.widget.sizeHint())
        
        # Setze initiales Status
        self.update_status(self.status)
        
    def _update_animation(self):
        """Aktualisiert den Animationsframe."""
        if self.status == "copying":
            self.animation_index = (self.animation_index + 1) % len(self.STATUS_ICONS["copying"])
            self._update_display()
            
    def update_excluded_status(self, is_excluded: bool):
        """Aktualisiert den Ausschlussstatus des Laufwerks."""
        self.is_excluded = is_excluded
        if is_excluded:
            self.status = "excluded"
        elif self.status == "excluded":
            self.status = "ready"
        self._update_display()

    def _update_display(self):
        """Aktualisiert die Anzeige des Items."""
        try:
            # Update drive name
            display_name = f"{self.drive_letter}"
            if self.drive_name:
                display_name += f" ({self.drive_name})"
            self.drive_label.setText(display_name)
            
            # Update drive icon
            drive_icon_type = self.DRIVE_ICONS.get(self.drive_type, self.DRIVE_ICONS["unknown"])
            drive_pixmap = self.style.standardPixmap(drive_icon_type)
            self.icon_label.setPixmap(drive_pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            
            # Determine status
            if self.is_excluded:
                status = "excluded"
            elif self.is_mapped:
                status = "mapped"
            elif self.transfer_complete:
                status = "done"
            else:
                status = self.status
                
            # Update status display
            status_color = self.STATUS_COLORS[status]
            status_icon = self.STATUS_ICONS[status]
            status_text = self.STATUS_TEXT[status]
            
            # Kombiniere Icon und Text im Status-Label
            self.status_label.setText(f"{status_icon} {status_text}")
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {status_color};
                    color: white;
                    border-radius: 4px;
                    padding: 0px 12px;
                    font-size: 12px;
                    font-weight: bold;
                }}
            """)
            
            # Update size
            self.widget.adjustSize()
            self.setSizeHint(self.widget.sizeHint())
            
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der Anzeige: {e}", exc_info=True)
            
    def update_status(self, status: str):
        """Setzt den Status des Items."""
        if status in self.STATUS_TEXT:
            self.status = status
            self._update_display()
    
    def set_excluded(self, excluded: bool):
        """Setzt den Ausschluss-Status des Items."""
        self.is_excluded = excluded
        self._update_display()
        
    def set_mapped(self, mapped: bool):
        """Setzt den Zuordnungs-Status des Items."""
        self.is_mapped = mapped
        self._update_display()
        
    def set_transfer_complete(self, complete: bool):
        """Setzt den Transfer-Status des Items."""
        self.transfer_complete = complete
        self._update_display()
