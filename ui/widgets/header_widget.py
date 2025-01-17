#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Widget für einheitliche Header mit garantiertem Platz."""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt

from ui.style_helper import StyleHelper

class HeaderWidget(QWidget):
    """Ein Widget, das einen Header mit garantiertem Platz darstellt."""
    
    def __init__(self, title, parent=None):
        """Initialisiert das HeaderWidget.
        
        Args:
            title (str): Der anzuzeigende Titel
            parent (QWidget, optional): Das Eltern-Widget
        """
        super().__init__(parent)
        
        # Hauptlayout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header-Container mit eigenem Hintergrund
        self.header_container = QWidget()
        self.header_container.setFixedHeight(40)
        self.header_container.setStyleSheet(f"""
            QWidget {{
                background-color: {StyleHelper.BACKGROUND};
                border: none;
                margin: 0;
                padding: 0;
            }}
        """)
        header_layout = QVBoxLayout(self.header_container)
        header_layout.setContentsMargins(5, 5, 5, 5)
        
        # Header-Label
        self.header = QLabel(title)
        self.header.setStyleSheet(f"""
            QLabel {{
                color: {StyleHelper.TEXT};
                font-weight: bold;
                padding: 5px 10px;
                background-color: {StyleHelper.SURFACE};
                border: 1px solid {StyleHelper.BORDER};
                border-radius: 4px;
            }}
        """)
        header_layout.addWidget(self.header)
        layout.addWidget(self.header_container)
        
        # Content-Container
        self.content_container = QWidget()
        self.content_container.setStyleSheet(f"""
            QWidget {{
                background-color: {StyleHelper.BACKGROUND};
                border: 1px solid {StyleHelper.BORDER};
                border-radius: 4px;
                margin-top: 5px;
            }}
        """)
        
        # Content Layout
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(10)
        
        layout.addWidget(self.content_container)
        
    def add_widget(self, widget):
        """Fügt ein Widget zum Inhalt hinzu."""
        self.content_layout.addWidget(widget)
        
    def add_layout(self, layout):
        """Fügt ein Layout zum Inhalt hinzu."""
        self.content_layout.addLayout(layout)
