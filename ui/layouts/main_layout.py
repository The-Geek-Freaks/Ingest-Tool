#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Layout-Manager für das Hauptfenster."""

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QComboBox,
    QLineEdit, QCheckBox, QListWidget,
    QWidget, QSplitter, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt
from datetime import datetime
import logging

from .top_layout import create_top_layout
from .middle_layout import create_middle_layout
from .settings_layout import create_settings_layout
from .progress_layout import create_progress_layout
from ui.style_helper import StyleHelper
from ui.widgets.drop_zone import DropZone
from ui.widgets.ingesting_drives_widget import IngestingDrivesWidget
from ui.widgets import ModernTransferWidget
from utils.logging_widgets import QTextEditLogger
from ui.widgets.header_widget import HeaderWidget
from ui.widgets.theme_toggle_button import ThemeToggleButton
from ui.theme_manager import ThemeManager
from ui.sections.header_section import HeaderSection
from PyQt5.QtGui import QFont

class MainLayout:
    """Verwaltet das Layout des Hauptfensters."""
    
    def __init__(self, main_window):
        self.main_window = main_window
        
    def setup_ui(self):
        """Erstellt das komplette UI-Layout."""
        # Theme Manager initialisieren
        self.theme_manager = ThemeManager()
        
        # Erstelle ein zentrales Widget
        central_widget = QWidget()
        self.main_window.setCentralWidget(central_widget)
        
        # Hauptlayout (Vertikal)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)  
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header hinzufügen
        from ui.sections.header_section import HeaderSection
        header = HeaderSection()
        # Keine fixe Höhe mehr, lasse das Banner die Höhe bestimmen
        main_layout.addWidget(header)
        
        # Content Layout
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)  
        content_layout.setContentsMargins(20, 0, 20, 20)  
        
        # Linker Sidebar für verbundene Laufwerke
        drives_widget = HeaderWidget("💾 " + self.main_window.i18n.get("ui.connected_drives"))
        drives_widget.setFixedWidth(430)
        drives_widget.setContentsMargins(0, 0, 0, 0)  # Entferne innere Margins
        
        # DriveList soll die gesamte verfügbare Höhe ausfüllen
        self.main_window.drives_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_window.drives_list.setMinimumHeight(400)
        drives_widget.add_widget(self.main_window.drives_list)
        
        # Container für die linke Spalte
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_layout.addWidget(drives_widget)
        
        # Füge den Container zum Content Layout hinzu
        content_layout.addWidget(left_container)
        
        # Rechter Bereich
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)  # Entferne innere Margins
        right_layout.setSpacing(20)
        
        # Zeile 2: Zuordnungen und ausgeschlossene Laufwerke
        right_layout.addLayout(create_middle_layout(self.main_window))
        
        # Ingestierende Laufwerke Widget (nur Instanz, nicht im Layout)
        self.main_window.ingesting_drives_widget = IngestingDrivesWidget()
        
        # Gefilterte Laufwerksliste (nur Instanz, nicht im Layout)
        self.main_window.filtered_drives_list = QListWidget()
        self.main_window.filtered_drives_list.setMaximumHeight(250)
        
        # Transfer-Bereich mit Transfer-Widget und DropZone nebeneinander
        transfer_section = QWidget()
        transfer_layout = QHBoxLayout(transfer_section)
        transfer_layout.setContentsMargins(0, 0, 0, 0)
        transfer_layout.setSpacing(20)
        
        # Transfer-Widget (links)
        transfer_container = QWidget()
        transfer_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        transfer_container_layout = QVBoxLayout(transfer_container)
        transfer_container_layout.setContentsMargins(0, 0, 0, 0)
        transfer_container_layout.setSpacing(0)
        
        transfer_widget = HeaderWidget("📤 " + self.main_window.i18n.get("Aktive Transfers"))
        transfer_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        transfer_widget.add_widget(self.main_window.transfer_widget)
        transfer_container_layout.addWidget(transfer_widget)
        
        # DropZone (rechts)
        dropzone_container = QWidget()
        dropzone_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        dropzone_container.setFixedWidth(250)  # Feste Breite für die DropZone
        dropzone_layout = QVBoxLayout(dropzone_container)
        dropzone_layout.setContentsMargins(0, 0, 0, 0)
        dropzone_layout.setSpacing(0)
        
        dropzone = DropZone(self.main_window)
        dropzone.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        dropzone_layout.addWidget(dropzone)
        
        # Widgets zum Layout hinzufügen
        transfer_layout.addWidget(transfer_container, stretch=1)
        transfer_layout.addWidget(dropzone_container)
        
        # Transfer-Sektion zum rechten Layout hinzufügen
        right_layout.addWidget(transfer_section)
        
        # Mittlerer Bereich mit Progress Widget und 
        middle_section = QWidget()
        middle_layout = QHBoxLayout(middle_section)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(10)
        
        # Füge mittleren Bereich zum Layout hinzu
        right_layout.addWidget(middle_section)
        
        # Protokoll und Einstellungen
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(20)  # Abstand zwischen den Widgets
        
        # Protokoll Widget
        log_widget = HeaderWidget("📝 " + self.main_window.i18n.get("ui.protocol"))
        
        # Log Widget erstellen und konfigurieren
        self.main_window.log_widget = QTextEditLogger(parent=self.main_window)
        self.main_window.log_widget.widget.setMinimumWidth(300)
        self.main_window.log_widget.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        logging.getLogger().addHandler(self.main_window.log_widget)
        logging.getLogger().setLevel(logging.INFO)
        
        log_widget.add_widget(self.main_window.log_widget.widget)
        bottom_layout.addWidget(log_widget)
        
        # Einstellungen Button
        settings_widget = HeaderWidget("⚙️ " + self.main_window.i18n.get("Preset Manager"))
        settings_content = create_settings_layout(self.main_window)
        settings_widget.add_widget(settings_content)
        bottom_layout.addWidget(settings_widget)
        
        # Füge das Bottom Layout zum rechten Layout hinzu
        right_layout.addLayout(bottom_layout)
        
        # Füge rechten Bereich zum Content Layout hinzu
        content_layout.addWidget(right_widget, 2)
        
        # Füge Content Layout zum Hauptlayout hinzu
        main_layout.addLayout(content_layout)
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(20)
        footer_layout.setContentsMargins(10, 10, 0, 10)  
        
        # Linke Seite des Footers
        left_footer = QWidget()
        left_footer_layout = QHBoxLayout(left_footer)
        left_footer_layout.setContentsMargins(0, 0, 0, 0)
        
        # Theme Toggle Button
        theme_toggle = ThemeToggleButton()
        left_footer_layout.addWidget(theme_toggle)
        
        # Trennlinie nach Theme Toggle
        separator_theme = QFrame()
        separator_theme.setFrameShape(QFrame.VLine)
        separator_theme.setFrameShadow(QFrame.Sunken)
        left_footer_layout.addWidget(separator_theme)
        
        # Bereitschaftsanzeige
        self.main_window.ready_label = QLabel(" " + self.main_window.i18n.get("ui.ready"))
        left_footer_layout.addWidget(self.main_window.ready_label)
        
        # Speicherplatz
        self.main_window.storage_label = QLabel()
        self.main_window.storage_label.setText(" " + self.main_window.i18n.get("ui.storage", free="0 GB", total="0 GB"))
        left_footer_layout.addWidget(self.main_window.storage_label)
        
        # CPU-Auslastung
        self.main_window.cpu_label = QLabel()
        self.main_window.cpu_label.setText(" " + self.main_window.i18n.get("ui.cpu", usage="0"))
        left_footer_layout.addWidget(self.main_window.cpu_label)
        
        # Trennlinie
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        left_footer_layout.addWidget(separator)
        
        # Copyright
        year = datetime.now().year
        copyright_label = QLabel("Copyright TheGeekFreaks | Alexander Zuber-Jatzke")
        copyright_label.setStyleSheet("color: #666;")
        left_footer_layout.addWidget(copyright_label)
        
        footer_layout.addWidget(left_footer)
        
        # Füge maximalen Stretch hinzu um die Buttons nach ganz rechts zu schieben
        footer_layout.addStretch(1)
        
        # Start und Stop Buttons in einem eigenen Widget
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 10, 0)  
        
        # Start und Stop Buttons
        buttons_layout.addWidget(self.main_window.start_button)
        buttons_layout.addWidget(self.main_window.cancel_button)
        
        # Abort Button
        self.main_window.abort_button = QPushButton("Transfer abbrechen")
        self.main_window.abort_button.setEnabled(False)  
        self.main_window.abort_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
            }
        """)
        buttons_layout.addWidget(self.main_window.abort_button)
        
        footer_layout.addWidget(buttons_widget)
        
        main_layout.addLayout(footer_layout)
        
        # Verbinde Theme-Änderungen
        self.theme_manager.theme_changed.connect(
            lambda theme: self.main_window.app.setStyleSheet(self.theme_manager.get_stylesheet())
        )
        
        # Setze Fenstergröße und Titel
        self.main_window.setWindowTitle("TheGeekFreaks - Ingest Tool")
        self.main_window.setMinimumSize(1024, 768)  
        self.main_window.resize(1280, 800)  
