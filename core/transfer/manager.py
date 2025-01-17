"""
Hauptmodul für die Verwaltung von Dateiübertragungen.
"""

import os
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from queue import PriorityQueue, Empty, Queue
import threading
import traceback
import subprocess
import uuid
from typing import Dict, Optional, Callable
from datetime import datetime
from core.optimized_copy_engine import OptimizedCopyEngine, TransferStats

from .metadata import MetadataManager
from .priority import TransferPriority
from .queue_manager import QueueManager

logger = logging.getLogger(__name__)

class Manager:
    """Manager für Dateitransfers mit Prioritätswarteschlange."""
    
    def __init__(self, max_workers=4):
        self.logger = logging.getLogger(__name__)
        self.max_workers = max_workers
        self.transfers = {}  # transfer_id -> transfer_info
        self.active_transfers = set()
        self.paused_transfers = set()
        self._recursion_check = set()  # Schutz vor Rekursion
        self._lock = threading.Lock()  # Thread-Sicherheit
        self._processed_files = {}  # Dict für verarbeitete Dateien: {file_id: (size, target)}
        self.progress_trackers = {}
        
        # Initialisiere OptimizedCopyEngine
        self.copy_engine = OptimizedCopyEngine()
        self.copy_engine.set_progress_callback(self._on_copy_progress)
        
        # Queue für Transfers
        self.transfer_queue = PriorityQueue()
        
        # ThreadPool für parallele Transfers
        self.worker_pool = ThreadPoolExecutor(max_workers=max_workers)
        
        # Callbacks
        self.progress_callback = None
        self.completion_callback = None
        self.error_callback = None
        
        logger.info(f"Manager initialisiert mit {max_workers} Workern")
        
    def set_callbacks(self, progress_callback=None, completion_callback=None, error_callback=None):
        """Setzt die Callbacks für Transfer-Events."""
        self.progress_callback = progress_callback
        self.completion_callback = completion_callback
        self.error_callback = error_callback
        
    def enqueue_transfer(self, source: str, target: str, priority: TransferPriority = TransferPriority.NORMAL, metadata: dict = None) -> str:
        """Fügt einen neuen Transfer zur Warteschlange hinzu.
        
        Args:
            source: Quelldatei
            target: Zieldatei
            priority: Priorität des Transfers
            
        Returns:
            ID des Transfers
        """
        try:
            logger.info(f"[Thread {threading.current_thread().name}] "
                       f"Füge neuen Transfer hinzu: {source} -> {target}")
            
            # Generiere Transfer-ID
            transfer_id = str(uuid.uuid4())
            
            # Erstelle Transfer-Info
            self.transfers[transfer_id] = {
                'id': transfer_id,
                'source': source,
                'target': target,
                'status': 'queued',
                'priority': priority,
                'metadata': metadata or {},
                'start_time': None,
                'end_time': None,
                'progress': 0.0,
                'total_size': os.path.getsize(source),
                'processed_size': 0,
                'current_speed': 0.0,
                'estimated_time': 0
            }
            
            # Füge zur Queue hinzu
            self.transfer_queue.put((priority.value, transfer_id))
            
            # Starte Queue-Verarbeitung
            self._process_queue()
            
            return transfer_id
            
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen des Transfers: {e}", exc_info=True)
            raise
            
    def pause_drive_transfers(self, drive_letter: str):
        """Pausiert alle Transfers von einem bestimmten Laufwerk."""
        drive_letter = drive_letter.upper()
        for transfer_id, transfer in self.transfers.items():
            if transfer['source'].upper().startswith(f"{drive_letter}:"):
                self.pause_transfer(transfer_id)
                
    def pause_transfer(self, transfer_id: str):
        """Pausiert einen spezifischen Transfer."""
        if transfer_id in self.active_transfers:
            self.active_transfers.remove(transfer_id)
            self.paused_transfers.add(transfer_id)
            self.transfers[transfer_id]['status'] = 'paused'
            
    def resume_transfer(self, transfer_id: str):
        """Setzt einen pausierten Transfer fort."""
        if transfer_id in self.paused_transfers:
            self.paused_transfers.remove(transfer_id)
            self.transfers[transfer_id]['status'] = 'queued'
            self.transfer_queue.put((self.transfers[transfer_id]['priority'].value, transfer_id))
            self._process_queue()
            
    def cancel_transfer(self, transfer_id: str):
        """Bricht einen Transfer ab."""
        if transfer_id in self.active_transfers:
            self.active_transfers.remove(transfer_id)
        if transfer_id in self.paused_transfers:
            self.paused_transfers.remove(transfer_id)
        if transfer_id in self.transfers:
            self.transfers[transfer_id]['status'] = 'cancelled'
            
    def cancel_all_transfers(self):
        """Bricht alle Transfers ab."""
        logger.info("Breche alle Transfers ab")
        
        try:
            # Leere die Warteschlange
            while not self.transfer_queue.empty():
                try:
                    _, transfer_id = self.transfer_queue.get_nowait()
                    if transfer_id in self.transfers:
                        del self.transfers[transfer_id]
                except Empty:
                    break
            
            # Stoppe aktive Transfers
            for transfer_id in list(self.active_transfers):
                self.cancel_transfer(transfer_id)
                
            # Lösche alle Transfer-Informationen
            self.transfers.clear()
            self.active_transfers.clear()
            self.paused_transfers.clear()
            
        except Exception as e:
            logger.error(f"Fehler beim Abbrechen aller Transfers: {e}", exc_info=True)
            raise
            
    def get_transfer_status(self, transfer_id: str) -> Optional[Dict]:
        """Gibt den Status eines Transfers zurück.
        
        Args:
            transfer_id: ID des Transfers
            
        Returns:
            Dictionary mit Statusinformationen oder None wenn nicht gefunden
        """
        return self.transfers.get(transfer_id)
        
    def stop_all_transfers(self):
        """Stoppt alle laufenden Transfers."""
        try:
            # Stoppe alle aktiven Transfers
            for transfer_id in list(self.active_transfers):
                self._stop_transfer(transfer_id)
                
            # Leere die Warteschlange
            while not self.transfer_queue.empty():
                try:
                    self.transfer_queue.get_nowait()
                except Empty:
                    break
                    
            # Beende den Worker-Pool
            self.worker_pool.shutdown(wait=False)
            
            logger.info("Alle Transfers gestoppt")
            
        except Exception as e:
            logger.error(f"Fehler beim Stoppen der Transfers: {e}", exc_info=True)
            
    def _stop_transfer(self, transfer_id: str):
        """Stoppt einen einzelnen Transfer.
        
        Args:
            transfer_id: ID des Transfers
        """
        try:
            if transfer_id in self.transfers:
                transfer = self.transfers[transfer_id]
                transfer['status'] = 'stopped'
                if transfer_id in self.active_transfers:
                    self.active_transfers.remove(transfer_id)
                logger.info(f"Transfer {transfer_id} gestoppt")
        except Exception as e:
            logger.error(f"Fehler beim Stoppen des Transfers {transfer_id}: {e}", exc_info=True)
            
    def _process_queue(self):
        """Verarbeitet die Transfer-Warteschlange."""
        try:
            while True:
                # Hole nächsten Transfer aus der Queue
                try:
                    priority, transfer_id = self.transfer_queue.get_nowait()
                except Empty:
                    break
                    
                # Prüfe ob Transfer noch aktiv ist
                if transfer_id not in self.transfers:
                    continue
                    
                transfer_info = self.transfers[transfer_id]
                
                # Starte Transfer wenn nicht pausiert
                if transfer_id not in self.paused_transfers:
                    self._start_transfer(transfer_id)
                    
        except Exception as e:
            logger.error(f"Fehler bei Queue-Verarbeitung: {e}", exc_info=True)
            
    def _start_transfer(self, transfer_id: str):
        """Startet einen Transfer."""
        try:
            if transfer_id not in self.transfers:
                logger.warning(f"Transfer {transfer_id} nicht gefunden")
                return
                
            transfer_info = self.transfers[transfer_id]
            source = transfer_info['source']
            target = transfer_info['target']
            
            logger.info(f"Starte Transfer {transfer_id} von {source} nach {target}")
            
            # Füge zu aktiven Transfers hinzu
            self.active_transfers.add(transfer_id)
            
            # Setze Start-Zeit
            transfer_info['start_time'] = datetime.now()
            transfer_info['status'] = 'running'
            
            # Starte Transfer im ThreadPool
            self.worker_pool.submit(
                self._execute_transfer,
                transfer_id,
                source,
                target
            )
            
        except Exception as e:
            logger.error(f"Fehler beim Starten des Transfers {transfer_id}: {e}", exc_info=True)
            if self.error_callback:
                self.error_callback(transfer_id, str(e))
            raise
            
    def _execute_transfer(self, transfer_id: str, source: str, target: str):
        """Führt den eigentlichen Transfer aus."""
        try:
            # Erstelle Zielverzeichnis falls nötig
            os.makedirs(os.path.dirname(target), exist_ok=True)
            
            # Starte Transfer mit OptimizedCopyEngine
            self._copy_file(transfer_id, source, target, self._handle_progress)
            
            # Markiere Transfer als erfolgreich
            self.transfers[transfer_id]['status'] = 'completed'
            self.transfers[transfer_id]['end_time'] = datetime.now()
            self.active_transfers.remove(transfer_id)
            
            if self.completion_callback:
                self.completion_callback(transfer_id)
                
            logger.info(f"Transfer {transfer_id} erfolgreich abgeschlossen")
            
        except Exception as e:
            logger.error(f"Fehler beim Transfer {transfer_id}: {e}", exc_info=True)
            self.transfers[transfer_id]['status'] = 'failed'
            self.transfers[transfer_id]['error'] = str(e)
            self.active_transfers.remove(transfer_id)
            
            if self.error_callback:
                self.error_callback(transfer_id, str(e))
                
    def _copy_file(self, transfer_id: str, source: str, target: str, callback=None):
        """Kopiert eine Datei und aktualisiert den Fortschritt.
        
        Args:
            transfer_id: ID des Transfers
            source: Quellpfad
            target: Zielpfad
            callback: Callback für Fortschrittsupdate
        """
        try:
            # Hole Dateigröße
            total_size = os.path.getsize(source)
            
            # Speichere Transfer-Info für Progress Callback
            self.transfers[transfer_id] = {
                'source': source,
                'target': target,
                'total_bytes': total_size,
                'callback': callback,
                'file_size': total_size
            }
            
            # Kopiere Datei mit OptimizedCopyEngine
            self.copy_engine.copy_file(source, target)
            
            # Finaler Update
            if callback:
                callback(transfer_id, total_size, total_size, 0.0)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Kopieren von {source} nach {target}: {e}")
            if callback:
                callback(transfer_id, 0, 0, 0.0)
            return False

    def _on_copy_progress(self, transfer_id: str, progress: float, speed: float):
        """Callback für Fortschrittsupdates von der Copy-Engine."""
        if transfer_id in self.transfers:
            transfer = self.transfers[transfer_id]
            total_bytes = transfer.get('total_bytes', 0)
            transferred_bytes = int(total_bytes * (progress / 100))
            self._handle_progress(transfer_id, total_bytes, transferred_bytes, speed)
            
    def _handle_progress(self, transfer_id: str, total_bytes: int, transferred_bytes: int, speed: float):
        """Callback für Fortschrittsupdates."""
        if transfer_id in self.transfers:
            transfer_info = self.transfers[transfer_id]
            source = transfer_info['source']
            file_size = os.path.getsize(source)
            
            # Aktualisiere Transfer-Info
            transfer_info.update({
                'progress': transferred_bytes / total_bytes * 100,
                'processed_size': transferred_bytes,
                'current_speed': speed,
                'estimated_time': (file_size - transferred_bytes) / speed if speed > 0 else 0
            })
            
            # Rufe Callback auf
            if self.progress_callback:
                self.progress_callback(
                    transfer_id=transfer_id,
                    filename=os.path.basename(source),
                    progress=transfer_info['progress'],
                    speed=speed,
                    eta=transfer_info['estimated_time'],
                    total_size=file_size,
                    processed_size=transfer_info['processed_size']
                )
        
    def _handle_transfer_complete(self, transfer_id: str, success: bool):
        """Behandelt den Abschluss eines Transfers.
        
        Args:
            transfer_id: ID des Transfers
            success: True wenn erfolgreich
        """
        try:
            with self._lock:
                if transfer_id in self.active_transfers:
                    self.active_transfers.remove(transfer_id)
                    
                if success and self.completion_callback:
                    self.completion_callback(transfer_id)
                elif not success and self.error_callback:
                    self.error_callback(transfer_id, "Transfer fehlgeschlagen")
                    
        except Exception as e:
            logger.error(f"Fehler beim Abschluss von Transfer {transfer_id}: {str(e)}")

    def _get_file_id(self, file_path: str) -> str:
        """Generiert eine eindeutige ID für eine Datei basierend auf Name und Größe.
        
        Args:
            file_path: Pfad zur Datei
            
        Returns:
            Eindeutige ID als String
        """
        try:
            size = os.path.getsize(file_path)
            return f"{os.path.basename(file_path)}_{size}"
        except OSError as e:
            logger.error(f"Fehler beim Lesen der Dateigröße von {file_path}: {e}")
            return os.path.basename(file_path)  # Fallback auf nur Dateinamen

class TransferProgress:
    def __init__(self):
        self._last_update = time.time()
        self._total_copied = 0
        self._update_interval = 0.1  # Sekunden

    def update(self, copied_bytes):
        now = time.time()
        
        # Update nur alle 100ms
        if now - self._last_update >= self._update_interval:
            self._last_update = now
            self._total_copied += copied_bytes
            return self._total_copied / (now - self._last_update)
        return 0.0
