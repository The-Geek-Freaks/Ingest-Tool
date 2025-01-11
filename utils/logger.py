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
from PyQt5.QtGui import QTextCharFormat, QBrush, QColor, QTextCursor
from PyQt5.QtCore import Qt

from config.constants import LOG_VERZEICHNIS, LOG_DATEI

# Erstelle Log-Verzeichnis falls nicht vorhanden
os.makedirs(LOG_VERZEICHNIS, exist_ok=True)

# Logging-Konfiguration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DATEI, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class ProtokollWidget(QTextEdit):
    """Erweitertes QTextEdit für formatierte Protokollausgabe."""
    
    # Log-Level Definitionen
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    DEBUG = "DEBUG"
    
    # Farben für verschiedene Log-Level
    LEVEL_COLORS = {
        INFO: "#89d0ff",      # Helles Blau
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
        
        self._append_formatted_entry(entry)

    def _append_formatted_entry(self, entry):
        """Fügt einen formatierten Log-Eintrag hinzu."""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # Format für Zeitstempel
        format_time = QTextCharFormat()
        format_time.setForeground(QColor("#808080"))
        cursor.insertText(f"[{entry['timestamp']}] ", format_time)
        
        # Format für Level
        format_level = QTextCharFormat()
        format_level.setForeground(QColor(self.LEVEL_COLORS.get(entry['level'], "#ffffff")))
        cursor.insertText(f"[{entry['level']}] ", format_level)
        
        # Format für Gruppe
        if entry['group']:
            format_group = QTextCharFormat()
            format_group.setForeground(QColor("#0078d4"))
            cursor.insertText(f"[{entry['group']}] ", format_group)
        
        # Format für Text
        format_text = QTextCharFormat()
        format_text.setForeground(QColor("#ffffff"))
        cursor.insertText(f"{entry['text']}\n", format_text)
        
        # Details hinzufügen
        if entry['details']:
            format_details = QTextCharFormat()
            format_details.setForeground(QColor("#808080"))
            for key, value in entry['details'].items():
                cursor.insertText(f"  {key}: {value}\n", format_details)
        
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

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
            self._append_formatted_entry(entry)
        
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
