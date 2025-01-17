"""
Einfacher Dateisystem-Watcher ohne externe Abhängigkeiten.
"""
import os
import time
import logging
from typing import Dict, Callable, Set
from datetime import datetime
import threading
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

class FileWatcher:
    """Überwacht ein Verzeichnis auf neue oder geänderte Dateien."""
    
    def __init__(self, path: str, file_types: list, poll_interval: float = 5.0):
        """Initialisiert den FileWatcher.
        
        Args:
            path: Pfad zum zu überwachenden Verzeichnis
            file_types: Liste der zu überwachenden Dateitypen (z.B. ['.mp4', '.jpg'])
            poll_interval: Intervall in Sekunden zwischen Verzeichnisscans
        """
        self.path = path
        # Normalisiere Dateitypen (mit und ohne Punkt, case-insensitive)
        self.file_types = []
        for t in file_types:
            t = t.lower()
            if not t.startswith('.'):
                t = '.' + t
            self.file_types.append(t)
            
        self.poll_interval = poll_interval
        self._callbacks = {}
        self._running = False
        self._thread = None
        self._known_files = {}  # Persistente Liste der bekannten Dateien
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.logger.info(f"FileWatcher initialisiert für {path} mit Typen {self.file_types}")
        
    def add_callback(self, callback_id: str, callback: Callable[[str], None]):
        """Fügt einen Callback für gefundene Dateien hinzu."""
        self._callbacks[callback_id] = callback
        self.logger.debug(f"Callback {callback_id} hinzugefügt")
        
    def remove_callback(self, callback_id: str):
        """Entfernt einen Callback."""
        if callback_id in self._callbacks:
            del self._callbacks[callback_id]
            self.logger.debug(f"Callback {callback_id} entfernt")
            
    def start(self):
        """Startet die Überwachung."""
        if self._running:
            return
            
        self._running = True
        self._thread = threading.Thread(target=self._watch_directory)
        self._thread.daemon = True
        self._thread.start()
        self.logger.info(f"Überwachung von {self.path} gestartet")
        
    def stop(self):
        """Stoppt die Überwachung."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
        self.logger.info(f"Überwachung von {self.path} gestoppt")
        
    def _watch_directory(self):
        """Überwacht das Verzeichnis auf neue oder geänderte Dateien."""
        self.logger.debug(f"Starte Verzeichnisüberwachung in Thread: {threading.current_thread().name}")
        
        while self._running:
            try:
                # Scanne rekursiv nach Dateien
                current_files = {}
                
                self.logger.debug(f"Scanne Verzeichnis {self.path} nach Dateitypen {self.file_types}")
                
                for root, _, files in os.walk(self.path):
                    for filename in files:
                        filepath = os.path.join(root, filename)
                        
                        # Prüfe Dateityp (case-insensitive)
                        _, ext = os.path.splitext(filename)
                        ext = ext.lower()
                        
                        if ext in self.file_types:
                            self.logger.debug(f"Gefundene Datei: {filepath} (Typ: {ext})")
                            
                            # Hole Änderungszeit
                            try:
                                mtime = os.path.getmtime(filepath)
                                current_files[filepath] = mtime
                                
                                # Prüfe ob Datei neu oder geändert
                                if filepath not in self._known_files:
                                    # Neue Datei
                                    self.logger.info(f"Neue Datei gefunden: {filepath}")
                                    self.on_file_found(filepath)
                                    self._known_files[filepath] = mtime
                                elif mtime > self._known_files[filepath]:
                                    # Geänderte Datei
                                    self.logger.info(f"Geänderte Datei gefunden: {filepath}")
                                    self.on_file_found(filepath)
                                    self._known_files[filepath] = mtime
                                    
                            except OSError as e:
                                self.logger.error(f"Fehler beim Zugriff auf {filepath}: {str(e)}")
                                continue
                                
                # Entferne nicht mehr existierende Dateien
                for filepath in list(self._known_files.keys()):
                    if filepath not in current_files:
                        del self._known_files[filepath]
                
                # Warte bis zum nächsten Scan
                time.sleep(self.poll_interval)
                
            except Exception as e:
                self.logger.error(f"Fehler beim Scannen von {self.path}: {str(e)}", exc_info=True)
                time.sleep(1)  # Kurze Pause bei Fehler
                
    def check_files(self):
        """Überprüft das Verzeichnis auf neue oder geänderte Dateien."""
        known_files = {}  # Pfad -> Änderungszeit
        
        try:
            # Scanne rekursiv nach Dateien
            current_files = {}
            
            self.logger.debug(f"Scanne Verzeichnis {self.path} nach Dateitypen {self.file_types}")
            
            for root, _, files in os.walk(self.path):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    
                    # Prüfe Dateityp (case-insensitive)
                    _, ext = os.path.splitext(filename)
                    ext = ext.lower()
                    
                    if ext in self.file_types:
                        self.logger.debug(f"Gefundene Datei: {filepath} (Typ: {ext})")
                        
                        # Hole Änderungszeit
                        try:
                            mtime = os.path.getmtime(filepath)
                            current_files[filepath] = mtime
                            
                            if filepath not in known_files:
                                # Neue Datei gefunden
                                self.logger.info(f"Neue Datei gefunden: {filepath}")
                                self._on_file_found(filepath)
                                known_files[filepath] = mtime
                            elif mtime > known_files[filepath]:
                                # Datei wurde geändert
                                self.logger.info(f"Datei wurde geändert: {filepath}")
                                self._on_file_found(filepath)
                                known_files[filepath] = mtime
                                
                        except (OSError, PermissionError) as e:
                            self.logger.error(f"Fehler beim Zugriff auf {filepath}: {e}")
                            continue
                    else:
                        self.logger.debug(f"Überspringe Datei {filepath} (Typ: {ext} nicht in {self.file_types})")
                            
            # Entferne nicht mehr existierende Dateien
            for filepath in list(known_files.keys()):
                if filepath not in current_files:
                    self.logger.debug(f"Datei wurde entfernt: {filepath}")
                    del known_files[filepath]
                    
        except Exception as e:
            self.logger.error(f"Fehler beim Scannen von {self.path}: {e}", exc_info=True)

    def _on_file_found(self, file_path: str):
        """Wird aufgerufen wenn eine neue oder geänderte Datei gefunden wurde."""
        self.logger.debug(f"Verarbeite Datei: {file_path}")
        for callback_id, callback in self._callbacks.items():
            try:
                self.logger.debug(f"Rufe Callback {callback_id} für {file_path} auf")
                callback(file_path)
            except Exception as e:
                self.logger.error(f"Fehler in Callback {callback_id} für {file_path}: {e}", exc_info=True)
                
    def on_file_found(self, file_path: str):
        """Hook-Methode für abgeleitete Klassen."""
        self._on_file_found(file_path)

class SignalFileWatcher(QObject, FileWatcher):
    """FileWatcher der Signale für gefundene Dateien ausgibt."""
    
    file_found = pyqtSignal(str)
    
    def __init__(self, path: str, file_types: list, poll_interval: float = 5.0):
        """Initialisiert den SignalFileWatcher.
        
        Args:
            path: Zu überwachender Pfad
            file_types: Liste der zu überwachenden Dateitypen
            poll_interval: Zeit zwischen Scans in Sekunden
        """
        QObject.__init__(self)
        FileWatcher.__init__(self, path, file_types, poll_interval)
        self.logger = logging.getLogger(__name__)
        
    def on_file_found(self, file_path: str):
        """Sendet das file_found Signal."""
        self.logger.debug(f"Emittiere file_found Signal für {file_path}")
        self.file_found.emit(file_path)
        super().on_file_found(file_path)
        
class FileWatcherManager:
    """Verwaltet mehrere FileWatcher für verschiedene Laufwerke."""
    
    def __init__(self):
        """Initialisiert den FileWatcherManager."""
        self.logger = logging.getLogger(__name__)
        self.watchers = {}  # {drive_letter: SignalFileWatcher}
        self.mappings = {}  # {file_type: target_path}
        
    def update_mappings(self, mappings: Dict[str, str]):
        """Aktualisiert die Dateitypzuordnungen.
        
        Args:
            mappings: Dict mit {Dateityp: Zielpfad}
        """
        self.mappings = mappings
        self.logger.debug(f"Aktualisierte Zuordnungen: {mappings}")
        
    def start_watcher(self, drive_path: str, file_types: list) -> bool:
        """Startet einen neuen Watcher für ein Laufwerk.
        
        Args:
            drive_path: Pfad zum Laufwerk (z.B. "D:\\")
            file_types: Liste der zu überwachenden Dateitypen
            
        Returns:
            bool: True wenn erfolgreich gestartet
        """
        try:
            drive_letter = os.path.splitdrive(drive_path)[0].rstrip(':')
            
            # Stoppe existierenden Watcher falls vorhanden
            if drive_letter in self.watchers:
                self.stop_watcher(drive_letter)
            
            # Erstelle und starte neuen Watcher
            watcher = SignalFileWatcher(drive_path, file_types)
            watcher.start()
            
            # Speichere Watcher
            self.watchers[drive_letter] = watcher
            self.logger.info(f"Watcher für Laufwerk {drive_letter} gestartet")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Starten des Watchers: {str(e)}")
            return False
            
    def stop_watcher(self, drive_letter: str):
        """Stoppt den Watcher für ein Laufwerk.
        
        Args:
            drive_letter: Laufwerksbuchstabe
        """
        if drive_letter in self.watchers:
            try:
                self.watchers[drive_letter].stop()
                del self.watchers[drive_letter]
                self.logger.info(f"Watcher für Laufwerk {drive_letter} gestoppt")
            except Exception as e:
                self.logger.error(f"Fehler beim Stoppen des Watchers: {str(e)}")
                
    def stop_all(self):
        """Stoppt alle aktiven Watcher."""
        for drive_letter in list(self.watchers.keys()):
            self.stop_watcher(drive_letter)
