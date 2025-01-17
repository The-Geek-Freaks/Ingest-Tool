#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Qt-Wrapper für die OptimizedCopyEngine."""

from PyQt5.QtCore import QObject, pyqtSignal
from core.optimized_copy_engine import OptimizedCopyEngine
from datetime import datetime, timedelta
import logging

class QtCopyEngine(QObject):
    """Qt-Wrapper für die OptimizedCopyEngine mit Signal-Support."""
    
    # Signale
    copy_started = pyqtSignal(str, str)  # transfer_id, filename
    copy_progress = pyqtSignal(str, float, float, timedelta, int, int)  # transfer_id, progress, speed, eta, total, transferred
    copy_completed = pyqtSignal(str)  # transfer_id
    copy_error = pyqtSignal(str, str)  # transfer_id, error_message
    
    def __init__(self):
        """Initialisiert die Qt Copy Engine."""
        super().__init__()
        self.engine = OptimizedCopyEngine()
        self.logger = logging.getLogger(__name__)
        
        # Verbinde den Progress-Callback
        self.engine.set_progress_callback(self._on_progress)
        
    def start_copy(self, source: str, target: str) -> str:
        """Startet einen Kopiervorgang.
        
        Args:
            source: Quelldatei
            target: Zieldatei
            
        Returns:
            Transfer-ID
        """
        try:
            transfer_id = str(id(source))  # Eindeutige ID
            self.copy_started.emit(transfer_id, source)
            
            # Starte den Kopiervorgang
            future = self.engine.copy_file(source, target, transfer_id)
            
            # Füge Callback für Fertigstellung hinzu
            future.add_done_callback(
                lambda f: self._on_complete(transfer_id, f)
            )
            
            return transfer_id
            
        except Exception as e:
            self.logger.error(f"Fehler beim Starten des Kopiervorgangs: {e}", exc_info=True)
            self.copy_error.emit(transfer_id, str(e))
            return None
            
    def _on_progress(self, transfer_id: str, progress: float, speed: float,
                    total_bytes: int, transferred_bytes: int):
        """Callback für Fortschrittsupdates."""
        try:
            self.copy_progress.emit(
                transfer_id, progress, speed, timedelta(0), total_bytes, transferred_bytes
            )
        except Exception as e:
            self.logger.error(f"Fehler beim Senden des Fortschritts: {e}", exc_info=True)
            
    def _on_complete(self, transfer_id: str, future):
        """Callback für abgeschlossene Transfers."""
        try:
            # Prüfe ob ein Fehler aufgetreten ist
            error = future.exception()
            if error:
                self.copy_error.emit(transfer_id, str(error))
            else:
                self.copy_completed.emit(transfer_id)
                
        except Exception as e:
            self.logger.error(f"Fehler beim Abschließen des Transfers: {e}", exc_info=True)
            self.copy_error.emit(transfer_id, str(e))
