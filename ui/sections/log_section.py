"""
Log-Sektion der UI.
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit,
    QLabel
)
from ui.widgets.header_widget import HeaderWidget

class LogSection(QWidget):
    """Sektion für die Log-Anzeige."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Richtet das UI der Sektion ein."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header und Content in HeaderWidget
        log_widget = HeaderWidget("📝 Protokoll")
        
        # Log Text
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        log_widget.add_widget(self.log_text)
        
        layout.addWidget(log_widget)
        self.setLayout(layout)
        
    def log(self, message: str):
        """Fügt eine neue Nachricht zum Log hinzu."""
        self.log_text.append(message)
        
    def clear(self):
        """Löscht den Log."""
        self.log_text.clear()
