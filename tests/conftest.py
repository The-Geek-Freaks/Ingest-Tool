#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Pytest Konfiguration."""

import os
import sys

# Füge das Hauptverzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def pytest_configure(config):
    """Konfiguriert pytest für Qt Tests."""
    import sys
    from PyQt5.QtWidgets import QApplication
    
    # Initialisiere QApplication wenn noch nicht vorhanden
    if not QApplication.instance():
        app = QApplication(sys.argv)
        
    # Setze Logging-Level auf DEBUG für Tests
    import logging
    logging.basicConfig(level=logging.DEBUG)
