"""
Verwaltung der Transfer-Warteschlange.
"""

import queue
from typing import Dict, Optional
from datetime import datetime
from .priority import TransferPriority, PriorityQueueItem

class QueueManager:
    """Verwaltet die Warteschlange für Dateiübertragungen."""
    
    def __init__(self):
        self._transfer_queue = queue.PriorityQueue()
        self._active_transfers = {}
        self._completed_transfers = {}
        
    def enqueue(
        self, 
        transfer_data: Dict,
        priority: TransferPriority = TransferPriority.NORMAL
    ):
        """Fügt einen Transfer zur Warteschlange hinzu."""
        queue_item = PriorityQueueItem(
            priority=priority,
            timestamp=datetime.now(),
            data=transfer_data
        )
        self._transfer_queue.put(queue_item)
        
    def get_next(self, timeout: Optional[float] = None) -> Optional[Dict]:
        """Holt den nächsten Transfer aus der Warteschlange."""
        try:
            queue_item = self._transfer_queue.get(timeout=timeout)
            transfer = queue_item.data
            self._active_transfers[transfer['id']] = transfer
            return transfer
        except queue.Empty:
            return None
            
    def complete_transfer(self, transfer_id: str):
        """Markiert einen Transfer als abgeschlossen."""
        if transfer_id in self._active_transfers:
            transfer = self._active_transfers.pop(transfer_id)
            self._completed_transfers[transfer_id] = transfer
            
    def get_transfer(self, transfer_id: str) -> Optional[Dict]:
        """Gibt den Status eines Transfers zurück."""
        return (
            self._active_transfers.get(transfer_id) or 
            self._completed_transfers.get(transfer_id)
        )
        
    def cancel_transfer(self, transfer_id: str) -> bool:
        """Bricht einen Transfer ab."""
        if transfer_id in self._active_transfers:
            transfer = self._active_transfers[transfer_id]
            transfer['status'] = 'cancelled'
            transfer['end_time'] = datetime.now()
            self.complete_transfer(transfer_id)
            return True
        return False
        
    def pause_transfer(self, transfer_id: str) -> bool:
        """Pausiert einen aktiven Transfer."""
        if transfer_id in self._active_transfers:
            transfer = self._active_transfers[transfer_id]
            if transfer['status'] == 'active':
                transfer['status'] = 'paused'
                transfer['pause_time'] = datetime.now()
                return True
        return False
        
    def resume_transfer(self, transfer_id: str) -> bool:
        """Setzt einen pausierten Transfer fort."""
        if transfer_id in self._active_transfers:
            transfer = self._active_transfers[transfer_id]
            if transfer['status'] == 'paused':
                transfer['status'] = 'active'
                pause_duration = (
                    datetime.now() - transfer['pause_time']
                ).total_seconds()
                transfer['start_time'] = datetime.now() - pause_duration
                return True
        return False
        
    def get_queue_status(self) -> Dict:
        """Gibt den Status der Warteschlange zurück."""
        return {
            'queued': self._transfer_queue.qsize(),
            'active': len(self._active_transfers),
            'completed': len(self._completed_transfers)
        }
