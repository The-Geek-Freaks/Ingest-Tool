"""
Log-Sektion der UI.
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit,
    QLabel
)

class LogSection(QWidget):
    """Sektion für die Log-Anzeige."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Richtet das UI der Sektion ein."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QLabel("Protokoll")
        header.setStyleSheet("font-weight: bold; color: white;")
        layout.addWidget(header)
        
        # Log Text
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #555;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.log_text)
        
        self.setLayout(layout)
        
    def log(self, message: str):
        """Fügt eine neue Nachricht zum Log hinzu."""
        self.log_text.append(message)
        
    def clear(self):
        """Löscht den Log."""
        self.log_text.clear()
