"""
Angepasstes ListWidget mit einheitlichem Styling.
"""
from PyQt5.QtWidgets import QListWidget
from PyQt5.QtCore import Qt
from ui.style_helper import StyleHelper

class CustomListWidget(QListWidget):
    """Ein angepasstes ListWidget mit einheitlichem Styling."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_style()
        
    def setup_style(self):
        """Wendet das einheitliche Styling an."""
        self.setStyleSheet(f"""
            QListWidget {{
                background-color: {StyleHelper.SURFACE};
                border: 1px solid {StyleHelper.BORDER};
                border-radius: 4px;
                padding: 4px;
            }}
            QListWidget::item {{
                background-color: transparent;
                padding: 4px;
                margin: 2px 0px;
            }}
            QListWidget::item:selected {{
                background-color: {StyleHelper.SURFACE_LIGHT};
                color: {StyleHelper.TEXT};
            }}
            QListWidget::item:hover {{
                background-color: {StyleHelper.SURFACE_LIGHT};
            }}
            QScrollBar:vertical {{
                background-color: {StyleHelper.BACKGROUND};
                width: 8px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {StyleHelper.ACCENT};
                min-height: 20px;
                border-radius: 4px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
        
        # Weitere Einstellungen
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.setSpacing(2)
