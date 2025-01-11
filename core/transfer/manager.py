"""
Hauptmodul für die Verwaltung von Dateiübertragungen.
"""

import os
import uuid
import time
import logging
from typing import Dict, Optional, Callable
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from queue import PriorityQueue, Empty
import threading
import traceback

from .metadata import MetadataManager
from .analytics import TransferAnalytics
from .priority import TransferPriority
from .processor import TransferProcessor
from .queue_manager import QueueManager

logger = logging.getLogger(__name__)

class TransferManager:
    """Manager für Dateitransfers mit Prioritätswarteschlange."""
    
    def __init__(self, max_workers=4):
        self.max_workers = max_workers
        self.transfers = {}  # transfer_id -> transfer_info
        self.active_transfers = set()
        self.paused_transfers = set()
        self.worker_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.transfer_queue = PriorityQueue()
        self._recursion_check = set()  # Schutz vor Rekursion
        self._lock = threading.Lock()  # Thread-Sicherheit
        self._processed_files = {}  # Dict für verarbeitete Dateien: {file_id: (size, target)}
        
        # Callbacks
        self.progress_callback = None
        self.completion_callback = None
        self.error_callback = None
        
        logger.info(f"TransferManager initialisiert mit {max_workers} Workern")
        
    def set_callbacks(self, progress_callback=None, completion_callback=None, error_callback=None):
        """Setzt die Callbacks für Transfer-Events."""
        self.progress_callback = progress_callback
        self.completion_callback = completion_callback
        self.error_callback = error_callback
        
    def enqueue_transfer(self, source: str, target: str, priority: TransferPriority = TransferPriority.NORMAL, metadata: dict = None):
        """Fügt einen neuen Transfer zur Warteschlange hinzu."""
        try:
            current_thread = threading.current_thread()
            logger.info(f"[Thread {current_thread.name}] Füge neuen Transfer hinzu: {source} -> {target}")
            
            # Generiere eindeutige ID für den Transfer
            transfer_id = str(uuid.uuid4())
            
            # Prüfe auf Rekursion
            with self._lock:
                transfer_key = f"{source}:{target}"
                if transfer_key in self._recursion_check:
                    logger.warning(f"[Thread {current_thread.name}] Rekursion erkannt für Transfer {transfer_id} - Stack: {traceback.format_stack()}")
                    return None
                    
                # Füge Transfer zur Rekursionsprüfung hinzu
                self._recursion_check.add(transfer_key)
                logger.debug(f"[Thread {current_thread.name}] Aktive Transfers: {self._recursion_check}")
            
            # Prüfe ob die Quelldatei existiert
            if not os.path.exists(source):
                raise FileNotFoundError(f"Quelldatei nicht gefunden: {source}")
                
            # Prüfe ob die Datei bereits verarbeitet wurde
            file_id = self._get_file_id(source)
            if file_id in self._processed_files:
                size, old_target = self._processed_files[file_id]
                logger.debug(f"Datei bereits verarbeitet: {source} -> {old_target} (Größe: {size})")
                return None
                
            # Erstelle Transfer-Info
            transfer_info = {
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
                'current_speed': 0,
                'average_speed': 0,
                'estimated_time': 0,
                'total_files': 1,
                'processed_files': 0
            }
            
            # Speichere Transfer
            self.transfers[transfer_id] = transfer_info
            
            # Füge zur Warteschlange hinzu
            self.transfer_queue.put((priority.value, transfer_id))
            
            # Starte Verarbeitung
            self._process_queue()
            
            logger.info(f"[Thread {current_thread.name}] Starte Transfer {transfer_id} von {source} nach {target}")
            
            return transfer_id
            
        except Exception as e:
            logger.error(f"[Thread {current_thread.name}] Fehler beim Hinzufügen des Transfers: {e}", exc_info=True)
            if self.error_callback:
                self.error_callback(transfer_id, str(e))
            return None
            
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
        for transfer_id in list(self.transfers.keys()):
            self.cancel_transfer(transfer_id)
        
        # Leere die Warteschlange
        while not self.transfer_queue.empty():
            try:
                self.transfer_queue.get_nowait()
            except Empty:
                break
                
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
        logger.debug("Verarbeite Transfer-Warteschlange. Aktive Transfers: {}".format(len(self.active_transfers)))
        while not self.transfer_queue.empty() and len(self.active_transfers) < self.max_workers:
            try:
                _, transfer_id = self.transfer_queue.get_nowait()
                logger.debug("Transfer {} aus Warteschlange geholt".format(transfer_id))
                if transfer_id not in self.active_transfers and transfer_id not in self.paused_transfers:
                    self._start_transfer(transfer_id)
            except Empty:
                break
                
    def _start_transfer(self, transfer_id: str):
        """Startet einen Transfer."""
        try:
            with self._lock:
                if transfer_id in self._recursion_check:
                    logger.warning(f"Rekursion erkannt für Transfer {transfer_id}")
                    return
                    
                self._recursion_check.add(transfer_id)
            
            transfer = self.transfers[transfer_id]
            transfer['status'] = 'active'
            transfer['start_time'] = datetime.now()
            self.active_transfers.add(transfer_id)
            
            logger.info("Starte Transfer {} von {} nach {}".format(
                transfer_id, transfer['source'], transfer['target']))
            
            self.worker_pool.submit(
                self._transfer_file,
                transfer_id,
                transfer['source'],
                transfer['target']
            )
            
        except Exception as e:
            logger.error("Fehler beim Starten des Transfers {}: {}".format(transfer_id, e), exc_info=True)
            if self.error_callback:
                self.error_callback(transfer_id, str(e))
                
        finally:
            with self._lock:
                self._recursion_check.discard(transfer_id)
            
    def _transfer_file(self, transfer_id: str, source: str, target: str):
        """Führt den eigentlichen Dateitransfer durch."""
        try:
            with self._lock:
                if transfer_id in self._recursion_check:
                    logger.warning(f"Rekursion erkannt für Transfer {transfer_id}")
                    return
                    
                self._recursion_check.add(transfer_id)
            
            transfer = self.transfers[transfer_id]
            transfer['start_time'] = datetime.now()
            transfer['status'] = 'copying'
            
            # Erstelle Zielverzeichnis falls nicht vorhanden
            os.makedirs(os.path.dirname(target), exist_ok=True)
            
            # Initialisiere Transfer-Statistiken
            file_size = os.path.getsize(source)
            chunk_size = 1024 * 1024  # 1MB
            processed_size = 0
            start_time = time.time()
            last_update = start_time
            speed_samples = []
            
            with open(source, 'rb') as src, open(target, 'wb') as dst:
                while True:
                    chunk = src.read(chunk_size)
                    if not chunk:
                        break
                        
                    dst.write(chunk)
                    processed_size += len(chunk)
                    
                    # Aktualisiere Statistiken
                    current_time = time.time()
                    if current_time - last_update >= 0.5:  # Alle 500ms updaten
                        # Berechne Geschwindigkeit
                        elapsed = current_time - start_time
                        if elapsed > 0:
                            current_speed = processed_size / elapsed
                            speed_samples.append(current_speed)
                            if len(speed_samples) > 10:
                                speed_samples.pop(0)
                            average_speed = sum(speed_samples) / len(speed_samples)
                            
                            # Schätze verbleibende Zeit
                            if average_speed > 0:
                                remaining_bytes = file_size - processed_size
                                estimated_time = remaining_bytes / average_speed
                            else:
                                estimated_time = 0
                            
                            # Aktualisiere Transfer-Info
                            transfer['progress'] = processed_size / file_size
                            transfer['processed_size'] = processed_size
                            transfer['current_speed'] = current_speed
                            transfer['average_speed'] = average_speed
                            transfer['estimated_time'] = estimated_time
                            
                            # Rufe Callback auf
                            if self.progress_callback:
                                self.progress_callback(transfer_id, transfer['progress'])
                                
                            last_update = current_time
                            
            # Transfer abgeschlossen
            transfer['status'] = 'completed'
            transfer['end_time'] = datetime.now()
            transfer['progress'] = 1.0
            transfer['processed_size'] = file_size
            transfer['processed_files'] = 1
            
            # Speichere Datei als verarbeitet
            file_id = self._get_file_id(source)
            self._processed_files[file_id] = (file_size, target)
            
            if self.completion_callback:
                self.completion_callback(transfer_id)
                
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Übertragen der Datei: {e}", exc_info=True)
            transfer['status'] = 'failed'
            transfer['end_time'] = datetime.now()
            
            if self.error_callback:
                self.error_callback(transfer_id, str(e))
                
            return False
            
        finally:
            with self._lock:
                self._recursion_check.discard(transfer_id)

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
            
    def _copy_with_robocopy(self, source_file: str, target_file: str) -> bool:
        """Kopiert eine Datei mit robocopy unter Windows.
        
        Args:
            source_file: Quelldatei
            target_file: Zieldatei
            
        Returns:
            True wenn erfolgreich, False wenn fehlgeschlagen
        """
        try:
            import subprocess
            
            # Erstelle Quell- und Zielverzeichnis
            source_dir = os.path.dirname(source_file)
            source_file = os.path.basename(source_file)
            target_dir = os.path.dirname(target_file)
            target_file = os.path.basename(target_file)
            
            logger.info("Robocopy von {} nach {}".format(
                os.path.join(source_dir, source_file),
                os.path.join(target_dir, target_file)))
            
            # Führe robocopy aus
            cmd = [
                'robocopy',
                source_dir,
                target_dir,
                source_file,
                '/COPY:DAT',  # Copy Data, Attributes, and Timestamps
                '/Z',  # Restart mode
                '/W:5',  # Wait time between retries
                '/R:3',  # Number of retries
                '/MT:8',  # Multi-threaded copying
                '/J',    # Use unbuffered I/O
                '/NP',  # No progress
                '/NDL',  # No directory list
                '/NJH',  # No job header
                '/NJS',  # No job summary
                '/TEE'  # Output to console and log file
            ]
            
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                check=False  # Don't raise exception on non-zero return code
            )
            
            # Robocopy return codes:
            # 0 - No errors
            # 1 - One or more files copied successfully
            # 2 - Extra files or directories detected
            # 4 - Mismatched files or directories detected
            # 8 - Some files or directories could not be copied
            # 16 - Serious error occurred
            success = process.returncode <= 1
            
            if not success:
                logger.error(f"Robocopy fehlgeschlagen mit Code {process.returncode}")
                logger.error(f"Stdout: {process.stdout}")
                logger.error(f"Stderr: {process.stderr}")
                return False
                
            # Prüfe ob die Datei existiert und die Größe stimmt
            target_path = os.path.join(target_dir, target_file)
            if not os.path.exists(target_path):
                logger.error("Zieldatei wurde nicht erstellt")
                return False
                
            source_size = os.path.getsize(os.path.join(source_dir, source_file))
            target_size = os.path.getsize(target_path)
            
            if source_size != target_size:
                logger.error(
                    "Größe der Zieldatei ({}) stimmt nicht mit Quelldatei ({}) überein"
                    .format(target_size, source_size)
                )
                return False
                
            logger.info("Robocopy erfolgreich abgeschlossen")
            return True
            
        except Exception as e:
            logger.error("Fehler bei robocopy: {}".format(e), exc_info=True)
            return False

    def _copy_with_rsync(self, source_file: str, target_file: str):
        """Kopiert eine Datei mit rsync unter Unix.
        
        Args:
            source_file: Quelldatei
            target_file: Zieldatei
        """
        try:
            # rsync Optionen:
            # -a - Archiv-Modus (rekursiv, erhält Berechtigungen etc.)
            # -v - Ausführliche Ausgabe
            # -h - Menschenlesbare Zahlen
            # --progress - Zeige Fortschritt
            import subprocess
            cmd = [
                'rsync',
                '-avh',
                '--progress',
                source_file,
                target_file
            ]
            
            logging.info(f"Starte rsync: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"rsync Fehler: {result.stderr}")
            else:
                logging.info(f"Datei erfolgreich kopiert: {source_file}")
                
        except Exception as e:
            logging.error(f"Fehler bei rsync: {e}", exc_info=True)
            raise
