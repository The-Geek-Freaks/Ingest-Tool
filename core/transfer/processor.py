"""
Verarbeitung einzelner Dateiübertragungen.
"""

import os
import logging
from typing import Dict, Optional, Callable
from datetime import datetime

class TransferProcessor:
    """Verarbeitet einzelne Dateiübertragungen."""
    
    def __init__(
        self,
        metadata_manager,
        analytics_manager,
        progress_callback: Optional[Callable[[str, float], None]] = None,
        completion_callback: Optional[Callable[[str, bool], None]] = None,
        error_callback: Optional[Callable[[str, str], None]] = None
    ):
        self._metadata_manager = metadata_manager
        self._analytics = analytics_manager
        self._progress_callback = progress_callback
        self._completion_callback = completion_callback
        self._error_callback = error_callback
        
    def process_transfer(self, transfer: Dict):
        """Verarbeitet eine einzelne Übertragung."""
        try:
            # Initialisiere Transfer
            transfer['status'] = 'active'
            transfer['start_time'] = datetime.now()
            transfer['progress'] = 0
            
            # Prüfe Quelle und Ziel
            if not os.path.exists(transfer['source']):
                raise FileNotFoundError(
                    f"Quelldatei nicht gefunden: {transfer['source']}"
                )
                
            # Erstelle Zielverzeichnis falls nötig
            os.makedirs(os.path.dirname(transfer['destination']), exist_ok=True)
            
            # Kopiere in Chunks
            self._copy_file(transfer)
            
            # Prüfe Integrität
            if not self._metadata_manager.verify_file_integrity(
                transfer['source'], 
                transfer['destination']
            ):
                raise ValueError("Integritätsprüfung fehlgeschlagen")
                
            # Übertrage Metadaten
            if transfer['metadata']:
                self._metadata_manager.restore_metadata(
                    transfer['destination'], 
                    transfer['metadata']
                )
                
            # Markiere als erfolgreich
            self._complete_transfer(transfer, success=True)
            
        except Exception as e:
            # Fehlerbehandlung
            self._handle_error(transfer, e)
            
        finally:
            # Aktualisiere Analytics
            self._analytics.record_transfer(transfer)
            
    def _copy_file(self, transfer: Dict):
        """Kopiert eine Datei in Chunks."""
        total_size = transfer['size']
        copied_size = 0
        chunk_size = 8192  # 8KB
        
        with open(transfer['source'], 'rb') as src, \
             open(transfer['destination'], 'wb') as dst:
            while True:
                chunk = src.read(chunk_size)
                if not chunk:
                    break
                    
                # Prüfe auf Abbruch
                if transfer['status'] == 'cancelled':
                    raise InterruptedError("Transfer abgebrochen")
                    
                # Prüfe auf Pause
                while transfer['status'] == 'paused':
                    import threading
                    threading.Event().wait(1)
                    
                # Schreibe Chunk
                dst.write(chunk)
                copied_size += len(chunk)
                
                # Aktualisiere Fortschritt
                progress = (copied_size / total_size) * 100
                transfer['progress'] = progress
                
                # Rufe Fortschritts-Callback auf
                if self._progress_callback:
                    self._progress_callback(transfer['id'], progress)
                    
    def _complete_transfer(self, transfer: Dict, success: bool):
        """Schließt eine Übertragung ab."""
        transfer['status'] = 'completed' if success else 'failed'
        transfer['end_time'] = datetime.now()
        transfer['progress'] = 100 if success else transfer['progress']
        
        if success and self._completion_callback:
            self._completion_callback(transfer['id'], True)
            
    def _handle_error(self, transfer: Dict, error: Exception):
        """Behandelt Fehler während der Übertragung."""
        transfer['status'] = 'failed'
        transfer['end_time'] = datetime.now()
        transfer['error'] = str(error)
        
        # Lösche unvollständige Zieldatei
        if os.path.exists(transfer['destination']):
            try:
                os.remove(transfer['destination'])
            except:
                pass
                
        # Rufe Error-Callback auf
        if self._error_callback:
            self._error_callback(transfer['id'], str(error))
            
        # Zeichne Fehler auf
        self._analytics.record_error({
            'transfer_id': transfer['id'],
            'type': type(error).__name__,
            'message': str(error),
            'path': transfer['source']
        })
