#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QPushButton, QTabWidget, QWidget, QComboBox,
    QCheckBox, QTimeEdit, QListWidget, QListWidgetItem,
    QGroupBox, QLineEdit, QDesktopWidget
)
from PyQt5.QtCore import Qt, QTime, QDateTime
from PyQt5.QtGui import QIcon
import os

from ui.style_helper import StyleHelper
from ui.dialogs.batch_job_dialog import BatchJobDialog
from ui.widgets.plugin_manager import PluginManager

class AdvancedSettingsDialog(QDialog):
    def __init__(self, parent=None, settings=None, drives=None, file_types=None):
        super().__init__(parent)
        self.settings = settings or {}
        self.drives = drives or []
        self.file_types = file_types or []
        self.batch_jobs = []
        self.setup_ui()
        self.center_and_resize()
        
    def center_and_resize(self):
        """Zentriert das Fenster und setzt die Größe."""
        desktop = QDesktopWidget().availableGeometry()
        width = int(desktop.width() * 0.7)  # 70% der Bildschirmbreite
        height = int(desktop.height() * 0.8)  # 80% der Bildschirmhöhe
        self.resize(width, height)
        
        # Zentriere das Fenster
        frame_geometry = self.frameGeometry()
        center_point = desktop.center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())
        
    def setup_ui(self):
        """Erstellt die UI-Elemente."""
        self.setWindowTitle("Erweiterte Einstellungen")
        layout = QVBoxLayout(self)
        
        # Tabs
        tab_widget = QTabWidget()
        tab_widget.addTab(self.create_copy_tab(), "Kopieren")
        tab_widget.addTab(self.create_monitoring_tab(), "Überwachung")
        tab_widget.addTab(self.create_automation_tab(), "Automatisierung")
        tab_widget.addTab(self.create_logging_tab(), "Logging")
        tab_widget.addTab(self._create_rename_tab(), "Batch-Rename")
        tab_widget.addTab(self.create_plugins_tab(), "Plugins")
        layout.addWidget(tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Speichern")
        cancel_button = QPushButton("Abbrechen")
        save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        # Styling für die Buttons
        for button in [save_button, cancel_button]:
            button.setMinimumWidth(120)
            button.setMinimumHeight(32)
        
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)
        
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #495057;
                border: 1px solid #ced4da;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        layout.addLayout(button_layout)
        
    def create_copy_tab(self):
        """Erstellt den Tab für Kopiereinstellungen."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Puffergröße
        buffer_layout = QHBoxLayout()
        buffer_layout.addWidget(QLabel("Puffergröße:"))
        self.buffer_size = QSpinBox()
        self.buffer_size.setRange(1, 1024)
        self.buffer_size.setValue(self.settings.get("buffer_size", 64))
        self.buffer_size.setSuffix(" MB")
        buffer_layout.addWidget(self.buffer_size)
        buffer_layout.addStretch()
        layout.addLayout(buffer_layout)
        
        # Chunk-Größe
        chunk_layout = QHBoxLayout()
        chunk_layout.addWidget(QLabel("Chunk-Größe:"))
        self.chunk_size = QSpinBox()
        self.chunk_size.setRange(1, 64)
        self.chunk_size.setValue(self.settings.get("chunk_size", 8))
        self.chunk_size.setSuffix(" KB")
        chunk_layout.addWidget(self.chunk_size)
        chunk_layout.addStretch()
        layout.addLayout(chunk_layout)
        
        # Parallele Kopien
        parallel_layout = QHBoxLayout()
        parallel_layout.addWidget(QLabel("Gleichzeitige Kopien:"))
        self.parallel_copies = QSpinBox()
        self.parallel_copies.setRange(1, 8)
        self.parallel_copies.setValue(self.settings.get("parallel_copies", 2))
        parallel_layout.addWidget(self.parallel_copies)
        parallel_layout.addStretch()
        layout.addLayout(parallel_layout)
        
        # Verifizierungsmodus
        verify_layout = QHBoxLayout()
        verify_layout.addWidget(QLabel("Überprüfungsmodus:"))
        self.verify_mode = QComboBox()
        self.verify_mode.addItems(["Keine", "Schnell (Größe)", "MD5", "SHA1"])
        current_mode = self.settings.get("verify_mode", "none")
        mode_index = {"none": 0, "quick": 1, "md5": 2, "sha1": 3}.get(current_mode, 0)
        self.verify_mode.setCurrentIndex(mode_index)
        verify_layout.addWidget(self.verify_mode)
        verify_layout.addStretch()
        layout.addLayout(verify_layout)
        
        # Fehlerbehandlung
        error_layout = QHBoxLayout()
        error_layout.addWidget(QLabel("Wiederholungsversuche:"))
        self.retry_count = QSpinBox()
        self.retry_count.setRange(0, 10)
        self.retry_count.setValue(self.settings.get("retry_count", 3))
        error_layout.addWidget(self.retry_count)
        
        error_layout.addWidget(QLabel("Verzögerung:"))
        self.retry_delay = QSpinBox()
        self.retry_delay.setRange(1, 60)
        self.retry_delay.setValue(self.settings.get("retry_delay", 1))
        self.retry_delay.setSuffix(" s")
        error_layout.addWidget(self.retry_delay)
        error_layout.addStretch()
        layout.addLayout(error_layout)
        
        # Timeout
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel("Timeout:"))
        self.timeout = QSpinBox()
        self.timeout.setRange(5, 300)
        self.timeout.setValue(self.settings.get("timeout", 30))
        self.timeout.setSuffix(" s")
        timeout_layout.addWidget(self.timeout)
        timeout_layout.addStretch()
        layout.addLayout(timeout_layout)
        
        # Checkboxen für zusätzliche Optionen
        self.preserve_timestamps = QCheckBox("Zeitstempel beibehalten")
        self.preserve_timestamps.setChecked(self.settings.get("preserve_timestamps", True))
        layout.addWidget(self.preserve_timestamps)
        
        self.create_target_dirs = QCheckBox("Zielverzeichnisse automatisch erstellen")
        self.create_target_dirs.setChecked(self.settings.get("create_target_dirs", True))
        layout.addWidget(self.create_target_dirs)
        
        layout.addStretch()
        return widget
        
    def create_automation_tab(self):
        """Erstellt den Tab für Automatisierung."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Auto-Start
        self.auto_start = QCheckBox("Automatisch starten bei Laufwerksanschluss")
        self.auto_start.setChecked(self.settings.get("auto_start", False))
        layout.addWidget(self.auto_start)
        
        # Zeitgesteuerte Übertragung
        schedule_group = QVBoxLayout()
        self.schedule_enable = QCheckBox("Zeitgesteuerte Übertragung aktivieren")
        self.schedule_enable.setChecked(self.settings.get("schedule_enable", False))
        schedule_group.addWidget(self.schedule_enable)
        
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Startzeit:"))
        self.start_time = QTimeEdit()
        self.start_time.setTime(QTime.fromString(self.settings.get("start_time", "22:00"), "HH:mm"))
        time_layout.addWidget(self.start_time)
        time_layout.addStretch()
        schedule_group.addLayout(time_layout)
        layout.addLayout(schedule_group)
        
        # Batch-Verarbeitung
        layout.addWidget(QLabel("Batch-Verarbeitung:"))
        self.batch_list = QListWidget()
        self.batch_list.setMinimumHeight(150)
        layout.addWidget(self.batch_list)
        
        batch_buttons = QHBoxLayout()
        add_button = QPushButton("Hinzufügen")
        remove_button = QPushButton("Entfernen")
        up_button = QPushButton("↑")
        down_button = QPushButton("↓")
        
        add_button.clicked.connect(self.add_batch_job)
        remove_button.clicked.connect(self.remove_batch_job)
        up_button.clicked.connect(lambda: self.move_batch_job(-1))
        down_button.clicked.connect(lambda: self.move_batch_job(1))
        
        batch_buttons.addWidget(add_button)
        batch_buttons.addWidget(remove_button)
        batch_buttons.addWidget(up_button)
        batch_buttons.addWidget(down_button)
        batch_buttons.addStretch()
        layout.addLayout(batch_buttons)
        
        return widget
        
    def create_logging_tab(self):
        """Erstellt den Tab für Protokollierungseinstellungen."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        
        # Gruppe für Log-Level Filter
        level_group = QGroupBox("Log-Level Filter")
        level_layout = QVBoxLayout()
        
        # Checkboxen für verschiedene Log-Level
        self.show_debug = QCheckBox("Debug-Meldungen anzeigen")
        self.show_info = QCheckBox("Info-Meldungen anzeigen")
        self.show_warning = QCheckBox("Warnungen anzeigen")
        self.show_error = QCheckBox("Fehlermeldungen anzeigen")
        
        # Standardmäßig alle aktiviert außer Debug
        self.show_info.setChecked(True)
        self.show_warning.setChecked(True)
        self.show_error.setChecked(True)
        
        level_layout.addWidget(self.show_debug)
        level_layout.addWidget(self.show_info)
        level_layout.addWidget(self.show_warning)
        level_layout.addWidget(self.show_error)
        level_group.setLayout(level_layout)
        
        # Gruppe für Anzeigeoptionen
        display_group = QGroupBox("Anzeigeoptionen")
        display_layout = QVBoxLayout()
        
        # Maximale Anzahl der Einträge
        max_entries_layout = QHBoxLayout()
        max_entries_label = QLabel("Maximale Anzahl Einträge:")
        self.max_entries = QSpinBox()
        self.max_entries.setRange(100, 10000)
        self.max_entries.setValue(1000)
        self.max_entries.setSingleStep(100)
        max_entries_layout.addWidget(max_entries_label)
        max_entries_layout.addWidget(self.max_entries)
        max_entries_layout.addStretch()
        
        # Zeitstempelformat
        timestamp_layout = QHBoxLayout()
        timestamp_label = QLabel("Zeitstempelformat:")
        self.timestamp_format = QComboBox()
        self.timestamp_format.addItems([
            "HH:mm:ss",
            "HH:mm:ss.zzz",
            "dd.MM.yyyy HH:mm:ss",
            "yyyy-MM-dd HH:mm:ss"
        ])
        timestamp_layout.addWidget(timestamp_label)
        timestamp_layout.addWidget(self.timestamp_format)
        timestamp_layout.addStretch()
        
        # Weitere Optionen
        self.auto_scroll = QCheckBox("Automatisch zum Ende scrollen")
        self.auto_scroll.setChecked(True)
        self.group_messages = QCheckBox("Ähnliche Meldungen gruppieren")
        self.show_line_numbers = QCheckBox("Zeilennummern anzeigen")
        
        display_layout.addLayout(max_entries_layout)
        display_layout.addLayout(timestamp_layout)
        display_layout.addWidget(self.auto_scroll)
        display_layout.addWidget(self.group_messages)
        display_layout.addWidget(self.show_line_numbers)
        display_group.setLayout(display_layout)
        
        # Füge Gruppen zum Layout hinzu
        layout.addWidget(level_group)
        layout.addWidget(display_group)
        layout.addStretch()
        
        return tab
        
    def create_monitoring_tab(self):
        """Erstellt den Tab für Überwachungseinstellungen."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Überwachungsintervall
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Aktualisierungsintervall:"))
        self.poll_interval = QSpinBox()
        self.poll_interval.setRange(1, 60)
        self.poll_interval.setValue(self.settings.get("poll_interval", 5))
        self.poll_interval.setSuffix(" s")
        interval_layout.addWidget(self.poll_interval)
        interval_layout.addStretch()
        layout.addLayout(interval_layout)
        
        # Dateityp-Filter
        layout.addWidget(QLabel("Überwachte Dateitypen:"))
        self.file_type_list = QListWidget()
        self.file_type_list.setMinimumHeight(100)
        
        # Fülle die Liste mit den aktuellen Dateitypen
        monitored_types = self.settings.get("monitored_file_types", [".mp4", ".mov", ".avi"])
        for file_type in monitored_types:
            self.file_type_list.addItem(file_type)
            
        layout.addWidget(self.file_type_list)
        
        # Buttons für Dateitypen
        type_buttons = QHBoxLayout()
        add_type = QPushButton("Hinzufügen")
        remove_type = QPushButton("Entfernen")
        
        add_type.clicked.connect(self.add_file_type)
        remove_type.clicked.connect(self.remove_file_type)
        
        type_buttons.addWidget(add_type)
        type_buttons.addWidget(remove_type)
        type_buttons.addStretch()
        layout.addLayout(type_buttons)
        
        # Erweiterte Überwachungsoptionen
        self.recursive_monitoring = QCheckBox("Rekursive Überwachung (Unterordner einschließen)")
        self.recursive_monitoring.setChecked(self.settings.get("recursive_monitoring", True))
        layout.addWidget(self.recursive_monitoring)
        
        self.hidden_files = QCheckBox("Versteckte Dateien überwachen")
        self.hidden_files.setChecked(self.settings.get("monitor_hidden_files", False))
        layout.addWidget(self.hidden_files)
        
        self.system_files = QCheckBox("Systemdateien überwachen")
        self.system_files.setChecked(self.settings.get("monitor_system_files", False))
        layout.addWidget(self.system_files)
        
        layout.addStretch()
        return widget
        
    def _create_rename_tab(self):
        """Erstellt den Tab für Batch-Rename Einstellungen."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        
        # Gruppe für Umbenennungsmuster
        pattern_group = QGroupBox("Umbenennungsmuster")
        pattern_layout = QVBoxLayout()
        
        # Muster-Eingabe
        pattern_label = QLabel("Muster:")
        self.rename_pattern = QLineEdit()
        self.rename_pattern.setPlaceholderText("z.B. {date}_{counter}_{original}")
        pattern_layout.addWidget(pattern_label)
        pattern_layout.addWidget(self.rename_pattern)
        
        # Verfügbare Variablen
        variables_label = QLabel("Verfügbare Variablen:")
        variables_text = QLabel(
            "{date} - Aktuelles Datum\n"
            "{time} - Aktuelle Zeit\n"
            "{counter} - Fortlaufende Nummer\n"
            "{original} - Originaler Dateiname\n"
            "{ext} - Dateierweiterung\n"
            "{type} - Dateityp (Bild, Video, etc.)\n"
            "{camera} - Kameramodell (wenn verfügbar)\n"
            "{created} - Erstellungsdatum"
        )
        variables_text.setStyleSheet("color: #666;")
        pattern_layout.addWidget(variables_label)
        pattern_layout.addWidget(variables_text)
        pattern_group.setLayout(pattern_layout)
        
        # Gruppe für Optionen
        options_group = QGroupBox("Optionen")
        options_layout = QVBoxLayout()
        
        # Zähler-Einstellungen
        counter_layout = QHBoxLayout()
        counter_label = QLabel("Startnummer:")
        self.counter_start = QSpinBox()
        self.counter_start.setRange(0, 999999)
        self.counter_digits = QSpinBox()
        self.counter_digits.setRange(1, 6)
        self.counter_digits.setValue(3)
        digits_label = QLabel("Stellen:")
        counter_layout.addWidget(counter_label)
        counter_layout.addWidget(self.counter_start)
        counter_layout.addWidget(digits_label)
        counter_layout.addWidget(self.counter_digits)
        counter_layout.addStretch()
        
        # Weitere Optionen
        self.preserve_ext = QCheckBox("Originale Dateierweiterung beibehalten")
        self.preserve_ext.setChecked(True)
        self.lowercase = QCheckBox("Alles in Kleinbuchstaben")
        self.replace_spaces = QCheckBox("Leerzeichen durch Unterstrich ersetzen")
        
        options_layout.addLayout(counter_layout)
        options_layout.addWidget(self.preserve_ext)
        options_layout.addWidget(self.lowercase)
        options_layout.addWidget(self.replace_spaces)
        options_group.setLayout(options_layout)
        
        # Vorschau
        preview_group = QGroupBox("Vorschau")
        preview_layout = QVBoxLayout()
        self.preview_list = QListWidget()
        preview_layout.addWidget(self.preview_list)
        preview_group.setLayout(preview_layout)
        
        # Aktualisiere Vorschau wenn sich Einstellungen ändern
        self.rename_pattern.textChanged.connect(self._update_rename_preview)
        self.counter_start.valueChanged.connect(self._update_rename_preview)
        self.counter_digits.valueChanged.connect(self._update_rename_preview)
        self.preserve_ext.stateChanged.connect(self._update_rename_preview)
        self.lowercase.stateChanged.connect(self._update_rename_preview)
        self.replace_spaces.stateChanged.connect(self._update_rename_preview)
        
        # Layout zusammenbauen
        layout.addWidget(pattern_group)
        layout.addWidget(options_group)
        layout.addWidget(preview_group)
        
        return tab
        
    def _update_rename_preview(self):
        """Aktualisiert die Vorschau der Umbenennungen."""
        self.preview_list.clear()
        
        # Beispieldateien
        examples = [
            "IMG_20240118_123456.jpg",
            "Video_001.mp4",
            "Dokument mit Leerzeichen.pdf",
            "DSC00123.NEF"
        ]
        
        pattern = self.rename_pattern.text()
        counter = self.counter_start.value()
        digits = self.counter_digits.value()
        
        for original in examples:
            name, ext = os.path.splitext(original)
            if self.preserve_ext.isChecked():
                ext = ext
            
            # Ersetze Variablen
            new_name = pattern.replace("{original}", name)
            new_name = new_name.replace("{ext}", ext.lstrip('.'))
            new_name = new_name.replace("{counter}", str(counter).zfill(digits))
            new_name = new_name.replace("{date}", QDateTime.currentDateTime().toString("yyyyMMdd"))
            new_name = new_name.replace("{time}", QDateTime.currentDateTime().toString("HHmmss"))
            
            if self.lowercase.isChecked():
                new_name = new_name.lower()
            if self.replace_spaces.isChecked():
                new_name = new_name.replace(" ", "_")
                
            # Füge Erweiterung hinzu
            if self.preserve_ext.isChecked():
                new_name += ext
                
            # Zeige Original -> Neu
            self.preview_list.addItem(f"{original} → {new_name}")
            counter += 1
            
    def add_batch_job(self):
        """Öffnet den Dialog zum Hinzufügen eines Batch-Jobs."""
        dialog = BatchJobDialog(self, self.drives, self.file_types)
        if dialog.exec_():
            job_data = dialog.get_job_data()
            item = QListWidgetItem(
                f"{job_data['source_drive']} -> {job_data['target_path']} ({job_data['file_type']})"
            )
            item.setData(Qt.UserRole, job_data)
            self.batch_list.addItem(item)
            self.batch_jobs.append(job_data)
            
    def remove_batch_job(self):
        """Entfernt den ausgewählten Batch-Job."""
        current = self.batch_list.currentRow()
        if current >= 0:
            self.batch_list.takeItem(current)
            self.batch_jobs.pop(current)
            
    def move_batch_job(self, direction):
        """Verschiebt einen Batch-Job nach oben oder unten."""
        current = self.batch_list.currentRow()
        if current < 0:
            return
            
        new_pos = current + direction
        if 0 <= new_pos < self.batch_list.count():
            item = self.batch_list.takeItem(current)
            self.batch_list.insertItem(new_pos, item)
            self.batch_list.setCurrentRow(new_pos)
            
            job = self.batch_jobs.pop(current)
            self.batch_jobs.insert(new_pos, job)
            
    def add_file_type(self):
        """Fügt einen neuen Dateityp zur Liste hinzu."""
        from PyQt5.QtWidgets import QInputDialog
        file_type, ok = QInputDialog.getText(self, "Dateityp hinzufügen", 
                                           "Dateityp (z.B. .mp4):")
        if ok and file_type:
            if not file_type.startswith('.'):
                file_type = '.' + file_type
            self.file_type_list.addItem(file_type.lower())
            
    def remove_file_type(self):
        """Entfernt den ausgewählten Dateityp aus der Liste."""
        current = self.file_type_list.currentRow()
        if current >= 0:
            self.file_type_list.takeItem(current)
            
    def get_settings(self):
        """Gibt die aktuellen Einstellungen zurück."""
        mode_map = {0: "none", 1: "quick", 2: "md5", 3: "sha1"}
        
        # Sammle alle Dateitypen
        monitored_types = []
        for i in range(self.file_type_list.count()):
            monitored_types.append(self.file_type_list.item(i).text())
            
        return {
            "buffer_size": self.buffer_size.value(),
            "chunk_size": self.chunk_size.value(),
            "parallel_copies": self.parallel_copies.value(),
            "verify_mode": mode_map[self.verify_mode.currentIndex()],
            "retry_count": self.retry_count.value(),
            "retry_delay": self.retry_delay.value(),
            "timeout": self.timeout.value(),
            "preserve_timestamps": self.preserve_timestamps.isChecked(),
            "create_target_dirs": self.create_target_dirs.isChecked(),
            "auto_start": self.auto_start.isChecked(),
            "schedule_enable": self.schedule_enable.isChecked(),
            "start_time": self.start_time.time().toString("HH:mm"),
            "batch_jobs": self.batch_jobs,
            "poll_interval": self.poll_interval.value(),
            "monitored_file_types": monitored_types,
            "recursive_monitoring": self.recursive_monitoring.isChecked(),
            "monitor_hidden_files": self.hidden_files.isChecked(),
            "monitor_system_files": self.system_files.isChecked()
        }

    def show_dialog(self):
        """Zeigt den Dialog an und führt die Aktion aus."""
        # Lade aktuelle Einstellungen
        self.settings_handlers._load_copy_settings(self)
        self.settings_handlers._load_monitoring_settings(self)
        self.settings_handlers._load_logging_settings(self)
        
        if self.exec_() == QDialog.Accepted:
            # Wende Einstellungen an
            self.settings_handlers._apply_copy_settings(self)
            self.settings_handlers._apply_monitoring_settings(self)
            self.settings_handlers._apply_logging_settings(self)
            return True
            
        return False

    def create_plugins_tab(self):
        """Erstellt den Plugins-Tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Beschreibung
        description = QLabel(
            "Hier können Sie Plugins verwalten, die die Funktionalität des Tools erweitern. "
            "Installieren Sie neue Plugins oder verwalten Sie bestehende."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #666; margin-bottom: 20px;")
        layout.addWidget(description)
        
        # Plugin-Manager
        plugin_manager = PluginManager()
        layout.addWidget(plugin_manager)
        
        return tab
