#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import shutil
import logging
import threading
from queue import Queue
from typing import Dict, List, Optional
from PyQt5.QtCore import QObject, pyqtSignal
from core.parallel_copier import ParallelCopier

class TransferController(QObject):
    """Controller für Dateiübertragungen."""
    
    # Signale
    transfer_started = pyqtSignal(str, str)  # source, target
    transfer_progress = pyqtSignal(str, str, int, int)  # source, target, current, total
    transfer_completed = pyqtSignal(str, str)  # source, target
    transfer_failed = pyqtSignal(str, str, str)  # source, target, error
    transfer_cancelled = pyqtSignal(str)  # source
    
    def __init__(self, parallel_copier=None):
        """Initialisiert den TransferController.
        
        Args:
            parallel_copier: Optional, ein ParallelCopier für parallele Kopien
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.parallel_copier = parallel_copier or ParallelCopier()
        self.running = False
        self.current_transfer = None
        self.transfer_queue = Queue()
        self.worker_thread = None
        
    def start_transfer(self, source: str, target: str):
        """Startet eine neue Dateiübertragung."""
        try:
            # Prüfe ob die Quelldatei existiert
            if not os.path.exists(source):
                raise FileNotFoundError(f"Quelldatei nicht gefunden: {source}")
                
            # Erstelle Zielverzeichnis falls nötig
            target_dir = os.path.dirname(target)
            os.makedirs(target_dir, exist_ok=True)
            
            # Füge Transfer zur Warteschlange hinzu
            self.transfer_queue.put((source, target))
            
            # Starte Worker-Thread falls nötig
            if not self.worker_thread or not self.worker_thread.is_alive():
                self.running = True
                self.worker_thread = threading.Thread(target=self._process_transfers)
                self.worker_thread.daemon = True
                self.worker_thread.start()
                
        except Exception as e:
            self.logger.error(f"Fehler beim Starten der Übertragung: {e}")
            self.transfer_failed.emit(source, target, str(e))
            
    def stop(self):
        """Stoppt alle Transfers und den Worker-Thread."""
        if self.running:
            self.running = False
            if self.worker_thread and self.worker_thread.is_alive():
                self.worker_thread.join()
            self.logger.info("Transfer-Controller gestoppt")
            
    def cancel_transfer(self):
        """Bricht die aktuelle Übertragung ab."""
        if self.current_transfer:
            source, _ = self.current_transfer
            self.transfer_cancelled.emit(source)
            self.current_transfer = None
            
    def _process_transfers(self):
        """Verarbeitet die Übertragungswarteschlange."""
        while self.running:
            try:
                # Hole nächsten Transfer aus der Warteschlange
                source, target = self.transfer_queue.get(timeout=1)
                self.current_transfer = (source, target)
                
                # Signalisiere Start
                self.transfer_started.emit(source, target)
                self.logger.info(f"Starte Übertragung: {source} -> {target}")
                
                # Kopiere die Datei
                total_size = os.path.getsize(source)
                copied_size = 0
                
                with open(source, 'rb') as src, open(target, 'wb') as dst:
                    while self.running:
                        chunk = src.read(8192)  # 8KB Chunks
                        if not chunk:
                            break
                            
                        dst.write(chunk)
                        copied_size += len(chunk)
                        
                        # Signalisiere Fortschritt
                        self.transfer_progress.emit(source, target, copied_size, total_size)
                        
                if self.running:
                    # Signalisiere Abschluss
                    self.transfer_completed.emit(source, target)
                    self.logger.info(f"Übertragung abgeschlossen: {source}")
                    
                    # Kopiere Metadaten
                    shutil.copystat(source, target)
                    
            except Queue.Empty:
                continue
                
            except Exception as e:
                self.logger.error(f"Fehler bei der Übertragung: {e}")
                if self.current_transfer:
                    source, target = self.current_transfer
                    self.transfer_failed.emit(source, target, str(e))
                    
            finally:
                self.current_transfer = None
                
        self.logger.info("Transfer-Worker beendet")
