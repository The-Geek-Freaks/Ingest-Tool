"""
Angepasster Button mit einheitlichem Styling.
"""
from PyQt5.QtWidgets import QPushButton, QSizePolicy, QToolTip
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation
from PyQt5.QtGui import QFont
from ui.style_helper import StyleHelper

class CustomButton(QPushButton):
    """Ein angepasster Button mit einheitlichem Styling."""
    
    def __init__(self, text="", parent=None, tooltip=""):
        """Initialisiert den Button.
        
        Args:
            text: Button-Text oder Icon
            parent: Parent-Widget
            tooltip: Tooltip-Text (optional)
        """
        super().__init__(text, parent)
        self.tooltip = tooltip
        self.setup_style()
        
    def setup_style(self):
        """Wendet das einheitliche Styling an."""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {StyleHelper.SURFACE};
                color: {StyleHelper.TEXT};
                border: 1px solid {StyleHelper.BORDER};
                border-radius: 3px;
                padding: 5px 10px;
                min-width: 80px;
            }}
            
            QPushButton:hover {{
                background-color: {StyleHelper.SURFACE_LIGHT};
                border-color: {StyleHelper.ACCENT};
            }}
            
            QPushButton:pressed {{
                background-color: {StyleHelper.ACCENT};
                color: {StyleHelper.BACKGROUND};
            }}
            
            QPushButton:disabled {{
                background-color: {StyleHelper.SURFACE};
                border-color: {StyleHelper.BORDER};
                color: {StyleHelper.TEXT_SECONDARY};
            }}
        """)
        
        # Weitere Einstellungen
        self.setFont(QFont("Segoe UI", 9))
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setMinimumSize(QSize(80, 30))
        
        if self.tooltip:
            self.setToolTip(self.tooltip)
            QToolTip.setFont(QFont("Segoe UI", 8))
