#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class BatchJob:
    """Repräsentiert einen einzelnen Kopierauftrag in der Batch-Verarbeitung."""
    source_drive: str
    file_type: str
    target_path: str
    status: str = "pending"  # pending, running, completed, failed, stopped
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class BatchManager:
    """Verwaltet die Batch-Verarbeitung von Kopieraufträgen."""
    
    def __init__(self):
        self.jobs: List[BatchJob] = []
        self.current_job: Optional[BatchJob] = None
        
    def add_job(self, source_drive: str, file_type: str, target_path: str) -> BatchJob:
        """Fügt einen neuen Kopierauftrag zur Warteschlange hinzu."""
        job = BatchJob(source_drive, file_type, target_path)
        self.jobs.append(job)
        logger.info(f"Neuer Batch-Job hinzugefügt: {source_drive} -> {target_path} ({file_type})")
        return job
    
    def remove_job(self, job: BatchJob):
        """Entfernt einen Kopierauftrag aus der Warteschlange."""
        if job in self.jobs:
            self.jobs.remove(job)
            logger.info(f"Batch-Job entfernt: {job.source_drive} -> {job.target_path}")
    
    def move_job(self, job: BatchJob, direction: int):
        """Verschiebt einen Job in der Warteschlange nach oben oder unten."""
        if job not in self.jobs:
            return
            
        current_index = self.jobs.index(job)
        new_index = current_index + direction
        
        if 0 <= new_index < len(self.jobs):
            self.jobs.pop(current_index)
            self.jobs.insert(new_index, job)
            
    def get_next_job(self) -> Optional[BatchJob]:
        """Gibt den nächsten ausstehenden Job zurück."""
        for job in self.jobs:
            if job.status == "pending":
                return job
        return None
    
    def start_job(self, job: BatchJob):
        """Startet die Ausführung eines Jobs."""
        if job.status != "pending":
            return
            
        job.status = "running"
        job.start_time = datetime.now()
        self.current_job = job
        logger.info(f"Batch-Job gestartet: {job.source_drive} -> {job.target_path}")
    
    def complete_job(self, job: BatchJob, success: bool = True):
        """Markiert einen Job als abgeschlossen."""
        job.end_time = datetime.now()
        job.status = "completed" if success else "failed"
        
        if job == self.current_job:
            self.current_job = None
            
        logger.info(f"Batch-Job {'abgeschlossen' if success else 'fehlgeschlagen'}: {job.source_drive} -> {job.target_path}")
    
    def get_job_info(self, job: BatchJob) -> Dict:
        """Gibt Informationen über einen Job zurück."""
        duration = None
        if job.start_time and job.end_time:
            duration = (job.end_time - job.start_time).total_seconds()
            
        return {
            "source": job.source_drive,
            "type": job.file_type,
            "target": job.target_path,
            "status": job.status,
            "duration": duration
        }
    
    def clear_completed(self):
        """Entfernt alle abgeschlossenen Jobs aus der Warteschlange."""
        self.jobs = [job for job in self.jobs 
                    if job.status not in ("completed", "failed")]
                    
    def stop(self):
        """Stoppt alle laufenden Jobs und bereinigt die Warteschlange."""
        try:
            # Stoppe den aktuellen Job
            if self.current_job and self.current_job.status == "running":
                self.current_job.status = "stopped"
                self.current_job.end_time = datetime.now()
                logger.info(f"Laufender Job gestoppt: {self.current_job.source_drive} -> {self.current_job.target_path}")
                
            # Markiere alle anderen Jobs als gestoppt
            for job in self.jobs:
                if job.status == "running":
                    job.status = "stopped"
                    job.end_time = datetime.now()
                    
            self.current_job = None
            logger.info("Alle Batch-Jobs gestoppt")
            
        except Exception as e:
            logger.error(f"Fehler beim Stoppen der Batch-Jobs: {e}")
