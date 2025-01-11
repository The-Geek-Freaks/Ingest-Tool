#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import shutil
from pathlib import Path
from typing import Optional
import threading
from queue import Queue, Empty
from PyQt5.QtCore import QObject, pyqtSignal
import time

class FileTransferManager(QObject):
    """Verwaltet den Dateitransfer zwischen Quell- und Zielverzeichnissen."""
    
    # Signale für Transfer-Events
    transfer_started = pyqtSignal(str)  # Dateiname
    transfer_progress = pyqtSignal(str, float)  # Dateiname, Prozent
    transfer_completed = pyqtSignal(str)  # Dateiname
    transfer_error = pyqtSignal(str, str)  # Dateiname, Fehlermeldung
    transfer_aborted = pyqtSignal()  # Signal wenn Transfers abgebrochen wurden
    
    def __init__(self):
        """Initialisiert den FileTransferManager."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self._transfer_queue = Queue()
        self._transfer_thread = None
        self._running = False
        self._current_transfer = None
        self._start_time = None
        self._active_transfers = {}  # Track active transfers
        self._abort_requested = False
        
        # Starte Transfer-Thread
        self._start_transfer_thread()
        
    def _start_transfer_thread(self):
        """Startet den Transfer-Thread."""
        if self._transfer_thread is None or not self._transfer_thread.is_alive():
            self._running = True
            self._transfer_thread = threading.Thread(target=self._process_transfers)
            self._transfer_thread.daemon = True
            self._transfer_thread.start()
            
    def _process_transfers(self):
        """Verarbeitet die Transfer-Queue."""
        while self._running:
            try:
                # Prüfe auf Abbruch-Anforderung
                if self._abort_requested:
                    self._abort_requested = False
                    self._transfer_queue = Queue()  # Leere Queue
                    self._active_transfers.clear()
                    self.transfer_aborted.emit()
                    continue

                # Hole nächsten Transfer aus der Queue
                source_path, target_dir = self._transfer_queue.get(timeout=1.0)
                self._current_transfer = source_path
                
                try:
                    # Führe Transfer durch
                    success = self._transfer_file(source_path, target_dir)
                    
                    if success:
                        self.transfer_completed.emit(source_path)
                    else:
                        self.transfer_error.emit(source_path, "Transfer fehlgeschlagen")
                        
                except Exception as e:
                    self.logger.error(f"Fehler beim Transfer von {source_path}: {str(e)}", exc_info=True)
                    self.transfer_error.emit(source_path, str(e))
                    
                finally:
                    if source_path in self._active_transfers:
                        del self._active_transfers[source_path]
                    self._current_transfer = None
                    self._transfer_queue.task_done()
                    
            except Empty:
                # Queue ist leer, warte auf neue Transfers
                continue
            except Exception as e:
                self.logger.error(f"Fehler im Transfer-Thread: {str(e)}", exc_info=True)
                time.sleep(1)
                
    def transfer_file(self, source_path: str, target_dir: str) -> bool:
        """
        Fügt einen Dateitransfer zur Queue hinzu.
        
        Args:
            source_path: Vollständiger Pfad zur Quelldatei
            target_dir: Zielverzeichnis für die Datei
            
        Returns:
            bool: True wenn Transfer zur Queue hinzugefügt wurde
        """
        try:
            # Validiere Eingaben
            if not source_path or not target_dir:
                self.logger.error("Ungültige Parameter")
                return False
                
            # Track this transfer
            self._active_transfers[source_path] = {
                'start_time': time.time(),
                'total_size': os.path.getsize(source_path),
                'transferred': 0
            }
            
            # Füge Transfer zur Queue hinzu
            self._transfer_queue.put((source_path, target_dir))
            self.transfer_started.emit(source_path)
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Hinzufügen des Transfers: {str(e)}", exc_info=True)
            return False
            
    def _transfer_file(self, src_path: str, dst_path: str) -> bool:
        """Führt den eigentlichen Dateitransfer durch."""
        try:
            # Normalisiere Pfade
            src_path = os.path.normpath(src_path)
            dst_path = os.path.normpath(dst_path)
            
            # Prüfe ob Quelldatei existiert und lesbar ist
            if not os.path.exists(src_path):
                error_msg = f"Quelldatei nicht gefunden: {src_path}"
                self.logger.error(error_msg)
                self.transfer_error.emit(src_path, error_msg)
                return False
                
            # Prüfe ob Quelldatei gesperrt ist
            try:
                with open(src_path, 'rb') as test_file:
                    pass
            except IOError as e:
                error_msg = f"Quelldatei ist gesperrt oder nicht zugänglich: {src_path} - {str(e)}"
                self.logger.error(error_msg)
                self.transfer_error.emit(src_path, error_msg)
                return False
            
            # Stelle sicher, dass das Zielverzeichnis existiert
            dst_dir = os.path.dirname(dst_path)
            try:
                if not os.path.exists(dst_dir):
                    os.makedirs(dst_dir, exist_ok=True)
                    self.logger.info(f"Zielverzeichnis erstellt: {dst_dir}")
                
                # Teste Schreibrechte im Zielverzeichnis
                test_file = os.path.join(dst_dir, '.test_write')
                try:
                    with open(test_file, 'w') as f:
                        f.write('test')
                    os.remove(test_file)
                except (IOError, OSError) as e:
                    error_msg = f"Keine Schreibrechte im Zielverzeichnis {dst_dir}: {str(e)}"
                    self.logger.error(error_msg)
                    self.transfer_error.emit(src_path, error_msg)
                    return False
                    
            except Exception as e:
                error_msg = f"Fehler beim Erstellen des Zielverzeichnisses {dst_dir}: {str(e)}"
                self.logger.error(error_msg)
                self.transfer_error.emit(src_path, error_msg)
                return False
            
            # Bestimme Zieldatei
            filename = os.path.basename(src_path)
            dst_path = os.path.join(dst_dir, filename)
            
            # Hole Dateigröße für Fortschrittsberechnung
            total_size = os.path.getsize(src_path)
            transferred = 0
            
            # Kopiere die Datei in Blöcken
            try:
                with open(src_path, 'rb') as src, open(dst_path, 'wb') as dst:
                    while True:
                        chunk = src.read(8192)  # 8KB Blöcke
                        if not chunk:
                            break
                        dst.write(chunk)
                        transferred += len(chunk)
                        
                        # Update transfer tracking
                        if src_path in self._active_transfers:
                            self._active_transfers[src_path]['transferred'] = transferred
                        
                        # Berechne und emittiere Fortschritt
                        progress = (transferred / total_size) * 100
                        self.transfer_progress.emit(src_path, progress)
                        
            except IOError as e:
                error_msg = f"Fehler beim Lesen/Schreiben: {str(e)}"
                self.logger.error(error_msg)
                self.transfer_error.emit(src_path, error_msg)
                if os.path.exists(dst_path):
                    try:
                        os.remove(dst_path)
                    except:
                        pass
                return False
                        
            # Prüfe ob die Zieldatei existiert und die gleiche Größe hat
            if not os.path.exists(dst_path):
                error_msg = f"Zieldatei wurde nicht erstellt: {dst_path}"
                self.logger.error(error_msg)
                self.transfer_error.emit(src_path, error_msg)
                return False
                
            if os.path.getsize(src_path) != os.path.getsize(dst_path):
                error_msg = f"Größenunterschied zwischen Quelle und Ziel: {src_path}"
                self.logger.error(error_msg)
                self.transfer_error.emit(src_path, error_msg)
                try:
                    os.remove(dst_path)  # Lösche fehlerhafte Zieldatei
                except:
                    pass
                return False
                
            # Emittiere 100% Fortschritt am Ende
            self.transfer_progress.emit(src_path, 100.0)
            self.transfer_completed.emit(src_path)
            self.logger.info(f"Transfer erfolgreich: {dst_path}")
            
            # Lösche Quelldatei wenn aktiviert
            if self.parent() and self.parent().settings.get('delete_source_files', False):
                try:
                    os.remove(src_path)
                    self.logger.info(f"Quelldatei gelöscht: {src_path}")
                except Exception as e:
                    self.logger.error(f"Fehler beim Löschen der Quelldatei {src_path}: {str(e)}")
            
            return True
            
        except Exception as e:
            error_msg = f"Fehler beim Transfer: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.transfer_error.emit(src_path, error_msg)
            # Versuche fehlerhafte Zieldatei zu löschen
            try:
                if os.path.exists(dst_path):
                    os.remove(dst_path)
            except:
                pass
            return False
            
    def _ensure_dir_exists(self, directory: str) -> bool:
        """Stellt sicher, dass das Verzeichnis existiert."""
        try:
            os.makedirs(directory, exist_ok=True)
            return True
        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen des Verzeichnisses {directory}: {e}")
            return False
    
    def _verify_file_size(self, source: str, target: str) -> bool:
        """Überprüft, ob die Dateigröße von Quelle und Ziel übereinstimmt."""
        try:
            source_size = os.path.getsize(source)
            target_size = os.path.getsize(target)
            return source_size == target_size
        except Exception as e:
            self.logger.error(f"Fehler beim Größenvergleich: {e}")
            return False
    
    def _get_unique_target_path(self, target_dir: str, filename: str) -> str:
        """Generiert einen eindeutigen Zielpfad."""
        base_path = os.path.join(target_dir, filename)
        if not os.path.exists(base_path):
            return base_path
            
        name, ext = os.path.splitext(filename)
        counter = 1
        while True:
            new_path = os.path.join(target_dir, f"{name}({counter}){ext}")
            if not os.path.exists(new_path):
                return new_path
            counter += 1
            
    def stop(self):
        """Stoppt den Transfer-Thread."""
        self._running = False
        if self._transfer_thread:
            self._transfer_thread.join(timeout=1.0)
            self._transfer_thread = None
            
    def abort_transfers(self):
        """Bricht alle laufenden Transfers ab."""
        self._abort_requested = True
        self.logger.info("Alle Transfers werden abgebrochen")
