#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt

class StyleHelper:
    """Zentrale Style-Definitionen für die Anwendung."""
    
    # Hauptfarben
    BACKGROUND = "#1E1E1E"           # Dunkelgrau (Haupthintergrund)
    SURFACE = "#2D2D2D"              # Helleres Grau (Widget-Hintergrund)
    SURFACE_LIGHT = "#3D3D3D"        # Noch helleres Grau (Hover, Selected)
    ACCENT = "#6B7280"               # Mittleres Grau (Akzentfarbe)
    ACCENT_LIGHT = "#9CA3AF"         # Helles Grau
    BORDER = "#4D4D4D"               # Grau für Rahmen
    
    # Textfarben
    TEXT = "#FFFFFF"                 # Weiß
    TEXT_SECONDARY = "#A0A0A0"       # Hellgrau
    
    # Status-Farben
    SUCCESS = "#4CAF50"              # Grün
    WARNING = "#FF9800"              # Orange
    ERROR = "#F44336"                # Rot
    INFO = "#6B7280"                 # Grau (wie Akzentfarbe)
    
    DARK_PALETTE = {
        'window': BACKGROUND,
        'window-text': TEXT,
        'base': SURFACE,
        'alternate-base': SURFACE_LIGHT,
        'text': TEXT,
        'button': SURFACE,
        'button-text': TEXT,
        'bright-text': TEXT,
        'highlight': ACCENT,
        'highlight-text': BACKGROUND
    }
    
    @staticmethod
    def apply_dark_theme(widget):
        """Wendet das dunkle Theme auf ein Widget an."""
        # Erstelle Stylesheet
        style = f"""
            QMainWindow, QDialog {{
                background-color: {StyleHelper.DARK_PALETTE['window']};
                color: {StyleHelper.DARK_PALETTE['window-text']};
            }}
            
            QWidget {{
                background-color: {StyleHelper.DARK_PALETTE['window']};
                color: {StyleHelper.DARK_PALETTE['window-text']};
                border: none;
            }}
            
            QPushButton {{
                background-color: {StyleHelper.DARK_PALETTE['button']};
                color: {StyleHelper.DARK_PALETTE['button-text']};
                border: 1px solid {StyleHelper.DARK_PALETTE['highlight']};
                border-radius: 3px;
                padding: 5px;
                min-width: 80px;
            }}
            
            QPushButton:hover {{
                background-color: {StyleHelper.DARK_PALETTE['highlight']};
            }}
            
            QPushButton:pressed {{
                background-color: {StyleHelper.DARK_PALETTE['button']};
            }}
            
            QPushButton:disabled {{
                background-color: {StyleHelper.DARK_PALETTE['window']};
                color: {StyleHelper.DARK_PALETTE['window-text']};
                border: 1px solid {StyleHelper.DARK_PALETTE['window']};
            }}
            
            QLineEdit, QTextEdit, QComboBox, QSpinBox {{
                background-color: {StyleHelper.DARK_PALETTE['base']};
                color: {StyleHelper.DARK_PALETTE['text']};
                border: 1px solid {StyleHelper.DARK_PALETTE['highlight']};
                border-radius: 3px;
                padding: 2px 5px;
            }}
            
            QComboBox::drop-down {{
                border: none;
            }}
            
            QListWidget {{
                background-color: {StyleHelper.DARK_PALETTE['base']};
                color: {StyleHelper.DARK_PALETTE['text']};
                border: 1px solid {StyleHelper.DARK_PALETTE['highlight']};
                border-radius: 3px;
            }}
            
            QListWidget::item {{
                padding: 2px 5px;
            }}
            
            QListWidget::item:hover {{
                background-color: {StyleHelper.DARK_PALETTE['highlight']};
            }}
            
            QListWidget::item:selected {{
                background-color: {StyleHelper.DARK_PALETTE['button']};
            }}
            
            QProgressBar {{
                background-color: {StyleHelper.DARK_PALETTE['base']};
                color: {StyleHelper.DARK_PALETTE['text']};
                border: 1px solid {StyleHelper.DARK_PALETTE['highlight']};
                border-radius: 3px;
                text-align: center;
            }}
            
            QProgressBar::chunk {{
                background-color: {StyleHelper.DARK_PALETTE['highlight']};
            }}
            
            QCheckBox {{
                color: {StyleHelper.DARK_PALETTE['text']};
                spacing: 5px;
            }}
            
            QCheckBox::indicator {{
                width: 13px;
                height: 13px;
            }}
            
            QCheckBox::indicator:unchecked {{
                background-color: {StyleHelper.DARK_PALETTE['base']};
                border: 1px solid {StyleHelper.DARK_PALETTE['highlight']};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {StyleHelper.DARK_PALETTE['highlight']};
                border: 1px solid {StyleHelper.DARK_PALETTE['highlight']};
            }}
            
            QGroupBox {{
                border: 2px solid #999999;
                border-radius: 5px;
                margin-top: 1ex;
                padding: 10px;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
                color: #ffffff;
            }}
            
            QScrollBar:vertical {{
                background-color: {StyleHelper.DARK_PALETTE['base']};
                width: 12px;
                margin: 0;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {StyleHelper.DARK_PALETTE['highlight']};
                min-height: 20px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {StyleHelper.DARK_PALETTE['button']};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
                width: 0;
            }}
            
            QScrollBar:horizontal {{
                background-color: {StyleHelper.DARK_PALETTE['base']};
                height: 12px;
                margin: 0;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: {StyleHelper.DARK_PALETTE['highlight']};
                min-width: 20px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background-color: {StyleHelper.DARK_PALETTE['button']};
            }}
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                height: 0;
                width: 0;
            }}
            
            QTimeEdit {{
                background-color: {StyleHelper.DARK_PALETTE['base']};
                color: {StyleHelper.DARK_PALETTE['text']};
                border: 1px solid {StyleHelper.DARK_PALETTE['highlight']};
                border-radius: 3px;
                padding: 2px 5px;
            }}
        """
        
        # Wende Stylesheet an
        widget.setStyleSheet(style)

    @staticmethod
    def apply_dark_theme_old(widget: QWidget):
        """Wendet das dunkle Theme auf ein Widget an."""
        palette = QPalette()
        
        # Setze Farben für verschiedene Zustände
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
        
        widget.setPalette(palette)

    @staticmethod
    def style_button(button):
        """Wendet einheitliches Styling auf einen Button an."""
        button.setStyleSheet("""
            QPushButton {
                background-color: #2a82da;
                border: none;
                color: white;
                padding: 5px 15px;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #3d94ec;
            }
            QPushButton:pressed {
                background-color: #1e6cb8;
            }
            QPushButton:disabled {
                background-color: #666666;
            }
        """)

    @staticmethod
    def style_list_widget(list_widget):
        """Wendet einheitliches Styling auf ein ListWidget an."""
        list_widget.setStyleSheet("""
            QListWidget {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-radius: 3px;
            }
            QListWidget::item {
                color: white;
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #2a82da;
            }
            QListWidget::item:hover {
                background-color: #333333;
            }
        """)

    @staticmethod
    def style_progress_bar(progress_bar):
        """Wendet einheitliches Styling auf eine ProgressBar an."""
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #333333;
                border-radius: 3px;
                text-align: center;
                color: white;
                background-color: #1a1a1a;
            }
            QProgressBar::chunk {
                background-color: #2a82da;
                width: 10px;
                margin: 0.5px;
            }
        """)

    @staticmethod
    def style_text_edit(text_edit):
        """Wendet einheitliches Styling auf ein TextEdit an."""
        text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: white;
                border: 1px solid #333333;
                border-radius: 3px;
                padding: 5px;
            }
        """)

    @staticmethod
    def style_group_box(group_box):
        """Wendet einheitliches Styling auf eine GroupBox an."""
        group_box.setStyleSheet("""
            QGroupBox {
                border: 2px solid #999999;
                border-radius: 5px;
                margin-top: 1ex;
                padding: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
                color: #ffffff;
            }
        """)

    @staticmethod
    def style_check_box(check_box):
        """Wendet einheitliches Styling auf eine CheckBox an."""
        check_box.setStyleSheet("""
            QCheckBox {
                color: white;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 13px;
                height: 13px;
            }
            QCheckBox::indicator:unchecked {
                border: 1px solid #333333;
                background-color: #1a1a1a;
            }
            QCheckBox::indicator:checked {
                border: 1px solid #2a82da;
                background-color: #2a82da;
            }
        """)

    @staticmethod
    def style_combo_box(combo_box):
        """Wendet einheitliches Styling auf eine ComboBox an."""
        combo_box.setStyleSheet("""
            QComboBox {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-radius: 3px;
                color: white;
                padding: 3px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
            }
            QComboBox QAbstractItemView {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                selection-background-color: #2a82da;
                selection-color: white;
            }
        """)

    @staticmethod
    def style_line_edit(line_edit):
        """Wendet einheitliches Styling auf ein LineEdit an."""
        line_edit.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-radius: 3px;
                color: white;
                padding: 3px;
            }
            QLineEdit:focus {
                border: 1px solid #2a82da;
            }
        """)

    @staticmethod
    def style_scroll_area(scroll_area):
        """Wendet einheitliches Styling auf eine ScrollArea an."""
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-radius: 3px;
            }
            QScrollBar:vertical {
                border: none;
                background-color: #1a1a1a;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #333333;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QScrollBar:horizontal {
                border: none;
                background-color: #1a1a1a;
                height: 10px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background-color: #333333;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
            }
        """)

    @staticmethod
    def style_combobox(combo):
        """Styling für ComboBoxen.
        
        - Macht den Dropdown-Pfeil besser sichtbar
        - Vergrößert die Dropdown-Liste
        - Verbessert die Lesbarkeit
        """
        combo.setStyleSheet("""
            QComboBox {
                background-color: #2d2d2d;
                color: #ffffff;
                padding: 5px 30px 5px 10px;  
                border: 1px solid #555;
                border-radius: 3px;
                min-width: 6em;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
                padding-right: 5px;
            }
            
            QComboBox::down-arrow {
                border: none;
                background: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;  
                width: 0;
                height: 0;
                margin-right: 8px;
                margin-top: 3px;
            }
            
            QComboBox:hover {
                border-color: #0078d7;
            }
            
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: #ffffff;
                selection-background-color: #0078d7;
                selection-color: #ffffff;
                border: 1px solid #555;
                padding: 5px;
                min-height: 200px;
            }
            
            QComboBox QAbstractItemView::item {
                background-color: #2d2d2d;
                color: #ffffff;
                padding: 8px;
                min-height: 24px;
            }
            
            QComboBox QAbstractItemView::item:hover {
                background-color: #404040;
            }
            
            QComboBox QAbstractItemView::item:selected {
                background-color: #0078d7;
            }
        """)
        
        # Erhöhe die maximale Anzahl sichtbarer Items
        combo.setMaxVisibleItems(15)
        
        # Mache die ComboBox groß genug
        combo.setMinimumWidth(150)
        
        # Setze einen Platzhaltertext
        if combo.currentText() == "":
            combo.setPlaceholderText("Bitte auswählen")

    @classmethod
    def get_main_window_style(cls) -> str:
        """Stil für das Hauptfenster."""
        return f"""
            QMainWindow {{
                background-color: {cls.BACKGROUND};
            }}
        """
    
    @classmethod
    def get_widget_style(cls) -> str:
        """Basis-Stil für Widgets."""
        return f"""
            QWidget {{
                background-color: {cls.SURFACE};
                border: 1px solid {cls.BORDER};
                border-radius: 4px;
            }}
        """
    
    @classmethod
    def get_list_style(cls) -> str:
        """Stil für Listen."""
        return f"""
            QListWidget {{
                background-color: {cls.SURFACE};
                border: 1px solid {cls.BORDER};
                border-radius: 4px;
                padding: 4px;
            }}
            QListWidget::item {{
                background-color: transparent;
                padding: 0px;
                margin: 2px 0px;
            }}
            QListWidget::item:selected {{
                background-color: {cls.SURFACE_LIGHT};
            }}
            QListWidget::item:hover {{
                background-color: {cls.SURFACE_LIGHT};
            }}
        """
    
    @classmethod
    def get_scroll_bar_style(cls) -> str:
        """Stil für Scrollbars."""
        return f"""
            QScrollBar:vertical {{
                background-color: {cls.SURFACE};
                width: 12px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {cls.BORDER};
                min-height: 20px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {cls.ACCENT};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """
    
    @classmethod
    def get_button_style(cls) -> str:
        """Stil für Buttons."""
        return f"""
            QPushButton {{
                background-color: {cls.SURFACE};
                border: 1px solid {cls.BORDER};
                border-radius: 4px;
                padding: 6px 12px;
                color: {cls.TEXT};
            }}
            QPushButton:hover {{
                background-color: {cls.SURFACE_LIGHT};
                border-color: {cls.ACCENT};
            }}
            QPushButton:pressed {{
                background-color: {cls.ACCENT};
                color: {cls.BACKGROUND};
            }}
            QPushButton:disabled {{
                background-color: {cls.SURFACE};
                border-color: {cls.BORDER};
                color: {cls.TEXT_SECONDARY};
            }}
        """
