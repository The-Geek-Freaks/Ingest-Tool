#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Zentrale Style-Definitionen für die Anwendung."""

from PyQt5.QtWidgets import QWidget, QApplication, QStyleFactory
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt
from ui.theme_manager import ThemeManager, Theme

class StyleHelper:
    """Helper-Klasse für Style-Definitionen."""
    
    # Hauptfarben
    BACKGROUND = "#f8f9fa"           # Heller Hintergrund
    SURFACE = "#ffffff"              # Weiß für Karten/Widgets
    SURFACE_LIGHT = "#f1f3f5"        # Hellgrau für Hover
    SURFACE_HOVER = "#e9ecef"        # Hover-Effekt
    ACCENT = "#2196F3"               # Blau als Akzentfarbe
    ACCENT_LIGHT = "#90caf9"         # Helles Blau
    BORDER = "#dee2e6"               # Hellgrau für Rahmen
    
    # Textfarben
    TEXT = "#212529"                 # Dunkelgrau
    TEXT_SECONDARY = "#6c757d"       # Mittleres Grau
    
    # Status-Farben
    SUCCESS = "#28a745"              # Grün
    WARNING = "#ffc107"              # Gelb
    ERROR = "#dc3545"                # Rot
    INFO = "#17a2b8"                 # Türkis
    PRIMARY = "#2196F3"              # Blau
    PRIMARY_HOVER = "#1976D2"        # Dunkleres Blau
    
    @classmethod
    def update_colors(cls):
        """Aktualisiert die Farben basierend auf dem aktuellen Theme."""
        theme_manager = ThemeManager()
        if theme_manager.current_theme == Theme.LIGHT:
            cls.BACKGROUND = "#ffffff"
            cls.SURFACE = "#f8f9fa"
            cls.SURFACE_LIGHT = "#f1f3f5"
            cls.SURFACE_HOVER = "#e9ecef"
            cls.ACCENT = "#2196F3"
            cls.ACCENT_LIGHT = "#90caf9"
            cls.BORDER = "#dee2e6"
            cls.TEXT = "#212529"
            cls.TEXT_SECONDARY = "#6c757d"
            cls.SUCCESS = "#28a745"
            cls.WARNING = "#ffc107"
            cls.ERROR = "#dc3545"
            cls.INFO = "#17a2b8"
        else:
            cls.BACKGROUND = "#2b2b2b"
            cls.SURFACE = "#3d3d3d"
            cls.SURFACE_LIGHT = "#4d4d4d"
            cls.SURFACE_HOVER = "#5d5d5d"
            cls.ACCENT = "#2196F3"
            cls.ACCENT_LIGHT = "#90caf9"
            cls.BORDER = "#555555"
            cls.TEXT = "#ffffff"
            cls.TEXT_SECONDARY = "#cccccc"
            cls.SUCCESS = "#28a745"
            cls.WARNING = "#ffc107"
            cls.ERROR = "#dc3545"
            cls.INFO = "#17a2b8"
    
    @staticmethod
    def apply_theme(app: QApplication, theme: str = 'dark'):
        """Wendet ein Theme auf die Anwendung an.
        
        Args:
            app: Die QApplication-Instanz
            theme: Das zu verwendende Theme ('light', 'dark', oder 'system')
        """
        if theme == 'system':
            app.setStyle(QStyleFactory.create('Fusion'))
            return
            
        # Basis-Palette erstellen
        palette = QPalette()
        
        if theme == 'dark':
            # Dunkles Theme
            StyleHelper.update_colors()
            palette.setColor(QPalette.Window, QColor(StyleHelper.BACKGROUND))
            palette.setColor(QPalette.WindowText, QColor(StyleHelper.TEXT))
            palette.setColor(QPalette.Base, QColor(StyleHelper.SURFACE))
            palette.setColor(QPalette.AlternateBase, QColor(StyleHelper.SURFACE_LIGHT))
            palette.setColor(QPalette.ToolTipBase, QColor(StyleHelper.SURFACE))
            palette.setColor(QPalette.ToolTipText, QColor(StyleHelper.TEXT))
            palette.setColor(QPalette.Text, QColor(StyleHelper.TEXT))
            palette.setColor(QPalette.Button, QColor(StyleHelper.SURFACE))
            palette.setColor(QPalette.ButtonText, QColor(StyleHelper.TEXT))
            palette.setColor(QPalette.BrightText, QColor(StyleHelper.TEXT))
            palette.setColor(QPalette.Link, QColor(StyleHelper.ACCENT))
            palette.setColor(QPalette.Highlight, QColor(StyleHelper.ACCENT))
            palette.setColor(QPalette.HighlightedText, QColor(StyleHelper.TEXT))
        
        app.setPalette(palette)
        app.setStyle(QStyleFactory.create('Fusion'))
    
    @staticmethod
    def style_combobox(combobox):
        """Wendet das Style auf eine ComboBox an."""
        StyleHelper.update_colors()
        combobox.setStyleSheet(f"""
            QComboBox {{
                background-color: {StyleHelper.SURFACE};
                color: {StyleHelper.TEXT};
                border: 1px solid {StyleHelper.BORDER};
                border-radius: 3px;
                padding: 5px;
                min-width: 100px;
            }}
            QComboBox:hover {{
                background-color: {StyleHelper.SURFACE_LIGHT};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {StyleHelper.SURFACE};
                color: {StyleHelper.TEXT};
                selection-background-color: {StyleHelper.SURFACE_LIGHT};
                selection-color: {StyleHelper.TEXT};
                border: 1px solid {StyleHelper.BORDER};
            }}
        """)
    
    @staticmethod
    def apply_dark_theme(widget):
        """Wendet das dunkle Theme auf ein Widget an."""
        StyleHelper.update_colors()
        style = f"""
            QMainWindow, QDialog {{
                background-color: {StyleHelper.BACKGROUND};
                color: {StyleHelper.TEXT};
            }}
            
            QWidget {{
                background-color: {StyleHelper.BACKGROUND};
                color: {StyleHelper.TEXT};
                border: none;
            }}
            
            QPushButton {{
                background-color: {StyleHelper.SURFACE};
                color: {StyleHelper.TEXT};
                border: 1px solid {StyleHelper.BORDER};
                border-radius: 3px;
                padding: 5px;
                min-width: 80px;
            }}
            
            QPushButton:hover {{
                background-color: {StyleHelper.SURFACE_LIGHT};
            }}
            
            QPushButton:disabled {{
                background-color: {StyleHelper.BACKGROUND};
                color: {StyleHelper.TEXT_SECONDARY};
                border: 1px solid {StyleHelper.BORDER};
            }}
            
            QLineEdit, QTextEdit, QComboBox {{
                background-color: {StyleHelper.SURFACE};
                color: {StyleHelper.TEXT};
                border: 1px solid {StyleHelper.BORDER};
                border-radius: 3px;
                padding: 5px;
            }}
            
            QComboBox::drop-down {{
                border: none;
            }}
            
            QListWidget {{
                background-color: {StyleHelper.SURFACE};
                color: {StyleHelper.TEXT};
                border: 1px solid {StyleHelper.BORDER};
                border-radius: 3px;
            }}
            
            QListWidget::item {{
                padding: 5px;
            }}
            
            QListWidget::item:hover {{
                background-color: {StyleHelper.SURFACE_LIGHT};
            }}
            
            QGroupBox {{
                border: 1px solid {StyleHelper.BORDER};
                border-radius: 3px;
                margin-top: 1em;
                padding: 5px;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
                color: {StyleHelper.TEXT};
            }}
            
            QScrollBar:vertical {{
                background-color: {StyleHelper.BACKGROUND};
                width: 8px;
                margin: 0px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {StyleHelper.ACCENT};
                min-height: 20px;
                border-radius: 4px;
            }}
            
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar:horizontal {{
                background-color: {StyleHelper.BACKGROUND};
                height: 8px;
                margin: 0px;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: {StyleHelper.ACCENT};
                min-width: 20px;
                border-radius: 4px;
            }}
            
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
            
            QCheckBox {{
                color: {StyleHelper.TEXT};
            }}
            
            QCheckBox::indicator {{
                width: 13px;
                height: 13px;
                border: 1px solid {StyleHelper.BORDER};
                border-radius: 2px;
                background-color: {StyleHelper.SURFACE};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {StyleHelper.ACCENT};
            }}
            
            QProgressBar {{
                border: 1px solid {StyleHelper.BORDER};
                border-radius: 2px;
                text-align: center;
                background-color: {StyleHelper.BACKGROUND};
                height: 12px;
            }}
            
            QProgressBar::chunk {{
                background-color: {StyleHelper.ACCENT};
            }}
        """
        widget.setStyleSheet(style)

    @classmethod
    def get_main_window_style(cls) -> str:
        """Stil für das Hauptfenster."""
        StyleHelper.update_colors()
        return f"""
            QMainWindow {{
                background-color: {cls.BACKGROUND};
            }}
        """
    
    @classmethod
    def get_widget_style(cls) -> str:
        """Basis-Stil für Widgets."""
        StyleHelper.update_colors()
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
        StyleHelper.update_colors()
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
        StyleHelper.update_colors()
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
        StyleHelper.update_colors()
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

    @staticmethod
    def style_button(button):
        """Wendet einheitliches Styling auf einen Button an."""
        StyleHelper.update_colors()
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
        StyleHelper.update_colors()
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
        StyleHelper.update_colors()
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
        StyleHelper.update_colors()
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
        StyleHelper.update_colors()
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
        StyleHelper.update_colors()
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
        StyleHelper.update_colors()
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
        StyleHelper.update_colors()
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
        StyleHelper.update_colors()
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
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
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
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
            }
        """)

    @staticmethod
    def style_combobox(combobox):
        """Wendet das Style auf eine ComboBox an."""
        StyleHelper.update_colors()
        combobox.setStyleSheet(f"""
            QComboBox {{
                background-color: {StyleHelper.SURFACE};
                color: {StyleHelper.TEXT};
                border: 1px solid {StyleHelper.BORDER};
                border-radius: 3px;
                padding: 5px;
                min-width: 100px;
            }}
            QComboBox:hover {{
                background-color: {StyleHelper.SURFACE_LIGHT};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {StyleHelper.SURFACE};
                color: {StyleHelper.TEXT};
                selection-background-color: {StyleHelper.SURFACE_LIGHT};
                selection-color: {StyleHelper.TEXT};
                border: 1px solid {StyleHelper.BORDER};
            }}
        """)

    @staticmethod
    def get_header_style():
        """Gibt den einheitlichen Stil für Widget-Header zurück."""
        StyleHelper.update_colors()
        return f"""
            color: {StyleHelper.TEXT};
            font-weight: bold;
            padding: 5px;
            background-color: {StyleHelper.BACKGROUND};
            border: 1px solid {StyleHelper.BORDER};
            border-radius: 4px;
        """

    @staticmethod
    def get_group_box_header_style():
        """Gibt den einheitlichen Stil für GroupBox-Header zurück."""
        StyleHelper.update_colors()
        return f"""
            QGroupBox {{
                border: 1px solid {StyleHelper.BORDER};
                border-radius: 4px;
                margin-top: 30px;  
                margin-bottom: 10px;  
                padding: 15px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                background-color: {StyleHelper.BACKGROUND};
                color: {StyleHelper.TEXT};
                font-weight: bold;
                padding: 8px 12px;  
                border: 1px solid {StyleHelper.BORDER};
                border-radius: 4px;
                position: absolute;
                top: -20px;
                left: 15px;
            }}
        """

    @staticmethod
    def get_combo_box_style():
        """Gibt das Style-Sheet für ComboBoxen zurück."""
        StyleHelper.update_colors()
        return f"""
            QComboBox {{
                background-color: {StyleHelper.SURFACE};
                color: {StyleHelper.TEXT};
                border: 1px solid {StyleHelper.BORDER};
                border-radius: 3px;
                padding: 5px 25px 5px 10px;  
                min-width: 120px;
            }}
            QComboBox:hover {{
                background-color: {StyleHelper.SURFACE_LIGHT};
                border-color: {StyleHelper.ACCENT};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
                padding-right: 5px;
            }}
            QComboBox::down-arrow {{
                image: url(resources/icons/dropdown.svg);
                width: 12px;
                height: 12px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {StyleHelper.SURFACE};
                color: {StyleHelper.TEXT};
                border: 1px solid {StyleHelper.BORDER};
                selection-background-color: {StyleHelper.SURFACE_LIGHT};
                selection-color: {StyleHelper.TEXT};
                padding: 5px;
            }}
            QComboBox QLineEdit {{
                background-color: {StyleHelper.SURFACE};
                color: {StyleHelper.TEXT};
                border: none;
                padding: 0;
            }}
        """

    @staticmethod
    def get_button_style():
        """Gibt den einheitlichen Stil für Buttons zurück."""
        StyleHelper.update_colors()
        return f"""
            QPushButton {{
                background-color: {StyleHelper.SURFACE};
                color: {StyleHelper.TEXT};
                border: 1px solid {StyleHelper.BORDER};
                border-radius: 3px;
                padding: 5px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {StyleHelper.SURFACE_LIGHT};
            }}
        """

    @staticmethod
    def get_list_widget_style():
        """Gibt den einheitlichen Stil für ListWidgets zurück."""
        StyleHelper.update_colors()
        return f"""
            QListWidget {{
                background-color: {StyleHelper.SURFACE};
                color: {StyleHelper.TEXT};
                border: 1px solid {StyleHelper.BORDER};
                border-radius: 3px;
                padding: 5px;
            }}
            QListWidget::item {{
                padding: 5px;
            }}
            QListWidget::item:selected {{
                background-color: {StyleHelper.SURFACE_LIGHT};
            }}
            QListWidget::item:hover {{
                background-color: {StyleHelper.SURFACE_LIGHT};
            }}
        """

    @staticmethod
    def get_transfer_widget_style():
        """Gibt den einheitlichen Stil für das Transfer-Widget zurück."""
        return """
            QWidget#transfer_container {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
            }
            
            QLabel#empty_label {
                color: #666;
                font-size: 14px;
                padding: 20px;
            }
            
            QListWidget {
                border: none;
                background-color: transparent;
            }
            
            QListWidget::item {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                margin-bottom: 5px;
                padding: 5px;
            }
            
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
            
            QProgressBar {
                border: 1px solid #e0e0e0;
                border-radius: 2px;
                text-align: center;
                background-color: #f5f5f5;
            }
            
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 2px;
            }
        """

    @staticmethod
    def get_transfer_item_style():
        """Gibt das Style-Sheet für Transfer-Items zurück."""
        StyleHelper.update_colors()
        return f"""
            QWidget#transferItem {{
                background-color: {StyleHelper.SURFACE};
                border: 1px solid {StyleHelper.BORDER};
                border-radius: 4px;
                padding: 8px;
            }}
            
            QProgressBar {{
                border: none;
                background-color: {StyleHelper.SURFACE_LIGHT};
                border-radius: 9px;
                min-height: 18px;
                text-align: center;
            }}
            
            QProgressBar::chunk {{
                background-color: {StyleHelper.PRIMARY};
                border-radius: 9px;
            }}
            
            QLabel {{
                color: {StyleHelper.TEXT};
                font-size: 12px;
                min-height: 16px;
                padding: 2px 0;
            }}
            
            QLabel#speedLabel {{
                color: {StyleHelper.TEXT_SECONDARY};
            }}
            
            QPushButton {{
                background-color: {StyleHelper.SURFACE};
                border: 1px solid {StyleHelper.BORDER};
                border-radius: 3px;
                padding: 4px 8px;
                min-width: 70px;
                color: {StyleHelper.TEXT};
            }}
            
            QPushButton:hover {{
                background-color: {StyleHelper.SURFACE_HOVER};
            }}
            
            QPushButton:pressed {{
                background-color: {StyleHelper.SURFACE_LIGHT};
            }}
        """

    @classmethod
    def get_list_widget_style(cls) -> str:
        """Stil für ListWidgets."""
        cls.update_colors()
        return f"""
            QListWidget {{
                background-color: {cls.BACKGROUND};
                color: {cls.TEXT};
                border: 1px solid {cls.BORDER};
                border-radius: 3px;
                padding: 5px;
            }}
            QListWidget::item {{
                background-color: {cls.SURFACE};
                border: 1px solid {cls.BORDER};
                border-radius: 2px;
                margin: 2px;
                padding: 5px;
                color: {cls.TEXT};
            }}
            QListWidget::item:selected {{
                background-color: {cls.ACCENT};
                border: 1px solid {cls.ACCENT_LIGHT};
                color: white;
            }}
            QListWidget::item:hover {{
                background-color: {cls.SURFACE_HOVER};
                border: 1px solid {cls.BORDER};
            }}
        """
    
    @classmethod
    def get_button_style(cls) -> str:
        """Stil für Buttons."""
        cls.update_colors()
        return f"""
            QPushButton {{
                background-color: {cls.SURFACE};
                color: {cls.TEXT};
                border: 1px solid {cls.BORDER};
                border-radius: 3px;
                padding: 5px 10px;
            }}
            QPushButton:hover {{
                background-color: {cls.SURFACE_HOVER};
                border: 1px solid {cls.BORDER};
            }}
            QPushButton:pressed {{
                background-color: {cls.SURFACE_LIGHT};
            }}
            QPushButton:disabled {{
                background-color: {cls.SURFACE};
                color: {cls.TEXT_SECONDARY};
                border: 1px solid {cls.BORDER};
            }}
        """
    
    @classmethod
    def get_combobox_style(cls) -> str:
        """Stil für ComboBoxen."""
        cls.update_colors()
        return f"""
            QComboBox {{
                background-color: {cls.SURFACE};
                color: {cls.TEXT};
                border: 1px solid {cls.BORDER};
                border-radius: 3px;
                padding: 5px;
            }}
            QComboBox:hover {{
                background-color: {cls.SURFACE_HOVER};
                border: 1px solid {cls.BORDER};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {cls.SURFACE};
                color: {cls.TEXT};
                border: 1px solid {cls.BORDER};
                selection-background-color: {cls.ACCENT};
                selection-color: white;
            }}
        """
    
    @classmethod
    def get_lineedit_style(cls) -> str:
        """Stil für LineEdits."""
        cls.update_colors()
        return f"""
            QLineEdit {{
                background-color: {cls.SURFACE};
                color: {cls.TEXT};
                border: 1px solid {cls.BORDER};
                border-radius: 3px;
                padding: 5px;
            }}
            QLineEdit:focus {{
                border: 1px solid {cls.ACCENT};
            }}
            QLineEdit:disabled {{
                background-color: {cls.SURFACE};
                color: {cls.TEXT_SECONDARY};
                border: 1px solid {cls.BORDER};
            }}
        """
    
    @classmethod
    def get_progressbar_style(cls) -> str:
        """Stil für ProgressBars."""
        cls.update_colors()
        return f"""
            QProgressBar {{
                border: 1px solid {cls.BORDER};
                border-radius: 3px;
                background-color: {cls.SURFACE};
                text-align: center;
                color: {cls.TEXT};
            }}
            QProgressBar::chunk {{
                background-color: {cls.ACCENT};
                border-radius: 2px;
            }}
        """
