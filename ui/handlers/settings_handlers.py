import logging
from PyQt5.QtWidgets import (
    QFileDialog, QDialog, QListWidgetItem, QVBoxLayout, 
    QPushButton, QHBoxLayout, QListWidget, QDialogButtonBox, 
    QInputDialog, QMessageBox
)
from config.constants import (
    STANDARD_DATEITYPEN,
    STANDARD_SPRACHE,
    VERFUEGBARE_SPRACHEN
)
from ui.dialogs.advanced_settings import AdvancedSettingsDialog
from ui.dialogs.preset_dialog import PresetDialog

logger = logging.getLogger(__name__)

class SettingsHandlers:
    """Handler für Einstellungen-bezogene Events."""
    
    def __init__(self, main_window):
        self.main_window = main_window
        
    def show_preset_manager(self):
        """Zeigt den Preset-Manager Dialog."""
        current_settings = {
            'excluded_drives': [self.main_window.excluded_list.item(i).text() 
                              for i in range(self.main_window.excluded_list.count())],
            'mappings': [self.main_window.mappings_list.item(i).text() 
                        for i in range(self.main_window.mappings_list.count())],
            'parallel_copies': self.main_window.settings.get('parallel_copies', 2),
            'buffer_size': self.main_window.settings.get('buffer_size', 64*1024),
            'auto_start': self.main_window.settings.get('auto_start', False),
            'verify_copies': self.main_window.settings.get('verify_copies', False),
            'recursive_search': self.main_window.settings.get('recursive_search', True),
            'show_notifications': self.main_window.settings.get('show_notifications', True)
        }
        
        dialog = PresetDialog(current_settings, self.main_window)
        dialog.preset_selected.connect(self._on_preset_selected)
        dialog.exec_()
        
    def _on_preset_selected(self, settings: dict):
        """Wird aufgerufen wenn ein Preset ausgewählt wurde."""
        try:
            # Setze Einstellungen
            self.main_window.excluded_list.clear()
            for drive in settings.get('excluded_drives', []):
                self.main_window.excluded_list.addItem(drive)
                
            self.main_window.mappings_list.clear()
            for mapping in settings.get('mappings', []):
                self.main_window.mappings_list.addItem(mapping)
                
            # Aktualisiere erweiterte Einstellungen
            self.main_window.settings['parallel_copies'] = settings.get('parallel_copies', 2)
            self.main_window.settings['buffer_size'] = settings.get('buffer_size', 64*1024)
            self.main_window.settings['auto_start'] = settings.get('auto_start', False)
            self.main_window.settings['verify_copies'] = settings.get('verify_copies', False)
            self.main_window.settings['recursive_search'] = settings.get('recursive_search', True)
            self.main_window.settings['show_notifications'] = settings.get('show_notifications', True)
            
            # Aktualisiere Parallel Copier
            self.main_window.parallel_copier.max_workers = settings.get('parallel_copies', 2)
            self.main_window.parallel_copier.buffer_size = settings.get('buffer_size', 64*1024)
                
        except Exception as e:
            logger.error(f"Fehler beim Laden des Presets: {e}")
            QMessageBox.critical(
                self.main_window,
                "Fehler",
                f"Das Preset konnte nicht geladen werden: {str(e)}"
            )
            
    def on_manage_filetypes_clicked(self):
        """Handler für Dateityp-Verwaltung."""
        try:
            # Hole aktuelle Dateitypen
            current_types = []
            if hasattr(self.main_window, 'filetype_combo'):
                current_types = [
                    self.main_window.filetype_combo.itemText(i)
                    for i in range(self.main_window.filetype_combo.count())
                ]
            
            # Zeige Dialog
            dialog = QDialog(self.main_window)
            dialog.setWindowTitle(self.main_window.i18n.get("dialogs.filetype_manager.title"))
            dialog.setModal(True)
            
            layout = QVBoxLayout(dialog)
            
            # Liste der Dateitypen
            list_widget = QListWidget(dialog)
            list_widget.addItems(current_types)
            layout.addWidget(list_widget)
            
            # Buttons
            button_layout = QHBoxLayout()
            add_button = QPushButton(self.main_window.i18n.get("dialogs.filetype_manager.add_filetype"))
            remove_button = QPushButton(self.main_window.i18n.get("dialogs.filetype_manager.remove_filetype"))
            button_layout.addWidget(add_button)
            button_layout.addWidget(remove_button)
            layout.addLayout(button_layout)
            
            # OK/Abbrechen
            button_box = QDialogButtonBox(
                QDialogButtonBox.Ok | QDialogButtonBox.Cancel
            )
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            
            # Verbinde Buttons
            def on_add():
                text, ok = QInputDialog.getText(
                    dialog, 
                    self.main_window.i18n.get("dialogs.filetype_manager.add_filetype"),
                    self.main_window.i18n.get("dialogs.filetype_manager.filetype_name")
                )
                if ok and text:
                    if not text.startswith('.'):
                        text = '.' + text
                    list_widget.addItem(text)
                    
            def on_remove():
                current = list_widget.currentItem()
                if current:
                    if QMessageBox.question(
                        dialog,
                        self.main_window.i18n.get("dialogs.filetype_manager.remove_filetype"),
                        self.main_window.i18n.get("dialogs.filetype_manager.confirm_delete")
                    ) == QMessageBox.Yes:
                        list_widget.takeItem(list_widget.row(current))
                    
            add_button.clicked.connect(on_add)
            remove_button.clicked.connect(on_remove)
            
            # Zeige Dialog
            if dialog.exec_() == QDialog.Accepted:
                # Aktualisiere Dateitypen
                types = [list_widget.item(i).text() 
                        for i in range(list_widget.count())]
                
                if hasattr(self.main_window, 'filetype_combo'):
                    self.main_window.filetype_combo.clear()
                    self.main_window.filetype_combo.addItems(types)
                
                if hasattr(self.main_window, 'settings'):
                    self.main_window.settings.set('file_types', types)
                    
        except Exception as e:
            logger.error(f"Fehler beim Öffnen des Dateityp-Managers: {str(e)}")
            QMessageBox.critical(
                self.main_window,
                self.main_window.i18n.get("general.error"),
                f"Fehler beim Öffnen des Dateityp-Managers: {str(e)}"
            )
            
    def on_add_mapping_clicked(self):
        """Handler für Hinzufügen einer neuen Zuordnung."""
        filetype = self.main_window.filetype_combo.currentText()
        target_path = self.main_window.target_edit.text()
        
        if not filetype or not target_path:
            logger.warning("Bitte wählen Sie einen Dateityp und ein Zielverzeichnis aus")
            return
            
        # Füge neue Zuordnung zur Liste hinzu
        item = QListWidgetItem(f"{filetype} -> {target_path}")
        self.main_window.mappings_list.addItem(item)
        
    def on_browse_clicked(self):
        """Handler für Browse-Button."""
        path = QFileDialog.getExistingDirectory(
            self.main_window,
            "Zielverzeichnis auswählen",
            "",
            QFileDialog.ShowDirsOnly
        )
        if path:
            self.main_window.target_edit.setText(path)
            
    def on_language_changed(self, index):
        """Handler für Änderungen der Sprachauswahl."""
        # Hole Sprachcode aus ComboBox
        language = self.main_window.language_combo.itemData(index)
        if language:
            # Setze neue Sprache
            self.main_window.i18n.set_language(language)
            # Speichere Spracheinstellung
            self.main_window.settings.set('language', language)
            # Aktualisiere UI-Texte
            self.main_window.retranslate_ui()
            logger.info(f"Sprache auf {language} geändert")
            
    def load_settings(self):
        """Lädt die gespeicherten Einstellungen."""
        # Lade Sprache
        language = self.main_window.settings.get('language', STANDARD_SPRACHE)
        index = self.main_window.language_combo.findData(language)
        if index >= 0:
            self.main_window.language_combo.setCurrentIndex(index)
            
        # Lade Dateitypen
        self.main_window.filetype_combo.clear()
        self.main_window.filetype_combo.addItems(
            self.main_window.settings.get('file_types', STANDARD_DATEITYPEN)
        )
        
        # Lade Zuordnungen
        mappings = self.main_window.settings.get('mappings', {})
        for file_type, target_path in mappings.items():
            item = QListWidgetItem(f"{file_type} -> {target_path}")
            self.main_window.mappings_list.addItem(item)
            
        # Lade ausgeschlossene Laufwerke
        excluded = self.main_window.settings.get('excluded_drives', [])
        for drive in excluded:
            item = QListWidgetItem(drive)
            self.main_window.excluded_list.addItem(item)
            self.main_window.drive_controller.exclude_drive(drive)
        
        # Lade "Quelldateien löschen" Option
        self.main_window.delete_source_checkbox.setChecked(
            self.main_window.settings.get('delete_source', False)
        )
            
    def load_preset(self, settings: dict):
        """Lädt Einstellungen aus einem Preset."""
        # Dateitypen
        if 'file_types' in settings:
            self.main_window.settings.set('file_types', settings['file_types'])
            self.main_window.filetype_combo.clear()
            self.main_window.filetype_combo.addItems(settings['file_types'])
            
        # Quelldateien löschen
        if 'delete_source' in settings:
            self.main_window.delete_source_checkbox.setChecked(settings['delete_source'])
            
        # Netzwerk-Einstellungen
        if 'network_settings' in settings:
            self.main_window.settings.set('network_settings', settings['network_settings'])
            
        # UI-Einstellungen
        if 'ui_settings' in settings:
            self.main_window.settings.set('ui_settings', settings['ui_settings'])
            
    def save_settings(self):
        """Speichert aktuelle Einstellungen."""
        # Speichere Sprache
        self.main_window.settings.set(
            'language', 
            self.main_window.language_combo.currentData()
        )
        
        # Speichere Dateitypen
        file_types = [
            self.main_window.filetype_combo.itemText(i)
            for i in range(self.main_window.filetype_combo.count())
        ]
        self.main_window.settings.set('file_types', file_types)
        
        # Speichere Zuordnungen
        mappings = {}
        for i in range(self.main_window.mappings_list.count()):
            item = self.main_window.mappings_list.item(i)
            file_type, target = item.text().split(" -> ")
            mappings[file_type] = target
        self.main_window.settings.set('mappings', mappings)
        
        # Speichere ausgeschlossene Laufwerke
        excluded = [
            self.main_window.excluded_list.item(i).text()
            for i in range(self.main_window.excluded_list.count())
        ]
        self.main_window.settings.set('excluded_drives', excluded)
        
        # Speichere sonstige Einstellungen
        self.main_window.settings.set(
            'delete_source', 
            self.main_window.delete_source_checkbox.isChecked()
        )

    def show_advanced_settings(self):
        """Zeigt den Dialog für erweiterte Einstellungen."""
        try:
            settings = {
                "buffer_size": self.main_window.parallel_copier.buffer_size // 1024,  # Konvertiere zu KB
                "parallel_copies": self.main_window.parallel_copier.max_workers,
                "verify_mode": self.main_window.settings.get('verify_mode', 'none'),
                "auto_start": self.main_window.settings.get('auto_start', False),
                "schedule_enable": self.main_window.settings.get('schedule_enable', False),
                "start_time": self.main_window.settings.get('start_time', '22:00'),
                "batch_jobs": self.main_window.batch_manager.jobs if hasattr(self.main_window.batch_manager, 'jobs') else []
            }
            
            dialog = AdvancedSettingsDialog(
                self.main_window,
                settings,
                drives=self.main_window.drive_controller.get_drives(),
                file_types=self.main_window.get_file_types()
            )
            
            if dialog.exec_():
                new_settings = dialog.get_settings()
                
                # Aktualisiere Kopiereinstellungen
                self.main_window.parallel_copier.buffer_size = new_settings["buffer_size"] * 1024
                self.main_window.parallel_copier.max_workers = new_settings["parallel_copies"]
                
                # Speichere Batch-Jobs
                if hasattr(self.main_window.batch_manager, 'jobs'):
                    self.main_window.batch_manager.jobs = []
                    for job in new_settings["batch_jobs"]:
                        self.main_window.batch_manager.add_job(
                            job["source_drive"],
                            job["file_type"],
                            job["target_path"]
                        )
                    
                # Aktiviere/Deaktiviere Zeitsteuerung
                if new_settings["schedule_enable"]:
                    self.main_window.setup_scheduled_transfer(new_settings["start_time"])
                else:
                    self.main_window.disable_scheduled_transfer()
                    
        except Exception as e:
            logger.error(f"Fehler beim Öffnen der erweiterten Einstellungen: {e}")
