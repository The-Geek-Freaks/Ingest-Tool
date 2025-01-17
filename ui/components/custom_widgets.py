"""
Benutzerdefinierte UI-Widgets.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtWidgets import QPushButton, QListWidget, QListWidgetItem
from ui.style_helper import StyleHelper
from ui.theme_manager import ThemeManager

class CustomButton(QPushButton):
    """Angepasster Button mit Hover-Effekt und Tooltip."""
    
    def __init__(self, text, parent=None, tooltip=""):
        super().__init__(text, parent)
        self.default_style = ""
        self.hover_style = ""
        self.tooltip = tooltip
        self.setup_ui()
        
    def setup_ui(self):
        """Richtet das UI des Buttons ein."""
        self.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px 10px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border: 1px solid #666;
            }
            QPushButton:pressed {
                background-color: #1d1d1d;
            }
            QPushButton:disabled {
                background-color: #1d1d1d;
                color: #666;
                border: 1px solid #333;
            }
        """)
        if self.tooltip:
            self.setToolTip(self.tooltip)
            
    def enterEvent(self, event):
        """Handler für Mouse Enter Event."""
        if self.isEnabled():
            self.setStyleSheet(self.hover_style or """
                QPushButton {
                    background-color: #3d3d3d;
                    color: white;
                    border: 1px solid #666;
                    border-radius: 3px;
                    padding: 5px 10px;
                    min-width: 80px;
                }
            """)
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """Handler für Mouse Leave Event."""
        self.setStyleSheet(self.default_style or """
            QPushButton {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px 10px;
                min-width: 80px;
            }
        """)
        super().leaveEvent(event)

class CustomListWidget(QListWidget):
    """Angepasstes ListWidget mit Drag & Drop und Animationen."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setSelectionMode(QListWidget.ExtendedSelection)
        self.update_style()
        
        # Theme-Änderungen überwachen
        self.theme_manager = ThemeManager()
        self.theme_manager.theme_changed.connect(self.update_style)
    
    def update_style(self):
        """Aktualisiert den Style basierend auf dem aktuellen Theme."""
        self.setStyleSheet(StyleHelper.get_list_widget_style())
        
    def dragEnterEvent(self, event):
        """Handler für Drag Enter Events."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event):
        """Handler für Drop Events."""
        urls = event.mimeData().urls()
        for url in urls:
            path = url.toLocalFile()
            item = QListWidgetItem(path)
            item.setData(Qt.UserRole, {'path': path})
            self.addItem(item)
