"""
Icon-Generierung und -Verwaltung.
"""
import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QLinearGradient, QColor, QPen

class IconManager:
    """Verwaltet die Icons der Anwendung."""
    
    @staticmethod
    def create_drive_icon(program_dir: str) -> QIcon:
        """Erstellt das Laufwerks-Icon."""
        icon_path = os.path.join(program_dir, "assets", "drive.png")
        icon = QIcon(icon_path)
        
        if not icon.availableSizes():
            # Fallback: Erstelle ein einfaches Drive-Icon
            pixmap = QPixmap(16, 16)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setPen(QPen(Qt.white))
            painter.drawRect(2, 2, 12, 12)
            painter.end()
            icon = QIcon(pixmap)
            
        return icon
    
    @staticmethod
    def create_gradient_status_icon(colors: list) -> QIcon:
        """Erstellt ein Status-Icon mit Farbverlauf."""
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        gradient = QLinearGradient(0, 0, 16, 16)
        
        for i, color in enumerate(colors):
            gradient.setColorAt(i / (len(colors) - 1), QColor(color))
            
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, 16, 16)
        painter.end()
        
        return QIcon(pixmap)
    
    @staticmethod
    def get_status_icons() -> dict:
        """Gibt die Standard-Status-Icons zurück."""
        return {
            'ok': IconManager.create_gradient_status_icon(
                ["#27ae60", "#2ecc71"]  # Grün
            ),
            'warning': IconManager.create_gradient_status_icon(
                ["#f39c12", "#f1c40f"]  # Gelb
            ),
            'error': IconManager.create_gradient_status_icon(
                ["#c0392b", "#e74c3c"]  # Rot
            )
        }
