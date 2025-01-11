#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Handler für Transfer-bezogene Events."""

import logging
from datetime import datetime
import os
import time
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

class TransferEventHandlers(QObject):
    """Verwaltet Transfer-bezogene Events."""
    
    # Define signals
    transfer_started = pyqtSignal(str, str)  # drive_letter, drive_name
    transfer_progress = pyqtSignal(str, str, float, float, int, int)  # drive_letter, filename, progress, speed, total_size, transferred
    transfer_completed = pyqtSignal(str)  # drive_letter
    transfer_error = pyqtSignal(str, str)  # drive_letter, error_message
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
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
            if hasattr(self.main_window, 'progress_widget'):
                self.main_window.progress_widget.progress_updated.connect(self.main_window.on_progress_updated)
            
            self.main_window.transfer_coordinator.setup_callbacks(
                progress_callback=self.on_transfer_progress,
                completion_callback=self.on_transfer_completed,
                error_callback=self.on_transfer_error
            )
        except Exception as e:
            logger.error(f"Fehler beim Verbinden der Transfer-Signale: {e}")
        
    def on_transfer_started(self, filename: str):
        """Handler für gestartete Transfers."""
        try:
            # Get drive letter from filename
            drive_letter = os.path.splitdrive(filename)[0]
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
                self._active_transfers[drive_letter].add(filename)
                
                # Initialize transfer tracking for this file
                self._transfer_times[filename] = time.time()
                self._transfer_bytes[filename] = 0
                
                # Log message
                self.main_window.log_message(f"Transfer gestartet: {filename}")
                
        except Exception as e:
            logger.error(f"Fehler beim Verarbeiten des Transfer-Starts: {e}")

    def on_transfer_progress(self, transfer_id: str, progress: float):
        """Callback für Transfer-Fortschritt."""
        try:
            # Hole Transfer-Status
            transfer = self.main_window.transfer_coordinator.get_transfer_status(transfer_id)
            if transfer and isinstance(transfer, dict):
                # Extrahiere Quelldatei
                source = transfer.get('source', '')
                if source:
                    # Get drive letter
                    drive_letter = os.path.splitdrive(source)[0].rstrip(':').upper()
                    
                    # Calculate speed
                    start_time = self._transfer_times.get(source)
                    speed = 0
                    if start_time:
                        elapsed_time = time.time() - start_time
                        if elapsed_time > 0:
                            processed_size = transfer.get('processed_size', 0)
                            speed = (processed_size / elapsed_time) / (1024 * 1024)  # MB/s
                    
                    # Emit progress signal
                    self.transfer_progress.emit(
                        drive_letter,
                        os.path.basename(source),
                        progress * 100,  # Convert to percentage
                        speed,
                        transfer.get('total_size', 0),
                        transfer.get('processed_size', 0)
                    )
                    
                    # Update drive status if available
                    if hasattr(self.main_window, 'connected_drives_widget'):
                        self.main_window.connected_drives_widget.set_drive_status(
                            drive_letter, "Kopiere"
                        )
                
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren des Fortschritts: {e}")
            
    def on_transfer_progress_file(self, filename: str, progress: float):
        """Handler für Transfer-Fortschritt."""
        try:
            # Get drive letter
            drive_letter = os.path.splitdrive(filename)[0].rstrip(':')
            if not drive_letter:
                return
                
            # Check if we should update based on interval
            current_time = time.time()
            if drive_letter in self._last_update:
                if current_time - self._last_update[drive_letter] < self._update_interval:
                    return
            
            try:
                # Calculate total size and progress for all files (active and completed)
                total_size = 0
                total_transferred = 0
                
                # Add sizes of active files
                if drive_letter in self._active_transfers:
                    for active_file in self._active_transfers[drive_letter]:
                        try:
                            file_size = os.path.getsize(active_file)
                            total_size += file_size
                            
                            if active_file == filename:
                                # For current file, use progress percentage
                                current_bytes = int(file_size * (progress / 100))
                                total_transferred += current_bytes
                                # Update tracked bytes for this file
                                self._transfer_bytes[filename] = current_bytes
                            else:
                                # For other active files, use tracked bytes
                                total_transferred += self._transfer_bytes.get(active_file, 0)
                        except:
                            continue
                
                # Add sizes of completed files
                if drive_letter in self._completed_files:
                    for completed_file in self._completed_files[drive_letter]:
                        try:
                            file_size = os.path.getsize(completed_file)
                            total_size += file_size
                            total_transferred += file_size  # Completed files are fully transferred
                        except:
                            continue
                
                # Calculate speed
                time_diff = current_time - self._last_update.get(drive_letter, current_time)
                if time_diff > 0:
                    bytes_diff = total_transferred - self._last_bytes.get(drive_letter, total_transferred)
                    current_speed = (bytes_diff / time_diff) / (1024 * 1024)  # MB/s
                    # Smooth speed calculation (weighted average) with less aggressive smoothing
                    self._current_speed[drive_letter] = (
                        0.5 * self._current_speed.get(drive_letter, current_speed) +
                        0.5 * current_speed
                    )
                
                # Update tracking
                self._last_update[drive_letter] = current_time
                self._last_bytes[drive_letter] = total_transferred
                
                # Calculate drive progress
                drive_progress = (total_transferred / total_size * 100) if total_size > 0 else 0
                
                # Emit progress signal
                self.transfer_progress.emit(
                    drive_letter,
                    os.path.basename(filename),
                    min(drive_progress, 100),  # Ensure progress doesn't exceed 100%
                    max(self._current_speed.get(drive_letter, 0), 0),  # Use smoothed speed
                    total_size,
                    total_transferred
                )
                
            except Exception as e:
                logger.error(f"Fehler bei der Fortschrittsberechnung: {e}")
                
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren des Fortschritts: {e}")
            
    def on_transfer_completed(self, transfer_id: str):
        """Callback für abgeschlossene Transfers."""
        try:
            # Hole Transfer-Status
            transfer = self.main_window.transfer_coordinator.get_transfer_status(transfer_id)
            if transfer and isinstance(transfer, dict):
                source = transfer.get('source', '')
                if source:
                    drive_letter = source[0].upper()
                    
                    # Entferne das Laufwerk aus der Liste wenn keine weiteren Transfers aktiv sind
                    active_transfers = self.main_window.transfer_coordinator.get_active_transfers()
                    if not any(t.get('source', '')[0].upper() == drive_letter for t in active_transfers):
                        self.main_window.ingesting_drives_widget.remove_drive(drive_letter)
                        
                        # Setze Laufwerksstatus zurück
                        if hasattr(self.main_window, 'connected_drives_widget'):
                            self.main_window.connected_drives_widget.set_drive_status(
                                drive_letter, "Bereit"
                            )
                    
            # Aktualisiere UI nach Transfer
            self._update_ui_after_transfer()
                        
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der UI nach Transfer: {e}")
            
    def on_transfer_completed_file(self, filename: str):
        """Handler für abgeschlossene Transfers."""
        try:
            # Get drive letter
            drive_letter = os.path.splitdrive(filename)[0]
            if drive_letter:
                drive_letter = drive_letter.rstrip(':')
                
                # Move file from active to completed
                if drive_letter in self._active_transfers:
                    self._active_transfers[drive_letter].discard(filename)
                    if drive_letter not in self._completed_files:
                        self._completed_files[drive_letter] = set()
                    self._completed_files[drive_letter].add(filename)
                    
                    # If no more active transfers for this drive
                    if not self._active_transfers[drive_letter]:
                        # Clean up all tracking data
                        del self._active_transfers[drive_letter]
                        del self._completed_files[drive_letter]
                        del self._last_update[drive_letter]
                        del self._last_bytes[drive_letter]
                        del self._current_speed[drive_letter]
                        self.transfer_completed.emit(drive_letter)
                
                # Clean up file tracking
                if filename in self._transfer_times:
                    del self._transfer_times[filename]
                if filename in self._transfer_bytes:
                    del self._transfer_bytes[filename]
                
                # Log completion
                self.main_window.log_message(f"Transfer abgeschlossen: {filename}")
                
        except Exception as e:
            logger.error(f"Fehler beim Verarbeiten des Transfer-Abschlusses: {e}")
            
    def on_transfer_error(self, transfer_id: str, error_message: str):
        """Callback für Transfer-Fehler."""
        try:
            # Hole Transfer-Status
            transfer = self.main_window.transfer_coordinator.get_transfer_status(transfer_id)
            if transfer and isinstance(transfer, dict):
                source = transfer.get('source', '')
                if source:
                    drive_letter = source[0].upper()
                    
                    # Entferne das Laufwerk aus der Liste
                    self.main_window.ingesting_drives_widget.remove_drive(drive_letter)
                    
                    # Setze Laufwerksstatus zurück
                    if hasattr(self.main_window, 'connected_drives_widget'):
                        self.main_window.connected_drives_widget.set_drive_status(
                            drive_letter, "Bereit"
                        )
                    
            # Aktualisiere UI nach Fehler
            self._update_ui_after_transfer()
                    
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der UI nach Fehler: {e}")
            
    def on_transfer_error_file(self, filename: str, error: str):
        """Handler für Transfer-Fehler."""
        try:
            # Get drive letter
            drive_letter = os.path.splitdrive(filename)[0]
            if drive_letter:
                drive_letter = drive_letter.rstrip(':')
                
                # Clean up transfer tracking
                if filename in self._transfer_times:
                    del self._transfer_times[filename]
                if filename in self._transfer_bytes:
                    del self._transfer_bytes[filename]
                
                # Remove file from active transfers
                if drive_letter in self._active_transfers:
                    self._active_transfers[drive_letter].discard(filename)
                    
                    # If no more active transfers for this drive
                    if not self._active_transfers[drive_letter]:
                        del self._active_transfers[drive_letter]
                        if drive_letter in self._last_update:
                            del self._last_update[drive_letter]
                        self.transfer_error.emit(drive_letter, error)
                
                # Log error
                self.main_window.log_message(f"Fehler beim Transfer von {filename}: {error}")
                
        except Exception as e:
            logger.error(f"Fehler beim Verarbeiten des Transfer-Fehlers: {e}")
            
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
            logger.error(f"Fehler beim Aktualisieren der UI nach Transfer: {e}")
            
    def get_active_transfers(self) -> dict:
        """Gibt die aktiven Transfers zurück.
        
        Returns:
            Dictionary mit Transfer-IDs als Schlüssel
        """
        try:
            return self.main_window.transfer_coordinator.get_active_transfers()
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der aktiven Transfers: {e}")
            return {}
