"""
Metadaten-Verarbeitung und -Verwaltung.
"""

from .handler import MetadataHandler
from .cache import MetadataCache
from .rules import ValidationRules
from .handlers import (
    ImageHandler,
    VideoHandler,
    AudioHandler,
    DocumentHandler
)
from .types import FileType, MetadataDict

__all__ = [
    'MetadataHandler',
    'MetadataCache',
    'ValidationRules',
    'ImageHandler',
    'VideoHandler',
    'AudioHandler',
    'DocumentHandler',
    'FileType',
    'MetadataDict'
]
