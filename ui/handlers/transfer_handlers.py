import os
import time
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

class TransferHandlers:
    def __init__(self, main_window):
        self.main_window = main_window
        
    def on_transfer_started(self, drive_letter: str):
        """Handler für gestartete Transfers."""
        if drive_letter in self.main_window.drive_items:
            self.main_window.drive_items[drive_letter].set_status("copying")
            self.main_window.transfer_start_time = time.time()
            # Add drive to progress widget when transfer starts
            drive_name = self.main_window.drive_items[drive_letter].drive_name
            if not drive_name:
                drive_name = f"Laufwerk ({drive_letter}:)"
            self.main_window.progress_widget.add_drive(drive_letter, drive_name)
        
    def on_transfer_completed(self, drive_letter: str):
        """Handler für abgeschlossene Transfers."""
        if drive_letter in self.main_window.drive_items:
            self.main_window.drive_items[drive_letter].set_status("done")
            # Remove drive from progress widget when done
            self.main_window.progress_widget.remove_drive(drive_letter)
            
        # Aktiviere Start-Button wieder
        self.main_window.start_button.setEnabled(True)
        self.main_window.cancel_button.setEnabled(False)
        
    def on_transfer_failed(self, drive_letter: str, error: str):
        """Handler für fehlgeschlagene Transfers."""
        if drive_letter in self.main_window.drive_items:
            self.main_window.drive_items[drive_letter].set_status("failed")
            
        # Aktiviere Start-Button wieder
        self.main_window.start_button.setEnabled(True)
        self.main_window.cancel_button.setEnabled(False)
        
    def on_transfer_cancelled(self, drive_letter: str):
        """Handler für abgebrochene Transfers."""
        if drive_letter in self.main_window.drive_items:
            self.main_window.drive_items[drive_letter].set_status("ready")
            
    def handle_transfer_progress(self, transfer_id: str, progress: float, speed: float):
        """Behandelt Fortschrittsupdates von Transfers.
        
        Args:
            transfer_id: ID des Transfers (Format: "source->target")
            progress: Fortschritt in Prozent (0-100)
            speed: Geschwindigkeit in Bytes pro Sekunde
        """
        try:
            # Extrahiere Quelldatei aus Transfer-ID
            source = transfer_id.split('->')[0]
            filename = os.path.basename(source)
            
            # Ermittle Laufwerk und Namen
            drive_letter = os.path.splitdrive(source)[0].rstrip(':')
            if drive_letter in self.main_window.drive_items:
                drive_item = self.main_window.drive_items[drive_letter]
                drive_name = drive_item.drive_name
            else:
                drive_name = f"Laufwerk ({drive_letter}:)"
            
            # Hole Dateigrößen
            if os.path.exists(source):
                total_bytes = os.path.getsize(source)
                transferred_bytes = int(total_bytes * (progress / 100))
                
                # Berechne ETA basierend auf aktueller Geschwindigkeit
                if speed > 0:
                    remaining_bytes = total_bytes - transferred_bytes
                    eta_seconds = remaining_bytes / speed
                    eta = timedelta(seconds=int(eta_seconds))
                else:
                    eta = timedelta.max
            else:
                total_bytes = 0
                transferred_bytes = 0
                eta = timedelta.max
            
            # Aktualisiere UI
            self.main_window.progress_widget.update_transfer(
                transfer_id=transfer_id,
                filename=filename,
                drive=drive_name,
                progress=progress / 100,  # Konvertiere zu 0-1
                speed=speed,
                total_bytes=total_bytes,
                transferred_bytes=transferred_bytes,
                start_time=time.time(),
                eta=eta
            )
            
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren des Transfers: {str(e)}", exc_info=True)

    def get_file_types(self):
        """Gibt eine Liste der verfügbaren Dateitypen zurück."""
        file_types = []
        for i in range(self.main_window.mappings_list.count()):
            item = self.main_window.mappings_list.item(i)
            if item:
                text = item.text()
                if "➔" in text:
                    source = text.split("➔")[0]
                    file_type = source.strip().lower()
                    if file_type.startswith('*'):
                        file_type = file_type[1:]
                    elif not file_type.startswith('.'):
                        file_type = '.' + file_type
                    file_types.append(file_type)
        return file_types

    def get_source_files(self, source_drive: str):
        """Gibt eine Liste der zu kopierenden Dateien zurück.
        
        Args:
            source_drive: Laufwerksbuchstabe
            
        Returns:
            Liste der Dateipfade
        """
        source_files = []
        
        try:
            # Normalisiere Laufwerksbuchstaben
            source_drive = source_drive.rstrip(':').rstrip('\\')
            
            # Prüfe ob das Laufwerk in der Liste der verbundenen Laufwerke ist
            if source_drive not in self.main_window.drive_items:
                logger.warning(f"Laufwerk {source_drive} ist nicht in der Liste der verbundenen Laufwerke")
                return []
                
            # Prüfe ob das Laufwerk ausgeschlossen ist
            if self.main_window.drive_items[source_drive].is_excluded:
                logger.warning(f"Laufwerk {source_drive} ist ausgeschlossen")
                return []
                
            # Hole Dateitypen
            file_types = self.get_file_types()
            if not file_types:
                logger.warning("Keine Dateitypen konfiguriert")
                return []
                
            # Durchsuche das Laufwerk nach passenden Dateien
            drive_path = f"{source_drive}:\\"
            logger.debug(f"Durchsuche Laufwerk {drive_path} nach Dateitypen: {file_types}")
            
            for root, _, files in os.walk(drive_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if any(file.lower().endswith(ext.lower()) for ext in file_types):
                        source_files.append(file_path)
                        logger.debug(f"Gefundene Datei: {file_path}")
                        
            if source_files:
                logger.info(f"Gefundene Dateien auf Laufwerk {source_drive}: {len(source_files)}")
            else:
                logger.info(f"Keine passenden Dateien auf Laufwerk {source_drive} gefunden")
                
            return source_files
            
        except Exception as e:
            logger.error(f"Fehler beim Durchsuchen von Laufwerk {source_drive}: {e}")
            return []

    def get_mapping_for_type(self, file_type: str) -> str:
        """Gibt die Zuordnung für einen Dateityp zurück.
        
        Args:
            file_type: Dateityp (z.B. ".mp4")
            
        Returns:
            Zielpfad oder None wenn keine Zuordnung existiert
        """
        file_type = file_type.lower()  # Case-insensitive Vergleich
        logger.debug(f"Suche Zuordnung für Dateityp: {file_type}")
        
        for i in range(self.main_window.mappings_list.count()):
            item_text = self.main_window.mappings_list.item(i).text()
            source, target = item_text.split(" ➔ ")
            # Entferne * und konvertiere zu Kleinbuchstaben
            source = source.strip().lower()
            if source.startswith('*'):
                source = source[1:]
            target = target.strip()
            
            logger.debug(f"Prüfe Zuordnung: {source} -> {target}")
            if source == file_type:
                logger.info(f"Zuordnung gefunden: {file_type} -> {target}")
                return target
                
        logger.warning(f"Keine Zuordnung gefunden für Dateityp: {file_type}")
        return None
