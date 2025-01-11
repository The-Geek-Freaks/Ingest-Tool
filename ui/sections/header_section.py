from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QComboBox
)
from PyQt5.QtCore import Qt

class HeaderSection(QWidget):
    """Header-Sektion des Hauptfensters."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Richtet das UI der Header-Sektion ein."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Logo (falls vorhanden)
        logo_label = QLabel()
        if hasattr(self, 'logo_pixmap'):
            logo_label.setPixmap(self.logo_pixmap)
        layout.addWidget(logo_label)
        
        # Titel
        title_label = QLabel("IngestTool")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18pt;
                font-weight: bold;
            }
        """)
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # Sprach-Auswahl
        language_widget = QWidget()
        language_layout = QHBoxLayout(language_widget)
        language_layout.setContentsMargins(0, 0, 0, 0)
        
        language_label = QLabel("Sprache")
        language_label.setStyleSheet("color: white; font-size: 10pt;")
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Deutsch", "English"])
        self.language_combo.setFixedWidth(120)
        self.language_combo.setStyleSheet("""
            QComboBox {
                background-color: #3d3d3d;
                color: white;
                border: 1px solid gray;
                border-radius: 3px;
                padding: 5px;
                font-size: 10pt;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #3d3d3d;
                color: white;
                selection-background-color: rgb(13, 71, 161);
                selection-color: white;
            }
        """)
        
        language_layout.addWidget(language_label)
        language_layout.addWidget(self.language_combo)
        
        layout.addWidget(language_widget)
