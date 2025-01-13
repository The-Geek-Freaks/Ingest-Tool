"""Verwaltet die Verifikation von Dateitransfers."""

import hashlib
import logging
import os
from typing import Dict

logger = logging.getLogger(__name__)

class TransferVerification:
    """Manager für die Verifikation von Dateitransfers."""
    
    def __init__(self):
        """Initialisiert den TransferVerification Manager."""
        self.hash_cache: Dict[str, str] = {}
        logger.info("TransferVerification Manager initialisiert")
        
    def calculate_hash(self, file_path: str, chunk_size: int = 8192) -> str:
        """Berechnet den SHA-256 Hash einer Datei.
        
        Args:
            file_path: Pfad zur Datei
            chunk_size: Größe der zu lesenden Chunks
            
        Returns:
            str: Hash der Datei
        """
        if file_path in self.hash_cache:
            return self.hash_cache[file_path]
            
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    hasher.update(chunk)
            
            file_hash = hasher.hexdigest()
            self.hash_cache[file_path] = file_hash
            logger.debug(f"Hash berechnet für {file_path}: {file_hash[:8]}...")
            return file_hash
            
        except Exception as e:
            logger.error(f"Fehler bei Hash-Berechnung für {file_path}: {e}")
            return ""
        
    def verify_transfer(self, source: str, destination: str) -> bool:
        """Verifiziert einen Transfer durch Vergleich der Hashes.
        
        Args:
            source: Quellpfad
            destination: Zielpfad
            
        Returns:
            bool: True wenn Transfer erfolgreich verifiziert
        """
        source_hash = self.calculate_hash(source)
        dest_hash = self.calculate_hash(destination)
        
        if not source_hash or not dest_hash:
            return False
            
        verified = source_hash == dest_hash
        if verified:
            logger.info(f"Transfer verifiziert: {source} -> {destination}")
        else:
            logger.error(f"Verifikation fehlgeschlagen: {source} -> {destination}")
        return verified
        
    def resolve_conflict(self, target_path: str) -> str:
        """Löst Namenskonflikte durch Anhängen einer Nummer.
        
        Args:
            target_path: Gewünschter Zielpfad
            
        Returns:
            str: Konfliktfreier Zielpfad
        """
        if not os.path.exists(target_path):
            return target_path
            
        base, ext = os.path.splitext(target_path)
        counter = 1
        
        while True:
            new_path = f"{base}_{counter}{ext}"
            if not os.path.exists(new_path):
                logger.debug(f"Konflikt gelöst: {target_path} -> {new_path}")
                return new_path
            counter += 1
