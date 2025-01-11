"""
Typdefinitionen für Metadaten.
"""
from typing import Dict, List, TypedDict, Union, Optional

class FileType:
    """Unterstützte Dateitypen."""
    IMAGE = 'image'
    VIDEO = 'video'
    AUDIO = 'audio'
    DOCUMENT = 'document'
    
    EXTENSIONS = {
        IMAGE: ['.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif'],
        VIDEO: ['.mp4', '.mov', '.avi', '.mkv', '.mxf', '.m4v'],
        AUDIO: ['.mp3', '.wav', '.aac', '.flac', '.ogg'],
        DOCUMENT: ['.pdf', '.doc', '.docx', '.txt']
    }
    
    @classmethod
    def get_type(cls, extension: str) -> Optional[str]:
        """Ermittelt den Dateityp anhand der Erweiterung."""
        ext = extension.lower()
        if not ext.startswith('.'):
            ext = '.' + ext
            
        for file_type, extensions in cls.EXTENSIONS.items():
            if ext in extensions:
                return file_type
        return None

class MetadataDict(TypedDict, total=False):
    """Typdefinition für Metadaten-Dictionary."""
    # Basis-Metadaten
    size: int
    modified: float
    created: float
    quick_hash: str
    permissions: int
    
    # Erweiterte Attribute
    xattr: Dict[str, bytes]
    
    # Bild-Metadaten
    dimensions: tuple[int, int]
    color_space: str
    bit_depth: int
    camera_make: Optional[str]
    camera_model: Optional[str]
    exposure: Optional[float]
    iso: Optional[int]
    
    # Video-Metadaten
    duration: float
    frame_rate: float
    resolution: tuple[int, int]
    codec: str
    audio_codec: Optional[str]
    audio_channels: Optional[int]
    bitrate: Optional[int]
    
    # Audio-Metadaten
    sample_rate: int
    channels: int
    composer: Optional[str]
