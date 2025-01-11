"""
Metadata Handler (Legacy-Import).
Bitte das neue Modul core.metadata verwenden.
"""

from .metadata import (
    MetadataHandler,
    MetadataCache,
    ValidationRules,
    ImageHandler,
    VideoHandler,
    AudioHandler,
    DocumentHandler,
    FileType,
    MetadataDict
)

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
