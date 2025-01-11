#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QPushButton, QTabWidget, QWidget, QComboBox,
    QCheckBox, QTimeEdit, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, QTime

from ui.dialogs.batch_job_dialog import BatchJobDialog

class AdvancedSettingsDialog(QDialog):
    def __init__(self, parent=None, settings=None, drives=None, file_types=None):
        super().__init__(parent)
        self.settings = settings or {}
        self.drives = drives or []
        self.file_types = file_types or []
        self.batch_jobs = []
        self.setup_ui()
        
    def setup_ui(self):
        """Erstellt die UI-Elemente."""
        self.setWindowTitle("Erweiterte Einstellungen")
        self.setMinimumWidth(500)
        layout = QVBoxLayout(self)
        
        # Tabs
        tab_widget = QTabWidget()
        tab_widget.addTab(self.create_copy_tab(), "Kopieren")
        tab_widget.addTab(self.create_automation_tab(), "Automatisierung")
        tab_widget.addTab(self.create_logging_tab(), "Logging")
        layout.addWidget(tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Speichern")
        cancel_button = QPushButton("Abbrechen")
        save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
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
        """Erstellt den Tab für Logging-Einstellungen."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        # Existierende Logging-Einstellungen hier...
        return widget
        
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
            
    def get_settings(self):
        """Gibt die aktuellen Einstellungen zurück."""
        mode_map = {0: "none", 1: "quick", 2: "md5", 3: "sha1"}
        return {
            "buffer_size": self.buffer_size.value(),
            "parallel_copies": self.parallel_copies.value(),
            "verify_mode": mode_map[self.verify_mode.currentIndex()],
            "auto_start": self.auto_start.isChecked(),
            "schedule_enable": self.schedule_enable.isChecked(),
            "start_time": self.start_time.time().toString("HH:mm"),
            "batch_jobs": self.batch_jobs
        }
