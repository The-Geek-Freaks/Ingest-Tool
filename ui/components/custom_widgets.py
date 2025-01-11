"""
Benutzerdefinierte UI-Widgets.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtWidgets import QPushButton, QListWidget, QListWidgetItem

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
        self.setStyleSheet("""
            QListWidget {
                background-color: #3d3d3d;
                color: white;
                border: 1px solid gray;
                border-radius: 3px;
                padding: 5px;
            }
            QListWidget::item {
                background-color: #2d2d2d;
                border: 1px solid #555;
                border-radius: 2px;
                margin: 2px;
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: rgb(13, 71, 161);
                border: 1px solid rgb(25, 118, 210);
            }
            QListWidget::item:hover {
                background-color: #4d4d4d;
                border: 1px solid #666;
            }
        """)
        
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
