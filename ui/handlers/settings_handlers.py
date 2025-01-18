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
            # Aktuelle Einstellungen sammeln
            settings = {
                # Kopier-Einstellungen
                "buffer_size": self.main_window.parallel_copier.buffer_size // 1024,  # Konvertiere zu KB
                "chunk_size": self.main_window.parallel_copier.chunk_size // 1024,  # Konvertiere zu KB
                "parallel_copies": self.main_window.parallel_copier.max_workers,
                "verify_mode": self.main_window.settings.get('verify_mode', 'none'),
                "retry_count": self.main_window.settings.get('retry_count', 3),
                "retry_delay": self.main_window.settings.get('retry_delay', 1.0),
                "timeout": self.main_window.settings.get('timeout', 30.0),
                "preserve_timestamps": self.main_window.settings.get('preserve_timestamps', True),
                "create_target_dirs": self.main_window.settings.get('create_target_dirs', True),
                
                # Automatisierungs-Einstellungen
                "auto_start": self.main_window.settings.get('auto_start', False),
                "schedule_enable": self.main_window.settings.get('schedule_enable', False),
                "start_time": self.main_window.settings.get('start_time', '22:00'),
                "batch_jobs": self.main_window.batch_manager.jobs if hasattr(self.main_window.batch_manager, 'jobs') else [],
                
                # Überwachungs-Einstellungen
                "poll_interval": self.main_window.settings.get('poll_interval', 5),
                "monitored_file_types": self.main_window.settings.get('monitored_file_types', [".mp4", ".mov", ".avi"]),
                "recursive_monitoring": self.main_window.settings.get('recursive_monitoring', True),
                "monitor_hidden_files": self.main_window.settings.get('monitor_hidden_files', False),
                "monitor_system_files": self.main_window.settings.get('monitor_system_files', False)
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
                self.main_window.parallel_copier.chunk_size = new_settings["chunk_size"] * 1024
                self.main_window.parallel_copier.max_workers = new_settings["parallel_copies"]
                
                # Aktualisiere Fehlerbehandlung
                self.main_window.parallel_copier.retry_count = new_settings["retry_count"]
                self.main_window.parallel_copier.retry_delay = new_settings["retry_delay"]
                self.main_window.parallel_copier.timeout = new_settings["timeout"]
                
                # Aktualisiere Verzeichniseinstellungen
                self.main_window.parallel_copier.preserve_timestamps = new_settings["preserve_timestamps"]
                self.main_window.parallel_copier.create_target_dirs = new_settings["create_target_dirs"]
                
                # Aktualisiere Überwachungseinstellungen
                if hasattr(self.main_window, 'file_watcher_manager'):
                    self.main_window.file_watcher_manager.poll_interval = new_settings["poll_interval"]
                    self.main_window.file_watcher_manager.monitored_types = new_settings["monitored_file_types"]
                    self.main_window.file_watcher_manager.recursive = new_settings["recursive_monitoring"]
                    self.main_window.file_watcher_manager.monitor_hidden = new_settings["monitor_hidden_files"]
                    self.main_window.file_watcher_manager.monitor_system = new_settings["monitor_system_files"]
                    
                    # Starte FileWatcher neu mit neuen Einstellungen
                    self.main_window.file_watcher_manager.restart()
                
                # Speichere alle Einstellungen
                self.main_window.settings.update({
                    'verify_mode': new_settings["verify_mode"],
                    'auto_start': new_settings["auto_start"],
                    'schedule_enable': new_settings["schedule_enable"],
                    'start_time': new_settings["start_time"],
                    'retry_count': new_settings["retry_count"],
                    'retry_delay': new_settings["retry_delay"],
                    'timeout': new_settings["timeout"],
                    'preserve_timestamps': new_settings["preserve_timestamps"],
                    'create_target_dirs': new_settings["create_target_dirs"],
                    'poll_interval': new_settings["poll_interval"],
                    'monitored_file_types': new_settings["monitored_file_types"],
                    'recursive_monitoring': new_settings["recursive_monitoring"],
                    'monitor_hidden_files': new_settings["monitor_hidden_files"],
                    'monitor_system_files': new_settings["monitor_system_files"]
                })
                
                # Aktualisiere Batch-Jobs
                if hasattr(self.main_window, 'batch_manager'):
                    self.main_window.batch_manager.jobs = new_settings["batch_jobs"]
                
                # Speichere Einstellungen in Datei
                self.main_window.settings_manager.save_settings()
                
        except Exception as e:
            self.main_window.logger.error(f"Fehler beim Anwenden der erweiterten Einstellungen: {e}", exc_info=True)

    def _apply_logging_settings(self, dialog):
        """Wendet die Logging-Einstellungen an."""
        try:
            # Hole Referenz zum Protokoll-Widget
            log_widget = self.main_window.log_section.log_text
            
            # Setze Log-Level Filter
            log_widget.visible_levels = set()
            if dialog.show_debug.isChecked():
                log_widget.visible_levels.add(logging.DEBUG)
            if dialog.show_info.isChecked():
                log_widget.visible_levels.add(logging.INFO)
            if dialog.show_warning.isChecked():
                log_widget.visible_levels.add(logging.WARNING)
            if dialog.show_error.isChecked():
                log_widget.visible_levels.add(logging.ERROR)
                
            # Setze Anzeigeoptionen
            log_widget.max_entries = dialog.max_entries.value()
            log_widget.date_format = dialog.timestamp_format.currentText()
            log_widget.auto_scroll = dialog.auto_scroll.isChecked()
            log_widget.group_messages = dialog.group_messages.isChecked()
            log_widget.show_line_numbers = dialog.show_line_numbers.isChecked()
            
            # Aktualisiere die Anzeige
            log_widget.refresh_display()
            
            # Speichere Einstellungen
            settings = self.main_window.settings_manager
            settings.set('logging.levels.debug', dialog.show_debug.isChecked())
            settings.set('logging.levels.info', dialog.show_info.isChecked())
            settings.set('logging.levels.warning', dialog.show_warning.isChecked())
            settings.set('logging.levels.error', dialog.show_error.isChecked())
            settings.set('logging.max_entries', dialog.max_entries.value())
            settings.set('logging.timestamp_format', dialog.timestamp_format.currentText())
            settings.set('logging.auto_scroll', dialog.auto_scroll.isChecked())
            settings.set('logging.group_messages', dialog.group_messages.isChecked())
            settings.set('logging.show_line_numbers', dialog.show_line_numbers.isChecked())
            
            self.main_window.logger.info("Protokollierungseinstellungen aktualisiert")
            
        except Exception as e:
            self.main_window.logger.error(f"Fehler beim Anwenden der Protokollierungseinstellungen: {e}")
            
    def _load_logging_settings(self, dialog):
        """Lädt die Logging-Einstellungen in den Dialog."""
        try:
            settings = self.main_window.settings_manager
            
            # Lade Log-Level Einstellungen
            dialog.show_debug.setChecked(settings.get('logging.levels.debug', False))
            dialog.show_info.setChecked(settings.get('logging.levels.info', True))
            dialog.show_warning.setChecked(settings.get('logging.levels.warning', True))
            dialog.show_error.setChecked(settings.get('logging.levels.error', True))
            
            # Lade Anzeigeoptionen
            dialog.max_entries.setValue(settings.get('logging.max_entries', 1000))
            
            timestamp_format = settings.get('logging.timestamp_format', 'HH:mm:ss')
            index = dialog.timestamp_format.findText(timestamp_format)
            if index >= 0:
                dialog.timestamp_format.setCurrentIndex(index)
                
            dialog.auto_scroll.setChecked(settings.get('logging.auto_scroll', True))
            dialog.group_messages.setChecked(settings.get('logging.group_messages', False))
            dialog.show_line_numbers.setChecked(settings.get('logging.show_line_numbers', False))
            
        except Exception as e:
            self.main_window.logger.error(f"Fehler beim Laden der Protokollierungseinstellungen: {e}")
