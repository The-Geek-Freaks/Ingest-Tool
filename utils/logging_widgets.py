#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Logging-Widget-Komponenten."""

import logging
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtWidgets import QTextEdit

class ThreadSafeLogBridge(QObject):
    """Thread-sichere Brücke für Logging-Nachrichten."""
    
    log_message_received = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)

class QTextEditLogger(logging.Handler):
    """Logger-Handler für QTextEdit."""
    
    def __init__(self, parent=None):
        super().__init__()
        self.widget = QTextEdit(parent)
        self.widget.setReadOnly(True)
        
        # Erstelle Thread-Bridge
        self.bridge = ThreadSafeLogBridge(self.widget)
        self.bridge.log_message_received.connect(self._append_text)
        
    def emit(self, record):
        msg = self.format(record)
        # Sende Nachricht über Signal
        self.bridge.log_message_received.emit(msg)
    
    def _append_text(self, msg):
        """Fügt Text thread-sicher hinzu."""
        # Verwende append statt QTextCursor direkt
        self.widget.append(msg)
        # Scrolle zum Ende ohne QTextCursor
        scrollbar = self.widget.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
