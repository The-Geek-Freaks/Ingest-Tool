#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Handler für Transfer-bezogene Events."""

import logging
from datetime import datetime
import os
import time
from PyQt5.QtCore import QObject, pyqtSignal
from datetime import timedelta

logger = logging.getLogger(__name__)

class TransferEventHandlers(QObject):
    """Verwaltet Transfer-bezogene Events."""
    
    # Signal-Definitionen
    transfer_started = pyqtSignal(str, str)  # drive_letter, drive_name
    transfer_progress = pyqtSignal(str, str, float, float, int, int)  # drive_letter, filename, progress, speed, total_size, transferred
    transfer_completed = pyqtSignal(str)  # drive_letter
    transfer_error = pyqtSignal(str, str)  # drive_letter, error_message
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.logger = logging.getLogger(__name__)
        self.logger.debug("TransferEventHandlers initialisiert")
        self._transfer_times = {}  # Dictionary to store start times for each transfer
        self._transfer_bytes = {}  # Dictionary to store last transferred bytes for each file
        self._completed_files = {}  # Dictionary to store completed files per drive
        self._active_transfers = {}  # Dictionary to track active transfers per drive
        self._last_update = {}  # Dictionary to track last update time per drive
        self._last_bytes = {}  # Dictionary to track last bytes per drive for speed calculation
        self._current_speed = {}  # Dictionary to store current speed per drive
        self._update_interval = 0.25  # Update interval in seconds (reduced for more frequent updates)
        
    def connect_signals(self):
        """Verbindet Transfer-bezogene Signale."""
        try:
            self.logger.debug("Verbinde Transfer-Signale...")
            
            # Verbinde Coordinator-Signale mit dem Widget
            coordinator = self.main_window.transfer_coordinator
            widget = self.main_window.transfer_widget
            
            # Coordinator -> Widget Verbindungen
            coordinator.transfer_started.connect(widget.update_transfer_started)
            coordinator.transfer_progress.connect(widget.update_transfer_progress)
            coordinator.transfer_completed.connect(widget.transfer_completed)
            coordinator.transfer_error.connect(widget.transfer_error)
            
            # Widget -> Coordinator Verbindungen
            widget.transfer_cancelled.connect(coordinator.cancel_transfer)
            widget.transfer_retry.connect(coordinator.retry_transfer)
            widget.transfer_paused.connect(coordinator.pause_transfer)
            widget.transfer_resumed.connect(coordinator.resume_transfer)
            
            self.logger.info("Transfer-Signale erfolgreich verbunden")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Verbinden der Transfer-Signale: {e}", exc_info=True)

    def on_transfer_started(self, transfer_id: str):
        """Handler für gestartete Transfers."""
        try:
            self.logger.debug(f"Transfer gestartet - ID: {transfer_id}")
            
            # Hole Transfer-Status
            status = self.main_window.transfer_coordinator.get_transfer_status(transfer_id)
            if not status:
                self.logger.error(f"Kein Status gefunden für Transfer-ID: {transfer_id}")
                return
                
            # Extrahiere Laufwerksinformationen
            source_path = status.get('source', '')
            source_drive = os.path.splitdrive(source_path)[0]
            
            self.logger.debug(f"Emittiere transfer_started Signal für Laufwerk: {source_drive}")
            if drive_letter:
                drive_letter = drive_letter.rstrip(':')
                
                # Initialize transfer tracking for this drive if not exists
                if drive_letter not in self._active_transfers:
                    self._active_transfers[drive_letter] = set()
                    self._completed_files[drive_letter] = set()
                    self._last_update[drive_letter] = time.time()
                    self._last_bytes[drive_letter] = 0
                    self._current_speed[drive_letter] = 0
                    # Only emit signal when first file for this drive starts
                    self.transfer_started.emit(drive_letter, f"Laufwerk {drive_letter}")
                
                # Add file to active transfers for this drive
                self._active_transfers[drive_letter].add(transfer_id)
                
                # Initialize transfer tracking for this file
                self._transfer_times[transfer_id] = time.time()
                self._transfer_bytes[transfer_id] = 0
                
        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten des Transfer-Starts: {e}", exc_info=True)

    def on_transfer_progress(self, transfer_id: str, total_bytes: int, transferred_bytes: int, speed: float):
        """Handler für Transfer-Fortschritt."""
        try:
            progress = (transferred_bytes / total_bytes * 100) if total_bytes > 0 else 0
            drive_letter = os.path.splitdrive(transfer_id)[0].rstrip(':')
            if not drive_letter:
                return
                
            # Emit progress signal with all info
            self.logger.debug(
                f"Transfer-Fortschritt - ID: {transfer_id}, "
                f"Progress: {progress:.1f}%, Speed: {speed/1024/1024:.1f} MB/s"
            )
            
            self.transfer_progress.emit(
                drive_letter,
                os.path.basename(transfer_id),
                progress, speed, total_bytes, transferred_bytes
            )
                
        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten des Transfer-Fortschritts: {e}", exc_info=True)

    def on_transfer_completed(self, transfer_id: str):
        """Handler für abgeschlossene Transfers."""
        try:
            self.logger.debug(f"Transfer abgeschlossen - ID: {transfer_id}")
            drive_letter = os.path.splitdrive(transfer_id)[0].rstrip(':')
            if not drive_letter:
                return
                
            # Move file from active to completed
            if drive_letter in self._active_transfers:
                if transfer_id in self._active_transfers[drive_letter]:
                    self._active_transfers[drive_letter].remove(transfer_id)
                    if drive_letter not in self._completed_files:
                        self._completed_files[drive_letter] = set()
                    self._completed_files[drive_letter].add(transfer_id)
                    
                    # Clean up tracking
                    if transfer_id in self._transfer_times:
                        del self._transfer_times[transfer_id]
                    if transfer_id in self._transfer_bytes:
                        del self._transfer_bytes[transfer_id]
                    
                    # If no more active transfers for this drive, emit completed
                    if not self._active_transfers[drive_letter]:
                        self.logger.debug(f"Emittiere transfer_completed Signal für Laufwerk: {drive_letter}")
                        self.transfer_completed.emit(drive_letter)
                        
                        # Clean up drive tracking
                        del self._active_transfers[drive_letter]
                        del self._last_update[drive_letter]
                        del self._last_bytes[drive_letter]
                        del self._current_speed[drive_letter]
                        
        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten des Transfer-Abschlusses: {e}", exc_info=True)

    def on_transfer_error(self, transfer_id: str, error: str):
        """Handler für Transfer-Fehler."""
        try:
            self.logger.error(f"Transfer-Fehler - ID: {transfer_id}, Fehler: {error}")
            drive_letter = os.path.splitdrive(transfer_id)[0].rstrip(':')
            if drive_letter:
                # Remove from active transfers
                if drive_letter in self._active_transfers:
                    if transfer_id in self._active_transfers[drive_letter]:
                        self._active_transfers[drive_letter].remove(transfer_id)
                        
                # Clean up tracking
                if transfer_id in self._transfer_times:
                    del self._transfer_times[transfer_id]
                if transfer_id in self._transfer_bytes:
                    del self._transfer_bytes[transfer_id]
                    
                # Emit error signal
                self.logger.debug(f"Emittiere transfer_error Signal für Laufwerk: {drive_letter}")
                self.transfer_error.emit(drive_letter, error)
                
        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten des Transfer-Fehlers: {e}", exc_info=True)
            
    def on_disk_space_error(self, path: str, required: int, available: int):
        """Handler für Speicherplatzfehler."""
        self.main_window.transfer_widget.handle_disk_space_error(
            path=path,
            required=required,
            available=available
        )
        
    def on_timeout_error(self, transfer_id: str, duration: float):
        """Handler für Timeout-Fehler."""
        self.main_window.transfer_widget.handle_timeout_error(
            transfer_id=transfer_id,
            duration=duration
        )
        
    def on_transfer_retry(self, transfer_id: str):
        """Handler für Transfer-Wiederholungen."""
        try:
            # Hole original Transfer aus dem Coordinator
            coordinator = self.main_window.transfer_coordinator
            transfer = coordinator.get_transfer(transfer_id)
            
            if transfer:
                # Erstelle neuen Transfer mit gleichen Parametern
                coordinator.start_copy_for_files(
                    files=[transfer['source']],
                    target_dir=os.path.dirname(transfer['target'])
                )
                
        except Exception as e:
            self.logger.error(f"Fehler beim Wiederholen des Transfers: {e}", exc_info=True)
            
    def _update_ui_after_transfer(self):
        """Aktualisiert die UI nach einem abgeschlossenen oder fehlgeschlagenen Transfer."""
        try:
            # Prüfe ob noch aktive Transfers vorhanden sind
            active_transfers = self.main_window.transfer_coordinator.get_active_transfers()
            if not active_transfers:
                # Wenn keine aktiven Transfers mehr, aktiviere Start-Button
                if hasattr(self.main_window, 'start_button'):
                    self.main_window.start_button.setEnabled(True)
                    
                # Leere die Liste der ingestierenden Laufwerke
                self.main_window.ingesting_drives_widget.clear()
                
                # Setze Statistik zurück
                if hasattr(self.main_window, 'stats_widget'):
                    self.main_window.stats_widget.reset_stats()
                    
                # Setze Fortschritts-Widget zurück
                if hasattr(self.main_window, 'progress_widget'):
                    self.main_window.progress_widget.clear()
                
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren der UI nach Transfer: {e}", exc_info=True)
            
    def get_active_transfers(self) -> dict:
        """Gibt die aktiven Transfers zurück.
        
        Returns:
            Dictionary mit Transfer-IDs als Schlüssel
        """
        try:
            return self.main_window.transfer_coordinator.get_active_transfers()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der aktiven Transfers: {e}", exc_info=True)
            return {}

    def _handle_transfer_progress(self, transfer_id: str, filename: str, drive: str, 
                                progress: float, speed: float, total_bytes: int,
                                transferred_bytes: int, start_time: float, eta: float):
        """Behandelt Fortschrittsaktualisierungen von Transfers."""
        if self.transfer_progress_widget:
            self.transfer_progress_widget.update_transfer(
                transfer_id, filename, drive, progress, speed,
                total_bytes, transferred_bytes, start_time, eta
            )
