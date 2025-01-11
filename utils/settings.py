#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from config.constants import (
    EINSTELLUNGEN_DATEI,
    STANDARD_DATEITYPEN,
    MAX_LOG_EINTRAEGE,
    EINSTELLUNGEN_VERZEICHNIS
)

logger = logging.getLogger(__name__)

class PresetManager:
    """Verwaltet das Laden und Speichern von Presets."""
    
    TEMP_PRESET_NAME = "_temp_auto_save"
    MAX_RECENT_PRESETS = 5
    
    def __init__(self):
        self.presets_file = os.path.join(EINSTELLUNGEN_VERZEICHNIS, "presets.json")
        self.recent_file = os.path.join(EINSTELLUNGEN_VERZEICHNIS, "recent_presets.json")
        os.makedirs(EINSTELLUNGEN_VERZEICHNIS, exist_ok=True)
        self.presets = self._load_presets()
        self.recent_presets = self._load_recent_presets()
        
        # Erstelle Default-Preset falls keine Presets existieren
        if not self.presets:
            self.create_default_preset()
            
    def create_default_preset(self):
        """Erstellt ein Standard-Preset mit Standardeinstellungen."""
        default_settings = {
            'excluded_drives': [],
            'mappings': [],
            'parallel_copies': 2,
            'buffer_size': 64*1024,
            'auto_start': False,
            'verify_copies': False,
            'recursive_search': True,
            'show_notifications': True
        }
        self.preset_hinzufuegen("Standard", default_settings)
        
    def _load_presets(self) -> dict:
        """Lädt alle gespeicherten Presets."""
        if os.path.exists(self.presets_file):
            try:
                with open(self.presets_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Fehler beim Laden der Presets: {e}")
        return {}
        
    def _save_presets(self):
        """Speichert alle Presets."""
        try:
            with open(self.presets_file, 'w', encoding='utf-8') as f:
                # Temporäres Preset nicht mit speichern
                presets_to_save = {k: v for k, v in self.presets.items() 
                                 if k != self.TEMP_PRESET_NAME}
                json.dump(presets_to_save, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Presets: {e}")
            
    def _load_recent_presets(self) -> list:
        """Lädt die Liste der zuletzt verwendeten Presets."""
        if os.path.exists(self.recent_file):
            try:
                with open(self.recent_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Fehler beim Laden der letzten Presets: {e}")
        return []
        
    def _save_recent_presets(self):
        """Speichert die Liste der zuletzt verwendeten Presets."""
        try:
            with open(self.recent_file, 'w', encoding='utf-8') as f:
                json.dump(self.recent_presets, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Fehler beim Speichern der letzten Presets: {e}")
            
    def add_to_recent(self, preset_name: str):
        """Fügt ein Preset zur Liste der zuletzt verwendeten hinzu."""
        if preset_name == self.TEMP_PRESET_NAME:
            return
            
        # Entferne das Preset, falls es bereits in der Liste ist
        if preset_name in self.recent_presets:
            self.recent_presets.remove(preset_name)
            
        # Füge das Preset am Anfang der Liste hinzu
        self.recent_presets.insert(0, preset_name)
        
        # Begrenze die Liste auf MAX_RECENT_PRESETS Einträge
        self.recent_presets = self.recent_presets[:self.MAX_RECENT_PRESETS]
        
        self._save_recent_presets()
        
    def get_recent_presets(self) -> list:
        """Gibt die Liste der zuletzt verwendeten Presets zurück."""
        # Filtere nicht mehr existierende Presets heraus
        self.recent_presets = [name for name in self.recent_presets 
                             if name in self.presets]
        self._save_recent_presets()
        return self.recent_presets
        
    def auto_save(self, settings: dict):
        """Speichert die aktuellen Einstellungen temporär."""
        self.presets[self.TEMP_PRESET_NAME] = settings.copy()
        
    def has_auto_save(self) -> bool:
        """Prüft ob ein temporäres Auto-Save existiert."""
        return self.TEMP_PRESET_NAME in self.presets
        
    def load_auto_save(self) -> dict:
        """Lädt das temporäre Auto-Save."""
        return self.presets.get(self.TEMP_PRESET_NAME, {}).copy()
        
    def clear_auto_save(self):
        """Löscht das temporäre Auto-Save."""
        if self.TEMP_PRESET_NAME in self.presets:
            del self.presets[self.TEMP_PRESET_NAME]
            
    def alle_presets(self) -> list:
        """Gibt eine Liste aller verfügbaren Preset-Namen zurück."""
        return list(self.presets.keys())
        
    def preset_existiert(self, name: str) -> bool:
        """Prüft ob ein Preset mit dem Namen existiert."""
        return name in self.presets
        
    def preset_laden(self, name: str) -> dict:
        """Lädt ein spezifisches Preset."""
        return self.presets.get(name, {}).copy()
        
    def preset_hinzufuegen(self, name: str, settings: dict):
        """Fügt ein neues Preset hinzu oder überschreibt ein bestehendes."""
        self.presets[name] = settings.copy()
        self._save_presets()
        
    def preset_loeschen(self, name: str):
        """Löscht ein Preset."""
        if name in self.presets:
            del self.presets[name]
            self._save_presets()
            
    def import_presets(self, file_path: str) -> dict:
        """Importiert Presets aus einer JSON-Datei."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported = json.load(f)
                
            # Validiere das Format
            if not isinstance(imported, dict):
                raise ValueError("Ungültiges Preset-Format")
                
            # Füge die Presets hinzu
            self.presets.update(imported)
            self._save_presets()
            return imported
            
        except Exception as e:
            logger.error(f"Fehler beim Importieren der Presets: {e}")
            raise
            
    def export_presets(self, file_path: str, presets_to_export: dict):
        """Exportiert ausgewählte Presets in eine JSON-Datei."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(presets_to_export, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Fehler beim Exportieren der Presets: {e}")
            raise

class Settings:
    """Verwaltet die Programmeinstellungen."""
    
    def __init__(self, settings_file: str):
        """Initialisiert die Settings-Klasse.
        
        Args:
            settings_file (str): Pfad zur Einstellungsdatei
        """
        self.settings_file = settings_file
        self.settings = {}
        
    def load(self) -> Dict[str, Any]:
        """Lädt die Einstellungen aus der Datei.
        
        Returns:
            Dict[str, Any]: Die geladenen Einstellungen
        """
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
            else:
                self.settings = {}
                self.save(self.settings)  # Erstelle leere Einstellungsdatei
                
            return self.settings
            
        except Exception as e:
            logging.error(f"Fehler beim Laden der Einstellungen: {str(e)}")
            return {}
            
    def save(self, settings: Dict[str, Any]) -> bool:
        """Speichert die Einstellungen in die Datei.
        
        Args:
            settings (Dict[str, Any]): Die zu speichernden Einstellungen
            
        Returns:
            bool: True wenn erfolgreich gespeichert, sonst False
        """
        try:
            # Erstelle den Ordner, falls er nicht existiert
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            
            # Speichere Einstellungen
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
                
            self.settings = settings
            return True
            
        except Exception as e:
            logging.error(f"Fehler beim Speichern der Einstellungen: {str(e)}")
            return False
            
    def get(self, key: str, default: Any = None) -> Any:
        """Holt einen Einstellungswert.
        
        Args:
            key (str): Der Schlüssel der Einstellung
            default (Any, optional): Standardwert falls nicht vorhanden
            
        Returns:
            Any: Der Einstellungswert oder der Standardwert
        """
        return self.settings.get(key, default)
        
    def set(self, key: str, value: Any) -> None:
        """Setzt einen Einstellungswert.
        
        Args:
            key (str): Der Schlüssel der Einstellung
            value (Any): Der zu setzende Wert
        """
        self.settings[key] = value

class SettingsManager:
    """Verwaltet die Einstellungen der Anwendung."""
    
    def __init__(self, settings_file: str = "settings.json"):
        """Initialisiert den Settings Manager.
        
        Args:
            settings_file: Pfad zur Einstellungsdatei
        """
        self.settings_file = settings_file
        self.settings = {}
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        
    def load_settings(self) -> dict:
        """Lädt die Einstellungen aus der Datei.
        
        Returns:
            dict: Die geladenen Einstellungen
        """
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
                self.logger.debug(f"Einstellungen geladen: {self.settings}")
            else:
                self.logger.debug("Keine Einstellungsdatei gefunden, verwende Standardeinstellungen")
                self.settings = {
                    'mappings': {},
                    'excluded_drives': []
                }
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Einstellungen: {e}", exc_info=True)
            self.settings = {
                'mappings': {},
                'excluded_drives': []
            }
            
        return self.settings
        
    def save_settings(self, settings: dict):
        """Speichert die Einstellungen in der Datei.
        
        Args:
            settings: Die zu speichernden Einstellungen
        """
        try:
            # Stelle sicher dass das Verzeichnis existiert
            settings_dir = os.path.dirname(self.settings_file)
            if settings_dir:  # Nur erstellen wenn ein Verzeichnis angegeben wurde
                os.makedirs(settings_dir, exist_ok=True)
                
            # Speichere Einstellungen
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
            self.logger.debug(f"Einstellungen gespeichert in: {self.settings_file}")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Einstellungen: {e}", exc_info=True)
    
    def get(self, key, default=None):
        """Holt einen Wert aus den Einstellungen."""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """Setzt einen Wert in den Einstellungen."""
        self.settings[key] = value
        self.save_settings(self.settings)
    
    def save_preset(self, name):
        """Speichert die aktuellen Einstellungen als Preset."""
        try:
            preset_data = {
                'file_types': self.get('file_types', []),
                'mappings': self.get('mappings', {}),
                'excluded_drives': self.get('excluded_drives', []),
                'delete_source': self.get('delete_source', False),
                'network_settings': self.get('network_settings', {}),
                'ui_settings': self.get('ui_settings', {})
            }
            
            preset_file = os.path.join(EINSTELLUNGEN_VERZEICHNIS, f"{name}.json")
            with open(preset_file, 'w', encoding='utf-8') as f:
                json.dump(preset_data, f, indent=4, ensure_ascii=False)
            
            # Aktualisiere Liste der Presets
            presets = self.get('presets', {})
            presets[name] = preset_data
            self.set('presets', presets)
            
            logger.info(f"Preset '{name}' erfolgreich gespeichert")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Presets '{name}': {e}")
            return False
    
    def load_preset(self, name):
        """Lädt ein gespeichertes Preset."""
        try:
            preset_file = os.path.join(EINSTELLUNGEN_VERZEICHNIS, f"{name}.json")
            if not os.path.exists(preset_file):
                logger.error(f"Preset '{name}' existiert nicht")
                return None
            
            with open(preset_file, 'r', encoding='utf-8') as f:
                preset_data = json.load(f)
            
            # Aktualisiere Einstellungen mit Preset-Daten
            for key, value in preset_data.items():
                self.set(key, value)
            
            logger.info(f"Preset '{name}' erfolgreich geladen")
            return preset_data
            
        except Exception as e:
            logger.error(f"Fehler beim Laden des Presets '{name}': {e}")
            return None
    
    def delete_preset(self, name):
        """Löscht ein gespeichertes Preset."""
        try:
            preset_file = os.path.join(EINSTELLUNGEN_VERZEICHNIS, f"{name}.json")
            if os.path.exists(preset_file):
                os.remove(preset_file)
            
            # Entferne aus der Liste der Presets
            presets = self.get('presets', {})
            if name in presets:
                del presets[name]
                self.set('presets', presets)
            
            logger.info(f"Preset '{name}' erfolgreich gelöscht")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Löschen des Presets '{name}': {e}")
            return False
    
    def get_presets(self):
        """Gibt eine Liste aller verfügbaren Presets zurück."""
        try:
            presets = {}
            for file in os.listdir(EINSTELLUNGEN_VERZEICHNIS):
                if file.endswith('.json'):
                    name = os.path.splitext(file)[0]
                    preset_file = os.path.join(EINSTELLUNGEN_VERZEICHNIS, file)
                    with open(preset_file, 'r', encoding='utf-8') as f:
                        presets[name] = json.load(f)
            return presets
        except Exception as e:
            logger.error(f"Fehler beim Laden der Presets: {e}")
            return {}
    
    def save_settings(self, settings: dict):
        """Speichert die Einstellungen in der JSON-Datei.
        
        Args:
            settings: Die zu speichernden Einstellungen
        """
        try:
            # Stelle sicher dass das Verzeichnis existiert
            settings_dir = os.path.dirname(self.settings_file)
            if settings_dir:  # Nur erstellen wenn ein Verzeichnis angegeben wurde
                os.makedirs(settings_dir, exist_ok=True)
                
            # Speichere Einstellungen
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
            self.logger.debug(f"Einstellungen gespeichert in: {self.settings_file}")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Einstellungen: {e}", exc_info=True)
