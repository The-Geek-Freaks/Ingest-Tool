#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Adapter für die OptimizedCopyEngine zur Integration mit der UI.
"""

import os
import uuid
import logging
import threading
from typing import Dict, Optional
from datetime import datetime, timedelta
from PyQt5.QtCore import QObject, pyqtSignal

from core.optimized_copy_engine import OptimizedCopyEngine, TransferStats
from core.transfer.transfer_progress import TransferProgress

logger = logging.getLogger(__name__)

class CopyEngineAdapter(QObject):
    """Adapter für die OptimizedCopyEngine zur Integration mit der UI."""
    
    # Signale für UI-Updates
    transfer_started = pyqtSignal(str, str)  # transfer_id, filename
    transfer_progress = pyqtSignal(str, float, float, timedelta, int, int)  # transfer_id, progress, speed, eta, total, transferred
    transfer_completed = pyqtSignal(str)  # transfer_id
    transfer_error = pyqtSignal(str, str)  # transfer_id, error
    
    def __init__(self):
        """Initialisiert den CopyEngineAdapter."""
        super().__init__()
        self._engine = OptimizedCopyEngine()
        self._active_transfers: Dict[str, dict] = {}
        self._progress_trackers: Dict[str, TransferProgress] = {}
        self._lock = threading.Lock()
        
        # Setze Callback für Fortschrittsupdates
        self._engine.set_progress_callback(self._progress_callback)
        
    def start_transfer(self, source: str, target: str) -> str:
        """Startet einen neuen Dateitransfer.
        
        Args:
            source: Pfad zur Quelldatei
            target: Pfad zur Zieldatei (vollständiger Pfad inkl. Dateiname)
            
        Returns:
            str: Transfer-ID (UUID)
        """
        try:
            logger.debug(f"Starte Transfer von {source} nach {target}")
            
            # Erstelle Transfer-ID
            transfer_id = str(uuid.uuid4())
            filename = os.path.basename(source)
            
            with self._lock:
                # Erstelle Progress Tracker
                self._progress_trackers[transfer_id] = TransferProgress()
                
                # Speichere Transfer-Informationen
                self._active_transfers[transfer_id] = {
                    'filename': filename,
                    'source': source,
                    'target': target,
                    'start_time': datetime.now(),
                    'status': 'running'
                }
                
            # Signalisiere Start
            self.transfer_started.emit(transfer_id, filename)
            
            # Starte Transfer
            future = self._engine.copy_file(source, target, transfer_id)
            future.add_done_callback(
                lambda f: self._transfer_completed(transfer_id, f)
            )
            
            return transfer_id
            
        except Exception as e:
            logger.error(f"Fehler beim Starten des Transfers: {e}", exc_info=True)
            if transfer_id:
                self.transfer_error.emit(transfer_id, str(e))
            raise
            
    def _progress_callback(self, transfer_id: str, progress: float, speed: float, total_bytes: int, transferred_bytes: int):
        """Callback für Fortschrittsupdates von der Engine."""
        try:
            with self._lock:
                if transfer_id not in self._active_transfers:
                    return
                    
                transfer = self._active_transfers[transfer_id]
                tracker = self._progress_trackers[transfer_id]
                
                # Update Progress Tracker mit den exakten Werten von der Engine
                current_speed = tracker.update(transferred_bytes, total_bytes)
                
                # Berechne ETA
                if current_speed > 0:
                    remaining_bytes = total_bytes - transferred_bytes
                    eta_seconds = remaining_bytes / current_speed
                    eta = timedelta(seconds=int(eta_seconds))
                else:
                    eta = timedelta.max
                    
                # Sende Update an UI
                self.transfer_progress.emit(
                    transfer_id,
                    progress,
                    current_speed,
                    eta,
                    total_bytes,
                    transferred_bytes
                )
                
        except Exception as e:
            logger.error(f"Fehler im Progress-Callback: {e}", exc_info=True)
            
    def _transfer_completed(self, transfer_id: str, future):
        """Callback für abgeschlossene Transfers."""
        try:
            with self._lock:
                if transfer_id not in self._active_transfers:
                    return
                    
                transfer = self._active_transfers[transfer_id]
                
                try:
                    # Prüfe ob ein Fehler aufgetreten ist
                    future.result()
                    
                    # Markiere als abgeschlossen
                    transfer['status'] = 'completed'
                    self.transfer_completed.emit(transfer_id)
                    
                except Exception as e:
                    # Markiere als fehlgeschlagen
                    transfer['status'] = 'error'
                    transfer['error'] = str(e)
                    self.transfer_error.emit(transfer_id, str(e))
                    
                finally:
                    # Cleanup
                    self._cleanup_transfer(transfer_id)
                    
        except Exception as e:
            logger.error(f"Fehler beim Abschließen des Transfers: {e}", exc_info=True)
            
    def _cleanup_transfer(self, transfer_id: str):
        """Bereinigt die Ressourcen eines Transfers."""
        with self._lock:
            self._progress_trackers.pop(transfer_id, None)
            self._active_transfers.pop(transfer_id, None)
            
    def cancel_transfer(self, transfer_id: str):
        """Bricht einen Transfer ab."""
        try:
            with self._lock:
                if transfer_id not in self._active_transfers:
                    return
                    
                transfer = self._active_transfers[transfer_id]
                
                # Lösche temporäre Dateien
                if os.path.exists(transfer['target']):
                    try:
                        os.remove(transfer['target'])
                    except:
                        pass
                        
                # Markiere als abgebrochen
                transfer['status'] = 'cancelled'
                
                # Cleanup
                self._cleanup_transfer(transfer_id)
                
        except Exception as e:
            logger.error(f"Fehler beim Abbrechen des Transfers: {e}", exc_info=True)
            
    def get_transfer_status(self, transfer_id: str) -> Optional[dict]:
        """Gibt den Status eines Transfers zurück."""
        with self._lock:
            if transfer_id in self._active_transfers:
                transfer = self._active_transfers[transfer_id]
                tracker = self._progress_trackers.get(transfer_id)
                
                if tracker:
                    return {
                        'filename': transfer['filename'],
                        'source': transfer['source'],
                        'target': transfer['target'],
                        'start_time': transfer['start_time'],
                        'status': transfer['status'],
                        'progress': tracker.progress,
                        'speed': tracker.speed,
                        'eta': tracker.eta,
                        'transferred_bytes': tracker.transferred_bytes,
                        'total_bytes': tracker.total_bytes
                    }
            return None
