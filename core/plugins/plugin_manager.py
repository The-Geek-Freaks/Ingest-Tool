import os
import importlib.util
import logging
from typing import Dict, List, Type, Optional
from dataclasses import dataclass

@dataclass
class PluginInfo:
    """Informationen über ein Plugin."""
    name: str
    version: str
    description: str
    author: str
    enabled: bool = True

class PluginBase:
    """Basisklasse für Plugins."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    @property
    def info(self) -> PluginInfo:
        """Plugin-Informationen."""
        raise NotImplementedError
        
    def initialize(self) -> bool:
        """Initialisiert das Plugin."""
        return True
        
    def cleanup(self):
        """Wird beim Deaktivieren des Plugins aufgerufen."""
        pass
        
class PluginManager:
    """Verwaltet die Plugins der Anwendung."""
    
    def __init__(self, plugin_dir: str):
        self.plugin_dir = plugin_dir
        self.plugins: Dict[str, PluginBase] = {}
        self.logger = logging.getLogger(__name__)
        
    def discover_plugins(self) -> List[str]:
        """Sucht nach verfügbaren Plugins im Plugin-Verzeichnis."""
        plugin_files = []
        
        try:
            if not os.path.exists(self.plugin_dir):
                os.makedirs(self.plugin_dir)
                
            for file in os.listdir(self.plugin_dir):
                if file.endswith('.py') and not file.startswith('__'):
                    plugin_files.append(file)
                    
        except Exception as e:
            self.logger.error(f"Fehler beim Suchen nach Plugins: {e}")
            
        return plugin_files
        
    def load_plugin(self, plugin_file: str) -> Optional[PluginBase]:
        """Lädt ein Plugin aus einer Datei.
        
        Args:
            plugin_file: Name der Plugin-Datei
            
        Returns:
            Plugin-Instanz oder None bei Fehler
        """
        try:
            # Erstelle absoluten Pfad
            plugin_path = os.path.join(self.plugin_dir, plugin_file)
            
            # Lade Modul
            spec = importlib.util.spec_from_file_location(
                f"plugins.{plugin_file[:-3]}", 
                plugin_path
            )
            if not spec or not spec.loader:
                raise ImportError(f"Konnte Plugin {plugin_file} nicht laden")
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Suche nach Plugin-Klasse
            for item in dir(module):
                obj = getattr(module, item)
                if (isinstance(obj, type) and 
                    issubclass(obj, PluginBase) and 
                    obj != PluginBase):
                    return obj()
                    
            raise ValueError(f"Keine Plugin-Klasse in {plugin_file} gefunden")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden von Plugin {plugin_file}: {e}")
            return None
            
    def load_all_plugins(self):
        """Lädt alle verfügbaren Plugins."""
        plugin_files = self.discover_plugins()
        
        for plugin_file in plugin_files:
            plugin = self.load_plugin(plugin_file)
            if plugin and plugin.initialize():
                self.plugins[plugin.info.name] = plugin
                self.logger.info(f"Plugin '{plugin.info.name}' geladen")
                
    def get_plugin(self, name: str) -> Optional[PluginBase]:
        """Gibt ein Plugin anhand seines Namens zurück."""
        return self.plugins.get(name)
        
    def enable_plugin(self, name: str) -> bool:
        """Aktiviert ein Plugin."""
        plugin = self.get_plugin(name)
        if plugin:
            plugin.info.enabled = True
            return True
        return False
        
    def disable_plugin(self, name: str) -> bool:
        """Deaktiviert ein Plugin."""
        plugin = self.get_plugin(name)
        if plugin:
            plugin.cleanup()
            plugin.info.enabled = False
            return True
        return False
        
    def get_enabled_plugins(self) -> List[PluginBase]:
        """Gibt alle aktivierten Plugins zurück."""
        return [p for p in self.plugins.values() if p.info.enabled]
