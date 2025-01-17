#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Initialisierungsmodul für Qt-spezifische Komponenten.
"""

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtGui import QTextCursor

def register_metatypes():
    """Registriert alle benötigten Metatypen für Qt."""
    # Registriere QTextCursor für Signal/Slot-Verbindungen
    # Wir verwenden eine temporäre Klasse mit einem Signal
    class TempSignal(QObject):
        signal = pyqtSignal(QTextCursor)
    
    # Erstelle eine Instanz der Klasse, um das Signal zu registrieren
    TempSignal()
