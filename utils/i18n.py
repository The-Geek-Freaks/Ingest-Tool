#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Internationalisierungs-Modul."""

import json
import logging
import os
import string
from typing import Dict, Any

logger = logging.getLogger(__name__)

class I18n:
    """Verwaltet die Internationalisierung."""
    
    def __init__(self, translations_dir):
        """Initialisiert die Internationalisierung.
        
        Args:
            translations_dir (str): Pfad zum Verzeichnis mit den Übersetzungsdateien
        """
        self.translations_dir = translations_dir
        self.translations = {}
        self.current_language = 'de'  # Standard: Deutsch
        
        # Stelle sicher, dass das Verzeichnis existiert
        os.makedirs(self.translations_dir, exist_ok=True)
        
        # Prüfe, ob Übersetzungsdateien existieren
        de_file = os.path.join(self.translations_dir, 'de.json')
        en_file = os.path.join(self.translations_dir, 'en.json')
        
        if not (os.path.exists(de_file) and os.path.exists(en_file)):
            # Erstelle Standardübersetzungen, wenn Dateien nicht existieren
            self._create_default_translations()
        else:
            # Lade existierende Übersetzungen
            try:
                with open(de_file, 'r', encoding='utf-8') as f:
                    self.translations['de'] = json.load(f)
                with open(en_file, 'r', encoding='utf-8') as f:
                    self.translations['en'] = json.load(f)
            except Exception as e:
                logger.error(f"Fehler beim Laden der Übersetzungen: {e}")
                self._create_default_translations()
                
    def _load_all_translations(self):
        """Lädt alle verfügbaren Übersetzungen."""
        try:
            # Durchsuche das Übersetzungsverzeichnis
            for filename in os.listdir(self.translations_dir):
                if filename.endswith('.json'):
                    language = os.path.splitext(filename)[0]
                    self.translations[language] = self._load_language_file(language)
            
            # Wenn keine Übersetzungen geladen wurden, erstelle Standarddateien
            if not self.translations:
                self._create_default_translations()
                
        except Exception as e:
            logger.error(f"Fehler beim Laden der Übersetzungen: {e}")
            self._create_default_translations()
            
    def _load_language_file(self, lang: str) -> dict:
        """Lädt eine einzelne Sprachdatei.
        
        Args:
            lang: Sprachcode (z.B. 'de' oder 'en')
            
        Returns:
            Dictionary mit den Übersetzungen
        """
        try:
            file_path = os.path.join(self.translations_dir, f"{lang}.json")
            if not os.path.exists(file_path):
                logger.warning(f"Übersetzungsdatei {file_path} nicht gefunden")
                return {}
                
            with open(file_path, "r", encoding="utf-8") as f:
                translations = json.load(f)
                
            return translations
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der Übersetzungen für {lang}: {e}")
            return {}
    
    def set_language(self, language):
        """Setzt die aktuelle Sprache.
        
        Args:
            language (str): Sprachcode (z.B. 'de' oder 'en')
            
        Raises:
            ValueError: Wenn die Sprache nicht verfügbar ist
        """
        if language in self.translations:
            self.current_language = language
        else:
            raise ValueError(f"Sprache {language} nicht verfügbar")
    
    def get(self, key, **kwargs):
        """Holt einen übersetzten Text.
        
        Args:
            key (str): Schlüssel im Format 'kategorie.schluessel'
            **kwargs: Formatierungsparameter
        
        Returns:
            str: Übersetzter Text
            
        Raises:
            KeyError: Wenn ein erforderlicher Platzhalter fehlt
        """
        try:
            # Hole aktuelle Übersetzungen
            current = self.translations.get(self.current_language, {})
            
            # Traversiere den Schlüsselpfad
            parts = key.split('.')
            for part in parts:
                if not isinstance(current, dict):
                    logger.error(f"Fehler beim Abrufen der Übersetzung für '{key}': '{part}' ist kein Dictionary")
                    return key
                if part not in current:
                    logger.error(f"Fehler beim Abrufen der Übersetzung für '{key}': '{part}' nicht gefunden")
                    return key
                current = current[part]
            
            # Formatiere den Text falls nötig
            if not isinstance(current, str):
                logger.error(f"Fehler beim Abrufen der Übersetzung für '{key}': Wert ist kein String")
                return key
            
            # Prüfe, ob alle erforderlichen Platzhalter vorhanden sind
            placeholders = {p[1] for p in string.Formatter().parse(current) if p[1] is not None}
            if placeholders and not kwargs:
                raise KeyError(f"Fehlende Platzhalter: {placeholders}")
            
            if kwargs:
                try:
                    return current.format(**kwargs)
                except KeyError as e:
                    logger.error(f"Fehlender Platzhalter in '{key}': {e}")
                    raise
            
            return current
            
        except KeyError as e:
            logger.error(f"Fehler beim Abrufen der Übersetzung für '{key}': {e}")
            raise
    
    def _create_default_translations(self):
        """Erstellt Standardübersetzungsdateien."""
        default_de = {
            "language_name": "Deutsch",
            "settings": {
                "title": "Einstellungen",
                "general": {
                    "language": "Sprache"
                },
                "paths": {
                    "temp": {
                        "cleanup_temp": "Temporäre Dateien beim Beenden aufräumen"
                    }
                }
            },
            "general": {
                "ok": "OK",
                "cancel": "Abbrechen",
                "add": "Hinzufügen",
                "remove": "Entfernen",
                "save": "Speichern",
                "file_created": "Neue Datei: {filename}",
                "move_up": "Nach oben",
                "move_down": "Nach unten",
                "info": "Info"
            },
            "notifications": {
                "drive_connected": {
                    "message": "{label} ({letter})"
                }
            },
            "ui": {
                "progress": "Fortschritt",
                "starting_transfer": "Starte Übertragung...",
                "verify_none": "Keine Überprüfung",
                "verify_quick": "Schnelle Überprüfung",
                "verify_md5": "MD5-Überprüfung",
                "verify_sha1": "SHA1-Überprüfung",
                "verify_mode": "Überprüfungsmodus",
                "parallel_copies": "Parallele Kopien",
                "buffer_size": "Puffergröße",
                "copy_settings": "Kopiereinstellungen",
                "advanced_settings": "Erweiterte Einstellungen",
                "advanced_settings_tooltip": "Erweiterte Einstellungen anzeigen",
                "drop_files": "Dateien hier ablegen",
                "select_target_directory": "Zielverzeichnis auswählen",
                "actions": "Aktionen",
                "manage_presets_tooltip": "Voreinstellungen verwalten",
                "start_tooltip": "Übertragung starten",
                "cancel_tooltip": "Übertragung abbrechen",
                "save_preset": "Voreinstellung speichern",
                "load_preset": "Voreinstellung laden",
                "delete_preset": "Voreinstellung löschen",
                "transfer_completed": "Übertragung abgeschlossen",
                "transfer_failed": "Übertragung fehlgeschlagen",
                "transfer_cancelled": "Übertragung abgebrochen",
                "no_available_drives": "Keine verfügbaren Laufwerke",
                "select_filetype_first": "Bitte wählen Sie zuerst einen Dateityp aus",
                "cancel": "Abbrechen"
            },
            "messages": {
                "copy_started": "Kopiervorgang gestartet",
                "copy_completed": "Kopiervorgang abgeschlossen",
                "copy_failed": "Kopiervorgang fehlgeschlagen",
                "copy_cancelled": "Kopiervorgang abgebrochen",
                "verify_started": "Überprüfung gestartet",
                "file_created": "Datei erstellt",
                "file_modified": "Datei geändert",
                "file_deleted": "Datei gelöscht"
            },
            "dialogs": {
                "filetype_manager": {
                    "title": "Dateitypen verwalten",
                    "add_filetype": "Dateityp hinzufügen",
                    "remove_filetype": "Dateityp entfernen",
                    "filetype_name": "Dateityp-Name",
                    "invalid_filetype": "Ungültiger Dateityp",
                    "confirm_delete": "Möchten Sie diesen Dateityp wirklich löschen?"
                },
                "preset_manager": {
                    "title": "Voreinstellungen verwalten",
                    "new_preset": "Neue Voreinstellung",
                    "save_preset": "Voreinstellung speichern",
                    "load_preset": "Voreinstellung laden",
                    "delete_preset": "Voreinstellung löschen",
                    "preset_name": "Voreinstellungs-Name",
                    "invalid_preset": "Ungültige Voreinstellung",
                    "no_preset_name": "Bitte geben Sie einen Namen für die Voreinstellung ein",
                    "confirm_delete": "Möchten Sie diese Voreinstellung wirklich löschen?",
                    "confirm_overwrite": "Voreinstellung existiert bereits. Überschreiben?",
                    "preset_saved": "Voreinstellung gespeichert",
                    "preset_loaded": "Voreinstellung geladen",
                    "preset_deleted": "Voreinstellung gelöscht"
                }
            }
        }
        
        default_en = {
            "language_name": "English",
            "settings": {
                "title": "Settings",
                "general": {
                    "language": "Language"
                },
                "paths": {
                    "temp": {
                        "cleanup_temp": "Clean up temporary files on exit"
                    }
                }
            },
            "general": {
                "ok": "OK",
                "cancel": "Cancel",
                "add": "Add",
                "remove": "Remove",
                "save": "Save",
                "file_created": "New file: {filename}",
                "move_up": "Move Up",
                "move_down": "Move Down",
                "info": "Info"
            },
            "notifications": {
                "drive_connected": {
                    "message": "{label} ({letter})"
                }
            },
            "ui": {
                "progress": "Progress",
                "starting_transfer": "Starting transfer...",
                "verify_none": "No verification",
                "verify_quick": "Quick verification",
                "verify_md5": "MD5 verification",
                "verify_sha1": "SHA1 verification",
                "verify_mode": "Verification mode",
                "parallel_copies": "Parallel copies",
                "buffer_size": "Buffer size",
                "copy_settings": "Copy settings",
                "advanced_settings": "Advanced settings",
                "advanced_settings_tooltip": "Show advanced settings",
                "drop_files": "Drop files here",
                "select_target_directory": "Select target directory",
                "actions": "Actions",
                "manage_presets_tooltip": "Manage presets",
                "start_tooltip": "Start transfer",
                "cancel_tooltip": "Cancel transfer",
                "save_preset": "Save preset",
                "load_preset": "Load preset",
                "delete_preset": "Delete preset",
                "transfer_completed": "Transfer completed",
                "transfer_failed": "Transfer failed",
                "transfer_cancelled": "Transfer cancelled",
                "no_available_drives": "No available drives",
                "select_filetype_first": "Please select a file type first",
                "cancel": "Cancel"
            },
            "messages": {
                "copy_started": "Copy started",
                "copy_completed": "Copy completed",
                "copy_failed": "Copy failed",
                "copy_cancelled": "Copy cancelled",
                "verify_started": "Verification started",
                "file_created": "File created",
                "file_modified": "File modified",
                "file_deleted": "File deleted"
            },
            "dialogs": {
                "filetype_manager": {
                    "title": "Manage File Types",
                    "add_filetype": "Add file type",
                    "remove_filetype": "Remove file type",
                    "filetype_name": "File type name",
                    "invalid_filetype": "Invalid file type",
                    "confirm_delete": "Do you really want to delete this file type?"
                },
                "preset_manager": {
                    "title": "Manage Presets",
                    "new_preset": "New preset",
                    "save_preset": "Save preset",
                    "load_preset": "Load preset",
                    "delete_preset": "Delete preset",
                    "preset_name": "Preset name",
                    "invalid_preset": "Invalid preset",
                    "no_preset_name": "Please enter a name for the preset",
                    "confirm_delete": "Do you really want to delete this preset?",
                    "confirm_overwrite": "Preset already exists. Overwrite?",
                    "preset_saved": "Preset saved",
                    "preset_loaded": "Preset loaded",
                    "preset_deleted": "Preset deleted"
                }
            }
        }
        
        # Speichere Standardübersetzungen
        try:
            os.makedirs(self.translations_dir, exist_ok=True)
            
            with open(os.path.join(self.translations_dir, 'de.json'), 'w', encoding='utf-8') as f:
                json.dump(default_de, f, indent=4, ensure_ascii=False)
                
            with open(os.path.join(self.translations_dir, 'en.json'), 'w', encoding='utf-8') as f:
                json.dump(default_en, f, indent=4, ensure_ascii=False)
                
            self.translations = {
                'de': default_de,
                'en': default_en
            }
            
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Standardübersetzungen: {e}")
