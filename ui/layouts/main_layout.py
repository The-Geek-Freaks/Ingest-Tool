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
from ui.widgets.drop_zone import DropZone
from ui.widgets.ingesting_drives_widget import IngestingDrivesWidget
from ui.widgets.progress_widget import ProgressWidget
from utils.logging_widgets import QTextEditLogger

class MainLayout:
    """Verwaltet das Layout des Hauptfensters."""
    
    def __init__(self, main_window):
        self.main_window = main_window
        
    def setup_ui(self):
        """Erstellt das komplette UI-Layout."""
        # Erstelle ein zentrales Widget
        central_widget = QWidget()
        self.main_window.setCentralWidget(central_widget)
        
        # Hauptlayout (Horizontal für Sidebar)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Content Layout
        content_layout = QHBoxLayout()
        content_layout.setSpacing(0)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # Linker Sidebar für verbundene Laufwerke
        sidebar_widget = QWidget()
        sidebar_widget.setFixedWidth(430)  
        sidebar_widget.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border: 1px solid #4B5563;
                border-radius: 4px;
            }
            QListWidget {
                background-color: #2D2D2D;
                border: none;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setSpacing(5)
        sidebar_layout.setContentsMargins(8, 8, 8, 8)
        
        drives_label = QLabel(" " + self.main_window.i18n.get("ui.connected_drives"))
        drives_label.setStyleSheet("""
            QLabel {
                color: #E5E7EB;
                font-weight: bold;
                padding: 5px;
            }
        """)
        sidebar_layout.addWidget(drives_label)
        
        # DriveList soll die gesamte verfügbare Höhe ausfüllen
        self.main_window.drives_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_window.drives_list.setMinimumHeight(400)  
        sidebar_layout.addWidget(self.main_window.drives_list, stretch=1)  
        
        # Füge Sidebar zum Content Layout hinzu
        content_layout.addWidget(sidebar_widget, 1)
        
        # Rechter Bereich
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(10)
        
        # Zeile 2: Zuordnungen und ausgeschlossene Laufwerke
        right_layout.addLayout(create_middle_layout(self.main_window))
        
        # Ingestierende Laufwerke Widget (nur Instanz, nicht im Layout)
        self.main_window.ingesting_drives_widget = IngestingDrivesWidget()
        
        # Gefilterte Laufwerksliste (nur Instanz, nicht im Layout)
        self.main_window.filtered_drives_list = QListWidget()
        self.main_window.filtered_drives_list.setMaximumHeight(250)  
        
        # Mittlerer Bereich mit Progress Widget und DropZone
        middle_section = QWidget()
        middle_layout = QHBoxLayout(middle_section)
        middle_layout.setContentsMargins(10, 10, 10, 10)
        middle_layout.setSpacing(10)
        
        # Progress Widget (80% Breite)
        self.main_window.progress_widget = ProgressWidget(self.main_window)
        self.main_window.progress_widget.setMinimumWidth(400)
        self.main_window.progress_widget.setMinimumHeight(400)  
        self.main_window.progress_widget.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
            }
        """)
        middle_layout.addWidget(self.main_window.progress_widget, stretch=8)
        
        # Drop-Zone (20% Breite)
        self.main_window.drop_zone = DropZone(self.main_window)
        self.main_window.drop_zone.setMinimumWidth(100)
        middle_layout.addWidget(self.main_window.drop_zone, stretch=2)
        
        # Füge mittleren Bereich zum Layout hinzu
        right_layout.addWidget(middle_section)
        
        # Splitter für Protocol und Settings
        protocol_settings_splitter = QSplitter(Qt.Vertical)
        protocol_settings_splitter.setContentsMargins(0, 0, 0, 0)
        protocol_settings_splitter.setHandleWidth(1)
        protocol_settings_splitter.setStyleSheet(
            "QSplitter::handle { background-color: #2d5ca6; }"
        )
        
        # Protocol Group
        protocol_group = QGroupBox("Protokoll")
        protocol_layout = QVBoxLayout(protocol_group)
        
        # Erstelle das Log-Widget und verbinde es mit dem Logger
        self.main_window.log_widget = QTextEditLogger(parent=protocol_group)
        self.main_window.log_widget.widget.setMinimumWidth(300)
        self.main_window.log_widget.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        logging.getLogger().addHandler(self.main_window.log_widget)
        logging.getLogger().setLevel(logging.INFO)
        protocol_layout.addWidget(self.main_window.log_widget.widget)
        
        # Einstellungen (Rechts)
        settings_widget = create_settings_layout(self.main_window)
        
        # Füge beide zum Splitter hinzu (7:3 Verhältnis)
        protocol_settings_splitter.addWidget(protocol_group)
        protocol_settings_splitter.addWidget(settings_widget)
        protocol_settings_splitter.setStretchFactor(0, 7)
        protocol_settings_splitter.setStretchFactor(1, 3)
        
        right_layout.addWidget(protocol_settings_splitter)
        
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
        
        # Setze Fenstergröße und Titel
        self.main_window.setWindowTitle("Ingest Tool")
        self.main_window.setMinimumSize(1024, 768)  
        self.main_window.resize(1280, 800)  
