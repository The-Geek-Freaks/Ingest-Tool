#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests für das Internationalisierungssystem.
"""
import os
import json
import unittest
from utils.i18n import I18n

class TestI18n(unittest.TestCase):
    """Testet die I18n-Klasse."""
    
    def setUp(self):
        """Test-Setup."""
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.translations_dir = os.path.join(
            os.path.dirname(self.test_dir),
            "translations"
        )
        self.i18n = I18n(self.translations_dir)
        
    def test_load_translations(self):
        """Testet das Laden von Übersetzungen."""
        # Prüfe, ob Übersetzungsdateien existieren
        self.assertTrue(
            os.path.exists(os.path.join(self.translations_dir, "de.json")),
            "Deutsche Übersetzungsdatei nicht gefunden"
        )
        self.assertTrue(
            os.path.exists(os.path.join(self.translations_dir, "en.json")),
            "Englische Übersetzungsdatei nicht gefunden"
        )
        
        # Prüfe, ob Übersetzungen gültig sind
        for lang in ["de", "en"]:
            with open(os.path.join(self.translations_dir, f"{lang}.json"), encoding='utf-8') as f:
                try:
                    translations = json.load(f)
                    self.assertIsInstance(
                        translations,
                        dict,
                        f"Übersetzungen für {lang} sind kein Dictionary"
                    )
                except json.JSONDecodeError as e:
                    self.fail(f"Ungültige JSON-Datei für {lang}: {e}")
                    
    def test_language_switching(self):
        """Testet das Umschalten zwischen Sprachen."""
        # Deutsch
        self.i18n.set_language("de")
        self.assertEqual(
            self.i18n.get("settings.title"),
            "Einstellungen",
            "Falsche deutsche Übersetzung"
        )
        
        # Englisch
        self.i18n.set_language("en")
        self.assertEqual(
            self.i18n.get("settings.title"),
            "Settings",
            "Falsche englische Übersetzung"
        )
        
        # Ungültige Sprache
        with self.assertRaises(ValueError):
            self.i18n.set_language("invalid")
            
    def test_nested_keys(self):
        """Testet verschachtelte Übersetzungsschlüssel."""
        self.i18n.set_language("de")
        
        # Einfacher Schlüssel
        self.assertEqual(
            self.i18n.get("general.ok"),
            "OK"
        )
        
        # Verschachtelter Schlüssel
        self.assertEqual(
            self.i18n.get("settings.general.language"),
            "Sprache"
        )
        
        # Tief verschachtelter Schlüssel
        self.assertEqual(
            self.i18n.get("settings.paths.temp.cleanup_temp"),
            "Temporäre Dateien beim Beenden aufräumen"
        )
        
        # Nicht existierender Schlüssel
        self.assertEqual(
            self.i18n.get("non.existent.key"),
            "non.existent.key",
            "Nicht existierender Schlüssel sollte als Fallback zurückgegeben werden"
        )
        
    def test_placeholders(self):
        """Testet Platzhalter in Übersetzungen."""
        self.i18n.set_language("de")
        
        # Einfacher Platzhalter
        self.assertEqual(
            self.i18n.get("general.file_created", filename="test.txt"),
            "Neue Datei: test.txt"
        )
        
        # Mehrere Platzhalter
        self.assertEqual(
            self.i18n.get(
                "notifications.drive_connected.message",
                label="USB-Stick",
                letter="E:"
            ),
            "USB-Stick (E:)"
        )
        
        # Fehlende Platzhalter
        with self.assertRaises(KeyError):
            self.i18n.get("general.file_created")
            
    def test_consistency(self):
        """Testet die Konsistenz zwischen den Übersetzungen."""
        # Lade beide Übersetzungsdateien
        with open(os.path.join(self.translations_dir, "de.json"), encoding='utf-8') as f:
            de_translations = json.load(f)
        with open(os.path.join(self.translations_dir, "en.json"), encoding='utf-8') as f:
            en_translations = json.load(f)
            
        # Hilfsfunktion zum Extrahieren aller Schlüssel
        def get_keys(d, prefix=""):
            keys = set()
            for k, v in d.items():
                full_key = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    keys.update(get_keys(v, full_key))
                else:
                    keys.add(full_key)
            return keys
            
        # Vergleiche Schlüssel
        de_keys = get_keys(de_translations)
        en_keys = get_keys(en_translations)
        
        # Prüfe auf fehlende Schlüssel
        missing_in_en = de_keys - en_keys
        missing_in_de = en_keys - de_keys
        
        self.assertEqual(
            len(missing_in_en),
            0,
            f"Fehlende Schlüssel in en.json: {missing_in_en}"
        )
        self.assertEqual(
            len(missing_in_de),
            0,
            f"Fehlende Schlüssel in de.json: {missing_in_de}"
        )
        
if __name__ == "__main__":
    unittest.main()
