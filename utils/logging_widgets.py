#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Logging-Widget-Komponenten."""

import logging
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QTextEdit

class QTextEditLogger(logging.Handler):
    """Logger-Handler für QTextEdit."""
    
    def __init__(self, parent=None):
        super().__init__()
        self.widget = QTextEdit(parent)
        self.widget.setReadOnly(True)
        
    def emit(self, record):
        msg = self.format(record)
        self.widget.append(msg)
        
        # Scrolle zum Ende
        cursor = self.widget.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.widget.setTextCursor(cursor)
        self.widget.ensureCursorVisible()
