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
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QDateTime

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
    
    # Log-Level Konstanten und Farben
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    DEBUG = "DEBUG"
    
    LEVEL_COLORS = {
        INFO: "#89d0ff",      # Heltes Blau
        WARNING: "#ffd700",   # Gold
        ERROR: "#ff6b6b",     # Rot
        DEBUG: "#98c379",     # Grün
    }
    
    LEVEL_MAP = {
        INFO: logging.INFO,
        WARNING: logging.WARNING,
        ERROR: logging.ERROR,
        DEBUG: logging.DEBUG
    }
    
    def __init__(self, parent=None, max_entries=1000):
        super().__init__(parent)
        self.setReadOnly(True)
        
        # Einstellungen
        self.max_entries = max_entries
        self.date_format = "HH:mm:ss"
        self.auto_scroll = True
        self.group_messages = False
        self.show_line_numbers = False
        self.visible_levels = {logging.INFO, logging.WARNING, logging.ERROR}
        
        # Log-Einträge und Gruppen
        self.log_entries = []
        self.current_group = None
        self.group_entries = {}
        self.expanded_groups = set()
        
        # Suche
        self.search_text = ""
        self.search_results = []
        self.current_search_index = -1
        
    def log(self, text: str, level: str = INFO, details: dict = None):
        """Fügt einen formatierten Log-Eintrag hinzu.
        
        Args:
            text: Die Log-Nachricht
            level: Log-Level (INFO, WARNING, ERROR, DEBUG)
            details: Optionale zusätzliche Details
        """
        try:
            # Prüfe ob dieser Level angezeigt werden soll
            if self.LEVEL_MAP.get(level) not in self.visible_levels:
                return
                
            # Erstelle Log-Eintrag
            entry = {
                'text': text,
                'level': level,
                'timestamp': QDateTime.currentDateTime(),
                'details': details or {},
                'group_id': self.current_group
            }
            
            # Gruppiere ähnliche Nachrichten wenn aktiviert
            if self.group_messages and self.current_group:
                group = self.group_entries.get(self.current_group, [])
                group.append(entry)
                self.group_entries[self.current_group] = group
            else:
                self.log_entries.append(entry)
            
            # Entferne alte Einträge wenn Maximum überschritten
            while len(self.log_entries) > self.max_entries:
                self.log_entries.pop(0)
            
            # Aktualisiere Anzeige
            self.refresh_display()
            
        except Exception as e:
            print(f"Fehler beim Loggen: {e}")
            
    def refresh_display(self):
        """Aktualisiert die komplette Anzeige."""
        try:
            self.clear()
            cursor = self.textCursor()
            
            for i, entry in enumerate(self.log_entries):
                if entry['group_id'] and self.group_messages:
                    self._format_group_entry(cursor, entry, i)
                else:
                    self._format_single_entry(cursor, entry, i)
            
            if self.auto_scroll:
                self.scrollToBottom()
                
        except Exception as e:
            print(f"Fehler beim Aktualisieren der Anzeige: {e}")
            
    def _format_single_entry(self, cursor: QTextCursor, entry: dict, index: int):
        """Formatiert einen einzelnen Log-Eintrag."""
        # Zeilennummer
        if self.show_line_numbers:
            number_format = QTextCharFormat()
            number_format.setForeground(QBrush(QColor("#666666")))
            cursor.insertText(f"{index+1:04d} ", number_format)
        
        # Zeitstempel
        time_format = QTextCharFormat()
        time_format.setForeground(QBrush(QColor("#666666")))
        timestamp = entry['timestamp'].toString(self.date_format)
        cursor.insertText(f"[{timestamp}] ", time_format)
        
        # Level-Badge
        level_format = QTextCharFormat()
        level_format.setBackground(QBrush(QColor(self.LEVEL_COLORS[entry['level']])))
        level_format.setForeground(QBrush(QColor("#000000")))
        cursor.insertText(f" {entry['level']} ", level_format)
        cursor.insertText(" ")
        
        # Nachricht
        msg_format = QTextCharFormat()
        msg_format.setForeground(QBrush(QColor("#ffffff")))
        cursor.insertText(entry['text'], msg_format)
        cursor.insertText("\n")
        
    def _format_group_entry(self, cursor: QTextCursor, entry: dict, index: int):
        """Formatiert eine Gruppe von ähnlichen Log-Einträgen."""
        group = self.group_entries.get(entry['group_id'], [])
        if not group:
            return
            
        # Nur den ersten Eintrag der Gruppe anzeigen
        self._format_single_entry(cursor, group[0], index)
        
        # Wenn Gruppe erweitert ist, zeige alle Einträge
        if entry['group_id'] in self.expanded_groups:
            for sub_entry in group[1:]:
                cursor.insertText("  ")  # Einrückung
                self._format_single_entry(cursor, sub_entry, index)
        else:
            # Zeige Anzahl der gruppierten Nachrichten
            count = len(group) - 1
            if count > 0:
                count_format = QTextCharFormat()
                count_format.setForeground(QBrush(QColor("#666666")))
                cursor.insertText(f"  +{count} weitere ähnliche Meldungen\n", count_format)

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
        
        # Suche
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
        if entry['group_id']:
            self.expanded_groups.add(entry['group_id'])
        
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
