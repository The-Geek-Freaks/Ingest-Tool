#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import logging
import hashlib
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from threading import Thread, Lock
from queue import Queue

logger = logging.getLogger(__name__)

@dataclass
class CopyTask:
    """Repräsentiert einen einzelnen Kopiervorgang."""
    source: str
    target: str
    file_size: int
    verify_mode: str = "none"
    status: str = "pending"
    bytes_copied: int = 0
    speed: float = 0.0  # Bytes pro Sekunde
    start_time: Optional[datetime] = None
    
    @property
    def progress(self) -> float:
        """Gibt den Fortschritt in Prozent zurück."""
        if self.file_size == 0:
            return 100.0
        return (self.bytes_copied / self.file_size) * 100

class ParallelCopier:
    """Verwaltet parallele Kopiervorgänge."""
    
    def __init__(self, max_workers: int = 2, buffer_size: int = 64*1024):
        self.max_workers = max_workers
        self.buffer_size = buffer_size
        self.tasks: Dict[str, CopyTask] = {}
        self.active_tasks: Dict[str, CopyTask] = {}
        self.queue: Queue = Queue()
        self.workers: List[Thread] = []
        self.running = False
        self.lock = Lock()
        self.progress_callback: Optional[Callable] = None
        
    def set_progress_callback(self, callback: Callable):
        """Setzt die Callback-Funktion für Fortschrittsupdates."""
        self.progress_callback = callback
        
    def add_task(self, source: str, target: str, verify_mode: str = "none") -> str:
        """Fügt einen neuen Kopiervorgang hinzu."""
        try:
            file_size = os.path.getsize(source)
            task_id = f"{source}->{target}"
            task = CopyTask(source, target, file_size, verify_mode)
            self.tasks[task_id] = task
            self.queue.put(task_id)
            logger.info(f"Neue Kopieraufgabe hinzugefügt: {source} -> {target}")
            return task_id
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen der Kopieraufgabe: {str(e)}")
            return None
            
    def start(self):
        """Startet die Verarbeitung der Kopiervorgänge."""
        if self.running:
            return
            
        self.running = True
        for _ in range(self.max_workers):
            worker = Thread(target=self._worker_thread)
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
            
    def stop(self):
        """Stoppt alle Kopiervorgänge."""
        self.running = False
        for worker in self.workers:
            worker.join()
        self.workers.clear()
        
    def _worker_thread(self):
        """Worker-Thread für Kopiervorgänge."""
        while self.running:
            try:
                task_id = self.queue.get(timeout=1)
                task = self.tasks[task_id]
                
                with self.lock:
                    self.active_tasks[task_id] = task
                    
                task.status = "running"
                task.start_time = datetime.now()
                
                try:
                    self._copy_file(task)
                    task.status = "completed"
                except Exception as e:
                    logger.error(f"Fehler beim Kopieren: {str(e)}")
                    task.status = "failed"
                    
                with self.lock:
                    if task_id in self.active_tasks:
                        del self.active_tasks[task_id]
                        
                self.queue.task_done()
                
            except Queue.Empty:
                continue
                
    def _copy_file(self, task: CopyTask):
        """Kopiert eine einzelne Datei.
        
        Args:
            task: Die auszuführende Kopieraufgabe
        """
        try:
            # Stelle sicher dass das Zielverzeichnis existiert
            target_dir = os.path.dirname(task.target)
            os.makedirs(target_dir, exist_ok=True)
            
            # Verwende robocopy für Windows
            source_dir = os.path.dirname(task.source)
            source_file = os.path.basename(task.source)
            target_dir = os.path.dirname(task.target)
            
            # Robocopy-Befehl vorbereiten
            cmd = [
                'robocopy',
                source_dir,  # Quellverzeichnis
                target_dir,  # Zielverzeichnis
                source_file, # Dateiname
                '/COPY:DAT',  # Kopiere Daten, Attribute und Timestamps
                '/Z',         # Kopiere im Wiederaufnahme-Modus
                '/R:1',       # Anzahl der Wiederholungen bei Fehler
                '/W:1',       # Wartezeit zwischen Wiederholungen (Sekunden)
                '/MT',        # Multithreaded kopieren
                '/NFL',       # Keine Dateiliste
                '/NDL',       # Keine Verzeichnisliste
                '/NP'         # Kein Fortschritt (vermeidet Encoding-Probleme)
            ]
            
            logger.info(f"Starte robocopy: {' '.join(cmd)}")
            
            # Starte Prozess
            import subprocess
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            # Warte auf Beendigung
            stdout, stderr = process.communicate()
            
            # Prüfe ob die Datei kopiert wurde
            if not os.path.exists(task.target):
                raise Exception(f"Datei wurde nicht kopiert: {task.target}")
            
            # Prüfe Dateigröße
            if os.path.getsize(task.target) != task.file_size:
                raise Exception(f"Kopierte Datei hat falsche Größe: {task.target}")
            
            # Wenn erfolgreich, logge es
            logger.info(f"Datei erfolgreich kopiert: {os.path.basename(task.target)}")
            
            # Aktualisiere Task-Status
            task.bytes_copied = task.file_size
            if self.progress_callback:
                self.progress_callback(task)
                
        except Exception as e:
            logger.error(f"Fehler beim Kopieren von {task.source}: {str(e)}")
            task.status = "failed"
            raise
            
    def get_active_tasks(self) -> List[CopyTask]:
        """Gibt eine Liste der aktiven Kopiervorgänge zurück."""
        with self.lock:
            return list(self.active_tasks.values())
            
    def get_total_progress(self) -> float:
        """Berechnet den Gesamtfortschritt aller Aufgaben."""
        total_size = sum(task.file_size for task in self.tasks.values())
        total_copied = sum(task.bytes_copied for task in self.tasks.values())
        
        if total_size == 0:
            return 100.0
        return (total_copied / total_size) * 100
        
    def get_total_speed(self) -> float:
        """Berechnet die Gesamtgeschwindigkeit aller aktiven Aufgaben."""
        with self.lock:
            return sum(task.speed for task in self.active_tasks.values())
