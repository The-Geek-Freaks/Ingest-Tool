"""
Validierungsregeln für Metadaten.
"""
from typing import Dict, List, Callable, Any
from .types import FileType, MetadataDict

class ValidationRules:
    """Verwaltet Validierungsregeln für Metadaten."""
    
    def __init__(self):
        self._rules: Dict[str, Dict] = {
            FileType.IMAGE: {
                'required': ['dimensions', 'color_space', 'bit_depth'],
                'optional': ['camera_make', 'camera_model', 'exposure', 'iso'],
                'validate': self._validate_image_metadata
            },
            FileType.VIDEO: {
                'required': ['duration', 'frame_rate', 'resolution', 'codec'],
                'optional': ['audio_codec', 'audio_channels', 'bitrate'],
                'validate': self._validate_video_metadata
            },
            FileType.AUDIO: {
                'required': ['duration', 'sample_rate', 'channels'],
                'optional': ['bitrate', 'codec', 'composer'],
                'validate': self._validate_audio_metadata
            }
        }
        
    def add_rule(self, file_type: str, rule: Dict):
        """Fügt eine neue Validierungsregel hinzu."""
        if not all(k in rule for k in ['required', 'optional', 'validate']):
            raise ValueError("Regel muss 'required', 'optional' und 'validate' enthalten")
            
        self._rules[file_type] = rule
        
    def validate(self, metadata: MetadataDict, file_type: str) -> bool:
        """Validiert Metadaten gegen definierte Regeln."""
        if file_type not in self._rules:
            return True
            
        rule = self._rules[file_type]
        
        # Prüfe required fields
        if not all(field in metadata for field in rule['required']):
            return False
            
        # Führe benutzerdefinierte Validierung aus
        return rule['validate'](metadata)
        
    def _validate_image_metadata(self, metadata: MetadataDict) -> bool:
        """Validiert Bildmetadaten."""
        if not isinstance(metadata['dimensions'], tuple) or len(metadata['dimensions']) != 2:
            return False
            
        if not all(isinstance(d, int) and d > 0 for d in metadata['dimensions']):
            return False
            
        if not isinstance(metadata['bit_depth'], int) or metadata['bit_depth'] <= 0:
            return False
            
        return True
        
    def _validate_video_metadata(self, metadata: MetadataDict) -> bool:
        """Validiert Videometadaten."""
        if not isinstance(metadata['duration'], (int, float)) or metadata['duration'] <= 0:
            return False
            
        if not isinstance(metadata['frame_rate'], (int, float)) or metadata['frame_rate'] <= 0:
            return False
            
        if not isinstance(metadata['resolution'], tuple) or len(metadata['resolution']) != 2:
            return False
            
        if not all(isinstance(d, int) and d > 0 for d in metadata['resolution']):
            return False
            
        return True
        
    def _validate_audio_metadata(self, metadata: MetadataDict) -> bool:
        """Validiert Audiometadaten."""
        if not isinstance(metadata['duration'], (int, float)) or metadata['duration'] <= 0:
            return False
            
        if not isinstance(metadata['sample_rate'], int) or metadata['sample_rate'] <= 0:
            return False
            
        if not isinstance(metadata['channels'], int) or metadata['channels'] <= 0:
            return False
            
        return True
