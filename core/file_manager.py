#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import logging
import hashlib
from typing import Optional, Tuple, List
from datetime import datetime
from pathlib import Path

try:
    import xxhash
    XXHASH_VERFUEGBAR = True
except ImportError:
    XXHASH_VERFUEGBAR = False

from PyQt5.QtCore import QObject, pyqtSignal

from config.constants import (
    KOPIER_PUFFER_GROESSE,
    HASH_PUFFER_GROESSE,
    STATUS_BEREIT,
    STATUS_KOPIEREN,
    STATUS_VERIFIZIEREN,
    STATUS_FERTIG,
    STATUS_FEHLER
)

class DateiManager(QObject):
    """Verwaltet Dateioperationen wie Kopieren und Verifizieren."""
    
    # Signale
    fortschritt_aktualisiert = pyqtSignal(str, float)  # (datei, prozent)
    status_aktualisiert = pyqtSignal(str, str)  # (datei, status)
    fehler_aufgetreten = pyqtSignal(str, str)  # (datei, fehlermeldung)

    def __init__(self):
        super().__init__()
        self.abbrechen = False

    def kopiere_datei(self, quelle: str, ziel: str, verifizieren: bool = True) -> bool:
        """Kopiert eine Datei von Quelle nach Ziel.
        
        Args:
            quelle: Pfad zur Quelldatei
            ziel: Pfad zur Zieldatei
            verifizieren: Ob die Kopie verifiziert werden soll
            
        Returns:
            True wenn erfolgreich, sonst False
        """
        try:
            self.status_aktualisiert.emit(quelle, STATUS_KOPIEREN)
            
            # Erstelle Zielverzeichnis falls nicht vorhanden
            ziel_verzeichnis = os.path.dirname(ziel)
            os.makedirs(ziel_verzeichnis, exist_ok=True)

            # Kopiere Datei mit Fortschrittsanzeige
            dateigroesse = os.path.getsize(quelle)
            kopiert = 0

            with open(quelle, 'rb') as quelle_datei, \
                 open(ziel, 'wb') as ziel_datei:
                
                while True:
                    if self.abbrechen:
                        raise Exception("Kopiervorgang abgebrochen")
                        
                    chunk = quelle_datei.read(KOPIER_PUFFER_GROESSE)
                    if not chunk:
                        break
                        
                    ziel_datei.write(chunk)
                    kopiert += len(chunk)
                    
                    # Aktualisiere Fortschritt
                    prozent = (kopiert / dateigroesse) * 100
                    self.fortschritt_aktualisiert.emit(quelle, prozent)

            # Verifiziere Kopie
            if verifizieren:
                self.status_aktualisiert.emit(quelle, STATUS_VERIFIZIEREN)
                if not self._verifiziere_kopie(quelle, ziel):
                    raise Exception("Verifizierung fehlgeschlagen")

            # Kopiere Metadaten (Zeitstempel etc.)
            shutil.copystat(quelle, ziel)

            self.status_aktualisiert.emit(quelle, STATUS_FERTIG)
            return True

        except Exception as e:
            self.status_aktualisiert.emit(quelle, STATUS_FEHLER)
            self.fehler_aufgetreten.emit(quelle, str(e))
            
            # Lösche unvollständige Zieldatei
            if os.path.exists(ziel):
                try:
                    os.remove(ziel)
                except:
                    pass
                    
            return False

    def _verifiziere_kopie(self, quelle: str, ziel: str) -> bool:
        """Verifiziert ob zwei Dateien identisch sind.
        
        Args:
            quelle: Pfad zur Quelldatei
            ziel: Pfad zur Zieldatei
            
        Returns:
            True wenn identisch, sonst False
        """
        if XXHASH_VERFUEGBAR:
            # Nutze xxhash für schnellere Verifizierung
            hash_quelle = xxhash.xxh64()
            hash_ziel = xxhash.xxh64()
        else:
            # Fallback auf SHA256
            hash_quelle = hashlib.sha256()
            hash_ziel = hashlib.sha256()

        # Lese und hashe Quelldatei
        with open(quelle, 'rb') as f:
            while True:
                if self.abbrechen:
                    return False
                    
                chunk = f.read(HASH_PUFFER_GROESSE)
                if not chunk:
                    break
                hash_quelle.update(chunk)

        # Lese und hashe Zieldatei
        with open(ziel, 'rb') as f:
            while True:
                if self.abbrechen:
                    return False
                    
                chunk = f.read(HASH_PUFFER_GROESSE)
                if not chunk:
                    break
                hash_ziel.update(chunk)

        # Vergleiche Hashes
        return hash_quelle.hexdigest() == hash_ziel.hexdigest()

    def loesche_datei(self, datei: str) -> bool:
        """Löscht eine Datei.
        
        Args:
            datei: Zu löschende Datei
            
        Returns:
            True wenn erfolgreich, sonst False
        """
        try:
            if os.path.exists(datei):
                os.remove(datei)
            return True
        except Exception as e:
            self.fehler_aufgetreten.emit(datei, f"Fehler beim Löschen: {e}")
            return False

    def get_datei_info(self, datei: str) -> Tuple[int, datetime]:
        """Gibt Informationen über eine Datei zurück.
        
        Args:
            datei: Pfad zur Datei
            
        Returns:
            Tuple aus (Größe in Bytes, Änderungsdatum)
        """
        stats = os.stat(datei)
        return (stats.st_size, datetime.fromtimestamp(stats.st_mtime))

    def finde_dateien(self, verzeichnis: str, dateitypen: List[str]) -> List[str]:
        """Findet alle Dateien mit bestimmten Endungen in einem Verzeichnis.
        
        Args:
            verzeichnis: Zu durchsuchendes Verzeichnis
            dateitypen: Liste der Dateiendungen (z.B. ['.mp4', '.mov'])
            
        Returns:
            Liste der gefundenen Dateipfade
        """
        gefundene_dateien = []
        
        for root, _, files in os.walk(verzeichnis):
            for file in files:
                if self.abbrechen:
                    return []
                    
                if any(file.lower().endswith(typ.lower()) for typ in dateitypen):
                    gefundene_dateien.append(os.path.join(root, file))
                    
        return gefundene_dateien

    def abbrechen_transfer(self):
        """Bricht laufende Transfers ab."""
        self.abbrechen = True
