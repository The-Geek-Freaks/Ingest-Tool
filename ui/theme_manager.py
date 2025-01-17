from PyQt5.QtCore import QObject, pyqtSignal
from enum import Enum

class Theme(Enum):
    LIGHT = "light"
    DARK = "dark"

class ThemeManager(QObject):
    theme_changed = pyqtSignal(Theme)
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ThemeManager, cls).__new__(cls)
            cls._instance._theme = Theme.DARK  # Default theme
        return cls._instance
        
    def __init__(self):
        if not self._initialized:
            super().__init__()
            self._initialized = True
    
    @property
    def current_theme(self) -> Theme:
        return self._theme
        
    def toggle_theme(self):
        self._theme = Theme.LIGHT if self._theme == Theme.DARK else Theme.DARK
        # Aktualisiere StyleHelper Farben
        from ui.style_helper import StyleHelper
        StyleHelper.update_colors()
        self.theme_changed.emit(self._theme)
        
    def get_stylesheet(self) -> str:
        if self._theme == Theme.DARK:
            return """
            QMainWindow, QDialog, QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QPushButton {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
            QPushButton:pressed {
                background-color: #5d5d5d;
            }
            QLabel {
                color: #ffffff;
            }
            QGroupBox {
                border: 1px solid #555555;
                border-radius: 3px;
                margin-top: 0.5em;
                color: #ffffff;
            }
            QGroupBox::title {
                color: #ffffff;
            }
            QLineEdit {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
            }
            QTextEdit {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
            }
            QComboBox {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
            }
            QComboBox:hover {
                background-color: #4d4d4d;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QProgressBar {
                border: 1px solid #555555;
                border-radius: 3px;
                background-color: #3d3d3d;
                color: #ffffff;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
            }
            QScrollBar:vertical {
                background-color: #2b2b2b;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #3d3d3d;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QScrollBar:horizontal {
                background-color: #2b2b2b;
                height: 12px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background-color: #3d3d3d;
                min-width: 20px;
                border-radius: 6px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
            }
            """
        else:
            return """
            QMainWindow, QDialog, QWidget {
                background-color: #ffffff;
                color: #212529;
            }
            QPushButton {
                background-color: #f8f9fa;
                color: #212529;
                border: 1px solid #dee2e6;
                border-radius: 3px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
            QLabel {
                color: #212529;
            }
            QGroupBox {
                border: 1px solid #dee2e6;
                border-radius: 3px;
                margin-top: 0.5em;
                color: #212529;
            }
            QGroupBox::title {
                color: #212529;
            }
            QLineEdit {
                background-color: #ffffff;
                color: #212529;
                border: 1px solid #dee2e6;
                border-radius: 3px;
                padding: 5px;
            }
            QTextEdit {
                background-color: #ffffff;
                color: #212529;
                border: 1px solid #dee2e6;
                border-radius: 3px;
            }
            QComboBox {
                background-color: #ffffff;
                color: #212529;
                border: 1px solid #dee2e6;
                border-radius: 3px;
                padding: 5px;
            }
            QComboBox:hover {
                background-color: #f8f9fa;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #212529;
                border: 1px solid #dee2e6;
            }
            QProgressBar {
                border: 1px solid #dee2e6;
                border-radius: 3px;
                background-color: #ffffff;
                color: #212529;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
            }
            QScrollBar:vertical {
                background-color: #f8f9fa;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #dee2e6;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QScrollBar:horizontal {
                background-color: #f8f9fa;
                height: 12px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background-color: #dee2e6;
                min-width: 20px;
                border-radius: 6px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
            }
            """
