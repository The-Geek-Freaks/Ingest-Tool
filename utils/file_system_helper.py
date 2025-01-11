#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hilfsfunktionen für Dateisystem-Operationen.
"""

import os
import logging
import ctypes
import platform
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class FileSystemHelper:
    """Hilfsklasse für Dateisystem-Operationen."""
    
    @staticmethod
    def has_matching_files(drive_letter: str, file_types: List[str]) -> bool:
        """Prüft ob auf dem Laufwerk Dateien mit den angegebenen Typen existieren.
        
        Args:
            drive_letter: Laufwerksbuchstabe zu prüfen
            file_types: Liste der zu suchenden Dateitypen
            
        Returns:
            True wenn passende Dateien gefunden wurden, sonst False
        """
        try:
            drive_path = f"{drive_letter}:\\"
            
            # Durchsuche das Laufwerk rekursiv nach passenden Dateien
            for root, _, files in os.walk(drive_path):
                for file in files:
                    file_ext = os.path.splitext(file)[1].lower()
                    if file_ext in file_types:
                        return True
                        
            return False
            
        except Exception as e:
            logger.error(f"Fehler beim Prüfen von Laufwerk {drive_letter}: {e}")
            return False
            
    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """Gibt die Dateiendung zurück.
        
        Args:
            file_path: Pfad zur Datei
            
        Returns:
            Dateiendung in Kleinbuchstaben
        """
        return os.path.splitext(file_path)[1].lower()

    @staticmethod
    def get_free_space(path: str) -> Optional[int]:
        """Ermittelt den freien Speicherplatz auf einem Laufwerk.
        
        Args:
            path: Pfad zum Laufwerk oder Verzeichnis
            
        Returns:
            Freier Speicherplatz in Bytes oder None bei Fehler
        """
        try:
            if platform.system() == 'Windows':
                free_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    ctypes.c_wchar_p(path),
                    None,
                    None,
                    ctypes.pointer(free_bytes)
                )
                return free_bytes.value
            else:
                # Für andere Betriebssysteme
                st = os.statvfs(path)
                return st.f_bavail * st.f_frsize
                
        except Exception as e:
            return None
