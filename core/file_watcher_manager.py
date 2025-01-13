#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Verwaltet die Dateiüberwachung für verschiedene Laufwerke.
"""

import os
import logging
import threading
import re
from typing import Dict, List, Callable
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot, QMetaObject, Qt, Q_ARG, QMetaType, QTimer
from PyQt5.QtGui import QTextCursor
from utils.file_watcher import FileWatcher as BaseFileWatcher
from core.file_transfer_manager import FileTransferManager
import sys

logger = logging.getLogger(__name__)

class SignalFileWatcher(BaseFileWatcher, QObject):
    """Erweitert den FileWatcher um Signal-Slot Funktionalität."""
    
    file_found = pyqtSignal(str)
    
    def __init__(self, path: str, file_types: list, poll_interval: float = 5.0):
        """Initialisiert den SignalFileWatcher.
        
        Args:
            path: Zu überwachendes Verzeichnis
            file_types: Liste der zu überwachenden Dateitypen (z.B. ['.mp4', '.jpg'])
            poll_interval: Zeit zwischen Polls in Sekunden (Standard: 5.0)
        """
        QObject.__init__(self)
        BaseFileWatcher.__init__(self, path, file_types, poll_interval)
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"SignalFileWatcher initialisiert für {path} mit Typen {file_types}")
        
    def on_file_found(self, file_path: str):
        """Wird aufgerufen wenn eine neue oder geänderte Datei gefunden wurde."""
        try:
            self.file_found.emit(file_path)
        except Exception as e:
            self.logger.error(f"Fehler beim Emittieren des Signals: {e}", exc_info=True)

class FileWatcherManager(QObject):
    """Verwaltet die Überwachung von Laufwerken auf neue Dateien."""
    
    file_found = pyqtSignal(str)  # Signal wenn eine Datei gefunden wurde
    
    def __init__(self, main_window=None):
        """Initialisiert den FileWatcherManager.
        
        Args:
            main_window: Hauptfenster der Anwendung
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.watchers = {}
        self.file_types = []
        self.excluded_drives = []
        self._is_watching = False
        self.main_window = main_window
        self.file_mappings = {}
        
        # Initialisiere Transfer Manager
        self.transfer_manager = FileTransferManager()
        self.transfer_manager.transfer_started.connect(self._on_transfer_started)
        self.transfer_manager.transfer_progress.connect(self._on_transfer_progress)
        self.transfer_manager.transfer_completed.connect(self._on_transfer_completed)
        self.transfer_manager.transfer_error.connect(self._on_transfer_error)
        
        # Initialisiere Zuordnungen
        if self.main_window:
            self.update_file_mappings()
            
        self.logger.debug("FileWatcherManager initialisiert")
        
    @property
    def is_watching(self) -> bool:
        """Gibt zurück ob die Überwachung aktiv ist."""
        return self._is_watching
        
    @is_watching.setter 
    def is_watching(self, value: bool):
        """Setzt den Überwachungsstatus."""
        self._is_watching = value
        # Aktualisiere auch den Status im MainWindow
        if self.main_window:
            self.main_window.is_watching = value

    def _get_excluded_drives(self) -> List[str]:
        """Holt die Liste der ausgeschlossenen Laufwerke aus der UI."""
        excluded = []
        try:
            if not self.main_window or not hasattr(self.main_window, 'excluded_list'):
                return excluded
                
            for i in range(self.main_window.excluded_list.count()):
                item = self.main_window.excluded_list.item(i)
                if item and item.text():
                    # Extrahiere Laufwerksbuchstaben (erstes Zeichen)
                    drive = item.text().split()[0].strip().rstrip(':').upper()
                    if drive:
                        excluded.append(drive)
                        
            self.logger.debug(f"Ausgeschlossene Laufwerke: {excluded}")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Lesen der ausgeschlossenen Laufwerke: {e}")
            
        return excluded

    def set_excluded_drives(self, drives: List[str]):
        """Setzt die Liste der ausgeschlossenen Laufwerke."""
        try:
            self.excluded_drives = [d.upper() for d in drives if d]
            self.logger.info(f"Ausgeschlossene Laufwerke aktualisiert: {self.excluded_drives}")
            
            # Stoppe Watcher für ausgeschlossene Laufwerke
            for drive in list(self.watchers.keys()):
                if drive in self.excluded_drives:
                    self.stop_watcher(drive)
                    
        except Exception as e:
            self.logger.error(f"Fehler beim Setzen der ausgeschlossenen Laufwerke: {e}")

    def start(self):
        """Startet die Dateiüberwachung."""
        try:
            if self._is_watching:
                return
                
            self.logger.info("Starte Datenträgerüberwachung")
            self.update_file_mappings()
            
            # Hole verfügbare und nicht ausgeschlossene Laufwerke
            available_drives = []
            if self.main_window:
                # Hole alle verfügbaren Laufwerke
                all_drives = self.main_window.drives_list.get_drive_letters()
                # Hole ausgeschlossene Laufwerke
                excluded_drives = self._get_excluded_drives()
                # Filtere ausgeschlossene Laufwerke
                available_drives = [d for d in all_drives if d.upper() not in excluded_drives]
                self.logger.info(f"Verfügbare Laufwerke: {available_drives}")
                self.logger.info(f"Ausgeschlossene Laufwerke: {excluded_drives}")
            
            # Starte Überwachung für jedes nicht ausgeschlossene Laufwerk
            for drive in available_drives:
                self.start_watching_drive(drive)
            
            self._is_watching = True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Starten der Überwachung: {e}")

    def start_watching_drive(self, drive_letter: str):
        """Startet die Überwachung für ein bestimmtes Laufwerk."""
        try:
            if not drive_letter or drive_letter in self.watchers:
                return
                
            # Erstelle Pfad
            drive_path = f"{drive_letter}:\\"
            
            # Hole aktuelle Dateitypen aus den Zuordnungen
            file_types = list(self.file_mappings.keys())
            if not file_types:
                self.logger.warning(f"Keine Dateitypen konfiguriert für {drive_path}")
                return
                
            # Erstelle und starte Watcher
            watcher = SignalFileWatcher(drive_path, file_types)
            
            # Verbinde Signal direkt mit unserem Handler
            watcher.file_found.connect(self._on_file_found)
            
            # Starte Überwachung
            watcher.start()
            
            # Speichere Watcher
            self.watchers[drive_letter] = watcher
            self.logger.info(f"Überwachung von {drive_path} gestartet")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Starten der Überwachung für {drive_letter}: {str(e)}", exc_info=True)

    def stop_watcher(self, drive_letter: str):
        """Stoppt den Watcher für das angegebene Laufwerk."""
        try:
            if drive_letter in self.watchers:
                watcher = self.watchers[drive_letter]
                watcher.stop()
                del self.watchers[drive_letter]
                self.logger.info(f"Watcher für Laufwerk {drive_letter} gestoppt")
                
        except Exception as e:
            self.logger.error(f"Fehler beim Stoppen des Watchers für {drive_letter}: {e}")

    def stop(self):
        """Stoppt die Dateiüberwachung."""
        try:
            if not self._is_watching:
                return
                
            self.logger.info("Stoppe Datenträgerüberwachung")
            
            # Stoppe alle Watcher
            for drive, watcher in self.watchers.items():
                try:
                    watcher.stop()
                    self.logger.info(f"Überwachung von {drive}:\\ gestoppt")
                except Exception as e:
                    self.logger.error(f"Fehler beim Stoppen des Watchers für {drive}: {e}")
            
            # Stoppe auch den Transfer Manager
            if hasattr(self, 'transfer_manager'):
                self.transfer_manager.abort_transfers()
            
            self.watchers.clear()
            self._is_watching = False
            self.logger.info("Datenträgerüberwachung gestoppt")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Stoppen der Überwachung: {e}")

    def update_file_mappings(self):
        """Aktualisiert die Zuordnungen zwischen Dateitypen und Zielverzeichnissen."""
        try:
            self.file_mappings.clear()
            if not self.main_window:
                return
                
            # Hole Zuordnungen aus der UI
            for i in range(self.main_window.mappings_list.count()):
                item = self.main_window.mappings_list.item(i)
                if item and item.text():
                    text = item.text()
                    if "➔" in text:
                        file_type, target = text.split("➔")
                        file_type = file_type.strip()  # z.B. "*.mp4"
                        target = target.strip()
                        
                        # Entferne * und füge . hinzu wenn nötig
                        clean_type = file_type.replace('*', '')
                        if not clean_type.startswith('.'):
                            clean_type = '.' + clean_type
                            
                        # Normalisiere den Zielpfad
                        target_path = os.path.abspath(target)
                        
                        # Füge die Zuordnung hinzu
                        self.file_mappings[clean_type.lower()] = target_path
                        self.logger.info(f"Zuordnung hinzugefügt: {clean_type} -> {target_path}")
                        
            self.logger.debug(f"Aktualisierte Zuordnungen: {self.file_mappings}")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren der Zuordnungen: {str(e)}", exc_info=True)

    def _on_file_found(self, file_path: str):
        """Callback für gefundene Dateien."""
        try:
            self.logger.info(f"Neue Datei gefunden: {file_path}")
            
            # Hole Dateierweiterung (case-insensitive)
            file_ext = os.path.splitext(file_path)[1].lower()
            if not file_ext:
                self.logger.warning(f"Keine Dateierweiterung gefunden für: {file_path}")
                return
                
            # Debug-Ausgaben
            self.logger.debug(f"Verarbeite: {file_path}")
            self.logger.debug(f"Dateityp: {file_ext}")
            self.logger.debug(f"Verfügbare Zuordnungen: {self.file_mappings}")
            
            # Aktualisiere Zuordnungen
            self.update_file_mappings()
            
            # Prüfe Zuordnung
            target_dir = self.file_mappings.get(file_ext)
            
            if target_dir:
                self.logger.info(f"Zuordnung gefunden für {file_ext} -> {target_dir}")
                
                # Stelle sicher, dass das Zielverzeichnis existiert
                try:
                    os.makedirs(target_dir, exist_ok=True)
                    self.logger.info(f"Zielverzeichnis bereit: {target_dir}")
                except Exception as e:
                    self.logger.error(f"Fehler beim Erstellen des Zielverzeichnisses: {str(e)}")
                    return
                
                # Bestimme Zieldatei
                filename = os.path.basename(file_path)
                target_path = os.path.join(target_dir, filename)
                
                # Führe Transfer durch
                try:
                    self.logger.info(f"Starte Transfer: {file_path} -> {target_dir}")
                    success = self.transfer_manager.transfer_file(file_path, target_path)
                    
                    if success:
                        self.logger.info(f"Transfer erfolgreich: {filename}")
                        # Aktualisiere UI im Hauptthread
                        if self.main_window:
                            # Verwende QMetaObject.invokeMethod für thread-sichere UI-Aktualisierung
                            message = f"Datei gefunden und Transfer gestartet: {filename}"
                            QMetaObject.invokeMethod(self.main_window, 
                                                   "log_message",
                                                   Qt.QueuedConnection,
                                                   Q_ARG(str, message))
                    else:
                        self.logger.error(f"Transfer fehlgeschlagen: {filename}")
                        
                except Exception as e:
                    self.logger.error(f"Fehler beim Transfer: {str(e)}")
            else:
                self.logger.debug(f"Keine Zuordnung gefunden für {file_ext}")
                
        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten der gefundenen Datei: {str(e)}", exc_info=True)

    def _handle_file_found(self, file_path: str):
        """Verarbeitet gefundene Dateien im Hauptthread."""
        try:
            self.logger.info(f"Neue Datei gefunden: {file_path}")
            
            # Hole Dateierweiterung (case-insensitive)
            file_ext = os.path.splitext(file_path)[1].lower()
            if not file_ext:
                self.logger.warning(f"Keine Dateierweiterung gefunden für: {file_path}")
                return
                
            # Debug-Ausgaben
            self.logger.debug(f"Verarbeite: {file_path}")
            self.logger.debug(f"Dateityp: {file_ext}")
            self.logger.debug(f"Verfügbare Zuordnungen: {self.file_mappings}")
            
            # Aktualisiere Zuordnungen
            self.update_file_mappings()
            
            # Prüfe Zuordnung
            target_dir = self.file_mappings.get(file_ext)
            
            if target_dir:
                self.logger.info(f"Zuordnung gefunden für {file_ext} -> {target_dir}")
                
                # Stelle sicher, dass das Zielverzeichnis existiert
                try:
                    os.makedirs(target_dir, exist_ok=True)
                    self.logger.info(f"Zielverzeichnis bereit: {target_dir}")
                except Exception as e:
                    self.logger.error(f"Fehler beim Erstellen des Zielverzeichnisses: {str(e)}")
                    return
                
                # Führe Transfer durch
                try:
                    self.logger.info(f"Starte Transfer: {file_path} -> {target_dir}")
                    success = self.transfer_manager.transfer_file(file_path, target_dir)
                    
                    if success:
                        self.logger.info(f"Transfer erfolgreich: {os.path.basename(file_path)}")
                        # Aktualisiere UI im Hauptthread
                        if self.main_window:
                            # Verwende QTimer.singleShot für thread-sichere UI-Aktualisierung
                            QTimer.singleShot(0, lambda: self.main_window.log_message(
                                f"Datei kopiert: {os.path.basename(file_path)}"))
                    else:
                        self.logger.error(f"Transfer fehlgeschlagen: {file_path}")
                except Exception as e:
                    self.logger.error(f"Fehler beim Transfer: {str(e)}", exc_info=True)
            else:
                self.logger.warning(f"Keine Zuordnung für Dateityp gefunden: {file_ext}")
                
        except Exception as e:
            self.logger.error(f"Fehler in _handle_file_found: {str(e)}", exc_info=True)

    def _on_transfer_progress(self, filename: str, progress: float, speed: float):
        """Handler für Transfer-Fortschritt."""
        try:
            if self.main_window:
                # Hole Laufwerksbuchstaben
                drive_letter = os.path.splitdrive(filename)[0].rstrip(':')
                if drive_letter:
                    # Hole Dateigröße
                    total_size = os.path.getsize(filename)
                    transferred = int(total_size * (progress / 100))
                    
                    # Aktualisiere UI
                    self.main_window.on_progress_updated(
                        drive_letter,  # Laufwerk
                        os.path.basename(filename),  # Dateiname
                        progress,  # Fortschritt in Prozent
                        speed,  # Geschwindigkeit in MB/s
                        total_size,  # Gesamtgröße
                        transferred  # Übertragene Bytes
                    )
                    
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren des Fortschritts: {e}")

    def _on_transfer_started(self, filename: str):
        """Handler für gestartete Transfers."""
        self.logger.info(f"Transfer gestartet: {filename}")
        if self.main_window:
            QTimer.singleShot(0, lambda: self.main_window.log_message(
                f"Starte Transfer: {filename}"))
                
    def _on_transfer_completed(self, filename: str):
        """Handler für abgeschlossene Transfers."""
        self.logger.info(f"Transfer abgeschlossen: {filename}")
        if self.main_window:
            QTimer.singleShot(0, lambda: self.main_window.log_message(
                f"Transfer abgeschlossen: {filename}"))
                
    def _on_transfer_error(self, filename: str, error: str):
        """Handler für Transfer-Fehler."""
        self.logger.error(f"Transfer-Fehler für {filename}: {error}")
        if self.main_window:
            QTimer.singleShot(0, lambda: self.main_window.log_message(
                f"Fehler beim Transfer von {filename}: {error}"))

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
            
            # Verbinde Signal mit unserem Handler
            watcher.file_found.connect(self._on_file_found)
            
            watcher.start()
            
            # Speichere Watcher
            self.watchers[drive_letter] = watcher
            self.logger.info(f"Watcher für Laufwerk {drive_letter} gestartet")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Starten des Watchers: {str(e)}")
            return False

    def abort_transfers(self):
        """Bricht alle laufenden Transfers ab."""
        try:
            self.logger.info("Breche alle Transfers ab")
            
            # Stoppe den Transfer Manager
            if hasattr(self, 'transfer_manager'):
                self.transfer_manager.abort_transfers()
            
            # Stoppe die Überwachung
            self.stop()
            
            # Aktualisiere UI wenn verfügbar
            if self.main_window:
                self.main_window.abort_button.setEnabled(False)
                
        except Exception as e:
            self.logger.error(f"Fehler beim Abbrechen der Transfers: {e}")
