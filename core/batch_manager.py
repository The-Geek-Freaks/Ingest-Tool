#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import uuid
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class Batch:
    """Repräsentiert einen Batch von Transfers."""
    id: str
    name: str
    description: str
    created: str
    transfers: Set[str] = field(default_factory=set)
    status: str = "pending"  # pending, running, paused, completed, failed

class BatchManager:
    """Verwaltet Batches von Transfers."""
    
    def __init__(self):
        self.batches: Dict[str, Batch] = {}
        
    def create_batch(self, batch_id: str, name: str, description: str = "", created: str = None) -> str:
        """Erstellt einen neuen Batch.
        
        Args:
            batch_id: Eindeutige ID für den Batch
            name: Name des Batches
            description: Optionale Beschreibung
            created: Erstellungszeitpunkt (ISO-Format)
            
        Returns:
            ID des erstellten Batches
        """
        if not created:
            created = datetime.now().isoformat()
            
        batch = Batch(
            id=batch_id,
            name=name,
            description=description,
            created=created
        )
        self.batches[batch_id] = batch
        logger.info(f"Neuer Batch erstellt: {name} ({batch_id})")
        return batch_id
        
    def get_batch(self, batch_id: str) -> Optional[Dict]:
        """Gibt Informationen über einen Batch zurück.
        
        Args:
            batch_id: ID des Batches
            
        Returns:
            Dict mit Batch-Informationen oder None
        """
        batch = self.batches.get(batch_id)
        if not batch:
            return None
            
        return {
            'id': batch.id,
            'name': batch.name,
            'description': batch.description,
            'created': batch.created,
            'transfers': list(batch.transfers),
            'status': batch.status
        }
        
    def add_transfer(self, batch_id: str, transfer_id: str) -> bool:
        """Fügt einen Transfer zu einem Batch hinzu.
        
        Args:
            batch_id: ID des Batches
            transfer_id: ID des Transfers
            
        Returns:
            True wenn erfolgreich hinzugefügt
        """
        batch = self.batches.get(batch_id)
        if not batch:
            return False
            
        batch.transfers.add(transfer_id)
        logger.debug(f"Transfer {transfer_id} zu Batch {batch_id} hinzugefügt")
        return True
        
    def remove_transfer(self, batch_id: str, transfer_id: str) -> bool:
        """Entfernt einen Transfer aus einem Batch.
        
        Args:
            batch_id: ID des Batches
            transfer_id: ID des Transfers
            
        Returns:
            True wenn erfolgreich entfernt
        """
        batch = self.batches.get(batch_id)
        if not batch or transfer_id not in batch.transfers:
            return False
            
        batch.transfers.remove(transfer_id)
        logger.debug(f"Transfer {transfer_id} aus Batch {batch_id} entfernt")
        return True
        
    def remove_batch(self, batch_id: str) -> bool:
        """Entfernt einen Batch.
        
        Args:
            batch_id: ID des Batches
            
        Returns:
            True wenn erfolgreich entfernt
        """
        if batch_id not in self.batches:
            return False
            
        del self.batches[batch_id]
        logger.info(f"Batch {batch_id} entfernt")
        return True
        
    def update_batch_status(self, batch_id: str, status: str) -> bool:
        """Aktualisiert den Status eines Batches.
        
        Args:
            batch_id: ID des Batches
            status: Neuer Status
            
        Returns:
            True wenn erfolgreich aktualisiert
        """
        batch = self.batches.get(batch_id)
        if not batch:
            return False
            
        batch.status = status
        logger.debug(f"Status von Batch {batch_id} auf {status} gesetzt")
        return True
        
    def get_all_batches(self) -> List[Dict]:
        """Gibt eine Liste aller Batches zurück.
        
        Returns:
            Liste von Batch-Informationen
        """
        return [self.get_batch(batch_id) for batch_id in self.batches]
        
    def clear_completed(self):
        """Entfernt alle abgeschlossenen Batches."""
        completed_batches = [
            batch_id for batch_id, batch in self.batches.items()
            if batch.status in ("completed", "failed")
        ]
        
        for batch_id in completed_batches:
            self.remove_batch(batch_id)
            
        logger.info(f"{len(completed_batches)} abgeschlossene Batches entfernt")
