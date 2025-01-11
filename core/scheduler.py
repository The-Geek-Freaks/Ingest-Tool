#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Scheduler für zeitgesteuerte Transfers."""

import logging
from PyQt5.QtCore import QTimer, QTime

logger = logging.getLogger(__name__)

class TransferScheduler:
    """Scheduler für zeitgesteuerte Transfers."""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.schedule_timer = None
        
    def setup_scheduled_transfer(self, start_time: str):
        """Richtet die zeitgesteuerte Übertragung ein."""
        time = QTime.fromString(start_time, "HH:mm")
        if not self.schedule_timer:
            self.schedule_timer = QTimer(self.main_window)
            self.schedule_timer.timeout.connect(self.main_window.batch_manager.start_batch_processing)
            
        # Berechne die Zeit bis zum nächsten Start
        current_time = QTime.currentTime()
        target_time = QTime(time.hour(), time.minute())
        
        msecs_until = current_time.msecsTo(target_time)
        if msecs_until < 0:  # Wenn die Zeit heute schon vorbei ist, plane für morgen
            msecs_until += 24 * 60 * 60 * 1000
            
        self.schedule_timer.start(msecs_until)
        logger.info(f"Zeitgesteuerte Übertragung eingerichtet für {start_time}")
        
    def disable_scheduled_transfer(self):
        """Deaktiviert die zeitgesteuerte Übertragung."""
        if self.schedule_timer:
            self.schedule_timer.stop()
            logger.info("Zeitgesteuerte Übertragung deaktiviert")
