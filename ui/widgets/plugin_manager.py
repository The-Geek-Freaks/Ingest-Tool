#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Plugin-Manager Widget für die erweiterten Einstellungen."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget,
    QListWidgetItem, QCheckBox, QFrame,
    QFileDialog, QMessageBox, QProgressBar
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor

class PluginManager(QWidget):
    """Widget zur Verwaltung von Plugins."""
    
    plugin_activated = pyqtSignal(str)  # Signal wenn ein Plugin aktiviert wird
    plugin_deactivated = pyqtSignal(str)  # Signal wenn ein Plugin deaktiviert wird
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.plugins = {}  # Dictionary für Plugin-Informationen
        self.setup_ui()
        self.apply_dark_mode()
        
    def apply_dark_mode(self):
        """Wendet das Dark Mode Design an."""
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#1e1e1e"))
        palette.setColor(QPalette.WindowText, QColor("#ffffff"))
        palette.setColor(QPalette.Base, QColor("#2d2d2d"))
        palette.setColor(QPalette.AlternateBase, QColor("#353535"))
        palette.setColor(QPalette.Text, QColor("#ffffff"))
        palette.setColor(QPalette.Button, QColor("#353535"))
        palette.setColor(QPalette.ButtonText, QColor("#ffffff"))
        self.setPalette(palette)
        
    def setup_ui(self):
        """Erstellt das UI des Plugin-Managers."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # Header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Plugin installieren Button
        install_button = QPushButton("Plugin installieren")
        install_button.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #353535;
            }
        """)
        install_button.clicked.connect(self.install_plugin)
        header_layout.addWidget(install_button)
        
        # Aktualisieren Button
        refresh_button = QPushButton("Aktualisieren")
        refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #353535;
            }
        """)
        refresh_button.clicked.connect(self.refresh_plugins)
        header_layout.addWidget(refresh_button)
        
        header_layout.addStretch()
        layout.addWidget(header)
        
        # Plugin-Liste
        self.plugin_list = QListWidget()
        self.plugin_list.setStyleSheet("""
            QListWidget {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 4px;
            }
            QListWidget::item {
                color: #ffffff;
                padding: 10px;
                border-bottom: 1px solid #404040;
            }
            QListWidget::item:hover {
                background-color: #353535;
            }
            QListWidget::item:selected {
                background-color: #404040;
            }
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #404040;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4a4a4a;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background-color: #2d2d2d;
            }
        """)
        layout.addWidget(self.plugin_list)
        
        # Dummy-Plugins für die Vorschau
        self.add_dummy_plugins()
        
    def add_dummy_plugins(self):
        """Fügt Dummy-Plugins für die Vorschau hinzu."""
        dummy_plugins = [
            {
                "name": "Automatische Ordnerstruktur",
                "version": "1.0.0",
                "description": "Erstellt automatisch Ordnerstrukturen basierend auf Metadaten",
                "author": "TheGeekFreaks",
                "enabled": True
            },
            {
                "name": "Metadaten-Extraktor",
                "version": "1.2.1",
                "description": "Extrahiert Metadaten aus Medien-Dateien",
                "author": "TheGeekFreaks",
                "enabled": False
            },
            {
                "name": "Thumbnail-Generator",
                "version": "0.9.5",
                "description": "Generiert Vorschaubilder für Medien-Dateien",
                "author": "TheGeekFreaks",
                "enabled": True
            }
        ]
        
        for plugin in dummy_plugins:
            self.add_plugin_to_list(plugin)
    
    def add_plugin_to_list(self, plugin_info):
        """Fügt ein Plugin zur Liste hinzu."""
        item = QListWidgetItem(self.plugin_list)
        widget = PluginListItem(plugin_info)
        item.setSizeHint(widget.sizeHint())
        self.plugin_list.addItem(item)
        self.plugin_list.setItemWidget(item, widget)
        
    def install_plugin(self):
        """Öffnet einen Dialog zur Plugin-Installation."""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Plugin installieren",
            "",
            "Plugin-Dateien (*.zip *.py)"
        )
        
        if file_name:
            # Hier würde die tatsächliche Plugin-Installation stattfinden
            QMessageBox.information(
                self,
                "Plugin Installation",
                "Das Plugin wurde erfolgreich installiert."
            )
            
    def refresh_plugins(self):
        """Aktualisiert die Plugin-Liste."""
        # Hier würde die tatsächliche Plugin-Aktualisierung stattfinden
        QMessageBox.information(
            self,
            "Plugins aktualisiert",
            "Alle Plugins wurden erfolgreich aktualisiert."
        )

class PluginListItem(QWidget):
    """Widget für einen einzelnen Plugin-Eintrag in der Liste."""
    
    def __init__(self, plugin_info, parent=None):
        super().__init__(parent)
        self.plugin_info = plugin_info
        self.setup_ui()
        
    def setup_ui(self):
        """Erstellt das UI des Plugin-Eintrags."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Plugin-Informationen
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(5)
        
        # Name und Version
        name_layout = QHBoxLayout()
        name_label = QLabel(self.plugin_info["name"])
        name_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        name_label.setStyleSheet("color: #ffffff;")
        name_layout.addWidget(name_label)
        
        version_label = QLabel(f"v{self.plugin_info['version']}")
        version_label.setStyleSheet("color: #b0b0b0;")
        name_layout.addWidget(version_label)
        name_layout.addStretch()
        info_layout.addLayout(name_layout)
        
        # Beschreibung
        description = QLabel(self.plugin_info["description"])
        description.setStyleSheet("color: #b0b0b0;")
        info_layout.addWidget(description)
        
        # Autor
        author = QLabel(f"Autor: {self.plugin_info['author']}")
        author.setStyleSheet("color: #808080; font-size: 11px;")
        info_layout.addWidget(author)
        
        layout.addWidget(info_widget)
        
        # Aktivieren/Deaktivieren Checkbox
        self.enabled_checkbox = QCheckBox("Aktiviert")
        self.enabled_checkbox.setChecked(self.plugin_info["enabled"])
        self.enabled_checkbox.setStyleSheet("""
            QCheckBox {
                color: #ffffff;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #404040;
                border-radius: 3px;
                background-color: #2d2d2d;
            }
            QCheckBox::indicator:checked {
                background-color: #2196F3;
                border-color: #2196F3;
                image: url(checkmark.png);
            }
            QCheckBox::indicator:hover {
                border-color: #4a4a4a;
            }
        """)
        layout.addWidget(self.enabled_checkbox)
