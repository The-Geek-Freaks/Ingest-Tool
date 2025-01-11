#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

# Programm-Verzeichnis
PROGRAMM_VERZEICHNIS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Verzeichnisse
TRANSLATIONS_VERZEICHNIS = os.path.join(PROGRAMM_VERZEICHNIS, "translations")
EINSTELLUNGEN_VERZEICHNIS = os.path.expanduser("~/.ingest_tool")
LOG_VERZEICHNIS = os.path.join(EINSTELLUNGEN_VERZEICHNIS, "logs")

# Dateipfade
EINSTELLUNGEN_DATEI = os.path.join(EINSTELLUNGEN_VERZEICHNIS, "settings.json")
LOG_DATEI = os.path.join(LOG_VERZEICHNIS, "ingest_tool.log")

# Dateitypen
STANDARD_DATEITYPEN = {
    'VIDEO': ['.mov', '.mp4', '.mxf', '.avi', '.wmv'],
    'AUDIO': ['.wav', '.mp3', '.aac', '.m4a'],
    'IMAGE': ['.jpg', '.jpeg', '.png', '.raw', '.arw'],
    'DOCUMENT': ['.xml', '.srt', '.txt']
}

# Sprachen
VERFUEGBARE_SPRACHEN = {
    "de": "Deutsch",
    "en": "English"
}
STANDARD_SPRACHE = "de"

# Puffer-Größen
KOPIER_PUFFER_GROESSE = 1024 * 1024  # 1MB Puffer für Dateioperationen
HASH_PUFFER_GROESSE = 64 * 1024      # 64KB Puffer für Hash-Berechnungen

# Zeitintervalle (in Sekunden)
LAUFWERK_CHECK_INTERVALL = 1.0       # Intervall für Laufwerksprüfung
TRANSFER_UPDATE_INTERVALL = 0.5      # Intervall für Transfer-Updates

# Status-Codes
STATUS_BEREIT = "bereit"
STATUS_KOPIEREN = "kopieren"
STATUS_VERIFIZIEREN = "verifizieren"
STATUS_FERTIG = "fertig"
STATUS_FEHLER = "fehler"

# UI-Konstanten
MAX_LOG_EINTRAEGE = 1000            # Maximale Anzahl von Log-Einträgen
FENSTER_BREITE = 800                # Standard-Fensterbreite
FENSTER_HOEHE = 600                 # Standard-Fensterhöhe
