"""Verwaltet Datei-Chunks für optimierte Transfers."""

import logging
from typing import Dict

logger = logging.getLogger(__name__)

class ChunkManager:
    """Manager für optimierte Dateitransfers mit Puffer-Wiederverwendung."""
    
    def __init__(self, buffer_size: int = 8388608):  # 8MB Default
        """Initialisiert den ChunkManager.
        
        Args:
            buffer_size: Größe des Puffers in Bytes (Standard: 8MB)
        """
        self.buffer_size = buffer_size
        self._buffers: Dict[str, bytearray] = {}
        logger.info(f"ChunkManager initialisiert mit {buffer_size/1024/1024:.1f}MB Puffer")
        
    def get_buffer(self, transfer_id: str) -> bytearray:
        """Holt einen Puffer für einen Transfer.
        
        Args:
            transfer_id: ID des Transfers
            
        Returns:
            bytearray: Puffer für den Transfer
        """
        if transfer_id not in self._buffers:
            self._buffers[transfer_id] = bytearray(self.buffer_size)
            logger.debug(f"Neuer Puffer erstellt für Transfer {transfer_id}")
        return self._buffers[transfer_id]
        
    def release_buffer(self, transfer_id: str):
        """Gibt einen Puffer frei.
        
        Args:
            transfer_id: ID des Transfers
        """
        if transfer_id in self._buffers:
            del self._buffers[transfer_id]
            logger.debug(f"Puffer freigegeben für Transfer {transfer_id}")
            
    def get_chunk_size(self, file_size: int) -> int:
        """Ermittelt optimale Chunk-Größe basierend auf Dateigröße.
        
        Args:
            file_size: Größe der Datei in Bytes
            
        Returns:
            int: Optimale Chunk-Größe in Bytes
        """
        if file_size < 1024 * 1024:  # < 1MB
            return min(file_size, 65536)  # 64KB für kleine Dateien
        elif file_size < 100 * 1024 * 1024:  # < 100MB
            return min(file_size, self.buffer_size)  # Standard Puffer
        else:
            return min(file_size, self.buffer_size * 2)  # Doppelter Puffer für große Dateien
