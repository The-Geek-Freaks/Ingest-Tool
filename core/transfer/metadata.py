"""
Metadaten-Verwaltung für Dateiübertragungen.
"""

import os
import logging
import threading
import xxhash
from typing import Dict, Optional
from datetime import datetime

class MetadataManager:
    """Verwaltet Metadaten und Integritätsprüfungen für Dateien."""
    
    def __init__(self):
        self._hash_cache = {}
        self._metadata_cache = {}
        self._cache_lock = threading.Lock()
        self._chunk_size = 8192  # 8KB für Hash-Berechnung
        
    def get_file_metadata(self, filepath: str) -> Optional[Dict]:
        """Liest alle Metadaten einer Datei."""
        try:
            # Prüfe Cache
            with self._cache_lock:
                cached = self._metadata_cache.get(filepath)
                if cached:
                    mtime = os.path.getmtime(filepath)
                    if mtime == cached['mtime']:
                        return cached['metadata']
                        
            metadata = {
                'size': os.path.getsize(filepath),
                'mtime': os.path.getmtime(filepath),
                'ctime': os.path.getctime(filepath),
                'permissions': oct(os.stat(filepath).st_mode)[-3:],
                'quick_hash': self._calculate_quick_hash(filepath),
                'attributes': self._get_file_attributes(filepath)
            }
            
            # Hole EXIF-Daten für Bilder
            if self._is_image_file(filepath):
                metadata['exif'] = self._get_exif_data(filepath)
                
            # Hole erweiterte Attribute
            try:
                import xattr
                metadata['xattr'] = dict(xattr.xattr(filepath))
            except ImportError:
                pass
                
            # Aktualisiere Cache
            with self._cache_lock:
                self._metadata_cache[filepath] = {
                    'mtime': metadata['mtime'],
                    'metadata': metadata
                }
                
            return metadata
            
        except Exception as e:
            logging.error(f"Fehler beim Lesen der Metadaten von {filepath}: {e}")
            return None
            
    def restore_metadata(self, filepath: str, metadata: Dict) -> bool:
        """Stellt Metadaten einer Datei wieder her."""
        try:
            # Setze Zeitstempel
            os.utime(filepath, (
                metadata['ctime'],
                metadata['mtime']
            ))
            
            # Setze Berechtigungen
            os.chmod(filepath, int(f"0o{metadata['permissions']}", 8))
            
            # Stelle erweiterte Attribute wieder her
            if 'xattr' in metadata:
                try:
                    import xattr
                    x = xattr.xattr(filepath)
                    for key, value in metadata['xattr'].items():
                        x[key] = value
                except ImportError:
                    pass
                    
            # Stelle EXIF-Daten wieder her
            if 'exif' in metadata and self._is_image_file(filepath):
                self._restore_exif_data(filepath, metadata['exif'])
                
            return True
            
        except Exception as e:
            logging.error(
                f"Fehler beim Wiederherstellen der Metadaten von {filepath}: {e}"
            )
            return False
            
    def get_full_hash(self, filepath: str) -> Optional[str]:
        """Berechnet den vollständigen Hash einer Datei."""
        try:
            # Prüfe Cache
            with self._cache_lock:
                cached = self._hash_cache.get(filepath)
                if cached:
                    mtime = os.path.getmtime(filepath)
                    if mtime == cached['mtime']:
                        return cached['hash']
                        
            # Berechne Hash
            hasher = xxhash.xxh64()
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(self._chunk_size)
                    if not chunk:
                        break
                    hasher.update(chunk)
                    
            file_hash = hasher.hexdigest()
            
            # Aktualisiere Cache
            with self._cache_lock:
                self._hash_cache[filepath] = {
                    'mtime': os.path.getmtime(filepath),
                    'hash': file_hash
                }
                
            return file_hash
            
        except Exception as e:
            logging.error(f"Fehler bei Hash-Berechnung von {filepath}: {e}")
            return None
            
    def _calculate_quick_hash(self, filepath: str) -> Optional[str]:
        """Berechnet einen schnellen Hash basierend auf Stichproben."""
        try:
            hasher = xxhash.xxh64()
            file_size = os.path.getsize(filepath)
            
            with open(filepath, 'rb') as f:
                # Lese Anfang
                start_chunk = f.read(min(self._chunk_size, file_size))
                hasher.update(start_chunk)
                
                if file_size > self._chunk_size:
                    # Lese Mitte
                    f.seek(file_size // 2)
                    mid_chunk = f.read(min(self._chunk_size, file_size - f.tell()))
                    hasher.update(mid_chunk)
                    
                    # Lese Ende
                    f.seek(max(0, file_size - self._chunk_size))
                    end_chunk = f.read()
                    hasher.update(end_chunk)
                    
            return hasher.hexdigest()
            
        except Exception as e:
            logging.error(f"Fehler bei Quick-Hash von {filepath}: {e}")
            return None
            
    def _get_file_attributes(self, filepath: str) -> Dict:
        """Liest erweiterte Dateiattribute."""
        attributes = {}
        
        try:
            # Windows-spezifische Attribute
            if os.name == 'nt':
                import win32api
                import win32con
                attrs = win32api.GetFileAttributes(filepath)
                attributes['hidden'] = bool(attrs & win32con.FILE_ATTRIBUTE_HIDDEN)
                attributes['system'] = bool(attrs & win32con.FILE_ATTRIBUTE_SYSTEM)
                attributes['archive'] = bool(attrs & win32con.FILE_ATTRIBUTE_ARCHIVE)
                attributes['compressed'] = bool(
                    attrs & win32con.FILE_ATTRIBUTE_COMPRESSED
                )
                
            # UNIX-spezifische Attribute
            else:
                import stat
                st = os.stat(filepath)
                mode = st.st_mode
                attributes['executable'] = bool(mode & stat.S_IXUSR)
                attributes['symlink'] = os.path.islink(filepath)
                
        except Exception as e:
            logging.warning(f"Fehler beim Lesen der Attribute von {filepath}: {e}")
            
        return attributes
        
    def _is_image_file(self, filepath: str) -> bool:
        """Prüft ob eine Datei ein Bild ist."""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}
        return os.path.splitext(filepath)[1].lower() in image_extensions
        
    def _get_exif_data(self, filepath: str) -> Dict:
        """Liest EXIF-Daten aus einem Bild."""
        try:
            from PIL import Image, ExifTags
            
            with Image.open(filepath) as img:
                exif = img.getexif()
                if not exif:
                    return {}
                    
                # Konvertiere numerische Tags in lesbare Namen
                exif_data = {}
                for tag_id in exif:
                    tag = ExifTags.TAGS.get(tag_id, tag_id)
                    value = exif.get(tag_id)
                    
                    # Konvertiere Bytes in String
                    if isinstance(value, bytes):
                        try:
                            value = value.decode()
                        except:
                            value = str(value)
                            
                    exif_data[tag] = value
                    
                return exif_data
                
        except Exception as e:
            logging.warning(f"Fehler beim Lesen der EXIF-Daten von {filepath}: {e}")
            return {}
            
    def _restore_exif_data(self, filepath: str, exif_data: Dict) -> bool:
        """Stellt EXIF-Daten in einem Bild wieder her."""
        try:
            from PIL import Image, ExifTags
            
            # Öffne Bild
            with Image.open(filepath) as img:
                # Konvertiere Namen zurück in numerische Tags
                exif = img.getexif()
                for tag_name, value in exif_data.items():
                    # Finde Tag-ID
                    tag_id = None
                    for id, name in ExifTags.TAGS.items():
                        if name == tag_name:
                            tag_id = id
                            break
                            
                    if tag_id:
                        # Konvertiere String zurück in Bytes wenn nötig
                        if isinstance(value, str) and value.startswith("b'"):
                            try:
                                value = eval(value)
                            except:
                                pass
                                
                        exif[tag_id] = value
                        
                # Speichere Bild mit neuen EXIF-Daten
                img.save(filepath, exif=exif)
                
            return True
            
        except Exception as e:
            logging.error(
                f"Fehler beim Wiederherstellen der EXIF-Daten von {filepath}: {e}"
            )
            return False
            
    def verify_file_integrity(self, source: str, destination: str) -> bool:
        """Überprüft die Integrität einer kopierten Datei."""
        try:
            # Prüfe Existenz
            if not os.path.exists(source) or not os.path.exists(destination):
                return False
                
            # Prüfe Größe
            if os.path.getsize(source) != os.path.getsize(destination):
                return False
                
            # Prüfe Quick-Hash
            if (self._calculate_quick_hash(source) != 
                self._calculate_quick_hash(destination)):
                # Bei Unterschied prüfe Full-Hash
                if (self.get_full_hash(source) != 
                    self.get_full_hash(destination)):
                    return False
                    
            # Prüfe Metadaten
            source_meta = self.get_file_metadata(source)
            dest_meta = self.get_file_metadata(destination)
            
            if not source_meta or not dest_meta:
                return False
                
            # Vergleiche relevante Metadaten
            for key in ['size', 'quick_hash']:
                if source_meta[key] != dest_meta[key]:
                    return False
                    
            return True
            
        except Exception as e:
            logging.error(f"Fehler bei Integritätsprüfung: {e}")
            return False
            
    def cleanup_cache(self):
        """Bereinigt den Metadaten- und Hash-Cache."""
        with self._cache_lock:
            self._metadata_cache.clear()
            self._hash_cache.clear()
