from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel
)
from ..widgets import CustomButton

class SettingsSection(QWidget):
    """Einstellungs-Sektion des Hauptfensters."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Richtet das UI der Einstellungs-Sektion ein."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        settings_label = QLabel("Einstellungen")
        settings_label.setStyleSheet("color: white; font-size: 10pt;")
        layout.addWidget(settings_label)
        
        self.manage_presets_button = CustomButton("Presets verwalten")
        layout.addWidget(self.manage_presets_button)
