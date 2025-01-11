#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import hashlib
import logging
from typing import Dict, Optional, Any
from datetime import datetime

try:
    import xxhash
    XXHASH_AVAILABLE = True
except ImportError:
    XXHASH_AVAILABLE = False
    
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class MetadataHandler:
    """Behandelt die Übertragung und Verwaltung von Datei-Metadaten."""
    
    @staticmethod
    def get_quick_hash(filepath: str, sample_size: int = 65536) -> str:
        """Berechnet einen schnellen Hash der Datei.
        
        Verwendet eine Kombination aus:
        - Dateigröße
        - Hash des ersten Blocks
        - Hash des letzten Blocks
        - Hash eines Blocks aus der Mitte
        """
        try:
            import xxhash
            xxh = xxhash.xxh64()
            is_xxhash = True
        except ImportError:
            xxh = hashlib.md5()
            is_xxhash = False
            
        file_size = os.path.getsize(filepath)
        if file_size == 0:
            return "empty_file"
            
        if file_size < sample_size:
            sample_size = file_size
            
        with open(filepath, 'rb') as f:
            # Hash des ersten Blocks
            start_block = f.read(sample_size)
            xxh.update(start_block)
            
            if file_size > sample_size * 2:
                # Springe zur Mitte
                f.seek(file_size // 2)
                mid_block = f.read(sample_size)
                xxh.update(mid_block)
                
                # Springe zum Ende
                f.seek(-sample_size, 2)
                end_block = f.read(sample_size)
                xxh.update(end_block)
                
        # Füge Dateigröße zum Hash hinzu
        xxh.update(str(file_size).encode())
        
        return xxh.hexdigest() if is_xxhash else xxh.hexdigest()
    
    @staticmethod
    def get_full_hash(filepath: str) -> str:
        """Berechnet den vollständigen Hash der Datei."""
        try:
            import xxhash
            xxh = xxhash.xxh64()
        except ImportError:
            xxh = hashlib.md5()
            
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                xxh.update(chunk)
        return xxh.hexdigest()
    
    @staticmethod
    def get_file_metadata(filepath: str) -> Dict:
        """Ermittelt die Metadaten einer Datei."""
        metadata = {
            'size': os.path.getsize(filepath),
            'modified': os.path.getmtime(filepath),
            'created': os.path.getctime(filepath),
            'quick_hash': MetadataHandler.get_quick_hash(filepath)
        }
        
        # Füge EXIF-Daten für Bilder hinzu
        if (PIL_AVAILABLE and 
            any(filepath.lower().endswith(ext) 
                for ext in ['.jpg', '.jpeg', '.tiff', '.png'])):
            try:
                with Image.open(filepath) as img:
                    exif = img.getexif()
                    if exif:
                        metadata['exif'] = {str(k): str(v) for k, v in exif.items()}
            except Exception as e:
                logging.warning(f"Fehler beim Lesen der EXIF-Daten von {filepath}: {e}")
                
        # Füge erweiterte Attribute hinzu
        try:
            import xattr
            attrs = xattr.listxattr(filepath)
            if attrs:
                metadata['xattr'] = {
                    attr: xattr.getxattr(filepath, attr).decode('utf-8', 'ignore') 
                    for attr in attrs
                }
        except ImportError:
            pass
        except Exception as e:
            logging.warning(f"Fehler beim Lesen der erweiterten Attribute von {filepath}: {e}")
            
        return metadata
    
    @staticmethod
    def find_duplicate_in_directory(source_file: str, target_dir: str) -> Optional[str]:
        """Sucht nach einer identischen Datei im Zielverzeichnis."""
        source_metadata = MetadataHandler.get_file_metadata(source_file)
        source_size = source_metadata['size']
        
        # Suche zuerst nach Dateien mit gleicher Größe
        potential_duplicates = []
        for root, _, files in os.walk(target_dir):
            for filename in files:
                target_path = os.path.join(root, filename)
                if os.path.getsize(target_path) == source_size:
                    potential_duplicates.append(target_path)
        
        # Vergleiche Quick-Hash der potenziellen Duplikate
        for target_path in potential_duplicates:
            target_metadata = MetadataHandler.get_file_metadata(target_path)
            
            # Wenn Quick-Hash übereinstimmt, mache vollständigen Vergleich
            if target_metadata['quick_hash'] == source_metadata['quick_hash']:
                # Berechne vollständigen Hash nur wenn Quick-Hash übereinstimmt
                source_full_hash = MetadataHandler.get_full_hash(source_file)
                target_full_hash = MetadataHandler.get_full_hash(target_path)
                
                if source_full_hash == target_full_hash:
                    # Vergleiche zusätzliche Metadaten
                    if ('exif' in source_metadata and 'exif' in target_metadata and
                        source_metadata['exif'] == target_metadata['exif']):
                        return target_path
                    elif ('xattr' in source_metadata and 'xattr' in target_metadata and
                        source_metadata['xattr'] == target_metadata['xattr']):
                        return target_path
                    elif 'exif' not in source_metadata and 'xattr' not in source_metadata:
                        return target_path
                    
        return None
    
    def clear_cache(self):
        """Leert den Hash-Cache."""
        pass
