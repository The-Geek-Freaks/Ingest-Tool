#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Optimierte Copy-Engine für effiziente Dateiübertragungen.
"""

import os
import logging
import shutil
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import time
import json
import psutil
import mmap
import uuid

logger = logging.getLogger(__name__)

@dataclass
class TransferStats:
    """Statistiken für einen einzelnen Dateitransfer."""
    bytes_total: int
    bytes_transferred: int = 0
    speed_bytes_sec: float = 0.0
    start_time: Optional[datetime] = None
    last_update: Optional[datetime] = None
    resume_position: int = 0  # Position für Wiederaufnahme
    chunk_size: int = 0  # Verwendete Chunk-Größe
    checksum: Optional[str] = None  # MD5-Prüfsumme für Verifizierung

    @property
    def progress_percent(self) -> float:
        """Berechnet den Fortschritt in Prozent."""
        if self.bytes_total == 0:
            return 100.0
        return (self.bytes_transferred / self.bytes_total) * 100

    def to_json(self) -> dict:
        """Konvertiert die Statistiken in JSON-Format für Speicherung."""
        return {
            'bytes_total': self.bytes_total,
            'bytes_transferred': self.bytes_transferred,
            'resume_position': self.resume_position,
            'chunk_size': self.chunk_size,
            'checksum': self.checksum
        }

    @classmethod
    def from_json(cls, data: dict) -> 'TransferStats':
        """Erstellt TransferStats aus JSON-Daten."""
        return cls(
            bytes_total=data['bytes_total'],
            bytes_transferred=data['bytes_transferred'],
            resume_position=data['resume_position'],
            chunk_size=data['chunk_size'],
            checksum=data['checksum']
        )

class OptimizedCopyEngine:
    """Optimierte Copy-Engine mit adaptiver Strategie."""
    
    # Schwellenwerte für verschiedene Kopierstrategien
    _small_file_threshold = 10 * 1024 * 1024  # 10 MB
    _medium_file_threshold = 1024 * 1024 * 1024  # 1 GB
    
    def __init__(self):
        """Initialisiert die Copy-Engine."""
        self.max_workers = max(1, os.cpu_count() - 1)
        self._executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self._active_transfers: Dict[str, TransferStats] = {}
        self._progress_callback: Optional[Callable] = None
        self._min_progress_interval = 0.1  # Minimales Intervall zwischen Updates (100ms)
        
        # Adaptive Chunk-Größen
        self._base_chunk_size = 4 * 1024 * 1024  # 4MB Basis-Chunk-Größe
        self._min_chunk_size = 1 * 1024 * 1024   # 1MB minimum
        self._max_chunk_size = 64 * 1024 * 1024  # 64MB maximum
        
    def set_progress_callback(self, callback: Callable[[str, float, float, int, int], None]):
        """Setzt die Callback-Funktion für Fortschrittsupdates.
        
        Args:
            callback: Funktion die aufgerufen wird mit (transfer_id, progress, speed, total_bytes, transferred_bytes)
        """
        self._progress_callback = callback
        
    def copy_file(self, source: str, target: str, transfer_id: str = None) -> Future:
        """Kopiert eine Datei asynchron.
        
        Args:
            source: Quelldatei
            target: Zieldatei
            transfer_id: Optional ID für den Transfer
            
        Returns:
            Future-Objekt für den Transfer
            
        Raises:
            FileNotFoundError: Wenn die Quelldatei nicht existiert
            PermissionError: Wenn keine Berechtigung zum Lesen/Schreiben besteht
        """
        # Prüfe ob Quelldatei existiert
        if not os.path.exists(source):
            logger.error(f"Fehler beim Kopieren von {source}: Quelldatei nicht gefunden")
            raise FileNotFoundError(f"Quelldatei nicht gefunden: {source}")
            
        # Generiere Transfer-ID falls nicht angegeben
        if transfer_id is None:
            transfer_id = str(uuid.uuid4())
            
        # Erstelle temporären Zielpfad
        tmp_target = f"{target}.tmp"
        
        # Bestimme Dateigröße
        file_size = os.path.getsize(source)
        
        # Wähle Kopierstrategie basierend auf Dateigröße
        if file_size <= self._small_file_threshold:
            strategy = 'small'
            copy_func = lambda: self._copy_small_file(transfer_id, source, tmp_target)
        elif file_size <= self._medium_file_threshold:
            strategy = 'medium'
            copy_func = lambda: self._copy_medium_file(transfer_id, source, tmp_target)
        else:
            strategy = 'large'
            copy_func = lambda: self._copy_large_file(transfer_id, source, tmp_target)
            
        logger.debug(f"Verwende Strategie '{strategy}' für {file_size/1024/1024:.1f}MB")
        
        # Führe Kopiervorgang asynchron aus
        future = self._executor.submit(copy_func)
        
        # Füge Callback für Finalisierung hinzu
        future.add_done_callback(
            lambda f: self._finalize_transfer(f, tmp_target, target)
        )
        
        return future
            
    def _finalize_transfer(self, future: Future, tmp_target: str, target: str):
        """Finalisiert den Transfer durch Umbenennen der temporären Datei.
        
        Args:
            future: Future-Objekt des Kopiervorgangs
            tmp_target: Pfad zur temporären Datei
            target: Zielpfad für die finale Datei
        """
        try:
            # Prüfe ob der Transfer erfolgreich war
            if future.exception() is not None:
                logger.error(f"Transfer fehlgeschlagen: {future.exception()}")
                raise future.exception()
                
            logger.debug(f"Finalisiere Transfer: {tmp_target} -> {target}")
            
            # Stelle sicher, dass das Zielverzeichnis existiert
            target_dir = os.path.dirname(target)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)
                
            # Entferne existierende Zieldatei falls vorhanden
            if os.path.exists(target):
                try:
                    os.remove(target)
                except Exception as e:
                    logger.warning(f"Konnte existierende Zieldatei nicht entfernen: {e}")
                    
            # Prüfe ob die temporäre Datei existiert
            if not os.path.exists(tmp_target):
                logger.error(f"Temporäre Datei nicht gefunden: {tmp_target}")
                raise FileNotFoundError(f"Temporäre Datei nicht gefunden: {tmp_target}")
                
            # Versuche zuerst os.rename
            logger.debug(f"Benenne temporäre Datei um: {tmp_target} -> {target}")
            try:
                os.rename(tmp_target, target)
                logger.debug("Umbenennen erfolgreich")
            except OSError as e:
                # Falls os.rename fehlschlägt, versuche shutil.move
                logger.warning(f"os.rename fehlgeschlagen, versuche shutil.move: {e}")
                try:
                    shutil.move(tmp_target, target)
                    logger.debug("Umbenennen mit shutil.move erfolgreich")
                except Exception as e:
                    logger.error(f"Konnte temporäre Datei nicht umbenennen: {e}")
                    raise
                    
        except Exception as e:
            logger.error(f"Fehler beim Finalisieren des Transfers: {e}")
            # Lösche temporäre Datei falls vorhanden
            if os.path.exists(tmp_target):
                try:
                    os.remove(tmp_target)
                except Exception as cleanup_error:
                    logger.warning(f"Konnte temporäre Datei nicht löschen: {cleanup_error}")
            raise
            
    def _cleanup_transfer(self, transfer_id: str):
        """Räumt einen Transfer auf.
        
        Args:
            transfer_id: ID des Transfers
        """
        try:
            if transfer_id in self._active_transfers:
                del self._active_transfers[transfer_id]
        except Exception as e:
            logger.error(f"Fehler beim Aufräumen des Transfers {transfer_id}: {e}")
            
    def _get_optimal_strategy(self, file_size: int) -> Callable:
        """Wählt die optimale Kopierstrategie basierend auf der Dateigröße.
        
        Args:
            file_size: Größe der Datei in Bytes
            
        Returns:
            Funktion die den Kopiervorgang durchführt
        """
        if file_size < self._small_file_threshold:
            return 'small'
        elif file_size < self._medium_file_threshold:
            return 'medium'
        else:
            return 'large'
            
    def _update_progress(self, transfer_id: str, stats: TransferStats, force: bool = False):
        """Aktualisiert den Fortschritt mit Rate-Limiting.
        
        Args:
            transfer_id: ID des Transfers
            stats: Transfer-Statistiken
            force: Wenn True, wird das Update immer gesendet
        """
        now = datetime.now()
        if force or (stats.last_update is None or 
            (now - stats.last_update).total_seconds() >= self._min_progress_interval):
            progress = stats.progress_percent
            elapsed = (now - stats.start_time).total_seconds() if stats.start_time else 0
            speed = stats.bytes_transferred / max(1, elapsed)
            
            if self._progress_callback:
                logger.debug(f"Sende Progress-Update für {transfer_id}: {progress:.1f}%")
                self._progress_callback(transfer_id, progress, speed)
            
            stats.last_update = now
            stats.speed_bytes_sec = speed
            
    def _get_optimal_chunk_size(self, file_size: int) -> int:
        """Ermittelt die optimale Chunk-Größe basierend auf Systemressourcen.
        
        Args:
            file_size: Größe der zu kopierenden Datei
            
        Returns:
            Optimale Chunk-Größe in Bytes
        """
        try:
            # Verfügbarer Arbeitsspeicher (in Bytes)
            mem_info = psutil.virtual_memory()
            available_memory = mem_info.available
            
            # Basis-Chunk-Größe an verfügbaren Speicher anpassen
            chunk_size = min(
                self._base_chunk_size * (available_memory / (8 * 1024 * 1024 * 1024)),  # 8GB Referenz
                self._max_chunk_size
            )
            
            # Für sehr kleine Dateien kleinere Chunks verwenden
            if file_size < self._small_file_threshold:
                chunk_size = min(chunk_size, file_size // 4)
                
            # Minimum und Maximum einhalten
            chunk_size = max(self._min_chunk_size, min(chunk_size, self._max_chunk_size))
            
            return int(chunk_size)
            
        except Exception as e:
            logger.warning(f"Fehler bei Chunk-Größen-Optimierung: {e}")
            return self._base_chunk_size
            
    def _send_progress_update(self, transfer_id: str, progress: float):
        """Sendet ein Progress-Update für einen Transfer.
        
        Args:
            transfer_id: ID des Transfers
            progress: Fortschritt in Prozent
        """
        if self._progress_callback and transfer_id in self._active_transfers:
            stats = self._active_transfers[transfer_id]
            speed = stats.speed_bytes_sec if stats.speed_bytes_sec is not None else 0
            
            logger.debug(f"Sende Progress-Update für {transfer_id}: {progress:.1f}% - {speed/1024/1024:.1f}MB/s")
            self._progress_callback(
                transfer_id,
                progress,
                speed,
                stats.bytes_total,
                stats.bytes_transferred
            )
            
    def _copy_small_file(self, transfer_id: str, source: str, target: str):
        """Kopiert eine kleine Datei am Stück.
        
        Args:
            transfer_id: ID des Transfers
            source: Quelldatei
            target: Zieldatei
            
        Returns:
            True wenn der Transfer erfolgreich war
        """
        logger.debug(f"Starte Kopieren von kleiner Datei: {source} -> {target}")
        
        # Stelle sicher, dass das Zielverzeichnis existiert
        target_dir = os.path.dirname(target)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
            
        # Sende Start-Progress
        self._send_progress_update(transfer_id, 0)
        
        try:
            # Kopiere Datei
            with open(source, 'rb') as src:
                # Öffne Zieldatei
                with open(target, 'wb') as dst:
                    # Kopiere Inhalt
                    dst.write(src.read())
                    
            # Prüfe ob die Zieldatei existiert und die richtige Größe hat
            if not os.path.exists(target):
                raise FileNotFoundError(f"Zieldatei wurde nicht erstellt: {target}")
                
            if os.path.getsize(target) != os.path.getsize(source):
                raise IOError(f"Zieldatei hat falsche Größe: {target}")
                
            # Sende End-Progress
            self._send_progress_update(transfer_id, 100)
            
            # Gib True zurück, um den Erfolg zu signalisieren
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Kopieren von {source}: {e}")
            # Lösche temporäre Datei falls vorhanden
            if os.path.exists(target):
                try:
                    os.remove(target)
                except Exception as cleanup_error:
                    logger.warning(f"Konnte temporäre Datei nicht löschen: {cleanup_error}")
            raise
            
    def _copy_medium_file(self, transfer_id: str, source: str, target: str):
        """Kopiert eine mittlere Datei in Chunks.
        
        Args:
            transfer_id: ID des Transfers
            source: Quelldatei
            target: Zieldatei
            
        Returns:
            True wenn der Transfer erfolgreich war
        """
        logger.debug(f"Starte Kopieren von mittlerer Datei: {source} -> {target}")
        
        # Stelle sicher, dass das Zielverzeichnis existiert
        target_dir = os.path.dirname(target)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
            
        try:
            # Bestimme optimale Chunk-Größe
            file_size = os.path.getsize(source)
            chunk_size = self._get_optimal_chunk_size(file_size)
            
            # Öffne Quelldatei
            with open(source, 'rb') as src:
                # Öffne Zieldatei
                with open(target, 'wb') as dst:
                    bytes_copied = 0
                    
                    # Sende Start-Progress
                    self._send_progress_update(transfer_id, 0)
                    
                    # Kopiere in Chunks
                    while True:
                        chunk = src.read(chunk_size)
                        if not chunk:
                            break
                            
                        dst.write(chunk)
                        bytes_copied += len(chunk)
                        
                        # Berechne und sende Fortschritt
                        progress = (bytes_copied / file_size) * 100
                        self._send_progress_update(transfer_id, progress)
                        
            # Prüfe ob die Zieldatei existiert und die richtige Größe hat
            if not os.path.exists(target):
                raise FileNotFoundError(f"Zieldatei wurde nicht erstellt: {target}")
                
            if os.path.getsize(target) != file_size:
                raise IOError(f"Zieldatei hat falsche Größe: {target}")
                
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Kopieren von {source}: {e}")
            # Lösche temporäre Datei falls vorhanden
            if os.path.exists(target):
                try:
                    os.remove(target)
                except Exception as cleanup_error:
                    logger.warning(f"Konnte temporäre Datei nicht löschen: {cleanup_error}")
            raise
            
    def _copy_large_file(self, transfer_id: str, source: str, target: str):
        """Kopiert eine große Datei mit Memory-Mapping.
        
        Args:
            transfer_id: ID des Transfers
            source: Quelldatei
            target: Zieldatei
            
        Returns:
            True wenn der Transfer erfolgreich war
        """
        logger.debug(f"Starte Kopieren von großer Datei: {source} -> {target}")
        
        # Stelle sicher, dass das Zielverzeichnis existiert
        target_dir = os.path.dirname(target)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
            
        try:
            # Bestimme Dateigröße
            file_size = os.path.getsize(source)
            
            # Bestimme optimale Chunk-Größe
            chunk_size = self._get_optimal_chunk_size(file_size)
            
            # Öffne Quelldatei
            with open(source, 'rb') as src:
                # Memory-Map für Quelldatei
                with mmap.mmap(src.fileno(), 0, access=mmap.ACCESS_READ) as mm_src:
                    # Öffne Zieldatei
                    with open(target, 'wb') as dst:
                        bytes_copied = 0
                        
                        # Sende Start-Progress
                        self._send_progress_update(transfer_id, 0)
                        
                        # Kopiere in Chunks
                        while bytes_copied < file_size:
                            remaining = file_size - bytes_copied
                            current_chunk = min(chunk_size, remaining)
                            
                            chunk = mm_src.read(current_chunk)
                            dst.write(chunk)
                            
                            bytes_copied += current_chunk
                            
                            # Berechne und sende Fortschritt
                            progress = (bytes_copied / file_size) * 100
                            self._send_progress_update(transfer_id, progress)
                            
            # Prüfe ob die Zieldatei existiert und die richtige Größe hat
            if not os.path.exists(target):
                raise FileNotFoundError(f"Zieldatei wurde nicht erstellt: {target}")
                
            if os.path.getsize(target) != file_size:
                raise IOError(f"Zieldatei hat falsche Größe: {target}")
                
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Kopieren von {source}: {e}")
            # Lösche temporäre Datei falls vorhanden
            if os.path.exists(target):
                try:
                    os.remove(target)
                except Exception as cleanup_error:
                    logger.warning(f"Konnte temporäre Datei nicht löschen: {cleanup_error}")
            raise
            
    def _calculate_checksum(self, file_path: str, chunk_size: int = 8192) -> str:
        """Berechnet MD5-Prüfsumme einer Datei.
        
        Args:
            file_path: Pfad zur Datei
            chunk_size: Chunk-Größe für Berechnung
            
        Returns:
            MD5-Prüfsumme als Hex-String
        """
        import hashlib
        md5 = hashlib.md5()
        
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                md5.update(chunk)
                
        return md5.hexdigest()
    
    def _save_resume_state(self, stats: TransferStats, resume_file: str):
        """Speichert den Übertragungszustand in einer Datei.
        
        Args:
            stats: Transfer-Statistiken
            resume_file: Pfad zur Resume-Datei
        """
        try:
            with open(resume_file, 'w') as f:
                json.dump(stats.to_json(), f)
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Resume-Zustands: {str(e)}")
