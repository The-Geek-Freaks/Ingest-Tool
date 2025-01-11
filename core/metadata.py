"""
Behandelt die Übertragung und Verwaltung von Datei-Metadaten.
"""
import os
import hashlib
import logging
from datetime import datetime
import time
from PIL.ExifTags import TAGS as ExifTags

class MetadataHandler:
    """Behandelt die Übertragung und Verwaltung von Datei-Metadaten."""
    
    def __init__(self):
        self.metadata_cache = {}
        self.cache_lifetime = 300  # 5 Minuten Cache-Gültigkeit
        
    def _is_cache_valid(self, filepath):
        """Prüft ob der Cache für eine Datei noch gültig ist."""
        if filepath not in self.metadata_cache:
            return False
        
        cache_time = self.metadata_cache[filepath]['timestamp']
        return (time.time() - cache_time) < self.cache_lifetime
        
    @staticmethod
    def get_quick_hash(filepath, sample_size=65536):
        """Berechnet einen schnellen Hash der Datei."""
        try:
            file_size = os.path.getsize(filepath)
            if file_size == 0:
                return "empty_file"
                
            # Minimale Blockgröße für sehr kleine Dateien
            if file_size < sample_size:
                sample_size = file_size
                
            hasher = hashlib.md5()
            
            with open(filepath, 'rb') as f:
                # Hash des ersten Blocks
                start_block = f.read(sample_size)
                hasher.update(start_block)
                
                if file_size > sample_size * 2:
                    # Springe zur Mitte
                    f.seek(file_size // 2)
                    mid_block = f.read(sample_size)
                    hasher.update(mid_block)
                    
                    # Springe zum Ende
                    f.seek(-sample_size, 2)
                    end_block = f.read(sample_size)
                    hasher.update(end_block)
                    
            # Füge Dateigröße zum Hash hinzu
            hasher.update(str(file_size).encode())
            
            return hasher.hexdigest()
            
        except Exception as e:
            logging.error(f"Fehler beim Berechnen des Quick-Hash: {str(e)}")
            return None
    
    @staticmethod
    def get_full_hash(filepath):
        """Berechnet den vollständigen Hash der Datei."""
        try:
            hasher = hashlib.md5()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logging.error(f"Fehler beim Berechnen des Full-Hash: {str(e)}")
            return None
    
    def get_file_metadata(self, filepath):
        """Ermittelt die Metadaten einer Datei."""
        try:
            # Prüfe Cache
            if self._is_cache_valid(filepath):
                return self.metadata_cache[filepath]['data']
            
            metadata = {
                'size': os.path.getsize(filepath),
                'modified': os.path.getmtime(filepath),
                'created': os.path.getctime(filepath),
                'quick_hash': self.get_quick_hash(filepath)
            }
            
            # Dateityp-spezifische Metadaten
            ext = os.path.splitext(filepath)[1].lower()
            
            # Bild-Metadaten
            if ext in ['.jpg', '.jpeg', '.tiff', '.png', '.gif', '.bmp']:
                try:
                    from PIL import Image
                    with Image.open(filepath) as img:
                        metadata['image'] = {
                            'format': img.format,
                            'mode': img.mode,
                            'size': img.size
                        }
                        # EXIF-Daten
                        exif = img.getexif()
                        if exif:
                            metadata['exif'] = {
                                ExifTags.TAGS.get(k, k): str(v)
                                for k, v in exif.items()
                            }
                except ImportError:
                    logging.warning("PIL nicht verfügbar - Bildmetadaten werden nicht verarbeitet")
                except Exception as e:
                    logging.error(f"Fehler beim Lesen der Bildmetadaten: {e}")
            
            # Video-Metadaten
            elif ext in ['.mp4', '.mov', '.avi', '.mkv', '.flv']:
                try:
                    import cv2
                    video = cv2.VideoCapture(filepath)
                    if video.isOpened():
                        metadata['video'] = {
                            'fps': video.get(cv2.CAP_PROP_FPS),
                            'frame_count': video.get(cv2.CAP_PROP_FRAME_COUNT),
                            'width': video.get(cv2.CAP_PROP_FRAME_WIDTH),
                            'height': video.get(cv2.CAP_PROP_FRAME_HEIGHT)
                        }
                        video.release()
                except ImportError:
                    logging.warning("OpenCV nicht verfügbar - Videometadaten werden nicht verarbeitet")
                except Exception as e:
                    logging.error(f"Fehler beim Lesen der Videometadaten: {e}")
            
            # Audio-Metadaten
            elif ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg']:
                try:
                    import mutagen
                    audio = mutagen.File(filepath)
                    if audio:
                        metadata['audio'] = {
                            'length': audio.info.length,
                            'bitrate': getattr(audio.info, 'bitrate', None),
                            'channels': getattr(audio.info, 'channels', None),
                            'sample_rate': getattr(audio.info, 'sample_rate', None)
                        }
                except ImportError:
                    logging.warning("mutagen nicht verfügbar - Audiometadaten werden nicht verarbeitet")
                except Exception as e:
                    logging.error(f"Fehler beim Lesen der Audiometadaten: {e}")
            
            # Speichere im Cache
            self.metadata_cache[filepath] = {
                'data': metadata,
                'timestamp': time.time()
            }
            
            return metadata
            
        except Exception as e:
            logging.error(f"Fehler beim Ermitteln der Metadaten für {filepath}: {e}")
            return None
    
    @staticmethod
    def find_duplicate_in_directory(source_file, target_dir):
        """Sucht nach einer identischen Datei im Zielverzeichnis."""
        try:
            source_metadata = MetadataHandler.get_file_metadata(source_file)
            if not source_metadata:
                return None
                
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
                if not target_metadata:
                    continue
                    
                # Wenn Quick-Hash übereinstimmt, mache vollständigen Vergleich
                if target_metadata['quick_hash'] == source_metadata['quick_hash']:
                    # Berechne vollständigen Hash nur wenn Quick-Hash übereinstimmt
                    source_full_hash = MetadataHandler.get_full_hash(source_file)
                    target_full_hash = MetadataHandler.get_full_hash(target_path)
                    
                    if source_full_hash and target_full_hash and source_full_hash == target_full_hash:
                        return target_path
                        
            return None
            
        except Exception as e:
            logging.error(f"Fehler bei der Duplikatsuche: {str(e)}")
            return None
