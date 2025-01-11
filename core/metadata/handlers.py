"""
Handler für verschiedene Dateitypen.
"""
import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional

from .types import MetadataDict

class BaseHandler(ABC):
    """Basis-Klasse für Metadaten-Handler."""
    
    @abstractmethod
    def extract(self, filepath: str) -> Optional[MetadataDict]:
        """Extrahiert Metadaten aus einer Datei."""
        pass

class ImageHandler(BaseHandler):
    """Handler für Bildmetadaten."""
    
    def extract(self, filepath: str) -> Optional[MetadataDict]:
        try:
            from PIL import Image
            with Image.open(filepath) as img:
                metadata: MetadataDict = {
                    'dimensions': img.size,
                    'color_space': img.mode,
                    'bit_depth': img.bits
                }
                
                # EXIF-Daten
                if hasattr(img, '_getexif') and img._getexif():
                    exif = img._getexif()
                    if exif:
                        if 271 in exif:  # Make
                            metadata['camera_make'] = str(exif[271])
                        if 272 in exif:  # Model
                            metadata['camera_model'] = str(exif[272])
                        if 33434 in exif:  # Exposure
                            metadata['exposure'] = float(exif[33434])
                        if 34855 in exif:  # ISO
                            metadata['iso'] = int(exif[34855])
                            
                return metadata
                
        except ImportError:
            logging.warning("PIL nicht verfügbar - Bildmetadaten deaktiviert")
        except Exception as e:
            logging.error(f"Fehler bei Bildmetadaten: {e}")
            
        return None

class VideoHandler(BaseHandler):
    """Handler für Videometadaten."""
    
    def extract(self, filepath: str) -> Optional[MetadataDict]:
        try:
            import ffmpeg
            probe = ffmpeg.probe(filepath)
            
            # Video-Stream finden
            video_stream = next(
                (stream for stream in probe['streams']
                 if stream['codec_type'] == 'video'),
                None
            )
            
            if not video_stream:
                return None
                
            # Basis-Videometadaten
            metadata: MetadataDict = {
                'duration': float(probe['format'].get('duration', 0)),
                'frame_rate': eval(video_stream.get('r_frame_rate', '0/1')),
                'resolution': (
                    int(video_stream.get('width', 0)),
                    int(video_stream.get('height', 0))
                ),
                'codec': video_stream.get('codec_name', 'unknown')
            }
            
            # Audio-Stream suchen
            audio_stream = next(
                (stream for stream in probe['streams']
                 if stream['codec_type'] == 'audio'),
                None
            )
            
            if audio_stream:
                metadata.update({
                    'audio_codec': audio_stream.get('codec_name'),
                    'audio_channels': int(audio_stream.get('channels', 0)),
                    'bitrate': int(probe['format'].get('bit_rate', 0))
                })
                
            return metadata
            
        except ImportError:
            logging.warning("ffmpeg-python nicht verfügbar - Videometadaten deaktiviert")
        except Exception as e:
            logging.error(f"Fehler bei Videometadaten: {e}")
            
        return None

class AudioHandler(BaseHandler):
    """Handler für Audiometadaten."""
    
    def extract(self, filepath: str) -> Optional[MetadataDict]:
        try:
            import ffmpeg
            probe = ffmpeg.probe(filepath)
            
            # Audio-Stream finden
            audio_stream = next(
                (stream for stream in probe['streams']
                 if stream['codec_type'] == 'audio'),
                None
            )
            
            if not audio_stream:
                return None
                
            metadata: MetadataDict = {
                'duration': float(probe['format'].get('duration', 0)),
                'sample_rate': int(audio_stream.get('sample_rate', 0)),
                'channels': int(audio_stream.get('channels', 0)),
                'codec': audio_stream.get('codec_name', 'unknown'),
                'bitrate': int(probe['format'].get('bit_rate', 0))
            }
            
            # Zusätzliche Tags
            if 'tags' in probe['format']:
                tags = probe['format']['tags']
                if 'composer' in tags:
                    metadata['composer'] = tags['composer']
                    
            return metadata
            
        except ImportError:
            logging.warning("ffmpeg-python nicht verfügbar - Audiometadaten deaktiviert")
        except Exception as e:
            logging.error(f"Fehler bei Audiometadaten: {e}")
            
        return None

class DocumentHandler(BaseHandler):
    """Handler für Dokumentmetadaten."""
    
    def extract(self, filepath: str) -> Optional[MetadataDict]:
        # TODO: Implementiere Dokumentmetadaten
        # z.B. mit python-docx für Word-Dokumente
        # oder PyPDF2 für PDF-Dateien
        return None
