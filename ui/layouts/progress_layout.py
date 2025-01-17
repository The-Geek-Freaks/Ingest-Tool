#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Layout für die Fortschrittsanzeige."""

from PyQt5.QtWidgets import QVBoxLayout, QLabel, QProgressBar, QWidget
from ui.widgets.header_widget import HeaderWidget

def create_progress_layout(parent: QWidget) -> QVBoxLayout:
    """Erstellt das Layout für die Fortschrittsanzeige.
    
    Args:
        parent: Das übergeordnete Widget
        
    Returns:
        QVBoxLayout mit der Fortschrittsanzeige
    """
    layout = QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(5)
    
    # Progress Widget mit Header
    progress_widget = HeaderWidget("📊 Kopierfortschritt")
    
    # Progress Bar
    progress_bar = QProgressBar()
    progress_bar.setStyleSheet("""
        QProgressBar {
            border: 1px solid #4B5563;
            border-radius: 3px;
            text-align: center;
            background-color: #1F2937;
        }
        QProgressBar::chunk {
            background-color: #10B981;
            border-radius: 2px;
        }
    """)
    progress_widget.add_widget(progress_bar)
    
    # Status Label
    status_label = QLabel("Bereit")
    status_label.setStyleSheet("color: #E5E7EB;")
    progress_widget.add_widget(status_label)
    
    layout.addWidget(progress_widget)
    return layout
