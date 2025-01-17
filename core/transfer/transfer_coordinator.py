#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TransferCoordinator für die Verwaltung von Dateitransfers.
Koordiniert einzelne Transfers und Batch-Operationen.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, List, Tuple, Optional, Callable
import os
import time
import asyncio
import concurrent.futures
import threading
from uuid import uuid4
from queue import PriorityQueue, Queue, Empty
from PyQt5.QtCore import (
    QObject, pyqtSignal, QMutexLocker, QMutex, 
    QThread, QTimer, Qt, Q_ARG, pyqtSlot, QMetaObject, QThreadPool
)
from PyQt5.QtWidgets import QApplication
import logging

from .exceptions import TransferError, TransferCancelled
from .settings import TransferSettings
from .status import TransferStatus
from .info import TransferInfo
from .optimized_copy_engine import OptimizedCopyEngine

class TransferStatus(Enum):
    """Status eines Transfers."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    SKIPPED = "skipped"  # Neuer Status für übersprungene Transfers

class TransferProgress:
    """Speichert den Fortschritt eines Transfers."""
    def __init__(self):
        self.progress = 0.0
        self.speed = 0.0
        self.eta = timedelta(seconds=0)
        self.total_bytes = 0
        self.transferred_bytes = 0

    def update(self, progress: float):
        """Aktualisiert den Fortschritt."""
        self.progress = progress

class TransferQueueItem:
    """Ein Element in der Transfer-Queue."""
    def __init__(self, priority: int, transfer: 'TransferInfo'):
        self.priority = priority
        self.transfer = transfer
        
    def __lt__(self, other):
        if not isinstance(other, TransferQueueItem):
            return NotImplemented
        return self.priority < other.priority

class TransferInfo:
    """Speichert Informationen über einen Transfer."""
    def __init__(self, id: str, source: str, target: str, status: 'TransferStatus', progress: float = 0.0,
                 speed: float = 0.0, eta: timedelta = timedelta(), total_size: int = 0, copied_size: int = 0,
                 start_time: datetime = None, end_time: datetime = None, error: str = None, metadata: Dict[str, Any] = None,
                 batch_id: str = None):
        self.id = id
        self.source = source
        self.target = target
        self.status = status
        self.progress = progress
        self.speed = speed
        self.eta = eta
        self.total_bytes = total_size
        self.transferred_bytes = copied_size
        self.start_time = start_time
        self.end_time = end_time
        self.error = error
        self.metadata = metadata or {}
        self.batch_id = batch_id

class TransferCoordinator(QObject):
    """Koordiniert Dateiübertragungen."""
    
    # Signale
    transfer_started = pyqtSignal(str, str)  # transfer_id, filename
    transfer_progress = pyqtSignal(str, float, float, timedelta, int, int)  # transfer_id, progress, speed, eta, total, copied
    transfer_completed = pyqtSignal(str)  # transfer_id
    transfer_error = pyqtSignal(str, str)  # transfer_id, error_message
    transfer_cancelled = pyqtSignal(str)  # transfer_id
    transfer_paused = pyqtSignal(str)  # transfer_id
    transfer_resumed = pyqtSignal(str)  # transfer_id
    transfer_skipped = pyqtSignal(str, str)  # transfer_id, reason
    
    def __init__(self, settings: Optional[Dict[str, Any]] = None, copy_engine=None):
        """Initialisiert den TransferCoordinator.
        
        Args:
            settings: Optionale Einstellungen
            copy_engine: Optional, eine Instanz der CopyEngine
        """
        super().__init__()
        
        # Initialisiere Logger
        self.logger = logging.getLogger(__name__)
        
        # Initialisiere Copy Engine
        self._copy_engine = copy_engine or OptimizedCopyEngine()
        
        # Einstellungen
        self.settings = TransferSettings(**settings) if settings else TransferSettings()
        
        # Initialisiere Datenstrukturen
        self._transfers = {}  # Dict für Transfer-Infos
        self._active_transfers = set()  # Set für aktive Transfer-IDs
        self._mutex = QMutex()  # Mutex für Thread-Sicherheit
        
        # Initialisiere Thread-Pool
        self._thread_pool = QThreadPool()
        self._thread_pool.setMaxThreadCount(4)  # Maximal 4 parallele Transfers
        
        # Queue für Transfers
        self._transfer_queue = PriorityQueue()
        
        # Thread-Synchronisation
        self._stop_event = threading.Event()
        self._queue_lock = threading.Lock()
        self._lock = threading.Lock()  # Lock für Thread-Synchronisation
        self._queue_thread = None  # Thread für Queue-Verarbeitung
        
        # Status und Tracking
        self._cancelled_transfers = set()
        self._paused_transfers = set()
        
        # Initialisiere Batch-Manager und Callbacks
        self.batch_manager = None  # Wird von außen gesetzt
        self.error_callback = None  # Wird von außen gesetzt
        self.progress_callback = None  # Wird von außen gesetzt
        
        # Starte Queue-Verarbeitung
        self.start()
        
    def _emit_signal(self, signal, *args):
        """Emittiert ein Signal thread-sicher.
        
        Args:
            signal: Das zu emittierende Signal
            *args: Argumente für das Signal
        """
        try:
            # Wenn wir im GUI-Thread sind, direkt emittieren
            if QThread.currentThread() == QApplication.instance().thread():
                signal.emit(*args)
            else:
                # Ansonsten über invokeMethod
                # Erstelle Q_ARG für jeden Parameter
                signal_args = [Q_ARG(type(arg), arg) for arg in args]
                
                # Hole Signal-Namen aus der Signal-Signatur
                signal_name = signal.signal.split('(')[0].strip('2')
                
                # Rufe invokeMethod mit Signal-Namen auf
                QMetaObject.invokeMethod(
                    self,
                    signal_name,
                    Qt.ConnectionType.QueuedConnection,
                    *signal_args
                )
        except Exception as e:
            self.logger.error(f"Fehler beim Emittieren des Signals: {e}", exc_info=True)
            # Versuche direkte Emission als Fallback
            try:
                signal.emit(*args)
            except Exception as e2:
                self.logger.error(f"Auch direktes Emittieren fehlgeschlagen: {e2}", exc_info=True)
            
    @pyqtSlot(str, str, list)
    def start_copy(self, source_drive: str, target_path: str, file_types: List[str]) -> bool:
        """Startet einen Kopiervorgang.
        
        Args:
            source_drive: Quell-Laufwerk
            target_path: Zielpfad
            file_types: Liste der Dateitypen
            
        Returns:
            bool: True wenn erfolgreich gestartet, sonst False
        """
        try:
            self.logger.info(f"Starte Kopiervorgang von {source_drive} nach {target_path}")
            
            # Prüfe Parameter
            if not all([source_drive, target_path, file_types]):
                raise ValueError("Ungültige Parameter")
                
            # Erstelle Transfer für jede Datei
            for file_type in file_types:
                self.logger.debug(f"Suche Dateien vom Typ {file_type}")
                
                # Suche Dateien
                pattern = f"*{file_type}"
                for root, _, files in os.walk(source_drive):
                    for file in files:
                        if file.endswith(file_type):
                            # Erstelle Pfade
                            source = os.path.join(root, file)
                            rel_path = os.path.relpath(source, source_drive)
                            target = os.path.join(target_path, rel_path)
                            
                            # Füge Transfer hinzu
                            self.add_transfer(source, target)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Starten des Kopiervorgangs: {e}", exc_info=True)
            return False

    def get_source_files(self, source_drive: str, file_types: List[str]) -> List[str]:
        """Gibt eine Liste der zu kopierenden Dateien zurück.
        
        Args:
            source_drive: Quelllaufwerk
            file_types: Liste der zu kopierenden Dateitypen (ohne Punkt)
            
        Returns:
            Liste der Dateipfade
        """
        files = []
        drive_path = f"{source_drive}\\"
        
        try:
            # Normalisiere die Dateiendungen
            normalized_types = []
            for ft in file_types:
                # Entferne Punkt und Wildcard falls vorhanden
                ft = ft.lower().replace(".", "").replace("*", "")
                normalized_types.append(ft)
                
            self._log_transfer_info(f"Suche nach Dateien mit Endungen: {normalized_types}")
            
            for root, _, filenames in os.walk(drive_path):
                for filename in filenames:
                    file_ext = os.path.splitext(filename)[1][1:].lower()  # Entferne Punkt und konvertiere zu Kleinbuchstaben
                    if file_ext in normalized_types:
                        full_path = os.path.join(root, filename)
                        files.append(full_path)
                        
        except Exception as e:
            self._log_transfer_info(f"Fehler beim Suchen von Dateien: {e}", "error")
            
        return files
        
    @pyqtSlot(list, str)
    def start_copy_for_files(self, files: List[str], target_dir: str, batch_name: str = None):
        """Startet den Kopiervorgang für eine Liste von Dateien.
        
        Args:
            files: Liste der zu kopierenden Dateien
            target_dir: Zielverzeichnis
            batch_name: Optionaler Name für den Batch
        """
        self.logger.info(f"Kopiere {len(files)} Dateien nach {target_dir}")
        
        # Erstelle Zielverzeichnis falls nicht vorhanden
        os.makedirs(target_dir, exist_ok=True)
        
        # Erstelle Batch wenn Name angegeben
        batch_id = None
        if batch_name:
            batch_id = self.create_batch(batch_name)
            
        # Erstelle Transfer-Liste
        transfers = []
        for source in files:
            if not os.path.exists(source):
                self.logger.warning(f"Quelldatei existiert nicht: {source}")
                continue
                
            filename = os.path.basename(source)
            target = os.path.join(target_dir, filename)
            
            # Starte Transfer
            transfer_id = self.start_transfer(source, target)
            
            # Füge zu Batch hinzu wenn vorhanden
            if batch_id:
                self.add_to_batch(batch_id, transfer_id)
                
            transfers.append(transfer_id)
            
        return transfers

    def setup_callbacks(self,
                     progress_callback: Callable[[str, float], None] = None,
                     completion_callback: Callable[[str], None] = None,
                     error_callback: Callable[[str, str], None] = None):
        """Richtet Callbacks für Transfer-Events ein.
        
        Args:
            progress_callback: Wird aufgerufen wenn sich der Fortschritt ändert (transfer_id, progress)
            completion_callback: Wird aufgerufen wenn ein Transfer abgeschlossen ist (transfer_id)
            error_callback: Wird aufgerufen wenn ein Fehler auftritt (transfer_id, error_message)
        """
        self.progress_callback = progress_callback
        self.completion_callback = completion_callback
        self.error_callback = error_callback

    def get_transfer_status(self, transfer_id: str) -> Optional[Dict[str, Any]]:
        """Gibt den Status eines Transfers zurück.
        
        Args:
            transfer_id: ID des Transfers
            
        Returns:
            Dict mit Transfer-Status oder None wenn nicht gefunden
        """
        try:
            if transfer_id not in self._transfers:
                return None
                
            transfer_info = self._transfers[transfer_id]
            
            # Erstelle Dict mit Transfer-Status
            status_dict = {
                'filename': os.path.basename(transfer_info.source),
                'status': transfer_info.status,
                'progress': transfer_info.progress,
                'speed': transfer_info.speed,
                'total_bytes': transfer_info.total_bytes,
                'transferred_bytes': transfer_info.transferred_bytes,
                'start_time': transfer_info.start_time,
                'end_time': transfer_info.end_time,
                'error': transfer_info.error
            }
            
            return status_dict
            
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen des Transfer-Status: {e}", exc_info=True)
            return None
            
    def get_active_transfers(self) -> List[Dict]:
        """Gibt eine Liste aller aktiven Transfers zurück.
        
        Returns:
            Liste von Transfer-Dictionaries
        """
        active_transfers = []
        for drive_letter, transfer_info in self.active_copies.items():
            if transfer_info:
                transfer_info['drive_letter'] = drive_letter
                active_transfers.append(transfer_info)
        return active_transfers

    def cleanup(self) -> List[str]:
        """Räumt alle Ressourcen auf.
        
        Returns:
            Liste von Fehlermeldungen während der Bereinigung
        """
        cleanup_errors = []
        
        # Stoppe Transfer Manager
        try:
            self._log_transfer_info("Stoppe Transfer Manager...")
            self.transfer_manager.stop_all_transfers()
        except Exception as e:
            error_msg = f"Fehler beim Stoppen des Transfer Managers: {e}"
            self._log_transfer_info(error_msg, "error")
            cleanup_errors.append(error_msg)
            
        # Stoppe Batch Manager
        try:
            self._log_transfer_info("Stoppe Batch Manager...")
            self.batch_manager.stop()
        except Exception as e:
            error_msg = f"Fehler beim Stoppen des Batch Managers: {e}"
            self._log_transfer_info(error_msg, "error")
            cleanup_errors.append(error_msg)
        
        return cleanup_errors

    def abort_transfers(self):
        """Bricht alle laufenden Transfers ab."""
        try:
            self.logger.info("Breche alle Transfers ab")
            with self._lock:
                # Leere die Warteschlange
                while not self._transfer_queue.empty():
                    self._transfer_queue.get()
                
                # Stoppe Copy Engine
                if hasattr(self._copy_engine, 'stop'):
                    self._copy_engine.stop()
                
                # Breche aktive Transfers ab
                for transfer_id in list(self._active_transfers):
                    self.cancel_transfer(transfer_id)
                
                # Setze Status zurück
                self._active_transfers.clear()
                self._paused_transfers.clear()
                self._cancelled_transfers.clear()
                
        except Exception as e:
            self.logger.error(f"Fehler beim Abbrechen der Transfers: {e}", exc_info=True)

    def _log_transfer_info(self, message: str, level: str = "info"):
        """Loggt Transfer-Informationen einmal."""
        log_func = getattr(self.logger, level.lower())
        log_func(message)
        
    def _on_transfer_started(self, transfer_id: str):
        """Wird aufgerufen, wenn ein Transfer gestartet wurde.
        
        Args:
            transfer_id: ID des Transfers
        """
        try:
            with self._lock:
                transfer_info = self._transfers.get(transfer_id)
                if not transfer_info:
                    self.logger.error(f"Keine Transfer-Info gefunden für ID {transfer_id}")
                    return
                    
                filename = os.path.basename(transfer_info.source)
                self.logger.debug(f"Transfer gestartet: {transfer_id} - {filename}")
                self._emit_signal(self.transfer_started, transfer_id, filename)
                
        except Exception as e:
            self.logger.error(f"Fehler beim Transfer-Start: {str(e)}", exc_info=True)

    def _on_transfer_progress(self, transfer_id: str, progress: float, speed: float,
                            eta: timedelta, total: int, transferred: int):
        """Handler für Transfer-Fortschritt."""
        self.logger.debug(f"Transfer Fortschritt: {transfer_id} - {progress:.1%} @ {speed:.1f} MB/s")
        self._emit_signal(self.transfer_progress, transfer_id, progress, speed, eta, total, transferred)
        
    def _on_transfer_completed(self, transfer_id: str):
        """Handler für abgeschlossene Transfers."""
        self.logger.debug(f"Transfer abgeschlossen: {transfer_id}")
        self._emit_signal(self.transfer_completed, transfer_id)
        
    def _on_transfer_error(self, transfer_id: str, error: str):
        """Handler für Transfer-Fehler."""
        try:
            if transfer_id not in self._transfers:
                self.logger.warning(f"Transfer {transfer_id} nicht gefunden für Fehler-Event")
                return
                
            transfer_info = self._transfers[transfer_id]
            
            # Markiere als fehlgeschlagen
            transfer_info.status = TransferStatus.ERROR
            transfer_info.error = error
            transfer_info.end_time = datetime.now()
            
            self._log_transfer_info(f"Transfer Fehler: {transfer_id} - {error}", "error")
            
            # Cleanup und Signal-Emission
            self._cleanup_transfer(transfer_id)
            self._emit_signal(self.transfer_error, transfer_id, error)
            
            # Batch-Update wenn nötig
            batch_id = self._get_batch_for_transfer(transfer_id)
            if batch_id:
                self._update_batch_status(batch_id)
                
            # Error Callback
            if self.error_callback:
                self.error_callback(transfer_id, error)
                
        except Exception as e:
            self.logger.error(f"Fehler im Error-Handler: {e}", exc_info=True)

    def _connect_copy_engine_signals(self):
        """Verbindet die Copy Engine Signale mit optimierter Event-Verarbeitung."""
        self.copy_engine.transfer_started.connect(self._on_copy_started)
        self.copy_engine.transfer_progress.connect(self._on_copy_progress)
        self.copy_engine.transfer_completed.connect(self._on_copy_completed)
        self.copy_engine.transfer_error.connect(self._on_copy_error)
            
    def _on_copy_started(self, transfer_id: str):
        """Handler für gestartete Transfers."""
        try:
            with self._lock:
                # Erstelle Progress Tracker
                self._progress_trackers[transfer_id] = TransferProgress()
                
                # Speichere Transfer-Info
                self._transfers[transfer_id] = {
                    'start_time': datetime.now(),
                    'status': TransferStatus.RUNNING
                }
                
                # Signalisiere Start
                #self.transfer_started.emit(transfer_id)
                
                # Rufe Callback auf
                if self.progress_callback:
                    self.progress_callback(transfer_id, 0)
                    
        except Exception as e:
            self._log_transfer_info(f"Fehler beim Verarbeiten des Transfer-Starts: {e}", "error")
            
    def _on_copy_progress(self, transfer_id: str, progress: float):
        """Handler für Transfer-Fortschritt."""
        try:
            with self._progress_lock:
                if transfer_id not in self._transfers:
                    return
                    
                # Update Progress Tracker
                tracker = self._progress_trackers[transfer_id]
                tracker.update(progress)
                
                # Signalisiere Fortschritt
                self.transfer_progress.emit(transfer_id, tracker.progress, tracker.speed, tracker.eta, tracker.total_bytes, tracker.transferred_bytes)
                
                # Rufe Callback auf
                if self.progress_callback:
                    self.progress_callback(transfer_id, tracker.progress)
                    
        except Exception as e:
            self._log_transfer_info(f"Fehler beim Verarbeiten des Fortschritts: {e}", "error")
            
    def _on_copy_completed(self, transfer_id: str):
        """Handler für abgeschlossene Transfers."""
        try:
            with self._lock:
                if transfer_id not in self._transfers:
                    return
                    
                transfer = self._transfers[transfer_id]
                
                # Markiere als abgeschlossen
                transfer['status'] = TransferStatus.COMPLETED
                transfer['end_time'] = datetime.now()
                
                self._log_transfer_info(f"Transfer abgeschlossen: {transfer_id}")
                
                # Rufe Callback auf
                if self.completion_callback:
                    self.completion_callback(transfer_id)
                    
                # Cleanup
                self._cleanup_transfer(transfer_id)
                
        except Exception as e:
            self._log_transfer_info(f"Fehler beim Verarbeiten des Transfer-Abschlusses: {e}", "error")
            
    def _on_copy_error(self, transfer_id: str, error: str):
        """Handler für Transfer-Fehler."""
        try:
            with self._lock:
                if transfer_id not in self._transfers:
                    return
                    
                transfer = self._transfers[transfer_id]
                
                # Markiere als fehlgeschlagen
                transfer['status'] = TransferStatus.ERROR
                transfer['error'] = error
                transfer['end_time'] = datetime.now()
                
                self._log_transfer_info(f"Transfer Fehler: {transfer_id} - {error}", "error")
                
                # Rufe Callback auf
                if self.error_callback:
                    self.error_callback(transfer_id, error)
                    
                # Cleanup
                self._cleanup_transfer(transfer_id)
                
        except Exception as e:
            self._log_transfer_info(f"Fehler beim Verarbeiten des Transfer-Fehlers: {e}", "error")
            
    def _update_batch_progress(self, transfer_id: str):
        """Aktualisiert den Fortschritt eines Batches."""
        try:
            batch_id = self._get_batch_for_transfer(transfer_id)
            if not batch_id:
                return
                
            batch = self.batch_manager.get_batch(batch_id)
            if not batch:
                return
                
            # Berechne Batch-Fortschritt
            total_progress = 0
            total_speed = 0
            total_size = 0
            total_transferred = 0
            
            for tid in batch['transfers']:
                if tid in self._progress_trackers:
                    tracker = self._progress_trackers[tid]
                    total_progress += tracker.progress
                    total_speed += tracker.speed
                    total_size += tracker.total_bytes
                    total_transferred += tracker.transferred_bytes
                    
            if batch['transfers']:
                avg_progress = total_progress / len(batch['transfers'])
                avg_speed = total_speed / len(batch['transfers'])
                eta = self._calculate_batch_eta(total_size, total_transferred, avg_speed)
                
                # Signalisiere Batch-Fortschritt
                self.batch_progress.emit(batch_id, avg_progress)
                
        except Exception as e:
            self._log_transfer_info(f"Fehler beim Aktualisieren des Batch-Fortschritts: {e}", "error")
            
    def _update_batch_status(self, transfer_id: str):
        """Aktualisiert den Status eines Batches."""
        try:
            batch_id = self._get_batch_for_transfer(transfer_id)
            if not batch_id:
                return
                
            batch = self.batch_manager.get_batch(batch_id)
            if not batch:
                return
                
            # Prüfe ob alle Transfers abgeschlossen sind
            all_completed = True
            has_errors = False
            
            for tid in batch['transfers']:
                if tid in self._transfers:
                    transfer = self._transfers[tid]
                    if transfer['status'] == TransferStatus.RUNNING:
                        all_completed = False
                    elif transfer['status'] == TransferStatus.ERROR:
                        has_errors = True
                        
            if all_completed:
                if has_errors:
                    self.batch_error.emit(batch_id, "Ein oder mehrere Transfers sind fehlgeschlagen")
                else:
                    self.batch_completed.emit(batch_id)
                    
        except Exception as e:
            self._log_transfer_info(f"Fehler beim Aktualisieren des Batch-Status: {e}", "error")
            
    def _get_batch_for_transfer(self, transfer_id: str) -> Optional[str]:
        """Findet den Batch für einen Transfer."""
        try:
            for batch_id, batch in self.batch_manager.get_batches().items():
                if transfer_id in batch['transfers']:
                    return batch_id
            return None
        except Exception as e:
            self._log_transfer_info(f"Fehler beim Suchen des Batches: {e}", "error")
            return None
            
    def _calculate_batch_eta(self, total_bytes: int, transferred_bytes: int, current_speed: float) -> Optional[timedelta]:
        """Berechnet die geschätzte verbleibende Zeit für einen Batch.
        
        Args:
            total_bytes: Gesamtgröße in Bytes
            transferred_bytes: Bereits übertragene Bytes
            current_speed: Aktuelle Geschwindigkeit in MB/s
            
        Returns:
            Geschätzte verbleibende Zeit in Sekunden oder None
        """
        try:
            if current_speed <= 0 or total_bytes <= transferred_bytes:
                return None
                
            remaining_bytes = total_bytes - transferred_bytes
            return timedelta(seconds=int(remaining_bytes / (current_speed * 1024 * 1024)))  # MB/s zu B/s
            
        except Exception as e:
            self._log_transfer_info(f"Fehler bei der ETA-Berechnung: {e}", "error")
            return None

    def create_batch(self, name: str, description: str = "") -> str:
        """Erstellt einen neuen Transfer-Batch.
        
        Args:
            name: Name des Batches
            description: Optionale Beschreibung
            
        Returns:
            Batch-ID
        """
        try:
            batch_id = str(uuid4())
            self.batch_manager.create_batch(
                batch_id=batch_id,
                name=name,
                description=description,
                created=datetime.now().isoformat()
            )
            return batch_id
        except Exception as e:
            self._log_transfer_info(f"Fehler beim Erstellen des Batches: {e}", "error")
            return None
            
    def add_to_batch(self, batch_id: str, transfer_id: str) -> bool:
        """Fügt einen Transfer zu einem Batch hinzu.
        
        Args:
            batch_id: ID des Batches
            transfer_id: ID des Transfers
            
        Returns:
            True wenn erfolgreich hinzugefügt
        """
        try:
            return self.batch_manager.add_transfer(batch_id, transfer_id)
        except Exception as e:
            self._log_transfer_info(f"Fehler beim Hinzufügen zum Batch: {e}", "error")
            return False
            
    def remove_from_batch(self, batch_id: str, transfer_id: str) -> bool:
        """Entfernt einen Transfer aus einem Batch.
        
        Args:
            batch_id: ID des Batches
            transfer_id: ID des Transfers
            
        Returns:
            True wenn erfolgreich entfernt
        """
        try:
            return self.batch_manager.remove_transfer(batch_id, transfer_id)
        except Exception as e:
            self._log_transfer_info(f"Fehler beim Entfernen aus Batch: {e}", "error")
            return False
            
    def get_batch_status(self, batch_id: str) -> Optional[dict]:
        """Gibt den Status eines Batches zurück.
        
        Args:
            batch_id: ID des Batches
            
        Returns:
            Dict mit Batch-Status oder None wenn nicht gefunden
        """
        try:
            batch = self.batch_manager.get_batch(batch_id)
            if not batch:
                return None
                
            # Sammle Status aller Transfers im Batch
            transfers = batch.get('transfers', [])
            total_bytes = 0
            transferred_bytes = 0
            current_speed = 0
            completed_transfers = 0
            
            for transfer_id in transfers:
                status = self.get_transfer_status(transfer_id)
                if status:
                    total_bytes += status['total_bytes']
                    transferred_bytes += status['transferred_bytes']
                    current_speed += status['speed']
                    if status['progress'] >= 100:
                        completed_transfers += 1
                        
            # Berechne Gesamtfortschritt
            progress = (transferred_bytes / total_bytes) * 100 if total_bytes > 0 else 0
            
            return {
                'id': batch_id,
                'name': batch['name'],
                'description': batch.get('description', ''),
                'created': batch['created'],
                'total_transfers': len(transfers),
                'completed_transfers': completed_transfers,
                'total_bytes': total_bytes,
                'transferred_bytes': transferred_bytes,
                'progress': progress,
                'current_speed': current_speed,
                'eta': self._calculate_batch_eta(total_bytes, transferred_bytes, current_speed)
            }
            
        except Exception as e:
            self._log_transfer_info(f"Fehler beim Abrufen des Batch-Status: {e}", "error")
            return None
            
    @pyqtSlot(str)
    def pause_batch(self, batch_id: str) -> None:
        """Pausiert einen Batch-Transfer.
        
        Args:
            batch_id: ID des zu pausierenden Batches
        """
        with self._lock:
            if self.batch_manager.batch_exists(batch_id):
                # Pausiere alle Transfers im Batch
                for transfer_id in self.batch_manager.get_batch_transfers(batch_id):
                    if transfer_id in self._transfers:
                        transfer = self._transfers[transfer_id]
                        if transfer['status'] == TransferStatus.RUNNING:
                            transfer['status'] = TransferStatus.PAUSED
                            transfer['paused_time'] = datetime.now()
                            self.transfer_paused.emit(transfer_id)
                
                self.batch_paused.emit(batch_id)
                self._log_transfer_info(f"Batch {batch_id} pausiert")

    @pyqtSlot(str)
    def resume_batch(self, batch_id: str) -> None:
        """Setzt einen pausierten Batch-Transfer fort.
        
        Args:
            batch_id: ID des fortzusetzenden Batches
        """
        with self._lock:
            if self.batch_manager.batch_exists(batch_id):
                # Setze alle Transfers im Batch fort
                for transfer_id in self.batch_manager.get_batch_transfers(batch_id):
                    if transfer_id in self._transfers:
                        transfer = self._transfers[transfer_id]
                        if transfer['status'] == TransferStatus.PAUSED:
                            transfer['status'] = TransferStatus.QUEUED
                            transfer['resume_time'] = datetime.now()
                            self._transfer_queue.put((transfer['priority'], transfer_id))
                            self.transfer_resumed.emit(transfer_id)
                
                self.batch_resumed.emit(batch_id)
                self._log_transfer_info(f"Batch {batch_id} fortgesetzt")
                self._process_queue()

    @pyqtSlot(str)
    def cancel_batch(self, batch_id: str) -> None:
        """Bricht einen Batch-Transfer ab.
        
        Args:
            batch_id: ID des abzubrechenden Batches
        """
        self._log_transfer_info(f"Breche Batch ab: {batch_id}")
        with self._lock:
            if batch_id not in self._batch_manager.batches:
                self._log_transfer_info(f"Batch nicht gefunden: {batch_id}", "warning")
                return
                
            batch = self._batch_manager.batches[batch_id]
            
            # Breche alle aktiven Transfers ab
            for transfer_id in batch.transfers:
                if transfer_id in self._active_transfers:
                    self.cancel_transfer(transfer_id)
                    
            # Entferne Batch
            self._batch_manager.remove_batch(batch_id)
            
            # Emittiere Batch-Error Signal
            self._emit_signal(self.batch_error, batch_id, "Batch wurde abgebrochen")
            
    @pyqtSlot(str)
    def cancel_transfer(self, transfer_id: str):
        """Bricht einen Transfer ab.
        
        Args:
            transfer_id: ID des abzubrechenden Transfers
        """
        self.logger.info(f"Breche Transfer ab: {transfer_id}")
        try:
            with self._lock:
                # Markiere Transfer als abgebrochen
                self._cancelled_transfers.add(transfer_id)
                
                # Entferne aus aktiven Transfers
                self._active_transfers.discard(transfer_id)
                
                # Entferne aus pausierten Transfers
                self._paused_transfers.discard(transfer_id)
                
                # Sende Signal
                self._emit_signal(
                    self.transfer_cancelled,
                    transfer_id
                )
                
        except Exception as e:
            self.logger.error(f"Fehler beim Abbrechen des Transfers {transfer_id}: {e}", exc_info=True)

    def start_transfer(self, source: str, target: str, priority: int = 0) -> str:
        """Startet einen neuen Transfer.
        
        Args:
            source: Pfad zur Quelldatei
            target: Pfad zur Zieldatei
            priority: Priorität des Transfers (optional)
            
        Returns:
            str: Transfer-ID
        """
        self.logger.debug(f"Starte neuen Transfer: {source} -> {target}")
        try:
            # Prüfe ob Zieldatei bereits existiert
            if os.path.exists(target):
                source_size = os.path.getsize(source)
                target_size = os.path.getsize(target)
                
                # Wenn Dateigröße identisch, überspringe Transfer
                if source_size == target_size:
                    self.logger.info(f"Datei existiert bereits mit gleicher Größe: {target}")
                    transfer_id = str(uuid4())
                    transfer_info = TransferInfo(
                        id=transfer_id,
                        source=source,
                        target=target,
                        status=TransferStatus.SKIPPED,
                        start_time=datetime.now(),
                        end_time=datetime.now()
                    )
                    
                    # Speichere Transfer-Info
                    with self._lock:
                        self._transfers[transfer_id] = transfer_info
                    
                    # Emittiere Skip-Signal
                    self._emit_signal(self.transfer_skipped, transfer_id, "Datei existiert bereits mit gleicher Größe")
                    return transfer_id
                
                # Bei unterschiedlicher Größe, generiere neuen Zielpfad
                target = self._get_unique_target_path(target)
                self.logger.info(f"Datei existiert bereits mit anderer Größe. Neuer Zielpfad: {target}")
            
            # Generiere Transfer-ID
            transfer_id = str(uuid4())
            
            # Erstelle Transfer-Info
            transfer_info = TransferInfo(
                id=transfer_id,
                source=source,
                target=target,
                status=TransferStatus.QUEUED,
                progress=0.0,
                speed=0.0,
                eta=timedelta(),
                total_size=os.path.getsize(source),
                copied_size=0,
                start_time=None,
                end_time=None,
                error=None,
                metadata={}
            )
            
            # Speichere Transfer-Info
            with self._lock:
                self._transfers[transfer_info.id] = transfer_info
            
            # Emittiere Signal für Transfer-Start
            filename = os.path.basename(source)
            self.logger.info(f"Emittiere transfer_started Signal für {transfer_id} - {filename}")
            self.transfer_started.emit(transfer_id, filename)
            
            # Füge Transfer zur Queue hinzu
            self._transfer_queue.put(TransferQueueItem(priority, transfer_info))
            
            return transfer_info.id
            
        except Exception as e:
            self.logger.error(f"Fehler beim Starten des Transfers: {e}", exc_info=True)
            raise

    def _get_unique_target_path(self, target_path: str) -> str:
        """Generiert einen eindeutigen Zielpfad wenn die Datei bereits existiert.
        
        Args:
            target_path: Original Zielpfad
            
        Returns:
            str: Eindeutiger Zielpfad
        """
        if not os.path.exists(target_path):
            return target_path
            
        directory = os.path.dirname(target_path)
        filename = os.path.basename(target_path)
        name, ext = os.path.splitext(filename)
        
        counter = 1
        while True:
            new_target = os.path.join(directory, f"{name} ({counter}){ext}")
            if not os.path.exists(new_target):
                return new_target
            counter += 1

    def start_batch_transfer(self, transfers: List[Tuple[str, str]], priority: int = 0) -> str:
        """Startet einen neuen Batch-Transfer.
        
        Args:
            transfers: Liste von (source, target) Tupeln
            priority: Priorität des Batches (optional)
            
        Returns:
            str: Batch-ID
        """
        batch_id = str(uuid4())
        
        # Initialisiere Batch
        self.batch_manager.create_batch(batch_id, len(transfers))
        self._emit_signal('batch_started', batch_id)
        self._log_transfer_info(f"Batch {batch_id} gestartet mit {len(transfers)} Transfers")
        
        # Starte alle Transfers im Batch
        for source, target in transfers:
            transfer_id = self.start_transfer(source, target, priority)
            self._transfers[transfer_id].batch_id = batch_id
            self.batch_manager.add_transfer_to_batch(batch_id, transfer_id)
            
        return batch_id

    def _handle_event(self, handler, *args):
        """Thread-sicherer Event Handler."""
        try:
            with self._lock:
                return handler(*args)
        except Exception as e:
            self._log_transfer_info(f"Fehler in Event Handler: {e}", "error")
            
    def _cleanup_transfer(self, transfer_id: str):
        """Bereinigt die Ressourcen eines Transfers."""
        with self._lock:
            self._progress_trackers.pop(transfer_id, None)
            self._transfers.pop(transfer_id, None)

    def start(self):
        """Startet die Queue-Verarbeitung in einem separaten Thread."""
        with self._queue_lock:
            if self._queue_thread is None or not self._queue_thread.is_alive():
                self._stop_event.clear()
                self._queue_thread = threading.Thread(
                    target=self._process_queue,
                    name="TransferQueueProcessor",
                    daemon=True
                )
                self._queue_thread.start()
                self.logger.info("Transfer-Queue-Verarbeitung gestartet")

    def stop(self):
        """Stoppt die Queue-Verarbeitung."""
        self.logger.info("Stoppe Transfer-Queue-Verarbeitung")
        self._stop_event.set()
        
        if self._queue_thread and self._queue_thread.is_alive():
            self._queue_thread.join(timeout=2.0)  # Warte maximal 2 Sekunden
            
        # Breche alle laufenden Transfers ab
        with self._queue_lock:
            while not self._transfer_queue.empty():
                try:
                    _, transfer_id = self._transfer_queue.get_nowait()
                    self._on_transfer_error(transfer_id, "Transfer abgebrochen")
                except Empty:
                    break
            
            # Breche aktive Transfers ab
            for transfer_id in list(self._active_transfers):
                self._on_transfer_error(transfer_id, "Transfer abgebrochen")
            
            self._active_transfers.clear()
            self._queue_thread = None
            
        self.logger.info("Transfer-Queue-Verarbeitung gestoppt")

    def _process_queue(self):
        """Verarbeitet die Transfer-Queue im Hintergrund."""
        while not self._stop_event.is_set():
            try:
                # Hole nächsten Transfer aus der Queue
                try:
                    queue_item = self._transfer_queue.get(timeout=1.0)
                    if not isinstance(queue_item, TransferQueueItem):
                        self.logger.error(f"Ungültiges Queue-Item: {queue_item}")
                        continue
                        
                    transfer_info = queue_item.transfer
                    transfer_id = transfer_info.id
                except Empty:
                    continue
                
                # Prüfe ob Transfer noch aktiv sein soll
                if transfer_id in self._cancelled_transfers:
                    self._cancelled_transfers.remove(transfer_id)
                    continue
                    
                if transfer_id in self._paused_transfers:
                    # Lege pausierte Transfers wieder in die Queue
                    self._transfer_queue.put(TransferQueueItem(0, transfer_info))
                    continue
                
                # Führe Transfer aus
                if transfer_info:
                    self._execute_transfer(transfer_info)
                else:
                    self.logger.error(f"Keine Transfer-Info gefunden für {transfer_id}")
                
            except Exception as e:
                self.logger.error(f"Fehler in Queue-Verarbeitung: {e}", exc_info=True)

    def _execute_transfer(self, transfer_info: TransferInfo):
        """Führt einen Transfer aus.
        
        Args:
            transfer_info: Informationen zum Transfer
        """
        try:
            # Prüfe ob die Datei bereits existiert und die gleiche Größe hat
            if os.path.exists(transfer_info.target):
                source_size = os.path.getsize(transfer_info.source)
                target_size = os.path.getsize(transfer_info.target)
                
                if source_size == target_size:
                    # Datei existiert bereits mit korrekter Größe
                    self.logger.info(f"Datei {transfer_info.target} existiert bereits mit korrekter Größe")
                    
                    # Setze Transfer auf 100%
                    transfer_info.progress = 100.0
                    transfer_info.transferred_bytes = source_size
                    transfer_info.total_bytes = source_size
                    transfer_info.speed = 0.0
                    transfer_info.eta = timedelta()
                    transfer_info.status = TransferStatus.COMPLETED
                    transfer_info.end_time = datetime.now()
                    
                    # Sende finales Update
                    self._emit_signal(
                        self.transfer_progress,
                        transfer_info.id,
                        100.0,
                        0.0,
                        timedelta(),
                        source_size,
                        source_size
                    )
                    
                    # Sende Abschluss-Signal
                    self._emit_signal(self.transfer_completed, transfer_info.id)
                    self.logger.info(f"Transfer {transfer_info.id} als abgeschlossen markiert (Datei existiert bereits)")
                    
                    return True
            
            # Wenn die Datei nicht existiert oder eine andere Größe hat, führe den Transfer durch
            # Setze Start-Zeit und Status
            transfer_info.start_time = datetime.now()
            transfer_info.status = TransferStatus.RUNNING
            self._emit_signal(self.transfer_started, transfer_info.id, os.path.basename(transfer_info.source))
            
            # Hole Quelldatei-Größe
            total_size = os.path.getsize(transfer_info.source)
            transfer_info.total_bytes = total_size
            
            # Erstelle Callback für Fortschritts-Updates
            def progress_callback(copied_bytes: int, total_bytes: int, speed: float):
                try:
                    if total_bytes > 0:
                        progress = (copied_bytes / total_bytes) * 100
                        transfer_info.progress = progress
                        transfer_info.transferred_bytes = copied_bytes
                        transfer_info.speed = speed
                        
                        # Berechne ETA
                        if speed > 0:
                            remaining_bytes = total_bytes - copied_bytes
                            eta_seconds = remaining_bytes / (speed * 1024 * 1024)  # speed ist in MB/s
                            transfer_info.eta = timedelta(seconds=int(eta_seconds))
                        else:
                            transfer_info.eta = timedelta()
                            
                        # Sende Fortschritts-Update
                        self._emit_signal(
                            self.transfer_progress,
                            transfer_info.id,
                            progress,
                            speed,
                            transfer_info.eta,
                            total_bytes,
                            copied_bytes
                        )
                except Exception as e:
                    self.logger.error(f"Fehler im Progress-Callback: {e}", exc_info=True)
            
            # Führe Transfer durch
            target_dir = os.path.dirname(transfer_info.target)
            os.makedirs(target_dir, exist_ok=True)
            
            # Kopiere Datei mit Fortschritts-Updates
            success = self._copy_engine.copy_file_with_progress(
                transfer_info.source,
                transfer_info.target,
                progress_callback
            )
            
            if not success:
                raise Exception("Kopiervorgang fehlgeschlagen")
            
            # Prüfe ob die Zieldatei die korrekte Größe hat
            if os.path.exists(transfer_info.target):
                target_size = os.path.getsize(transfer_info.target)
                if target_size != total_size:
                    raise Exception(f"Zieldatei hat falsche Größe: {target_size} != {total_size}")
            else:
                raise Exception("Zieldatei wurde nicht erstellt")
            
            # Setze finale Werte
            transfer_info.progress = 100.0
            transfer_info.transferred_bytes = total_size
            transfer_info.speed = 0.0
            transfer_info.eta = timedelta()
            transfer_info.status = TransferStatus.COMPLETED
            transfer_info.end_time = datetime.now()
            
            # Sende finales Update
            self._emit_signal(
                self.transfer_progress,
                transfer_info.id,
                100.0,
                0.0,
                timedelta(),
                total_size,
                total_size
            )
            
            # Sende Abschluss-Signal
            self._emit_signal(self.transfer_completed, transfer_info.id)
            self.logger.info(f"Transfer {transfer_info.id} erfolgreich abgeschlossen")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Transfer: {e}", exc_info=True)
            transfer_info.status = TransferStatus.ERROR
            transfer_info.error = str(e)
            transfer_info.end_time = datetime.now()
            self._emit_signal(self.transfer_error, transfer_info.id, str(e))
            return False

    def cancel_all(self):
        """Bricht alle Transfers ab."""
        self.logger.info("Breche alle Transfers ab")
        try:
            with self._lock:
                # Setze Stop-Event
                self._stop_event.set()
                
                # Warte auf Queue-Thread
                if self._queue_thread and self._queue_thread.is_alive():
                    self._queue_thread.join(timeout=1.0)
                
                # Leere Queue
                while not self._transfer_queue.empty():
                    try:
                        self._transfer_queue.get_nowait()
                    except Empty:
                        break
                
                # Breche aktive Transfers ab
                for transfer_id in list(self._active_transfers):
                    self.cancel_transfer(transfer_id)
                
                # Leere die Sets
                self._active_transfers.clear()
                self._queue_thread = None
            
        except Exception as e:
            self.logger.error(f"Fehler beim Abbrechen der Transfers: {e}", exc_info=True)

    def _update_progress(self, transfer_id: str, bytes_transferred: int, total_bytes: int):
        """Aktualisiert den Fortschritt eines Transfers.
        
        Args:
            transfer_id: ID des Transfers
            bytes_transferred: Anzahl der übertragenen Bytes
            total_bytes: Gesamtgröße in Bytes
        """
        try:
            # Hole oder erstelle Progress-Info
            if transfer_id not in self._progress_trackers:
                self._progress_trackers[transfer_id] = {
                    'last_update': time.time(),
                    'last_bytes': 0,
                    'speed': 0.0,
                    'eta': timedelta(seconds=0)
                }
            
            tracker = self._progress_trackers[transfer_id]
            current_time = time.time()
            time_diff = current_time - tracker['last_update']
            
            # Berechne Geschwindigkeit nur wenn genügend Zeit vergangen ist
            if time_diff >= 0.5:  # Alle 500ms updaten
                bytes_diff = bytes_transferred - tracker['last_bytes']
                speed = bytes_diff / time_diff if time_diff > 0 else 0
                
                # Aktualisiere Tracker
                tracker.update({
                    'last_update': current_time,
                    'last_bytes': bytes_transferred,
                    'speed': speed
                })
                
                # Berechne ETA
                remaining_bytes = total_bytes - bytes_transferred
                if speed > 0:
                    eta_seconds = remaining_bytes / (speed * 1024 * 1024)  # speed ist in MB/s
                    tracker['eta'] = timedelta(seconds=int(eta_seconds))
                else:
                    tracker['eta'] = timedelta()
                    
                # Berechne Fortschritt
                progress = bytes_transferred / total_bytes if total_bytes > 0 else 0
                
                # Emittiere Signal
                self._emit_signal(
                    self.transfer_progress,
                    transfer_id,
                    progress,
                    speed,
                    tracker['eta'],
                    total_bytes,
                    bytes_transferred
                )
                
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren des Fortschritts: {e}", exc_info=True)

    def _handle_transfer_completion(self, transfer_id: str, future: concurrent.futures.Future):
        """Behandelt den Abschluss eines Transfers.
        
        Args:
            transfer_id: ID des Transfers
            future: Future-Objekt des Transfers
        """
        try:
            # Hole Transfer-Info
            transfer_info = self._transfers.get(transfer_id)
            if not transfer_info:
                self.logger.error(f"Keine Transfer-Info gefunden für {transfer_id}")
                return

            # Prüfe ob der Transfer erfolgreich war
            try:
                result = future.result()
                # Sende finales Fortschritts-Update
                self._emit_signal(
                    self.transfer_progress,
                    transfer_id,
                    100.0,  # Endfortschritt
                    0.0,    # Geschwindigkeit auf 0
                    timedelta(),  # Keine verbleibende Zeit
                    transfer_info.total_bytes,
                    transfer_info.total_bytes  # Kopierte Bytes = Gesamtgröße
                )
                
                # Setze Status und sende Abschluss-Signal
                transfer_info.status = TransferStatus.COMPLETED
                transfer_info.progress = 100.0
                transfer_info.end_time = datetime.now()
                self._emit_signal(self.transfer_completed, transfer_id)
                self.logger.info(f"Transfer {transfer_id} erfolgreich abgeschlossen")
                
            except Exception as e:
                # Bei Fehler
                transfer_info.status = TransferStatus.ERROR
                transfer_info.error = str(e)
                transfer_info.end_time = datetime.now()
                self._emit_signal(self.transfer_error, transfer_id, str(e))
                self.logger.error(f"Fehler beim Transfer {transfer_id}: {e}")
                
        except Exception as e:
            self.logger.error(f"Fehler bei der Verarbeitung des Transfer-Abschlusses: {e}", exc_info=True)
        finally:
            # Entferne aus aktiven Transfers
            if transfer_id in self._active_transfers:
                self._active_transfers.remove(transfer_id)

    def _on_transfer_error(self, transfer_id: str, error_message: str):
        """Behandelt Transfer-Fehler.
        
        Args:
            transfer_id: ID des fehlgeschlagenen Transfers
            error_message: Fehlermeldung
        """
        try:
            # Aktualisiere Transfer-Status
            transfer_info = self._transfers.get(transfer_id)
            if transfer_info:
                transfer_info.status = TransferStatus.ERROR
                transfer_info.error = error_message
                transfer_info.end_time = datetime.now()
                
                # Entferne aus aktiven Transfers
                self._active_transfers.discard(transfer_id)
                
                # Sende Fehler-Signal
                self._emit_signal(self.transfer_error, transfer_id, error_message)
                
                # Logge Fehler
                self.logger.error(f"Transfer Fehler: {transfer_id} - {error_message}")
                
                # Rufe Error-Callback auf falls vorhanden
                if self.error_callback:
                    try:
                        self.error_callback(transfer_id, error_message)
                    except Exception as e:
                        self.logger.error(f"Fehler im Error-Callback: {e}", exc_info=True)
                        
                # Aktualisiere Batch falls vorhanden
                if self.batch_manager:
                    try:
                        batch_id = self.batch_manager.get_batch_for_transfer(transfer_id)
                        if batch_id:
                            self.batch_manager.update_batch_status(batch_id)
                    except Exception as e:
                        self.logger.error(f"Fehler beim Aktualisieren des Batch-Status: {e}", exc_info=True)
                
        except Exception as e:
            self.logger.error(f"Fehler im Error-Handler: {e}", exc_info=True)

    def add_transfer(self, source: str, target: str, priority: int = 0, metadata: Dict[str, Any] = None) -> str:
        """Fügt einen neuen Transfer hinzu.
        
        Args:
            source: Quellpfad
            target: Zielpfad
            priority: Priorität (0 = normal)
            metadata: Optionale Metadaten für den Transfer
            
        Returns:
            str: Transfer-ID
        """
        try:
            # Erstelle Transfer-Info
            transfer_info = TransferInfo(
                id=str(uuid4()),
                source=source,
                target=target,
                status=TransferStatus.QUEUED,
                progress=0.0,
                speed=0.0,
                eta=timedelta(),
                total_size=os.path.getsize(source),
                copied_size=0,
                start_time=None,
                end_time=None,
                error=None,
                metadata=metadata or {}
            )
            
            # Speichere Transfer-Info
            with self._lock:
                self._transfers[transfer_info.id] = transfer_info
            
            # Füge zur Queue hinzu
            self._transfer_queue.put(TransferQueueItem(priority, transfer_info))
            self.logger.info(f"Transfer hinzugefügt: {transfer_info.id}")
            
            return transfer_info.id
            
        except Exception as e:
            self.logger.error(f"Fehler beim Hinzufügen des Transfers: {e}", exc_info=True)
            raise

    @pyqtSlot(str)
    def retry_transfer(self, transfer_id: str):
        """Versucht einen fehlgeschlagenen Transfer erneut.
        
        Args:
            transfer_id: ID des zu wiederholenden Transfers
        """
        self.logger.info(f"Wiederhole Transfer: {transfer_id}")
        
        with self._lock:
            if transfer_id in self._transfers:
                transfer_info = self._transfers[transfer_id]
                # Setze Status zurück
                transfer_info.status = TransferStatus.QUEUED
                # Füge erneut zur Queue hinzu
                self._transfer_queue.put(TransferQueueItem(0, transfer_info))
                # Starte Queue-Verarbeitung
                self._process_queue()
                
                self.logger.debug(f"Transfer {transfer_id} zur Queue hinzugefügt")
            else:
                self.logger.warning(f"Transfer {transfer_id} nicht gefunden")

    @pyqtSlot(str)
    def pause_transfer(self, transfer_id: str):
        """Pausiert einen laufenden Transfer.
        
        Args:
            transfer_id: ID des zu pausierenden Transfers
        """
        self.logger.info(f"Pausiere Transfer: {transfer_id}")
        
        with self._lock:
            if transfer_id in self._transfers:
                transfer_info = self._transfers[transfer_id]
                if transfer_info.status == TransferStatus.RUNNING:
                    transfer_info.status = TransferStatus.PAUSED
                    self._emit_signal(self.transfer_paused, transfer_id)
                    self.logger.debug(f"Transfer {transfer_id} pausiert")
            else:
                self.logger.warning(f"Transfer {transfer_id} nicht gefunden")

    @pyqtSlot(str)
    def resume_transfer(self, transfer_id: str):
        """Setzt einen pausierten Transfer fort.
        
        Args:
            transfer_id: ID des fortzusetzenden Transfers
        """
        self.logger.info(f"Setze Transfer fort: {transfer_id}")
        
        with self._lock:
            if transfer_id in self._transfers:
                transfer_info = self._transfers[transfer_id]
                if transfer_info.status == TransferStatus.PAUSED:
                    transfer_info.status = TransferStatus.QUEUED
                    # Füge erneut zur Queue hinzu
                    self._transfer_queue.put(TransferQueueItem(0, transfer_info))
                    # Starte Queue-Verarbeitung
                    self._process_queue()
                    
                    self._emit_signal(self.transfer_resumed, transfer_id)
                    self.logger.debug(f"Transfer {transfer_id} fortgesetzt")
            else:
                self.logger.warning(f"Transfer {transfer_id} nicht gefunden")
