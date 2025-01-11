"""
Angepasstes ListWidget mit einheitlichem Styling.
"""
from PyQt5.QtWidgets import QListWidget
from PyQt5.QtCore import Qt

class CustomListWidget(QListWidget):
    """Ein angepasstes ListWidget mit einheitlichem Styling."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_style()
        
    def setup_style(self):
        """Wendet das einheitliche Styling an."""
        self.setStyleSheet("""
            QListWidget {
                background-color: #323232;
                border: 1px solid #444444;
                border-radius: 4px;
                padding: 4px;
            }
            
            QListWidget::item {
                color: white;
                padding: 8px;
                margin: 2px 0;
                border-radius: 2px;
            }
            
            QListWidget::item:selected {
                background-color: #2d5ca6;
            }
            
            QListWidget::item:hover {
                background-color: #404040;
            }
            
            QScrollBar:vertical {
                border: none;
                background: #404040;
                width: 10px;
                margin: 0;
            }
            
            QScrollBar::handle:vertical {
                background: #666666;
                min-height: 20px;
                border-radius: 5px;
            }
            
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
                background: none;
            }
            
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        # Weitere Einstellungen
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.setSpacing(2)
