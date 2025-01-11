#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Manager für Anwendungseinstellungen."""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

class SettingsManager:
    """Verwaltet die Anwendungseinstellungen."""
    
    def __init__(self, settings_file: str = None):
        """Initialisiert den Settings-Manager.
        
        Args:
            settings_file: Pfad zur Einstellungsdatei (optional)
        """
        if settings_file is None:
            # Standard-Einstellungsdatei im Benutzerverzeichnis
            settings_dir = os.path.join(str(Path.home()), ".ingesttool")
            os.makedirs(settings_dir, exist_ok=True)
            settings_file = os.path.join(settings_dir, "settings.json")
            
        self.settings_file = settings_file
        self.settings = self.load_settings()
        
    def load_settings(self) -> Dict[str, Any]:
        """Lädt die Einstellungen aus der Datei.
        
        Returns:
            Dictionary mit den Einstellungen
        """
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            return self.get_default_settings()
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der Einstellungen: {e}")
            return self.get_default_settings()
            
    def save_settings(self, settings: Dict[str, Any] = None):
        """Speichert die Einstellungen in die Datei.
        
        Args:
            settings: Zu speichernde Einstellungen (optional)
        """
        try:
            if settings is not None:
                self.settings = settings
                
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4)
                
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Einstellungen: {e}")
            
    def get_default_settings(self) -> Dict[str, Any]:
        """Gibt die Standard-Einstellungen zurück.
        
        Returns:
            Dictionary mit den Standard-Einstellungen
        """
        return {
            "auto_start": False,
            "mappings": {},
            "excluded_drives": [],
            "parallel_copies": 2,
            "buffer_size": 64*1024,
            "language": "de",
            "theme": "dark",
            "window_size": {
                "width": 1200,
                "height": 800
            }
        }
        
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Gibt den Wert einer Einstellung zurück.
        
        Args:
            key: Schlüssel der Einstellung
            default: Standardwert falls nicht gefunden
            
        Returns:
            Wert der Einstellung
        """
        return self.settings.get(key, default)
        
    def set_setting(self, key: str, value: Any):
        """Setzt den Wert einer Einstellung.
        
        Args:
            key: Schlüssel der Einstellung
            value: Neuer Wert
        """
        self.settings[key] = value
        self.save_settings()
        
    def get_mappings(self) -> Dict[str, str]:
        """Gibt die Dateityp-Zuordnungen zurück.
        
        Returns:
            Dictionary mit Dateityp als Schlüssel und Zielpfad als Wert
        """
        return self.get_setting("mappings", {})
        
    def set_mappings(self, mappings: Dict[str, str]):
        """Setzt die Dateityp-Zuordnungen.
        
        Args:
            mappings: Dictionary mit Dateityp als Schlüssel und Zielpfad als Wert
        """
        self.set_setting("mappings", mappings)
        
    def get_excluded_drives(self) -> list:
        """Gibt die ausgeschlossenen Laufwerke zurück.
        
        Returns:
            Liste der ausgeschlossenen Laufwerke
        """
        return self.get_setting("excluded_drives", [])
        
    def set_excluded_drives(self, drives: list):
        """Setzt die ausgeschlossenen Laufwerke.
        
        Args:
            drives: Liste der ausgeschlossenen Laufwerke
        """
        self.set_setting("excluded_drives", drives)
        
    def get_window_size(self) -> Dict[str, int]:
        """Gibt die Fenstergröße zurück.
        
        Returns:
            Dictionary mit Breite und Höhe
        """
        return self.get_setting("window_size", {"width": 1200, "height": 800})
        
    def set_window_size(self, width: int, height: int):
        """Setzt die Fenstergröße.
        
        Args:
            width: Breite des Fensters
            height: Höhe des Fensters
        """
        self.set_setting("window_size", {"width": width, "height": height})
