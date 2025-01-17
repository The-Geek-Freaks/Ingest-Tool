#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Verwaltet Batch-Operationen für Dateitransfers.
"""

import uuid
import logging
import threading
from datetime import datetime
from typing import List

logger = logging.getLogger(__name__)

class BatchManager:
    """Manager für Transfer-Batches."""
    
    def __init__(self):
        """Initialisiert den BatchManager."""
        self._batches = {}
        self._lock = threading.Lock()
        
    def create_batch(self, batch_id: str, total_transfers: int) -> None:
        """Erstellt einen neuen Transfer-Batch.
        
        Args:
            batch_id: ID des Batches
            total_transfers: Gesamtanzahl der Transfers im Batch
        """
        with self._lock:
            self._batches[batch_id] = {
                'id': batch_id,
                'total_transfers': total_transfers,
                'completed_transfers': 0,
                'failed_transfers': 0,
                'status': 'created',
                'transfers': [],
                'start_time': datetime.now(),
                'end_time': None
            }
            
    def add_transfer_to_batch(self, batch_id: str, transfer_id: str) -> None:
        """Fügt einen Transfer zu einem Batch hinzu.
        
        Args:
            batch_id: ID des Batches
            transfer_id: ID des Transfers
        """
        with self._lock:
            if batch_id in self._batches:
                self._batches[batch_id]['transfers'].append(transfer_id)
                
    def update_transfer_status(self, batch_id: str, transfer_id: str, status: str) -> None:
        """Aktualisiert den Status eines Transfers im Batch.
        
        Args:
            batch_id: ID des Batches
            transfer_id: ID des Transfers
            status: Neuer Status ('completed', 'error', 'cancelled')
        """
        with self._lock:
            if batch_id in self._batches:
                batch = self._batches[batch_id]
                if status == 'completed':
                    batch['completed_transfers'] += 1
                elif status in ('error', 'cancelled'):
                    batch['failed_transfers'] += 1
                    
                if batch['completed_transfers'] + batch['failed_transfers'] == batch['total_transfers']:
                    batch['status'] = 'completed'
                    batch['end_time'] = datetime.now()
                    
    def is_batch_complete(self, batch_id: str) -> bool:
        """Prüft, ob ein Batch abgeschlossen ist.
        
        Args:
            batch_id: ID des Batches
            
        Returns:
            bool: True wenn alle Transfers abgeschlossen sind
        """
        with self._lock:
            if batch_id in self._batches:
                batch = self._batches[batch_id]
                return batch['completed_transfers'] + batch['failed_transfers'] == batch['total_transfers']
            return False
            
    def get_batch_transfers(self, batch_id: str) -> List[str]:
        """Gibt die Transfer-IDs eines Batches zurück.
        
        Args:
            batch_id: ID des Batches
            
        Returns:
            List[str]: Liste der Transfer-IDs
        """
        with self._lock:
            if batch_id in self._batches:
                return self._batches[batch_id]['transfers']
            return []
