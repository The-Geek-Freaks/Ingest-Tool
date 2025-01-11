"""
Controller für Dateiübertragungen.
"""
import logging
from concurrent.futures import ThreadPoolExecutor
from PyQt5.QtCore import QObject, pyqtSignal

from core.transfer import TransferManager

class TransferController(QObject):
    """Controller für Dateiübertragungen."""
    
    # Signale
    transfer_started = pyqtSignal(str, str)  # source, target
    transfer_progress = pyqtSignal(str, str, int, int)  # source, target, current, total
    transfer_completed = pyqtSignal(str, str)  # source, target
    transfer_failed = pyqtSignal(str, str)  # source, error
    transfer_cancelled = pyqtSignal(str)  # source
    
    def __init__(self):
        """Initialisiert den TransferController."""
        super().__init__()
        
        # Initialisiere Manager und Executor
        self.transfer_manager = TransferManager()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Verbinde Signale
        self._connect_signals()
        
    def _connect_signals(self):
        """Verbindet die Signale des TransferManagers."""
        try:
            self.transfer_manager.set_callbacks(
                progress_callback=lambda src, dst, cur, tot: self.transfer_progress.emit(src, dst, cur, tot),
                completion_callback=lambda src, dst: self.transfer_completed.emit(src, dst),
                error_callback=lambda src, err: self.transfer_failed.emit(src, err)
            )
        except Exception as e:
            logging.error(f"Fehler beim Verbinden der Signale: {str(e)}")
        
    def start_transfer(self, source_path: str = None, target_path: str = None):
        """Startet eine neue Übertragung."""
        try:
            if source_path and target_path:
                self.transfer_manager.start_transfer(source_path, target_path)
            else:
                logging.error("Quell- und Zielpfad müssen angegeben werden")
                self.transfer_failed.emit("", "Quell- und Zielpfad müssen angegeben werden")
                
        except Exception as e:
            logging.error(f"Fehler beim Starten der Übertragung: {str(e)}")
            self.transfer_failed.emit("", str(e))
            
    def cancel_transfer(self):
        """Bricht die aktuelle Übertragung ab."""
        try:
            self.transfer_manager.cancel_transfer()
        except Exception as e:
            logging.error(f"Fehler beim Abbrechen der Übertragung: {str(e)}")
            
    def cleanup(self):
        """Räumt den Controller auf."""
        try:
            self.executor.shutdown(wait=False)
            self.transfer_manager.shutdown()
        except Exception as e:
            logging.error(f"Fehler beim Aufräumen des TransferControllers: {str(e)}")
            
    def __del__(self):
        """Destruktor."""
        self.cleanup()
