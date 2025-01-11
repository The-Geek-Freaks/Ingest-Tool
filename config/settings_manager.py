#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class SettingsManager:
    """Manager für Anwendungseinstellungen."""
    
    def __init__(self, settings_file: str = "settings.json"):
        """Initialisiert den Settings-Manager.
        
        Args:
            settings_file: Pfad zur Settings-Datei
        """
        self.settings_file = settings_file
        self.settings = {}
        self.load_settings()
        
    def load_settings(self) -> Dict[str, Any]:
        """Lädt die Einstellungen aus der Datei.
        
        Returns:
            Dict mit den geladenen Einstellungen
        """
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
            else:
                self.settings = {}
                self.save()  # Erstelle leere Settings-Datei
        except Exception as e:
            logger.error(f"Fehler beim Laden der Einstellungen: {e}")
            self.settings = {}
        return self.settings
        
    def save(self):
        """Speichert die Einstellungen in der Datei."""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Einstellungen: {e}")
            
    def get(self, key: str, default: Any = None) -> Any:
        """Gibt den Wert für einen Schlüssel zurück.
        
        Args:
            key: Schlüssel
            default: Standardwert falls Schlüssel nicht existiert
            
        Returns:
            Wert für den Schlüssel oder default
        """
        return self.settings.get(key, default)
        
    def set(self, key: str, value: Any):
        """Setzt den Wert für einen Schlüssel.
        
        Args:
            key: Schlüssel
            value: Wert
        """
        self.settings[key] = value
        
    def update(self, settings: Dict[str, Any]):
        """Aktualisiert mehrere Einstellungen.
        
        Args:
            settings: Dict mit neuen Einstellungen
        """
        self.settings.update(settings)
        
    def get_all(self) -> Dict[str, Any]:
        """Gibt alle Einstellungen zurück.
        
        Returns:
            Dict mit allen Einstellungen
        """
        return self.settings.copy()
