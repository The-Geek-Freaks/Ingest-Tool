#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Optimierte Copy Engine für schnelle Dateiübertragungen.
Nutzt Buffering, Memory Mapping und adaptive Optimierungen für maximale Performance.
"""

import os
import mmap
import threading
import time
import psutil
import asyncio
from typing import Optional, Callable, Tuple
from dataclasses import dataclass
from datetime import timedelta

@dataclass
class CopyStats:
    """Statistiken für einen Kopiervorgang."""
    bytes_copied: int = 0
    start_time: float = 0.0
    last_update: float = 0.0
    speed: float = 0.0

class OptimizedCopyEngine:
    """Optimierte Copy Engine für schnelle Dateiübertragungen."""
    
    def __init__(self):
        """Initialisiert die Copy Engine mit adaptiven Optimierungen."""
        self.chunk_size = self._get_optimal_chunk_size()
        self.buffer_size = self._get_optimal_buffer_size()
        self.max_workers = self._get_optimal_workers()
        self._stop_event = threading.Event()
        
    def _get_optimal_chunk_size(self) -> int:
        """Ermittelt die optimale Chunk-Größe basierend auf System-Ressourcen."""
        try:
            # Nutze 1% des verfügbaren RAMs, mindestens 1MB, maximal 8MB
            mem_chunk = psutil.virtual_memory().available // 100
            return max(min(mem_chunk, 8 * 1024 * 1024), 1024 * 1024)
        except:
            return 1024 * 1024  # Fallback: 1MB
        
    def _get_optimal_buffer_size(self) -> int:
        """Ermittelt die optimale Buffer-Größe basierend auf System-Ressourcen."""
        try:
            # Nutze 2% des verfügbaren RAMs, mindestens 8MB, maximal 32MB
            mem_buffer = psutil.virtual_memory().available // 50
            return max(min(mem_buffer, 32 * 1024 * 1024), 8 * 1024 * 1024)
        except:
            return 8 * 1024 * 1024  # Fallback: 8MB
        
    def _get_optimal_workers(self) -> int:
        """Ermittelt die optimale Anzahl paralleler Worker."""
        try:
            cpu_count = psutil.cpu_count()
            io_count = len(psutil.disk_partitions())
            return min(max(4, cpu_count), io_count * 2)
        except:
            return 4  # Fallback: 4 Worker

    def _get_io_stats(self, path: str) -> Tuple[float, float]:
        """Ermittelt IO-Statistiken für einen Pfad."""
        try:
            disk_io = psutil.disk_io_counters(perdisk=True)
            disk = os.path.splitdrive(path)[0].strip(':')
            if disk in disk_io:
                stats = disk_io[disk]
                return stats.read_bytes / (stats.read_time or 1), stats.write_bytes / (stats.write_time or 1)
            return 0.0, 0.0
        except:
            return 0.0, 0.0

    async def copy_file(
        self,
        source: str,
        target: str,
        progress_callback: Optional[Callable[[str, float, float, timedelta], None]] = None,
        delete_source: bool = False
    ) -> bool:
        """Kopiert eine Datei mit optimaler Performance.
        
        Args:
            source: Quellpfad
            target: Zielpfad
            progress_callback: Callback für Fortschritts-Updates (filename, progress, speed, eta)
            delete_source: Wenn True, wird die Quelldatei nach erfolgreichem Kopieren gelöscht
            
        Returns:
            bool: True wenn erfolgreich
        """
        try:
            # Erstelle Zielverzeichnis
            os.makedirs(os.path.dirname(target), exist_ok=True)
            
            # Hole Dateigröße und IO-Stats
            file_size = os.path.getsize(source)
            read_speed, write_speed = self._get_io_stats(source)
            
            # Initialisiere Statistiken
            stats = CopyStats(
                start_time=time.time(),
                last_update=time.time()
            )
            
            # Wähle optimale Kopiermethode
            if file_size > 100 * 1024 * 1024:  # > 100MB
                success = await self._copy_large_file(source, target, file_size, stats, progress_callback)
            elif file_size > self.buffer_size:
                success = await self._copy_with_mmap(source, target, file_size, stats, progress_callback)
            else:
                success = await self._copy_with_chunks(source, target, file_size, stats, progress_callback)
            
            # Wenn das Kopieren erfolgreich war und die Quelldatei gelöscht werden soll
            if success and delete_source:
                try:
                    os.remove(source)
                except Exception as e:
                    print(f"Fehler beim Löschen der Quelldatei {source}: {e}")
                    # Das Kopieren war trotzdem erfolgreich, also geben wir True zurück
                
            return success
            
        except Exception as e:
            print(f"Fehler beim Kopieren: {e}")
            return False

    async def _copy_large_file(
        self,
        source: str,
        target: str,
        file_size: int,
        stats: CopyStats,
        progress_callback: Optional[Callable] = None
    ) -> bool:
        """Kopiert eine große Datei mit Direct IO und Memory Mapping."""
        try:
            # Öffne Dateien mit normalen Handles für Windows-Kompatibilität
            with open(source, 'rb', buffering=0) as src, open(target, 'wb', buffering=0) as dst:
                # Memory Map für Quelldatei
                with mmap.mmap(src.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    for offset in range(0, file_size, self.buffer_size):
                        if self._stop_event.is_set():
                            return False
                            
                        chunk_size = min(self.buffer_size, file_size - offset)
                        chunk = mm[offset:offset + chunk_size]
                        
                        # Asynchrones Schreiben
                        await asyncio.get_event_loop().run_in_executor(None, dst.write, chunk)
                        
                        # Update Statistiken
                        stats.bytes_copied += chunk_size
                        self._update_progress(stats, file_size, progress_callback, source)
                        
                        # Yield für andere Tasks
                        await asyncio.sleep(0)
                        
            return True
            
        except Exception as e:
            print(f"Fehler beim Kopieren großer Datei: {e}")
            return False

    async def _copy_with_mmap(
        self,
        source: str,
        target: str,
        file_size: int,
        stats: CopyStats,
        progress_callback: Optional[Callable] = None
    ) -> bool:
        """Kopiert eine Datei mit Memory Mapping."""
        try:
            with open(source, 'rb') as src, open(target, 'wb') as dst:
                with mmap.mmap(src.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    for offset in range(0, file_size, self.buffer_size):
                        if self._stop_event.is_set():
                            return False
                            
                        chunk_size = min(self.buffer_size, file_size - offset)
                        chunk = mm[offset:offset + chunk_size]
                        
                        await asyncio.get_event_loop().run_in_executor(None, dst.write, chunk)
                        
                        stats.bytes_copied += chunk_size
                        self._update_progress(stats, file_size, progress_callback, source)
                        
                        await asyncio.sleep(0)
                        
            return True
            
        except Exception as e:
            print(f"Fehler beim Kopieren mit mmap: {e}")
            return False

    async def _copy_with_chunks(
        self,
        source: str,
        target: str,
        file_size: int,
        stats: CopyStats,
        progress_callback: Optional[Callable] = None
    ) -> bool:
        """Kopiert eine Datei in Chunks."""
        try:
            with open(source, 'rb') as src, open(target, 'wb') as dst:
                while True:
                    if self._stop_event.is_set():
                        return False
                        
                    chunk = src.read(self.chunk_size)
                    if not chunk:
                        break
                        
                    await asyncio.get_event_loop().run_in_executor(None, dst.write, chunk)
                    
                    stats.bytes_copied += len(chunk)
                    self._update_progress(stats, file_size, progress_callback, source)
                    
                    await asyncio.sleep(0)
                    
            return True
            
        except Exception as e:
            print(f"Fehler beim Kopieren mit Chunks: {e}")
            return False

    def _update_progress(self, stats: CopyStats, total_size: int, callback: Optional[Callable] = None, source: str = None):
        """Aktualisiert die Fortschrittsanzeige.
        
        Args:
            stats: Kopier-Statistiken
            total_size: Gesamtgröße der Datei
            callback: Callback-Funktion für Updates
            source: Quellpfad der Datei
        """
        try:
            current_time = time.time()
            time_diff = current_time - stats.last_update
            
            # Update nur alle 100ms
            if time_diff < 0.1:
                return
                
            # Berechne Geschwindigkeit (Bytes/Sekunde)
            if time_diff > 0:
                current_speed = (stats.bytes_copied / (current_time - stats.start_time))
                # Aktualisiere gleitenden Durchschnitt
                stats.speed = (stats.speed * 0.7 + current_speed * 0.3)
            
            # Berechne Fortschritt
            progress = stats.bytes_copied / total_size if total_size > 0 else 0
            
            # Berechne ETA
            remaining_bytes = total_size - stats.bytes_copied
            if stats.speed > 0:
                eta_seconds = remaining_bytes / stats.speed
                eta = timedelta(seconds=int(eta_seconds))
            else:
                eta = timedelta(seconds=0)
            
            # Aktualisiere Zeitstempel
            stats.last_update = current_time
            
            # Rufe Callback auf
            if callback:
                filename = os.path.basename(source) if source else ""
                callback(filename, progress, stats.speed, eta)
                
        except Exception as e:
            print(f"Fehler beim Aktualisieren des Fortschritts: {e}")

    def copy_file_with_progress(
        self,
        source: str,
        target: str,
        progress_callback: Optional[Callable[[int, int, float], None]] = None
    ) -> bool:
        """Kopiert eine Datei mit Fortschritts-Updates.
        
        Args:
            source: Quellpfad
            target: Zielpfad
            progress_callback: Callback für Fortschritts-Updates (copied_bytes, total_bytes, speed)
            
        Returns:
            bool: True wenn erfolgreich
        """
        try:
            # Erstelle Zielverzeichnis
            os.makedirs(os.path.dirname(target), exist_ok=True)
            
            # Hole Dateigröße
            file_size = os.path.getsize(source)
            
            # Initialisiere Statistiken
            bytes_copied = 0
            start_time = time.time()
            last_update = start_time
            last_bytes = 0
            speed = 0.0
            
            # Öffne Dateien
            with open(source, 'rb') as src, open(target, 'wb') as dst:
                while True:
                    # Lese Chunk
                    chunk = src.read(self.chunk_size)
                    if not chunk:
                        break
                        
                    # Schreibe Chunk
                    dst.write(chunk)
                    bytes_copied += len(chunk)
                    
                    # Update Fortschritt
                    current_time = time.time()
                    if current_time - last_update >= 0.1:  # Update alle 100ms
                        # Berechne aktuelle Geschwindigkeit basierend auf dem letzten Intervall
                        interval = current_time - last_update
                        bytes_in_interval = bytes_copied - last_bytes
                        
                        if interval > 0:
                            current_speed = bytes_in_interval / interval  # Bytes pro Sekunde
                            speed = current_speed / (1024 * 1024)  # Konvertiere zu MB/s
                            
                            if progress_callback:
                                progress_callback(bytes_copied, file_size, speed)
                            
                        last_update = current_time
                        last_bytes = bytes_copied
            
            # Sende finales Update mit Durchschnittsgeschwindigkeit
            total_time = time.time() - start_time
            if total_time > 0:
                avg_speed = (file_size / total_time) / (1024 * 1024)  # MB/s
            else:
                avg_speed = 0.0
                
            if progress_callback:
                progress_callback(file_size, file_size, avg_speed)
            
            return True
            
        except Exception as e:
            print(f"Fehler beim Kopieren: {e}")
            return False

    def stop(self):
        """Stoppt alle laufenden Kopier-Operationen."""
        self._stop_event.set()
