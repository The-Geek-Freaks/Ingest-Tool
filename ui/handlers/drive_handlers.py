import logging
from PyQt5.QtCore import QThread, QObject, Qt, QMetaObject, Q_ARG
from PyQt5.QtWidgets import QListWidgetItem, QFileDialog
from ui.widgets.drive_list_item import DriveListItem
import os

logger = logging.getLogger(__name__)

class DriveHandlers(QObject):
    """Behandelt Laufwerks-Events."""
    
    def __init__(self, main_window):
        """Initialisiert den DriveHandler."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.main_window = main_window
        self._current_thread = None
        
    def on_drive_connected(self, drive_letter: str, drive_label: str = "", drive_type: str = "local"):
        """Handler für neu verbundene Laufwerke."""
        try:
            self._current_thread = QThread.currentThread()
            self.logger.debug(f"on_drive_connected() aufgerufen in Thread: {self._current_thread}")
            self.logger.debug(f"Main Window Thread: {self.main_window.thread()}")
            
            # Normalisiere Laufwerksbuchstaben
            drive_letter = drive_letter.rstrip(':').rstrip('\\')
            
            # Debug-Ausgabe
            self.logger.debug(f"Drive Handler - Laufwerk: {drive_letter}, Label: '{drive_label}', Typ: {drive_type}")
            
            # Prüfe ob das Laufwerk bereits existiert
            if drive_letter in self.main_window.drive_items:
                # Aktualisiere nur den Namen und Typ
                drive_item = self.main_window.drive_items[drive_letter]
                drive_item.drive_name = drive_label
                drive_item.drive_type = drive_type
                drive_item._update_display()
                self.logger.info(f"Laufwerksname aktualisiert: {drive_letter} ({drive_label}) - Typ: {drive_type}")
            else:
                # Erstelle neues DriveListItem
                drive_item = DriveListItem(drive_letter, drive_label, drive_type)
                self.main_window.drives_list.addItem(drive_item)
                self.main_window.drive_items[drive_letter] = drive_item
                self.logger.info(f"Neues Laufwerk hinzugefügt: {drive_letter} ({drive_label}) - Typ: {drive_type}")
            
            # Prüfe ob Laufwerk ausgeschlossen ist
            if drive_letter in self.main_window.excluded_drives:
                drive_item.set_excluded(True)
            
            # Wenn Überwachung läuft und Laufwerk nicht ausgeschlossen ist, starte Watcher
            if (self.main_window.file_watcher_manager and 
                self.main_window.file_watcher_manager.is_watching and
                drive_letter not in self.main_window.excluded_drives):
                self.logger.info(f"Starte Überwachung für neues Laufwerk {drive_letter}")
                
                # Hole aktuelle Dateitypen und Mappings
                file_types = list(self.main_window.file_watcher_manager.file_mappings.keys())
                
                if file_types:
                    self.logger.info(f"Starte Überwachung für Laufwerk {drive_letter} mit Dateitypen: {file_types}")
                    
                    # Normalisiere den Laufwerkspfad für Windows
                    drive_path = f"{drive_letter}:\\"
                    drive_path = os.path.normpath(drive_path)
                    
                    # Starte Watcher
                    success = self.main_window.file_watcher_manager.start_watcher(drive_path=drive_path, file_types=file_types)
                    
                    if success:
                        self.logger.info(f"Watcher für {drive_letter} erfolgreich gestartet")
                    else:
                        self.logger.error(f"Konnte Watcher für {drive_letter} nicht starten")
                else:
                    self.logger.warning("Keine Dateitypen zum Überwachen gefunden")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten des neuen Laufwerks: {e}", exc_info=True)

    def on_drive_disconnected(self, drive_letter: str):
        """Handler für getrennte Laufwerke."""
        try:
            # Normalisiere Laufwerksbuchstaben
            drive_letter = drive_letter.rstrip(':').rstrip('\\')
            
            # Entferne aus der Liste
            if drive_letter in self.main_window.drive_items:
                drive_item = self.main_window.drive_items[drive_letter]
                row = self.main_window.drives_list.row(drive_item)
                self.main_window.drives_list.takeItem(row)
                del self.main_window.drive_items[drive_letter]
                
                # Stoppe Watcher wenn aktiv
                if self.main_window.is_watching:
                    drive_path = f"{drive_letter}:\\"
                    self.main_window.file_watcher_manager.stop_watcher(drive_path)
                
                self.logger.info(f"Laufwerk entfernt: {drive_letter}")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Entfernen des Laufwerks {drive_letter}: {e}", exc_info=True)

    def on_file_found(self, file_path: str):
        """Handler für gefundene Dateien."""
        try:
            self._current_thread = QThread.currentThread()
            self.logger.debug(f"on_file_found() aufgerufen in Thread: {self._current_thread}")
            self.logger.debug(f"Main Window Thread: {self.main_window.thread()}")
            
            # Aktualisiere UI
            logging.getLogger("core.drive_controller").info(f"Datei gefunden: {file_path}")
        except Exception as e:
            logger.error(f"Fehler beim Verarbeiten der gefundenen Datei {file_path}: {e}")
            
    def on_add_excluded_clicked(self):
        """Handler für Hinzufügen eines ausgeschlossenen Laufwerks."""
        self._current_thread = QThread.currentThread()
        self.logger.debug(f"on_add_excluded_clicked() aufgerufen in Thread: {self._current_thread}")
        self.logger.debug(f"Main Window Thread: {self.main_window.thread()}")
        
        path = QFileDialog.getExistingDirectory(
            self.main_window,
            "Wähle ein Laufwerk aus",
            "",
            QFileDialog.ShowDirsOnly
        )
        if path:
            # Extrahiere Laufwerksbuchstaben
            drive_letter = path[0].upper() + ":"
            
            # Füge zur Liste hinzu
            if drive_letter not in self.main_window.excluded_drives:
                self.main_window.excluded_drives.append(drive_letter)
                self.main_window.excluded_list.addItem(drive_letter)
                
                # Speichere aktualisierte Liste
                self.main_window.settings.set('excluded_drives', self.main_window.excluded_drives)
                
                # Aktualisiere UI
                if drive_letter in self.main_window.drive_items:
                    self.main_window.drive_items[drive_letter].set_excluded(True)
                    
    def on_remove_excluded_clicked(self):
        """Handler für Entfernen eines ausgeschlossenen Laufwerks."""
        self._current_thread = QThread.currentThread()
        self.logger.debug(f"on_remove_excluded_clicked() aufgerufen in Thread: {self._current_thread}")
        self.logger.debug(f"Main Window Thread: {self.main_window.thread()}")
        
        current_item = self.main_window.excluded_list.currentItem()
        if current_item:
            drive_letter = current_item.text()
            
            # Entferne aus Liste
            if drive_letter in self.main_window.excluded_drives:
                self.main_window.excluded_drives.remove(drive_letter)
                self.main_window.excluded_list.takeItem(
                    self.main_window.excluded_list.row(current_item)
                )
                
                # Speichere aktualisierte Liste
                self.main_window.settings.set('excluded_drives', self.main_window.excluded_drives)
                
                # Aktualisiere UI
                if drive_letter in self.main_window.drive_items:
                    self.main_window.drive_items[drive_letter].set_excluded(False)
                    
    def on_exclude_all_clicked(self):
        """Handler für Ausschließen aller verbundenen Laufwerke."""
        self._current_thread = QThread.currentThread()
        self.logger.debug(f"on_exclude_all_clicked() aufgerufen in Thread: {self._current_thread}")
        self.logger.debug(f"Main Window Thread: {self.main_window.thread()}")
        
        # Hole alle verbundenen Laufwerke
        for item in self.main_window.drive_items.values():
            drive_letter = f"{item.drive_letter}/"
            if drive_letter not in self.main_window.excluded_drives:
                self.main_window.excluded_drives.append(drive_letter)
                self.main_window.excluded_list.addItem(drive_letter)
                
                # Aktualisiere UI
                if item.drive_letter.rstrip(':/') in self.main_window.drive_items:
                    self.main_window.drive_items[item.drive_letter.rstrip(':/')].set_excluded(True)
        
        # Speichere aktualisierte Liste
        self.main_window.settings.set('excluded_drives', self.main_window.excluded_drives)
        self.logger.debug(f"Ausgeschlossene Laufwerke aktualisiert: {self.main_window.excluded_drives}")
