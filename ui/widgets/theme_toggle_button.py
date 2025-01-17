from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt
from ui.theme_manager import ThemeManager, Theme

class ThemeToggleButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_manager = ThemeManager()
        self.setFixedSize(30, 30)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Theme wechseln")
        self._update_icon()
        
        # Connect signals
        self.clicked.connect(self._on_clicked)
        self.theme_manager.theme_changed.connect(self._update_icon)
        
    def _on_clicked(self):
        self.theme_manager.toggle_theme()
        
    def _update_icon(self):
        # Set the button text based on current theme
        self.setText("🌙" if self.theme_manager.current_theme == Theme.LIGHT else "☀️")
        self.setStyleSheet("""
            ThemeToggleButton {
                border: none;
                background: transparent;
                font-size: 16px;
            }
            ThemeToggleButton:hover {
                background: rgba(128, 128, 128, 0.1);
                border-radius: 15px;
            }
        """)
