"""
Angepasster Button mit einheitlichem Styling.
"""
from PyQt5.QtWidgets import QPushButton, QSizePolicy, QToolTip
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation
from PyQt5.QtGui import QFont

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
        # Setze Tooltip
        if self.tooltip:
            self.setToolTip(self.tooltip)
            QToolTip.setFont(QFont('Segoe UI', 9))
            
        # Aktiviere Mouse Tracking für Hover-Effekte
        self.setMouseTracking(True)
        
        # Größenpolicy
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        
        # Grundlegendes Styling
        self.setStyleSheet("""
            QPushButton {
                background-color: #2d5ca6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
            }
            
            QPushButton:hover {
                background-color: #3670c9;
            }
            
            QPushButton:pressed {
                background-color: #1f4179;
            }
            
            QPushButton:disabled {
                background-color: #666666;
            }
        """)
        self.setCursor(Qt.PointingHandCursor)
