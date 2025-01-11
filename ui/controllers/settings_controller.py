"""
Controller für die Einstellungs-Logik.
"""
import json
import os
from typing import Dict, Any, Optional

class SettingsController:
    """Verwaltet die Einstellungen der Anwendung."""
    
    def __init__(self, settings_file: str):
        self.settings_file = settings_file
        self._settings = self._load_settings()
        
    def _load_settings(self) -> Dict[str, Any]:
        """Lädt die Einstellungen aus der Datei."""
        if not os.path.exists(self.settings_file):
            return self._get_default_settings()
            
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return self._get_default_settings()
            
    def _save_settings(self):
        """Speichert die Einstellungen in der Datei."""
        os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(self._settings, f, indent=4)
            
    def _get_default_settings(self) -> Dict[str, Any]:
        """Gibt die Standard-Einstellungen zurück."""
        return {
            'language': 'Deutsch',
            'delete_source': False,
            'mappings': [],
            'file_types': [
                '.mp4', '.mov', '.avi', '.mkv',
                '.mxf', '.r3d', '.braw', '.arri',
                '.dng', '.raw'
            ]
        }
        
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Gibt den Wert einer Einstellung zurück."""
        return self._settings.get(key, default)
        
    def set_setting(self, key: str, value: Any):
        """Setzt den Wert einer Einstellung."""
        self._settings[key] = value
        self._save_settings()
        
    def get_all_settings(self) -> Dict[str, Any]:
        """Gibt alle Einstellungen zurück."""
        return self._settings.copy()
        
    def add_mapping(self, extension: str, target: str):
        """Fügt eine neue Zuordnung hinzu."""
        mappings = self.get_setting('mappings', [])
        mappings.append({
            'extension': extension,
            'target': target
        })
        self.set_setting('mappings', mappings)
        
    def remove_mapping(self, extension: str, target: str):
        """Entfernt eine Zuordnung."""
        mappings = self.get_setting('mappings', [])
        mappings = [m for m in mappings 
                   if not (m['extension'] == extension and m['target'] == target)]
        self.set_setting('mappings', mappings)
        
    def get_file_types(self) -> list:
        """Gibt die Liste der unterstützten Dateitypen zurück."""
        return self.get_setting('file_types', [])
        
    def set_file_types(self, file_types: list):
        """Setzt die Liste der unterstützten Dateitypen."""
        self.set_setting('file_types', file_types)
        
    def reset_to_defaults(self):
        """Setzt alle Einstellungen auf die Standardwerte zurück."""
        self._settings = self._get_default_settings()
        self._save_settings()
