#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VERALTET: Diese Datei ist veraltet und wird in einer zukünftigen Version entfernt.
Bitte verwenden Sie stattdessen core.transfer_controller.
"""

import warnings

warnings.warn(
    "Das Modul transfer ist veraltet. "
    "Bitte verwenden Sie stattdessen core.transfer_controller.",
    DeprecationWarning,
    stacklevel=2
)

from .transfer_controller import TransferController

# Abwärtskompatibilität
TransferManager = TransferController

import os
import json
import logging
import threading
from queue import Queue, Empty
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal
from typing import Dict, List, Set, Any, Optional
from pathlib import Path

"""
Verwaltet Dateiübertragungen.
"""
import time
import shutil

class SpeicherplatzFehler(Exception):
    """Wird ausgelöst, wenn nicht genügend Speicherplatz verfügbar ist."""
    pass

class TransferManager(QObject):
    """Verwaltet Dateiübertragungen."""
    
    # Definiere die Signale
    transfer_started = pyqtSignal(str, str)  # source, target
    transfer_progress = pyqtSignal(str, str, int, int)  # source, target, current, total
    transfer_completed = pyqtSignal(str, str)  # source, target
    transfer_failed = pyqtSignal(str, str, str)  # source, target, error
    transfer_cancelled = pyqtSignal(str)  # source
    
    def __init__(self):
        """Initialisiert den TransferManager."""
        super().__init__()
        
        self.transfers = {}  # Alle Transfers
        self.active_transfers = {}  # Aktive Transfers nach Laufwerk gruppiert
        self.transfer_queue = Queue()
        self.max_transfers = 2
        self.current_transfer = None
        self.running = True
        
        # Starte Worker-Thread für Übertragungen
        self.worker_thread = threading.Thread(target=self._process_transfers)
        self.worker_thread.daemon = True
        self.worker_thread.start()
        
    def start_transfer(self, source_path: str, target_path: str):
        """Startet eine neue Dateiübertragung.
        
        Args:
            source_path: Quellpfad der Datei
            target_path: Zielpfad für die Datei
        """
        try:
            # Füge Transfer zur Warteschlange hinzu
            self.transfer_queue.put((source_path, target_path))
            
        except Exception as e:
            self.transfer_failed.emit(source_path, target_path, str(e))
            
    def cancel_transfer(self):
        """Bricht die aktuelle Übertragung ab."""
        if self.current_transfer:
            self.running = False
            self.transfer_cancelled.emit(self.current_transfer[0])
            
    def _process_transfers(self):
        """Verarbeitet die Übertragungswarteschlange."""
        while self.running:
            try:
                source_path, target_path = self.transfer_queue.get(timeout=1)
                self.current_transfer = (source_path, target_path)
                
                # Signalisiere Start
                self.transfer_started.emit(source_path, target_path)
                
                # Erstelle Zielverzeichnis falls nötig
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                
                # Kopiere Datei
                total_size = os.path.getsize(source_path)
                copied_size = 0
                
                with open(source_path, 'rb') as src, open(target_path, 'wb') as dst:
                    while self.running:
                        chunk = src.read(8192)  # 8KB Chunks
                        if not chunk:
                            break
                            
                        dst.write(chunk)
                        copied_size += len(chunk)
                        
                        # Signalisiere Fortschritt
                        self.transfer_progress.emit(source_path, target_path, copied_size, total_size)
                        
                if self.running:
                    # Signalisiere Abschluss
                    self.transfer_completed.emit(source_path, target_path)
                    
                    # Kopiere Metadaten
                    try:
                        shutil.copystat(source_path, target_path)
                    except Exception as e:
                        logging.error(f"Fehler beim Kopieren der Metadaten: {str(e)}")
                        
            except Empty:
                # Queue ist leer, warte auf neue Transfers
                continue
            except Exception as e:
                if self.current_transfer:
                    self.transfer_failed.emit(self.current_transfer[0], self.current_transfer[1], str(e))
                self.running = False
            finally:
                self.current_transfer = None
                self.transfer_queue.task_done()
                
    def shutdown(self):
        """Beendet den TransferManager."""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join()
            
    def __del__(self):
        """Destruktor."""
        self.shutdown()
