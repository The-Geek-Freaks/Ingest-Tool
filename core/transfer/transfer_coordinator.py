#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Koordiniert Dateiübertragungen und verwaltet den Status.
"""

import os
import logging
from typing import List, Optional, Dict, Callable
from datetime import datetime
import threading
import uuid
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from queue import Queue

from core.transfer.manager import TransferManager
from core.transfer.priority import TransferPriority
from core.batch_manager import BatchManager
from core.parallel_copier import ParallelCopier
from utils.file_system_helper import FileSystemHelper

class TransferCoordinator(QObject):
    """Koordiniert und verwaltet Dateiübertragungen."""
    
    # Signale
    transfer_started = pyqtSignal(str)  # Transfer-ID
    transfer_progress = pyqtSignal(str, float)  # Transfer-ID, Fortschritt
    transfer_completed = pyqtSignal(str)  # Transfer-ID
    transfer_error = pyqtSignal(str, str)  # Transfer-ID, Fehlermeldung
    
    def __init__(self, settings: dict = None):
        """Initialisiert den TransferCoordinator.
        
        Args:
            settings: Programmeinstellungen
        """
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        self.settings = settings or {}
        
        # Initialisiere Manager
        self.transfer_manager = TransferManager(max_workers=4)
        self.batch_manager = BatchManager()
        self.parallel_copier = ParallelCopier()
        
        # Initialisiere Status
        self._is_processing = False
        self._recursion_guard = set()  # Verhindert Rekursion
        self._transfer_queue = Queue()
        self._lock = threading.Lock()
        
        # Initialisiere Callbacks
        self.progress_callback = None
        self.completion_callback = None
        self.error_callback = None
        
        # Verbinde Signale
        self.transfer_started.connect(self._on_transfer_started)
        self.transfer_progress.connect(self._on_transfer_progress)
        self.transfer_completed.connect(self._on_transfer_completed)
        self.transfer_error.connect(self._on_transfer_error)
        
        self.active_copies = {}
        self.transfer_start_time = None
        
    def start_copy(self, source_drive: str, target_path: str, file_types: List[str]) -> bool:
        """Startet einen Kopiervorgang.
        
        Args:
            source_drive: Quelllaufwerk
            target_path: Zielpfad
            file_types: Liste der zu kopierenden Dateitypen
            
        Returns:
            True wenn der Kopiervorgang gestartet wurde, sonst False
        """
        try:
            # Rekursionsschutz
            copy_id = f"{source_drive}_{target_path}"
            if copy_id in self._recursion_guard:
                self.logger.warning(f"Rekursion erkannt für Kopiervorgang: {copy_id}")
                return False
                
            with self._lock:
                self._recursion_guard.add(copy_id)
            
            try:
                if not target_path:
                    self.logger.error("Kein Zielpfad angegeben")
                    return False
                    
                # Normalisiere Pfade
                source_drive = source_drive.rstrip('\\').rstrip(':') + ':'
                target_path = os.path.normpath(target_path)
                
                # Finde zu kopierende Dateien
                source_files = self.get_source_files(source_drive, file_types)
                if not source_files:
                    self.logger.info(f"Keine zu kopierenden Dateien auf Laufwerk {source_drive} gefunden")
                    return False
                    
                self.logger.info(f"Kopiere {len(source_files)} Dateien vom Typ {file_types} nach {target_path}")
                
                # Stelle sicher dass der Zielpfad existiert
                os.makedirs(target_path, exist_ok=True)
                self.logger.info(f"Zielverzeichnis bereit: {target_path}")
                
                # Füge alle Dateien zur Warteschlange hinzu
                for source_file in source_files:
                    try:
                        filename = os.path.basename(source_file)
                        target_file = os.path.join(target_path, filename)
                        
                        self.logger.info(f"Füge Transfer zur Warteschlange hinzu: {source_file} -> {target_file}")
                        transfer_id = self.transfer_manager.enqueue_transfer(
                            source=source_file,
                            target=target_file,
                            priority=TransferPriority.NORMAL,
                            metadata={
                                'start_time': datetime.now().isoformat(),
                                'source_drive': source_drive
                            }
                        )
                        
                        if transfer_id:
                            self.logger.info(f"Transfer {transfer_id} erfolgreich zur Warteschlange hinzugefügt")
                            self.transfer_started.emit(transfer_id)
                        else:
                            self.logger.error(f"Fehler beim Hinzufügen des Transfers für {source_file}")
                            
                    except Exception as e:
                        self.logger.error(f"Fehler beim Verarbeiten von {source_file}: {e}", exc_info=True)
                        continue
                
                return True
                
            finally:
                with self._lock:
                    self._recursion_guard.discard(copy_id)
                    
        except Exception as e:
            self.logger.error(f"Fehler beim Starten des Kopiervorgangs: {e}", exc_info=True)
            return False
            
    def get_source_files(self, source_drive: str, file_types: List[str]) -> List[str]:
        """Gibt eine Liste der zu kopierenden Dateien zurück.
        
        Args:
            source_drive: Quelllaufwerk
            file_types: Liste der zu kopierenden Dateitypen
            
        Returns:
            Liste der Dateipfade
        """
        files = []
        drive_path = f"{source_drive}:\\"
        
        try:
            for root, _, filenames in os.walk(drive_path):
                for filename in filenames:
                    file_ext = FileSystemHelper.get_file_extension(filename)
                    if file_ext in file_types:
                        full_path = os.path.join(root, filename)
                        files.append(full_path)
                        
        except Exception as e:
            self.logger.error(f"Fehler beim Suchen von Dateien: {e}")
            
        return files
        
    @pyqtSlot(list, str)
    def start_copy_for_files(self, files: List[str], target_dir: str):
        """Startet den Kopiervorgang für eine Liste von Dateien.
        
        Args:
            files: Liste der zu kopierenden Dateien
            target_dir: Zielverzeichnis
        """
        try:
            self.logger.info(f"Starte Kopiervorgang für {len(files)} Dateien nach {target_dir}")
            
            # Erstelle Zielverzeichnis falls nicht vorhanden
            os.makedirs(target_dir, exist_ok=True)
            
            # Füge jede Datei zur Warteschlange hinzu
            for source_file in files:
                # Überspringe Dateien die bereits in Bearbeitung sind
                if source_file in self._recursion_guard:
                    self.logger.warning(f"Datei wird bereits verarbeitet: {source_file}")
                    continue
                    
                try:
                    # Füge zur Recursion Guard hinzu
                    self._recursion_guard.add(source_file)
                    
                    # Bestimme Zieldatei
                    file_name = os.path.basename(source_file)
                    target_file = os.path.join(target_dir, file_name)
                    
                    # Erstelle Transfer-Task
                    transfer = {
                        'id': str(uuid.uuid4()),
                        'source': source_file,
                        'target': target_file,
                        'size': os.path.getsize(source_file),
                        'progress': 0.0,
                        'status': 'pending'
                    }
                    
                    # Füge zur Warteschlange hinzu
                    self._transfer_queue.put(transfer)
                    self.logger.debug(f"Transfer zur Warteschlange hinzugefügt: {transfer['id']}")
                    self.transfer_started.emit(transfer['id'])
                    
                except Exception as e:
                    self.logger.error(f"Fehler beim Hinzufügen der Datei {source_file}: {e}")
                    if self.error_callback:
                        self.error_callback(source_file, str(e))
                finally:
                    # Entferne aus Recursion Guard
                    self._recursion_guard.remove(source_file)
                    
            # Starte Verarbeitung falls nicht bereits aktiv
            if not self._is_processing:
                self._process_queue()
                
        except Exception as e:
            self.logger.error(f"Fehler beim Starten des Kopiervorgangs: {e}")
            if self.error_callback:
                self.error_callback("batch", str(e))
                
    def cancel_copy(self, drive_letter: str):
        """Bricht einen laufenden Kopiervorgang ab.
        
        Args:
            drive_letter: Laufwerksbuchstabe des abzubrechenden Kopiervorgangs
        """
        try:
            if drive_letter in self.active_copies:
                self.transfer_manager.cancel_transfer(drive_letter)
                del self.active_copies[drive_letter]
                self.logger.info(f"Kopiervorgang für Laufwerk {drive_letter} abgebrochen")
                
        except Exception as e:
            self.logger.error(f"Fehler beim Abbrechen des Kopiervorgangs: {e}")
            
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

    def get_transfer_status(self, transfer_id: str) -> Optional[Dict]:
        """Gibt den Status eines Transfers zurück.
        
        Args:
            transfer_id: ID des Transfers
            
        Returns:
            Dictionary mit Statusinformationen oder None wenn nicht gefunden
        """
        try:
            return self.transfer_manager.get_transfer_status(transfer_id)
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen des Transfer-Status: {e}")
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

    def cleanup(self):
        """Bereinigt alle laufenden Transfers vor dem Beenden."""
        cleanup_errors = []
        
        # Stoppe Transfer Manager
        try:
            self.logger.info("Stoppe Transfer Manager...")
            self.transfer_manager.stop_all_transfers()
        except Exception as e:
            error_msg = f"Fehler beim Stoppen des Transfer Managers: {e}"
            self.logger.error(error_msg)
            cleanup_errors.append(error_msg)
            
        # Stoppe Parallel Copier
        try:
            self.logger.info("Stoppe Parallel Copier...")
            self.parallel_copier.stop()
        except Exception as e:
            error_msg = f"Fehler beim Stoppen des Parallel Copiers: {e}"
            self.logger.error(error_msg)
            cleanup_errors.append(error_msg)
            
        # Stoppe Batch Manager
        try:
            self.logger.info("Stoppe Batch Manager...")
            self.batch_manager.stop()
        except Exception as e:
            error_msg = f"Fehler beim Stoppen des Batch Managers: {e}"
            self.logger.error(error_msg)
            cleanup_errors.append(error_msg)
            
        # Bereinige aktive Kopien
        try:
            self.logger.info("Bereinige aktive Kopien...")
            self.active_copies.clear()
        except Exception as e:
            error_msg = f"Fehler beim Bereinigen der aktiven Kopien: {e}"
            self.logger.error(error_msg)
            cleanup_errors.append(error_msg)
            
        if cleanup_errors:
            error_msg = "Fehler während des Cleanups: " + "; ".join(cleanup_errors)
            self.logger.error(error_msg)
            raise Exception(error_msg)
        else:
            self.logger.info("Cleanup erfolgreich abgeschlossen")

    def _on_transfer_started(self, transfer_id: str):
        """Wird aufgerufen wenn ein Transfer startet."""
        self.logger.info(f"Transfer gestartet: {transfer_id}")
        
    def _on_transfer_progress(self, transfer_id: str, progress: float):
        """Wird aufgerufen wenn sich der Fortschritt ändert."""
        self.logger.debug(f"Transfer Fortschritt: {transfer_id} - {progress:.1f}%")
        if self.progress_callback:
            self.progress_callback(transfer_id, progress)
            
    def _on_transfer_completed(self, transfer_id: str):
        """Wird aufgerufen wenn ein Transfer abgeschlossen ist."""
        self.logger.info(f"Transfer abgeschlossen: {transfer_id}")
        if self.completion_callback:
            self.completion_callback(transfer_id)
            
    def _on_transfer_error(self, transfer_id: str, error: str):
        """Wird aufgerufen wenn ein Fehler auftritt."""
        self.logger.error(f"Transfer Fehler: {transfer_id} - {error}")
        if self.error_callback:
            self.error_callback(transfer_id, error)

    def _process_queue(self):
        """Verarbeitet die Transfer-Warteschlange."""
        if self._is_processing:
            return
            
        try:
            self._is_processing = True
            self.logger.debug("Starte Verarbeitung der Transfer-Warteschlange")
            
            while not self._transfer_queue.empty():
                # Hole nächsten Transfer
                transfer = self._transfer_queue.get()
                transfer_id = transfer['id']
                source = transfer['source']
                target = transfer['target']
                
                try:
                    # Prüfe ob die Quelldatei noch existiert
                    if not os.path.exists(source):
                        error_msg = f"Quelldatei existiert nicht mehr: {source}"
                        self.logger.error(error_msg)
                        self.transfer_error.emit(transfer_id, error_msg)
                        continue
                        
                    # Prüfe ob genug Speicherplatz vorhanden ist
                    required_space = transfer['size']
                    target_drive = os.path.splitdrive(target)[0]
                    free_space = FileSystemHelper.get_free_space(target_drive)
                    
                    if free_space is not None and free_space < required_space:
                        error_msg = f"Nicht genug Speicherplatz auf {target_drive}. Benötigt: {required_space}, Verfügbar: {free_space}"
                        self.logger.error(error_msg)
                        self.transfer_error.emit(transfer_id, error_msg)
                        continue
                        
                    # Erstelle Zielverzeichnis falls nicht vorhanden
                    target_dir = os.path.dirname(target)
                    os.makedirs(target_dir, exist_ok=True)
                    
                    # Starte Kopiervorgang
                    self.logger.info(f"Starte Kopiervorgang: {source} -> {target}")
                    
                    # Kopiere die Datei in Blöcken und aktualisiere den Fortschritt
                    with open(source, 'rb') as src, open(target, 'wb') as dst:
                        copied = 0
                        while True:
                            # Lese Block
                            chunk = src.read(8192)  # 8KB Blöcke
                            if not chunk:
                                break
                                
                            # Schreibe Block
                            dst.write(chunk)
                            
                            # Aktualisiere Fortschritt
                            copied += len(chunk)
                            progress = (copied / transfer['size']) * 100
                            self.transfer_progress.emit(transfer_id, progress)
                            
                    # Transfer erfolgreich
                    self.logger.info(f"Transfer abgeschlossen: {transfer_id}")
                    self.transfer_completed.emit(transfer_id)
                    
                except Exception as e:
                    error_msg = f"Fehler beim Kopieren von {source}: {str(e)}"
                    self.logger.error(error_msg)
                    self.transfer_error.emit(transfer_id, error_msg)
                    
                finally:
                    # Markiere Task als erledigt
                    self._transfer_queue.task_done()
                    
        except Exception as e:
            self.logger.error(f"Fehler bei der Verarbeitung der Warteschlange: {e}")
        finally:
            self._is_processing = False
            self.logger.debug("Transfer-Warteschlange Verarbeitung beendet")
