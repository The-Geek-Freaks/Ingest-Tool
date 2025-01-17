#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test-Skript für die OptimizedCopyEngine.
"""

import os
import sys
import logging
from datetime import datetime

# Füge Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.optimized_copy_engine import OptimizedCopyEngine

# Konfiguriere Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def progress_callback(transfer_id: str, progress: float, speed: float):
    """Callback für Fortschrittsupdates."""
    print(f"\rTransfer: {transfer_id}")
    print(f"Fortschritt: {progress:.1f}%")
    print(f"Geschwindigkeit: {speed / 1024 / 1024:.2f} MB/s")

def main():
    """Hauptfunktion für den Test."""
    try:
        # Erstelle Test-Verzeichnisse
        test_dir = os.path.join(os.path.dirname(__file__), "test_files")
        source_dir = os.path.join(test_dir, "source")
        target_dir = os.path.join(test_dir, "target")
        
        os.makedirs(source_dir, exist_ok=True)
        os.makedirs(target_dir, exist_ok=True)
        
        # Erstelle Test-Datei (200MB für Simulation einer großen Datei)
        source_file = os.path.join(source_dir, "test_200mb.dat")
        chunk_size = 1024 * 1024  # 1MB Chunks für Dateierstellung
        total_size = 200 * 1024 * 1024  # 200MB
        
        print(f"\nErstelle {total_size / 1024 / 1024}MB Test-Datei...")
        with open(source_file, 'wb') as f:
            remaining = total_size
            while remaining > 0:
                chunk = os.urandom(min(chunk_size, remaining))
                f.write(chunk)
                remaining -= len(chunk)
                if remaining % (10 * 1024 * 1024) == 0:  # Alle 10MB
                    print(f"Noch {remaining / 1024 / 1024}MB zu schreiben...")
        
        # Initialisiere Copy-Engine
        engine = OptimizedCopyEngine()
        engine.set_progress_callback(progress_callback)
        
        # Definiere Zieldatei
        target_file = os.path.join(target_dir, "test_200mb_copy.dat")
        
        print(f"\nStarte Test-Kopiervorgang...")
        print(f"Quelle: {source_file}")
        print(f"Ziel: {target_file}\n")
        
        # Starte Kopiervorgang
        start_time = datetime.now()
        future = engine.copy_file(source_file, target_file)
        future.result()  # Warte auf Abschluss
        duration = (datetime.now() - start_time).total_seconds()
        
        # Verifiziere Ergebnis
        if os.path.exists(target_file):
            source_size = os.path.getsize(source_file)
            target_size = os.path.getsize(target_file)
            
            if source_size == target_size:
                print(f"\nTest erfolgreich!")
                print(f"Kopierzeit: {duration:.2f} Sekunden")
                print(f"Durchschnittliche Geschwindigkeit: {(source_size / duration) / 1024 / 1024:.2f} MB/s")
                
                # Teste Wiederaufnahme
                print("\nTeste Wiederaufnahme-Funktionalität...")
                os.remove(target_file)  # Lösche Zieldatei
                future = engine.copy_file(source_file, target_file)
                future.result()
                
                if os.path.exists(target_file) and os.path.getsize(target_file) == source_size:
                    print("Wiederaufnahme-Test erfolgreich!")
                else:
                    print("Fehler beim Wiederaufnahme-Test!")
            else:
                print(f"\nFehler: Dateigrößen stimmen nicht überein!")
                print(f"Quelle: {source_size} Bytes")
                print(f"Ziel: {target_size} Bytes")
        else:
            print(f"\nFehler: Zieldatei wurde nicht erstellt!")
            
    except Exception as e:
        print(f"\nFehler während des Tests: {str(e)}")
    finally:
        # Aufräumen
        try:
            if os.path.exists(source_file):
                os.remove(source_file)
            if os.path.exists(target_file):
                os.remove(target_file)
            os.rmdir(source_dir)
            os.rmdir(target_dir)
            os.rmdir(test_dir)
        except Exception as e:
            print(f"Fehler beim Aufräumen: {str(e)}")

if __name__ == "__main__":
    main()
