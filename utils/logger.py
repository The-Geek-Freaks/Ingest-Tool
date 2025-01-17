#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
from datetime import datetime
from PyQt5.QtWidgets import (
    QTextEdit, QVBoxLayout, QMenu, QFileDialog, 
    QInputDialog, QMessageBox
)
from PyQt5.QtGui import QTextCharFormat, QBrush, QColor
from PyQt5.QtCore import Qt, QObject, pyqtSignal

from config.constants import LOG_VERZEICHNIS, LOG_DATEI

# Erstelle Log-Verzeichnis falls nicht vorhanden
os.makedirs(LOG_VERZEICHNIS, exist_ok=True)

class ThreadSafeLogBridge(QObject):
    """Thread-sichere Brücke für Logging-Nachrichten."""
    
    log_message_received = pyqtSignal(str, QTextCharFormat)
    
    def __init__(self, parent=None):
        super().__init__(parent)

class QTextEditLogHandler(logging.Handler):
    """Ein angepasster Handler für QTextEdit mit Formatierung."""

    def __init__(self, parent=None):
        super().__init__()
        self.widget = QTextEdit(parent)
        self.widget.setReadOnly(True)
        
        # Erstelle Thread-Bridge
        self.bridge = ThreadSafeLogBridge(self.widget)
        self.bridge.log_message_received.connect(self._append_text)
        
        # Format für verschiedene Log-Level
        self.formats = {
            logging.DEBUG: self._create_format(QColor("#666666")),  # Grau
            logging.INFO: self._create_format(QColor("#000000")),   # Schwarz
            logging.WARNING: self._create_format(QColor("#FFA500")), # Orange
            logging.ERROR: self._create_format(QColor("#FF0000")),   # Rot
            logging.CRITICAL: self._create_format(QColor("#FF0000"), True)  # Rot, fett
        }

    def _create_format(self, color, bold=False):
        """Erstellt ein QTextCharFormat mit der angegebenen Farbe."""
        fmt = QTextCharFormat()
        fmt.setForeground(QBrush(color))
        if bold:
            fmt.setFontWeight(75)  # Bold
        return fmt

    def emit(self, record):
        try:
            msg = self.format(record)
            fmt = self.formats.get(record.levelno, self.formats[logging.INFO])
            self.bridge.log_message_received.emit(msg, fmt)
        except Exception:
            self.handleError(record)

    def _append_text(self, msg, fmt):
        """Fügt formatierten Text thread-sicher hinzu."""
        # Setze das Format
        self.widget.setCurrentCharFormat(fmt)
        # Füge Text hinzu
        self.widget.append(msg)
        # Scrolle zum Ende
        scrollbar = self.widget.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

