#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fehlerklassen für das Transfer-System.
"""

from typing import Optional
from datetime import datetime

class TransferError(Exception):
    """Basisklasse für alle Transfer-bezogenen Fehler."""
    
    def __init__(self, message: str, transfer_id: Optional[str] = None):
        super().__init__(message)
        self.transfer_id = transfer_id
        self.timestamp = datetime.now()
        
    def __str__(self) -> str:
        base = f"{self.__class__.__name__}: {super().__str__()}"
        if self.transfer_id:
            return f"{base} (Transfer-ID: {self.transfer_id})"
        return base

class ValidationError(TransferError):
    """Fehler bei der Validierung von Transfer-Parametern."""
    pass

class ResourceError(TransferError):
    """Basisklasse für Ressourcen-bezogene Fehler."""
    pass

class DiskSpaceError(ResourceError):
    """Nicht genügend Speicherplatz verfügbar."""
    
    def __init__(self, message: str, required: int, available: int, transfer_id: Optional[str] = None):
        super().__init__(message, transfer_id)
        self.required = required
        self.available = available
        
    def __str__(self) -> str:
        return (f"{super().__str__()} - "
                f"Benötigt: {self.required / 1024 / 1024:.2f} MB, "
                f"Verfügbar: {self.available / 1024 / 1024:.2f} MB")

class IOError(ResourceError):
    """Fehler beim Lesen oder Schreiben von Dateien."""
    
    def __init__(self, message: str, path: str, transfer_id: Optional[str] = None):
        super().__init__(message, transfer_id)
        self.path = path
        
    def __str__(self) -> str:
        return f"{super().__str__()} - Pfad: {self.path}"

class NetworkError(ResourceError):
    """Netzwerk-bezogene Fehler."""
    pass

class TransferTimeoutError(TransferError):
    """Transfer-Timeout oder zu langsame Übertragung."""
    
    def __init__(self, message: str, duration: float, transfer_id: Optional[str] = None):
        super().__init__(message, transfer_id)
        self.duration = duration
        
    def __str__(self) -> str:
        return f"{super().__str__()} - Dauer: {self.duration:.1f}s"

class ConcurrencyError(TransferError):
    """Fehler bei der parallelen Verarbeitung."""
    pass

class BatchError(TransferError):
    """Fehler bei der Batch-Verarbeitung."""
    
    def __init__(self, message: str, batch_id: str, transfer_id: Optional[str] = None):
        super().__init__(message, transfer_id)
        self.batch_id = batch_id
        
    def __str__(self) -> str:
        return f"{super().__str__()} - Batch-ID: {self.batch_id}"

class StateError(TransferError):
    """Ungültiger Zustand oder Zustandsübergang."""
    
    def __init__(self, message: str, current_state: str, 
                 expected_state: Optional[str] = None, transfer_id: Optional[str] = None):
        super().__init__(message, transfer_id)
        self.current_state = current_state
        self.expected_state = expected_state
        
    def __str__(self) -> str:
        base = f"{super().__str__()} - Aktueller Status: {self.current_state}"
        if self.expected_state:
            base += f", Erwartet: {self.expected_state}"
        return base

class RetryableError(TransferError):
    """Fehler, die automatisch wiederholt werden können."""
    
    def __init__(self, message: str, retry_count: int = 0, 
                 max_retries: int = 3, transfer_id: Optional[str] = None):
        super().__init__(message, transfer_id)
        self.retry_count = retry_count
        self.max_retries = max_retries
        
    def can_retry(self) -> bool:
        """Prüft ob ein weiterer Versuch möglich ist."""
        return self.retry_count < self.max_retries
        
    def __str__(self) -> str:
        return (f"{super().__str__()} - "
                f"Versuch {self.retry_count + 1} von {self.max_retries}")

class TransferCancelledError(TransferError):
    """Wird ausgelöst wenn ein Transfer abgebrochen wurde."""
    
    def __init__(self, message: str, transfer_id: Optional[str] = None, 
                 cancelled_by: Optional[str] = None):
        super().__init__(message, transfer_id)
        self.cancelled_by = cancelled_by
        
    def __str__(self) -> str:
        base = super().__str__()
        if self.cancelled_by:
            base += f" (Abgebrochen durch: {self.cancelled_by})"
        return base

class TransferCancelled(TransferError):
    """Exception für abgebrochene Transfers."""
    pass

class ErrorHandler:
    """Zentrale Fehlerbehandlung für das Transfer-System."""
    
    def __init__(self):
        self._error_callbacks = []
        self._retry_handlers = {}
        
    def add_error_callback(self, callback):
        """Fügt einen Callback für Fehlerbehandlung hinzu."""
        self._error_callbacks.append(callback)
        
    def add_retry_handler(self, error_type, handler):
        """Fügt einen Handler für automatische Wiederholungen hinzu."""
        self._retry_handlers[error_type] = handler
        
    def handle_error(self, error: TransferError) -> bool:
        """Behandelt einen aufgetretenen Fehler.
        
        Args:
            error: Der aufgetretene Fehler
            
        Returns:
            bool: True wenn der Fehler behandelt wurde
        """
        # Informiere alle Callbacks
        for callback in self._error_callbacks:
            try:
                callback(error)
            except Exception as e:
                print(f"Fehler im Error-Callback: {e}")
                
        # Prüfe auf Retry-Handler
        if isinstance(error, RetryableError) and error.can_retry():
            handler = self._retry_handlers.get(type(error))
            if handler:
                try:
                    handler(error)
                    return True
                except Exception as e:
                    print(f"Fehler im Retry-Handler: {e}")
                    
        return False
