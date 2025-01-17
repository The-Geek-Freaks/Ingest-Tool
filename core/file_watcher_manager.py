#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Verwaltet die Dateiüberwachung für verschiedene Laufwerke.
"""

import logging
import os
import threading
from typing import Dict, List, Optional, Set, Callable, Any, Tuple
from PyQt5.QtCore import (
    QObject, pyqtSignal, pyqtSlot, Qt, QMutex,
    QMutexLocker, QTimer
)
from PyQt5.QtGui import QTextCursor
from utils.file_watcher import FileWatcher as BaseFileWatcher
from core.transfer.transfer_coordinator import TransferCoordinator
import sys
import time

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
    
    def __init__(self, main_window):
        """Initialisiert den FileWatcherManager.
        
        Args:
            main_window: Hauptfenster der Anwendung
        """
        super().__init__()
        
        # Logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("FileWatcherManager initialisiert")
        
        # Referenz auf Hauptfenster
        self.main_window = main_window
        
        # Hole TransferCoordinator vom Hauptfenster
        if not hasattr(main_window, 'transfer_coordinator'):
            self.logger.error("MainWindow hat keinen TransferCoordinator")
            raise AttributeError("MainWindow muss einen TransferCoordinator haben")
        self.transfer_coordinator = main_window.transfer_coordinator
        
        # Verbinde Signale
        self.transfer_coordinator.transfer_started.connect(
            self._on_transfer_started,
            type=Qt.QueuedConnection
        )
        self.transfer_coordinator.transfer_completed.connect(
            self._on_transfer_completed,
            type=Qt.QueuedConnection
        )
        self.transfer_coordinator.transfer_error.connect(
            self._on_transfer_error,
            type=Qt.QueuedConnection
        )
        
        # Initialisiere Watcher
        self._watchers: Dict[str, SignalFileWatcher] = {}  # Pfad -> FileWatcher
        self._mappings: Dict[str, str] = {}  # Dateityp -> Zielverzeichnis
        self._excluded_drives: Set[str] = set()  # Ausgeschlossene Laufwerke
        
        # Threading
        self._mutex = QMutex()
        self._is_watching = False
        self._processed_files: Dict[str, float] = {}
        self._processed_files_lock = threading.Lock()
        self._transfer_in_progress = False

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
            self._excluded_drives = set(drives)
            self.logger.info(f"Ausgeschlossene Laufwerke aktualisiert: {self._excluded_drives}")
            
            # Stoppe Watcher für ausgeschlossene Laufwerke
            for drive in list(self._watchers.keys()):
                if drive in self._excluded_drives:
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
            if not drive_letter or drive_letter in self._watchers:
                return
                
            # Erstelle Pfad
            drive_path = f"{drive_letter}:\\"
            
            # Hole aktuelle Dateitypen aus den Zuordnungen
            file_types = list(self._mappings.keys())
            if not file_types:
                self.logger.warning(f"Keine Dateitypen konfiguriert für {drive_path}")
                return
                
            # Erstelle und starte Watcher
            watcher = SignalFileWatcher(drive_path, file_types)
            
            # Verbinde Signal direkt mit unserem Handler
            watcher.file_found.connect(self._handle_new_file)
            
            # Starte Überwachung
            watcher.start()
            
            # Speichere Watcher
            self._watchers[drive_letter] = watcher
            self.logger.info(f"Überwachung von {drive_path} gestartet")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Starten der Überwachung für {drive_letter}: {str(e)}", exc_info=True)

    def stop_watcher(self, drive_letter: str):
        """Stoppt den Watcher für das angegebene Laufwerk."""
        try:
            if drive_letter in self._watchers:
                watcher = self._watchers[drive_letter]
                watcher.stop()
                del self._watchers[drive_letter]
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
            for drive, watcher in self._watchers.items():
                try:
                    watcher.stop()
                    self.logger.info(f"Überwachung von {drive}:\\ gestoppt")
                except Exception as e:
                    self.logger.error(f"Fehler beim Stoppen des Watchers für {drive}: {e}")
            
            # Stoppe auch den Transfer Manager
            if hasattr(self, 'transfer_coordinator'):
                self.transfer_coordinator.abort_transfers()
            
            self._watchers.clear()
            self._is_watching = False
            
            # Lösche verarbeitete Dateien und setze Transfer-Status zurück
            with self._processed_files_lock:
                self._processed_files.clear()
                self._transfer_in_progress = False
            
            self.logger.info("Datenträgerüberwachung gestoppt")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Stoppen der Überwachung: {e}")

    def update_file_mappings(self):
        """Aktualisiert die Zuordnungen zwischen Dateitypen und Zielverzeichnissen."""
        try:
            self._mappings.clear()
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
                        self._mappings[clean_type.lower()] = target_path
                        self.logger.info(f"Zuordnung hinzugefügt: {clean_type} -> {target_path}")
                        
            self.logger.debug(f"Aktualisierte Zuordnungen: {self._mappings}")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren der Zuordnungen: {str(e)}", exc_info=True)

    def _handle_new_file(self, file_path: str):
        """Verarbeitet eine neue Datei."""
        try:
            # Prüfe ob die Datei bereits verarbeitet wird oder ein Transfer läuft
            with self._processed_files_lock:
                if file_path in self._processed_files or self._transfer_in_progress:
                    return
                
                # Prüfe Dateiendung
                _, ext = os.path.splitext(file_path)
                ext = ext.lower()
                
                # Finde passendes Zielverzeichnis
                if ext not in self._mappings:
                    self.logger.debug(f"Keine Zuordnung für Dateiendung {ext}")
                    return
                    
                target_dir = self._mappings[ext]
                if not target_dir:
                    self.logger.warning(f"Kein Zielverzeichnis für {ext}")
                    return
                    
                # Erstelle Zielverzeichnis wenn nicht vorhanden
                if not os.path.exists(target_dir):
                    try:
                        os.makedirs(target_dir)
                    except Exception as e:
                        self.logger.error(f"Fehler beim Erstellen des Zielverzeichnisses: {e}")
                        return
                
                # Berechne Zielpfad (direkt im Zielverzeichnis, ohne Unterordner)
                filename = os.path.basename(file_path)
                target_path = os.path.join(target_dir, filename)
                
                # Starte Transfer
                self.logger.info(f"Starte Transfer: {file_path} -> {target_path}")
                self.transfer_coordinator.start_transfer(file_path, target_path)
                
                # Markiere Datei als verarbeitet
                self._processed_files[file_path] = time.time()
                
        except Exception as e:
            self.logger.error(f"Fehler bei der Verarbeitung von {file_path}: {str(e)}", exc_info=True)

    @pyqtSlot(str, str)
    def _on_transfer_started(self, transfer_id: str, filename: str):
        """Handler für gestartete Transfers."""
        self.logger.debug(f"Transfer gestartet: {transfer_id} - {filename}")
        
    @pyqtSlot(str)
    def _on_transfer_completed(self, transfer_id: str):
        """Handler für abgeschlossene Transfers."""
        self.logger.debug(f"Transfer abgeschlossen: {transfer_id}")
        
    @pyqtSlot(str, str)
    def _on_transfer_error(self, transfer_id: str, error: str):
        """Handler für Transfer-Fehler."""
        self.logger.debug(f"Transfer-Fehler: {transfer_id} - {error}")

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
            if drive_letter in self._watchers:
                self.stop_watcher(drive_letter)
            
            # Erstelle und starte neuen Watcher
            watcher = SignalFileWatcher(drive_path, file_types)
            
            # Verbinde Signal mit unserem Handler
            watcher.file_found.connect(self._handle_new_file)
            
            watcher.start()
            
            # Speichere Watcher
            self._watchers[drive_letter] = watcher
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
            if hasattr(self, 'transfer_coordinator'):
                self.transfer_coordinator.abort_transfers()
            
            # Stoppe die Überwachung
            self.stop()
            
            # Aktualisiere UI wenn verfügbar
            if self.main_window:
                self.main_window.abort_button.setEnabled(False)
                
        except Exception as e:
            self.logger.error(f"Fehler beim Abbrechen der Transfers: {e}")
