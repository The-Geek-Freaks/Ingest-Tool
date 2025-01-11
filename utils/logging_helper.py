import os
import sys
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Optional

class LoggingHelper:
    """Erweiterte Logging-Funktionalität mit Rotation und Formatierung."""
    
    DEFAULT_FORMAT = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    def __init__(self, 
                 log_dir: Optional[str] = None,
                 max_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5,
                 log_level: int = logging.INFO):
        """Initialisiert den LoggingHelper.
        
        Args:
            log_dir: Verzeichnis für Log-Dateien
            max_size: Maximale Größe einer Log-Datei
            backup_count: Anzahl der Backup-Dateien
            log_level: Standard-Log-Level
        """
        self.log_dir = log_dir or self._get_default_log_dir()
        self.max_size = max_size
        self.backup_count = backup_count
        self.log_level = log_level
        
        # Erstelle Log-Verzeichnis
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Konfiguriere Root-Logger
        self._setup_root_logger()
        
        # Speichere letzte Fehlermeldungen für UI
        self.error_history = []
        self.max_error_history = 100
    
    def _get_default_log_dir(self) -> str:
        """Ermittelt Standard-Log-Verzeichnis."""
        if sys.platform == 'win32':
            base_dir = os.environ.get('LOCALAPPDATA')
        else:
            base_dir = os.path.expanduser('~/.local/share')
        
        return os.path.join(base_dir, 'IngestTool', 'logs')
    
    def _setup_root_logger(self):
        """Konfiguriert den Root-Logger mit File- und Stream-Handler."""
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # Entferne existierende Handler
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Erstelle Formatter
        formatter = logging.Formatter(
            fmt=self.DEFAULT_FORMAT,
            datefmt=self.DEFAULT_DATE_FORMAT
        )
        
        # File Handler mit Rotation
        log_file = os.path.join(
            self.log_dir,
            f'ingest_tool_{datetime.now():%Y%m%d}.log'
        )
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.max_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # Stream Handler für Konsole
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    def add_error_to_history(self, error_msg: str):
        """Fügt einen Fehler zum Error-Verlauf hinzu."""
        timestamp = datetime.now().strftime(self.DEFAULT_DATE_FORMAT)
        self.error_history.append((timestamp, error_msg))
        
        # Begrenze Verlauf-Größe
        if len(self.error_history) > self.max_error_history:
            self.error_history.pop(0)
    
    def get_error_history(self, count: Optional[int] = None) -> list:
        """Gibt den Error-Verlauf zurück."""
        if count is None:
            return self.error_history
        return self.error_history[-count:]
    
    def clear_error_history(self):
        """Löscht den Error-Verlauf."""
        self.error_history.clear()
    
    def get_log_files(self) -> list:
        """Gibt eine Liste aller Log-Dateien zurück."""
        log_files = []
        for file in os.listdir(self.log_dir):
            if file.startswith('ingest_tool_') and file.endswith('.log'):
                file_path = os.path.join(self.log_dir, file)
                log_files.append({
                    'path': file_path,
                    'size': os.path.getsize(file_path),
                    'modified': datetime.fromtimestamp(
                        os.path.getmtime(file_path)
                    )
                })
        return sorted(log_files, key=lambda x: x['modified'], reverse=True)
    
    def rotate_logs(self):
        """Führt eine manuelle Log-Rotation durch."""
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                handler.doRollover()
    
    def set_log_level(self, level: int):
        """Setzt den Log-Level für alle Handler."""
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        for handler in root_logger.handlers:
            handler.setLevel(level)
    
    def archive_old_logs(self, days: int = 30):
        """Archiviert alte Log-Dateien."""
        import shutil
        from datetime import timedelta
        
        archive_dir = os.path.join(self.log_dir, 'archive')
        os.makedirs(archive_dir, exist_ok=True)
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for log_file in self.get_log_files():
            if log_file['modified'] < cutoff_date:
                file_name = os.path.basename(log_file['path'])
                archive_path = os.path.join(archive_dir, file_name)
                shutil.move(log_file['path'], archive_path)
    
    @staticmethod
    def format_exception(exc_info) -> str:
        """Formatiert eine Exception für das Logging."""
        import traceback
        return ''.join(traceback.format_exception(*exc_info))

# Erstelle eine globale Instanz
logging_helper = LoggingHelper()

def setup_logger(name: str) -> logging.Logger:
    """Hilfsfunktion zum Erstellen eines neuen Loggers."""
    logger = logging.getLogger(name)
    logger.setLevel(logging_helper.log_level)
    return logger

# Decorator für Exception-Logging
def log_exceptions(logger: Optional[logging.Logger] = None):
    """Decorator zum automatischen Logging von Exceptions."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = logging.getLogger(func.__module__)
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_msg = f"Exception in {func.__name__}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                logging_helper.add_error_to_history(error_msg)
                raise
        
        return wrapper
    return decorator
