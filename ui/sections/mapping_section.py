from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QLineEdit, QPushButton
)
from ..widgets import CustomButton, CustomListWidget

class MappingSection(QWidget):
    """Mapping-Sektion des Hauptfensters."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Richtet das UI der Mapping-Sektion ein."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        mapping_label = QLabel("Zuordnungen")
        mapping_label.setStyleSheet("color: white; font-size: 10pt;")
        layout.addWidget(mapping_label)
        
        mapping_input_widget = QWidget()
        mapping_input_layout = QHBoxLayout(mapping_input_widget)
        mapping_input_layout.setContentsMargins(0, 0, 0, 0)
        
        self.extension_combo = QComboBox()
        self.extension_combo.addItems([".mp4", ".mov", ".avi", ".mkv", ".mxf", ".r3d", ".braw", ".arri", ".dng", ".raw"])
        self.extension_combo.setFixedWidth(100)
        self.extension_combo.setStyleSheet("""
            QComboBox {
                background-color: #3d3d3d;
                color: white;
                border: 1px solid gray;
                padding: 5px;
                font-size: 10pt;
            }
        """)
        
        self.target_path = QLineEdit()
        self.target_path.setStyleSheet("""
            QLineEdit {
                background-color: #3d3d3d;
                color: white;
                border: 1px solid gray;
                padding: 5px;
                font-size: 10pt;
            }
        """)
        
        self.browse_button = QPushButton("...")
        self.browse_button.setFixedWidth(40)
        self.browse_button.setStyleSheet("""
            QPushButton {
                background-color: rgb(13, 71, 161);
                color: white;
                border: none;
                padding: 5px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: rgb(25, 118, 210);
            }
        """)
        
        mapping_input_layout.addWidget(self.extension_combo)
        mapping_input_layout.addWidget(self.target_path)
        mapping_input_layout.addWidget(self.browse_button)
        
        layout.addWidget(mapping_input_widget)
        
        mapping_buttons_widget = QWidget()
        mapping_buttons_layout = QHBoxLayout(mapping_buttons_widget)
        mapping_buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        self.add_mapping_button = CustomButton("Hinzufügen")
        self.remove_mapping_button = CustomButton("Entfernen")
        
        mapping_buttons_layout.addWidget(self.add_mapping_button)
        mapping_buttons_layout.addWidget(self.remove_mapping_button)
        mapping_buttons_layout.addStretch()
        
        layout.addWidget(mapping_buttons_widget)
        
        self.mappings_list = CustomListWidget()
        layout.addWidget(self.mappings_list)