class ProtokollWidget(QTextEdit):
    """Erweitertes QTextEdit für formatierte Protokollausgabe."""
    
    # Log-Level Definitionen
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    DEBUG = "DEBUG"
    
    # Farben für verschiedene Log-Level
    LEVEL_COLORS = {
        INFO: "#89d0ff",      # Heltes Blau
        WARNING: "#ffd700",   # Gold
        ERROR: "#ff6b6b",     # Rot
        DEBUG: "#98c379",     # Grün
    }
    
    def __init__(self, parent=None, max_entries=1000):
        super().__init__(parent)
        self.max_entries = max_entries
        self.log_entries = []
        self.current_group = None
        self.group_entries = {}
        self.expanded_groups = set()
        self.date_format = "%H:%M:%S"
        self.search_text = ""
        self.search_results = []
        self.current_search_index = -1
        
        # Layout und Styling
        self.setReadOnly(True)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 4px;
                selection-background-color: #264f78;
            }
        """)
        
        # Kontextmenü aktivieren
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        # Logging-Konfiguration
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        
        # Formatierung
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console Handler
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(formatter)
        self.logger.addHandler(console)
        
        # File Handler
        if not os.path.exists(LOG_VERZEICHNIS):
            os.makedirs(LOG_VERZEICHNIS)
            
        log_file = os.path.join(LOG_VERZEICHNIS, f"app_{datetime.now():%Y-%m-%d}.log")
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # QTextEditLogHandler
        self.text_edit_handler = QTextEditLogHandler(self)
        self.text_edit_handler.setFormatter(formatter)
        self.logger.addHandler(self.text_edit_handler)

    def log(self, text: str, level: str = INFO, details: dict = None):
        """Fügt einen formatierten Log-Eintrag hinzu."""
        if len(self.log_entries) >= self.max_entries:
            remove_count = len(self.log_entries) - self.max_entries + 1
            self.log_entries = self.log_entries[remove_count:]
            
        timestamp = datetime.now().strftime(self.date_format)
        entry = {
            'timestamp': timestamp,
            'level': level,
            'text': text,
            'details': details or {},
            'group': self.current_group
        }
        self.log_entries.append(entry)
        
        if self.current_group:
            if self.current_group not in self.group_entries:
                self.group_entries[self.current_group] = []
            self.group_entries[self.current_group].append(entry)
        
        self.logger.log(getattr(logging, level), text)

    def _show_context_menu(self, position):
        """Zeigt das Kontextmenü an der angegebenen Position."""
        menu = QMenu(self)
        
        # Standard-Aktionen
        copy_action = menu.addAction("Kopieren")
        copy_action.triggered.connect(self.copy)
        
        select_all_action = menu.addAction("Alles auswählen")
        select_all_action.triggered.connect(self.selectAll)
        
        menu.addSeparator()
        
        # Log-spezifische Aktionen
        save_action = menu.addAction("Log speichern...")
        save_action.triggered.connect(self.save_log)
        
        clear_action = menu.addAction("Log leeren")
        clear_action.triggered.connect(self.clear_log)
        
        menu.addSeparator()
        
        # Suchen
        search_action = menu.addAction("Suchen...")
        search_action.triggered.connect(self.show_search_dialog)
        
        if self.search_text:
            next_action = menu.addAction("Weitersuchen")
            next_action.triggered.connect(self.find_next)
            prev_action = menu.addAction("Rückwärts suchen")
            prev_action.triggered.connect(self.find_previous)
        
        menu.exec_(self.mapToGlobal(position))

    def save_log(self):
        """Speichert das Log als Textdatei."""
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Log speichern",
            "",
            "Text Dateien (*.txt);;Alle Dateien (*.*)"
        )
        if file_name:
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(self.toPlainText())

    def clear_log(self):
        """Löscht das Log."""
        self.log_entries = []
        self.clear()

    def show_search_dialog(self):
        """Zeigt den Suchdialog."""
        text, ok = QInputDialog.getText(
            self,
            "Suchen",
            "Suchtext:",
            text=self.search_text
        )
        if ok and text:
            self.search_text = text
            self.search_results = []
            self.current_search_index = -1
            
            # Suche in allen Einträgen
            for i, entry in enumerate(self.log_entries):
                if (
                    self.search_text.lower() in entry['text'].lower() or
                    any(
                        self.search_text.lower() in str(value).lower()
                        for value in entry['details'].values()
                        if entry['details']
                    )
                ):
                    self.search_results.append(i)
            
            if self.search_results:
                self.find_next()
            else:
                QMessageBox.information(
                    self,
                    "Suchen",
                    f'Keine Treffer für "{self.search_text}"'
                )

    def find_next(self):
        """Springt zum nächsten Suchergebnis."""
        if not self.search_results:
            return
        self.current_search_index = (self.current_search_index + 1) % len(self.search_results)
        self._highlight_search_result()

    def find_previous(self):
        """Springt zum vorherigen Suchergebnis."""
        if not self.search_results:
            return
        self.current_search_index = (
            self.current_search_index - 1
            if self.current_search_index > 0
            else len(self.search_results) - 1
        )
        self._highlight_search_result()

    def _highlight_search_result(self):
        """Hebt das aktuelle Suchergebnis hervor."""
        if not self.search_results:
            return
            
        index = self.search_results[self.current_search_index]
        entry = self.log_entries[index]
        
        # Stelle sicher, dass die Gruppe erweitert ist
        if entry['group']:
            self.expanded_groups.add(entry['group'])
        
        # Aktualisiere die Anzeige
        self.clear()
        for entry in self.log_entries:
            self.log(entry['text'], entry['level'], entry['details'])
        
        # Markiere den gefundenen Text
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.Start)
        
        found = False
        while not found and cursor.movePosition(QTextCursor.NextBlock):
            block_text = cursor.block().text()
            if self.search_text.lower() in block_text.lower():
                start = block_text.lower().find(self.search_text.lower())
                cursor.movePosition(QTextCursor.StartOfBlock)
                cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, start)
                cursor.movePosition(
                    QTextCursor.Right,
                    QTextCursor.KeepAnchor,
                    len(self.search_text)
                )
                
                format = QTextCharFormat()
                format.setBackground(QBrush(QColor("#264f78")))
                format.setForeground(QColor("#ffffff"))
                cursor.mergeCharFormat(format)
                
                self.setTextCursor(cursor)
                self.ensureCursorVisible()
                found = True

# Globaler Exception Handler
def setup_exception_handler():
    """Richtet einen globalen Exception Handler ein."""
    def exception_hook(exctype, value, traceback):
        logging.exception("Unbehandelte Ausnahme", exc_info=(exctype, value, traceback))
        sys.__excepthook__(exctype, value, traceback)
    
    sys.excepthook = exception_hook
