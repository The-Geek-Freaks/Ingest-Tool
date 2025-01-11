import os
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class SettingsManager:
    """Verwaltet Anwendungseinstellungen und Presets."""
    
    def __init__(self, settings_file: str = "settings.json"):
        self.settings_file = settings_file
        self.settings = {}
        self.preset_manager = PresetManager()
        self.load_settings()
        
    def load_settings(self) -> Dict:
        """Lädt die Einstellungen aus der Datei."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    self.settings = json.load(f)
            return self.settings
        except Exception as e:
            logger.error(f"Fehler beim Laden der Einstellungen: {e}")
            return {}
            
    def save_settings(self):
        """Speichert die Einstellungen in die Datei."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Einstellungen: {e}")
            
    def get(self, key: str, default=None):
        """Gibt eine Einstellung zurück."""
        return self.settings.get(key, default)
        
    def set(self, key: str, value):
        """Setzt eine Einstellung."""
        self.settings[key] = value
        self.save_settings()
        
    def get_all(self) -> Dict:
        """Gibt alle Einstellungen zurück."""
        return self.settings
        
    def load_preset(self, preset_name: str):
        """Lädt ein Preset."""
        preset = self.preset_manager.get_preset(preset_name)
        if preset:
            self.settings.update(preset)
            self.save_settings()
            
    def save_preset(self, preset_name: str, settings: Dict):
        """Speichert ein Preset."""
        self.preset_manager.save_preset(preset_name, settings)
        
    def get_presets(self) -> Dict:
        """Gibt alle verfügbaren Presets zurück."""
        return self.preset_manager.get_presets()
        
class PresetManager:
    """Verwaltet Einstellungs-Presets."""
    
    def __init__(self, presets_dir: str = "presets"):
        self.presets_dir = presets_dir
        os.makedirs(presets_dir, exist_ok=True)
        
    def get_preset(self, preset_name: str) -> Optional[Dict]:
        """Lädt ein Preset aus einer Datei."""
        try:
            preset_file = os.path.join(self.presets_dir, f"{preset_name}.json")
            if os.path.exists(preset_file):
                with open(preset_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Fehler beim Laden des Presets {preset_name}: {e}")
        return None
        
    def save_preset(self, preset_name: str, settings: Dict):
        """Speichert ein Preset in eine Datei."""
        try:
            preset_file = os.path.join(self.presets_dir, f"{preset_name}.json")
            with open(preset_file, 'w') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Presets {preset_name}: {e}")
            
    def get_presets(self) -> Dict[str, Dict]:
        """Gibt alle verfügbaren Presets zurück."""
        presets = {}
        try:
            for file in os.listdir(self.presets_dir):
                if file.endswith('.json'):
                    preset_name = os.path.splitext(file)[0]
                    preset = self.get_preset(preset_name)
                    if preset:
                        presets[preset_name] = preset
        except Exception as e:
            logger.error(f"Fehler beim Laden der Presets: {e}")
        return presets
