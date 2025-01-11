from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar
)
from PyQt5.QtCore import Qt
from ..widgets import CustomButton

class FooterSection(QWidget):
    """Footer-Sektion des Hauptfensters."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Richtet das UI der Footer-Sektion ein."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 0)
        
        # Status und Progress
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_label = QLabel("Bereit")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #2ecc71;
                font-size: 10pt;
            }
        """)
        
        self.speed_label = QLabel("0 MB/s")
        self.speed_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 10pt;
            }
        """)
        
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.speed_label)
        
        layout.addWidget(status_widget)
        
        # Fortschrittsbalken
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid gray;
                border-radius: 3px;
                background-color: #3d3d3d;
                text-align: center;
                color: white;
                font-size: 10pt;
            }
            QProgressBar::chunk {
                background-color: rgb(13, 71, 161);
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Buttons
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        self.start_button = CustomButton(
            "Start",
            tooltip="Transfer starten (Strg+Enter)"
        )
        
        self.stop_button = CustomButton(
            "Transfer abbrechen",
            tooltip="Transfer abbrechen (Strg+Esc)"
        )
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: black;
                border: 1px solid gray;
                padding: 8px 15px;
                font-size: 10pt;
                min-width: 120px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        
        layout.addWidget(button_widget)
        
        # Copyright
        copyright_label = QLabel("TheGeekFreaks - Alexander Zuber-Jatzke 2025")
        copyright_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 9pt;
            }
        """)
        copyright_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(copyright_label)
