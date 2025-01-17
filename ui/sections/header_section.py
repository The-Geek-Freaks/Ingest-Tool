from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QComboBox, QVBoxLayout
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from ui.style_helper import StyleHelper

class HeaderSection(QWidget):
    """Header-Sektion des Hauptfensters."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def resizeEvent(self, event):
        """Wird aufgerufen, wenn sich die Größe des Widgets ändert."""
        super().resizeEvent(event)
        
        # Aktualisiere die Header-Höhe basierend auf dem Banner-Ratio
        if hasattr(self, 'banner_pixmap'):
            banner_ratio = self.banner_pixmap.height() / self.banner_pixmap.width()
            self.setFixedHeight(int(self.width() * banner_ratio))
        
        self.update_banner()
        # Button-Container-Breite aktualisieren
        if hasattr(self, 'button_container'):
            self.button_container.resize(self.width(), 40)
            
    def update_banner(self):
        """Aktualisiert die Größe des Banners."""
        if hasattr(self, 'banner_pixmap') and hasattr(self, 'banner_label'):
            scaled_pixmap = self.banner_pixmap.scaled(
                self.width(), 
                self.height(),
                Qt.IgnoreAspectRatio, 
                Qt.SmoothTransformation
            )
            self.banner_label.setPixmap(scaled_pixmap)
            # Zentriere das Banner
            self.banner_label.setAlignment(Qt.AlignCenter)
    
    def setup_ui(self):
        """Richtet das UI der Header-Sektion ein."""
        # Hauptlayout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, -10)  # Negativer unterer Margin um den Abstand zu reduzieren
        main_layout.setSpacing(0)
        
        # Banner
        self.banner_label = QLabel(self)
        self.banner_pixmap = QPixmap("C:/Users/Shadow-PC/CascadeProjects/Ingest-Tool/docs/assets/banner_groß.png")
        
        # Berechne die Höhe basierend auf dem Banner-Ratio
        banner_ratio = self.banner_pixmap.height() / self.banner_pixmap.width()
        self.setFixedHeight(int(self.width() * banner_ratio))
        
        self.banner_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.banner_label)
        
        
        
        # Initialer Banner-Update
        self.update_banner()
