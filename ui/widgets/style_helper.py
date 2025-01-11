#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QStyleFactory, QWidget, QPushButton, QProgressBar, QListWidget, QComboBox

class StyleHelper:
    """Hilfsklasse für das Styling der Anwendung."""
    
    @staticmethod
    def apply_theme(app: QApplication, theme: str = 'system'):
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
            palette.setColor(QPalette.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.WindowText, Qt.white)
            palette.setColor(QPalette.Base, QColor(25, 25, 25))
            palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ToolTipBase, Qt.white)
            palette.setColor(QPalette.ToolTipText, Qt.white)
            palette.setColor(QPalette.Text, Qt.white)
            palette.setColor(QPalette.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ButtonText, Qt.white)
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.HighlightedText, Qt.black)
            
        else:  # Light Theme
            palette.setColor(QPalette.Window, QColor(240, 240, 240))
            palette.setColor(QPalette.WindowText, Qt.black)
            palette.setColor(QPalette.Base, QColor(255, 255, 255))
            palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
            palette.setColor(QPalette.ToolTipBase, Qt.white)
            palette.setColor(QPalette.ToolTipText, Qt.black)
            palette.setColor(QPalette.Text, Qt.black)
            palette.setColor(QPalette.Button, QColor(240, 240, 240))
            palette.setColor(QPalette.ButtonText, Qt.black)
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, QColor(0, 0, 255))
            palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
            palette.setColor(QPalette.HighlightedText, Qt.white)
            
        # Theme anwenden
        app.setStyle(QStyleFactory.create('Fusion'))
        app.setPalette(palette)
        
    @staticmethod
    def apply_dark_theme(widget: QWidget):
        """Wendet das dunkle Theme auf ein Widget an."""
        palette = QPalette()
        
        # Fenster-Hintergrund
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        
        # Widget-Hintergrund
        palette.setColor(QPalette.Base, QColor(42, 42, 42))
        palette.setColor(QPalette.AlternateBase, QColor(66, 66, 66))
        
        # Text
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.ButtonText, Qt.white)
        
        # Buttons
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        
        # Hervorhebungen
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        
        widget.setPalette(palette)
        
    @staticmethod
    def get_button_style(primary: bool = False) -> str:
        """Gibt den Style für einen Button zurück.
        
        Args:
            primary: Ob es sich um einen primären Button handelt
            
        Returns:
            Der CSS-Style für den Button
        """
        if primary:
            return """
                QPushButton {
                    background-color: #0078D7;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #1484D7;
                }
                QPushButton:pressed {
                    background-color: #006CC1;
                }
                QPushButton:disabled {
                    background-color: #CCCCCC;
                    color: #666666;
                }
            """
        else:
            return """
                QPushButton {
                    background-color: #F0F0F0;
                    border: 1px solid #CCCCCC;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #E5E5E5;
                }
                QPushButton:pressed {
                    background-color: #CCCCCC;
                }
                QPushButton:disabled {
                    background-color: #F5F5F5;
                    color: #999999;
                    border: 1px solid #E0E0E0;
                }
            """
            
    @staticmethod
    def style_button(button: QPushButton, primary: bool = False):
        """Stylt einen Button."""
        if primary:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #0d6efd;
                    color: white;
                    border: none;
                    padding: 5px 15px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #0b5ed7;
                }
                QPushButton:pressed {
                    background-color: #0a58ca;
                }
                QPushButton:disabled {
                    background-color: #6c757d;
                }
            """)
        else:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #6c757d;
                    color: white;
                    border: none;
                    padding: 5px 15px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #5c636a;
                }
                QPushButton:pressed {
                    background-color: #565e64;
                }
                QPushButton:disabled {
                    background-color: #adb5bd;
                }
            """)
            
    @staticmethod
    def get_progress_bar_style() -> str:
        """Gibt den Style für eine Fortschrittsleiste zurück.
        
        Returns:
            Der CSS-Style für die Fortschrittsleiste
        """
        return """
            QProgressBar {
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                text-align: center;
                padding: 1px;
                background-color: #F5F5F5;
            }
            QProgressBar::chunk {
                background-color: #0078D7;
                border-radius: 3px;
            }
        """
        
    @staticmethod
    def style_progress_bar(progress_bar: QProgressBar):
        """Stylt einen Fortschrittsbalken."""
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #e9ecef;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #0d6efd;
                border-radius: 3px;
            }
        """)
        
    @staticmethod
    def get_list_widget_style() -> str:
        """Gibt den Style für ein ListWidget zurück.
        
        Returns:
            Der CSS-Style für das ListWidget
        """
        return """
            QListWidget {
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 2px;
                background-color: white;
            }
            QListWidget::item {
                padding: 4px;
                border-bottom: 1px solid #EEEEEE;
            }
            QListWidget::item:selected {
                background-color: #0078D7;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #F0F0F0;
            }
        """

    @staticmethod
    def style_list_widget(list_widget: QListWidget):
        """Stylt eine ListWidget."""
        list_widget.setStyleSheet("""
            QListWidget {
                background-color: #2b2b2b;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
            }
            QListWidget::item {
                color: white;
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #0d6efd;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #343a40;
            }
        """)

    @staticmethod
    def style_combobox(combo: QComboBox):
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
