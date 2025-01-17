#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hauptfenster der Anwendung.
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, Optional, List, Tuple
import time
from datetime import timedelta

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QLineEdit,
    QComboBox, QCheckBox, QMessageBox, QFileDialog,
    QGroupBox, QSpacerItem, QSizePolicy,
    QDialog, QListWidgetItem, QShortcut, QSplitter
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QTimer, QMetaObject
from PyQt5.QtGui import QIcon, QFont, QKeySequence

from ui.style_helper import StyleHelper
from ui.dialogs.settings_dialog import SettingsDialog
from ui.widgets.drive_list import DriveList
from config.constants import (
    EINSTELLUNGEN_DATEI, STANDARD_DATEITYPEN,
    VERFUEGBARE_SPRACHEN, TRANSLATIONS_VERZEICHNIS
)

from utils.i18n import I18n
from utils.settings import SettingsManager
from utils.logging_widgets import QTextEditLogger
from utils.file_system_helper import FileSystemHelper

from core.drive_controller import DriveController
from core.transfer.transfer_coordinator import TransferCoordinator
from core.transfer.manager import Manager
from core.transfer.priority import TransferPriority
from core.scheduler import TransferScheduler
from core.batch_manager import BatchManager
from core.file_watcher_manager import FileWatcherManager

from ui.handlers.transfer_handlers import TransferHandlers
from ui.handlers.settings_handlers import SettingsHandlers
from ui.handlers.drive_handlers import DriveHandlers
from ui.handlers.ui_handlers import UIHandlers
from ui.handlers.event_handlers import EventHandlers
from ui.handlers.drive_event_handlers import DriveEventHandlers
from ui.handlers.transfer_event_handlers import TransferEventHandlers
from ui.layouts.main_layout import MainLayout
from ui.widgets import (
    CustomButton, CustomListWidget, DriveWidget,
    ModernTransferWidget
)
from ui.widgets.modern_transfer_widget import TransferStatus, TransferItemData
from ui.theme_manager import ThemeManager

# Logger konfigurieren
logger = logging.getLogger(__name__)

class ShutdownThread(QThread):
    """Thread zum sauberen Beenden der Anwendung."""
    
    finished = pyqtSignal()  # Signal wenn fertig
    save_settings = pyqtSignal()  # Signal zum Speichern der Einstellungen
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.logger = logging.getLogger(__name__)
        
    def run(self):
        """Führt den Shutdown-Prozess durch."""
        try:
            self.logger.info("Beginne Shutdown-Prozess...")
            
            # Speichere Einstellungen im Hauptthread
            self.save_settings.emit()
            QThread.msleep(100)  # Warte kurz auf Speicherung
            
            # Stoppe Drive Controller
            if hasattr(self.main_window, 'drive_controller'):
                self.main_window.drive_controller.stop_monitoring()
                self.logger.info("Drive Controller gestoppt")
            
            # Stoppe File Watcher
            if hasattr(self.main_window, 'file_watcher_manager'):
                self.main_window.file_watcher_manager.stop()
                self.logger.info("File Watcher Manager gestoppt")
            
            # Stoppe Transfer Coordinator
            if hasattr(self.main_window, 'transfer_coordinator'):
                self.main_window.transfer_coordinator.stop()
                self.logger.info("Transfer Coordinator gestoppt")
            
            # Warte auf Thread-Beendigung
            QThread.msleep(200)
            
            self.logger.info("Shutdown-Prozess abgeschlossen")
            self.finished.emit()
            
        except Exception as e:
            self.logger.error(f"Fehler im Shutdown-Thread: {e}", exc_info=True)
            self.finished.emit()

class MainWindow(QMainWindow):
    """Hauptfenster der Anwendung."""
    
    def __init__(self, app):
        """Initialisiert das Hauptfenster."""
        super().__init__()
        
        # Speichere die App-Referenz
        self.app = app
        
        # Setze das Programm-Icon
        self.setWindowIcon(QIcon("C:/Users/Shadow-PC/CascadeProjects/Ingest-Tool/ressourcen/icon.png"))
        
        # Initialisiere den Logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        
        # Theme Manager initialisieren
        self.theme_manager = ThemeManager()
        # Wende Theme auf die gesamte Anwendung an
        self.app.setStyleSheet(self.theme_manager.get_stylesheet())
        
        # Setze initiale Fenstergröße
        self.resize(1440, 1000)  # Erhöht um 100 Pixel in der Höhe (von 900 auf 1000)
        self.setMinimumSize(1200, 1000)
        
        # Flag für erstes Anzeigen
        self._first_show = True
        
        # Initialisiere Attribute
        self.drive_items = {}
        self.is_watching = False
        self.excluded_drives = []  # Liste der ausgeschlossenen Laufwerke
        self.active_copies = {}  # Dictionary für aktive Kopiervorgänge
        self.transfers = {}  # Dictionary für Transfer-Status
        
        # Initialisiere UI-Elemente
        self.drives_list = DriveList()
        self.filtered_drives_list = DriveList()  # Verwende DriveList statt QListWidget
        self.mappings_list = QListWidget()
        self.excluded_list = QListWidget()
        self.filetype_combo = QComboBox()
        self.filetype_combo.setPlaceholderText("Bitte auswählen")
        self.filetype_combo.setMaxVisibleItems(15)
        self.filetype_combo.setMinimumWidth(150)
        StyleHelper.style_combobox(self.filetype_combo)
        self.target_path_edit = QLineEdit()
        self.browse_button = QPushButton("📂")
        
        # Progress Widget initialisieren
        self.transfer_widget = ModernTransferWidget(self)
        
        # Start Button
        self.start_button = QPushButton("▶️ Start")
        self.start_button.setStyleSheet("""
            QPushButton { 
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        
        # Cancel Button
        self.cancel_button = QPushButton("⏹️ Stop")
        self.cancel_button.setStyleSheet("""
            QPushButton { 
                background-color: #f44336;
                color: white;
                border: none;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        
        # Abort Button
        self.abort_button = QPushButton("Transfer abbrechen")
        self.abort_button.setStyleSheet("""
            QPushButton { 
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
            }
        """)
        self.abort_button.setEnabled(False)
        
        # Andere Buttons
        self.add_mapping_button = QPushButton("➕ Hinzufügen")
        self.remove_mapping_button = QPushButton("🗑️ Entfernen")
        self.add_excluded_button = QPushButton("🚫 Ausschließen")
        self.remove_excluded_button = QPushButton("✅ Entfernen")
        self.exclude_all_button = QPushButton("⛔ Alle ausschließen")
        self.auto_start_checkbox = QCheckBox("🔄 Automatisch starten")
        
        # Button Styles
        button_style = f"""
            QPushButton {{
                background-color: {StyleHelper.SURFACE};
                color: {StyleHelper.TEXT};
                border: 1px solid {StyleHelper.BORDER};
                border-radius: 3px;
                padding: 5px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {StyleHelper.SURFACE_LIGHT};
            }}
        """
        
        self.add_mapping_button.setStyleSheet(button_style)
        self.remove_mapping_button.setStyleSheet(button_style)
        self.add_excluded_button.setStyleSheet(button_style)
        self.remove_excluded_button.setStyleSheet(button_style)
        self.exclude_all_button.setStyleSheet(button_style)
        
        # Initialisiere Manager und Controller
        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.load_settings()
        self.i18n = I18n(TRANSLATIONS_VERZEICHNIS)
        
        # Initialisiere Handler
        self.ui_handlers = UIHandlers(self)
        self.transfer_handlers = TransferHandlers(self)
        self.settings_handlers = SettingsHandlers(self)
        self.drive_handlers = DriveHandlers(self)
        self.event_handlers = EventHandlers(self)
        self.drive_event_handlers = DriveEventHandlers(self)
        self.transfer_event_handlers = TransferEventHandlers(self)
        
        # Verbinde UI-Signale
        self.event_handlers.connect_signals()
        
        # Initialisiere TransferCoordinator
        self.transfer_settings = {
            'max_workers': 4,
            'chunk_size': 8192,
            'buffer_size': 65536,
            'retry_count': 3,
            'retry_delay': 1.0,
            'timeout': 30.0
        }
        self.transfer_coordinator = TransferCoordinator(self.transfer_settings)
        
        # Verbinde TransferCoordinator Signale mit dem Widget
        self.logger.debug("Verbinde TransferCoordinator Signale mit dem Widget")
        
        # Verbinde Signale direkt mit Qt.DirectConnection um sicherzustellen, dass sie sofort verarbeitet werden
        self.transfer_coordinator.transfer_started.connect(
            self.transfer_widget.on_transfer_started,
            type=Qt.DirectConnection
        )
        self.transfer_coordinator.transfer_progress.connect(
            self.transfer_widget.on_transfer_progress,
            type=Qt.DirectConnection
        )
        self.transfer_coordinator.transfer_completed.connect(
            self.transfer_widget.on_transfer_completed,
            type=Qt.DirectConnection
        )
        self.transfer_coordinator.transfer_error.connect(
            self.transfer_widget.on_transfer_error,
            type=Qt.DirectConnection
        )
        self.transfer_coordinator.transfer_paused.connect(
            self.transfer_widget.on_transfer_paused,
            type=Qt.DirectConnection
        )
        self.transfer_coordinator.transfer_resumed.connect(
            self.transfer_widget.on_transfer_resumed,
            type=Qt.DirectConnection
        )
        self.transfer_coordinator.transfer_cancelled.connect(
            self.transfer_widget.on_transfer_cancelled,
            type=Qt.DirectConnection
        )
        
        # Verbinde Widget Signale mit dem Coordinator
        self.transfer_widget.request_retry.connect(
            self.transfer_coordinator.retry_transfer,
            type=Qt.DirectConnection
        )
        self.transfer_widget.request_cancel.connect(
            self.transfer_coordinator.cancel_transfer,
            type=Qt.DirectConnection
        )
        self.transfer_widget.request_pause.connect(
            self.transfer_coordinator.pause_transfer,
            type=Qt.DirectConnection
        )
        self.transfer_widget.request_resume.connect(
            self.transfer_coordinator.resume_transfer,
            type=Qt.DirectConnection
        )
        
        # Initialisiere FileWatcherManager
        self.file_watcher_manager = FileWatcherManager(self)  # Übergebe self als main_window
        
        # Verbinde FileWatcherManager Signale mit dem TransferCoordinator
        self.file_watcher_manager.file_found.connect(
            lambda file_path: self._handle_file_found(file_path)
        )
        
        # Initialisiere Controller
        self.drive_controller = DriveController()
        
        # Initialisiere Layout
        self.layout_manager = MainLayout(self)
        self.layout_manager.setup_ui()
        
        # Verbinde Drive-Controller Signale
        self.drive_controller.drive_connected.connect(self.drive_event_handlers.on_drive_connected, Qt.QueuedConnection)
        self.drive_controller.drive_disconnected.connect(self.drive_event_handlers.on_drive_disconnected, Qt.QueuedConnection)
        self.drive_controller.file_found.connect(self.drive_event_handlers.on_file_found, Qt.QueuedConnection)
        
        # Initialisiere Shortcuts
        self.setup_shortcuts()
        
        # Auto-Save Timer
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.save_current_state)
        self.auto_save_timer.start(60000)  # Speichere alle 60 Sekunden
        
        # Lade gespeicherte Einstellungen
        self._load_settings()
        
        # Starte Laufwerksüberwachung
        self.drive_controller.start_monitoring()
        
        # Deaktiviere Abbrechen-Button
        self.cancel_button.setEnabled(False)
        
        # Wende Dark Theme an
        StyleHelper.apply_dark_theme(self)
        
        # Verbinde Signale für die gefilterte Liste
        self.mappings_list.model().rowsInserted.connect(self.update_filtered_drives_list)
        self.mappings_list.model().rowsRemoved.connect(self.update_filtered_drives_list)
        self.excluded_list.model().rowsInserted.connect(self.update_filtered_drives_list)
        self.excluded_list.model().rowsRemoved.connect(self.update_filtered_drives_list)
        
        self._shutdown_thread = None
        self._is_shutting_down = False
        
        # Debug-Logging für Signale
        self.logger.debug("MainWindow initialisiert und Signale verbunden")
        
    def _connect_transfer_signals(self):
        """Verbindet die Transfer-Signale mit den UI-Updates."""
        # Transfer Events vom Coordinator
        self.transfer_coordinator.transfer_started.connect(self._on_transfer_started)
        self.transfer_coordinator.transfer_progress.connect(self._on_transfer_progress)
        self.transfer_coordinator.transfer_completed.connect(self._on_transfer_completed)
        self.transfer_coordinator.transfer_error.connect(self._on_transfer_error)
        
    def _on_transfer_started(self, transfer_id: str):
        """Handler für gestartete Transfers."""
        try:
            status = self.transfer_coordinator.get_transfer_status(transfer_id)
            if status:
                source_drive = os.path.splitdrive(status['source'])[0]
                self.transfer_widget.add_drive(source_drive, f"Laufwerk {source_drive}")
                
                # Initialen Status setzen
                self._on_transfer_progress(
                    transfer_id=transfer_id,
                    total_bytes=status['total_size'],
                    transferred_bytes=0,
                    speed=0.0
                )
        except Exception as e:
            logger.error(f"Fehler beim Verarbeiten des Transfer-Starts: {e}")
            
    def _on_transfer_progress(self, transfer_id: str, total_bytes: int, 
                          transferred_bytes: int, speed: float):
        """Handler für Transfer-Fortschritt."""
        try:
            status = self.transfer_coordinator.get_transfer_status(transfer_id)
            if status:
                source_path = status['source']
                source_drive = os.path.splitdrive(source_path)[0]
                filename = os.path.basename(source_path)
                
                # Berechne Fortschritt
                progress = (transferred_bytes / total_bytes * 100) if total_bytes > 0 else 0
                
                # Aktualisiere UI
                self.transfer_widget.update_transfer(
                    transfer_id=transfer_id,
                    filename=filename,
                    drive=source_drive,
                    progress=progress,
                    speed=speed,
                    total_bytes=total_bytes,
                    transferred_bytes=transferred_bytes,
                    start_time=time.time(),  # Aktuelle Zeit als Fallback
                    eta=status['eta']
                )
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren des Transfer-Fortschritts: {e}")
            
    def _on_transfer_completed(self, transfer_id: str):
        """Handler für abgeschlossene Transfers."""
        try:
            status = self.transfer_coordinator.get_transfer_status(transfer_id)
            if status:
                source_drive = os.path.splitdrive(status['source'])[0]
                self.transfer_widget.remove_transfer(f"{source_drive}:{transfer_id}")
        except Exception as e:
            logger.error(f"Fehler beim Verarbeiten des Transfer-Abschlusses: {e}")
            
    def _on_transfer_error(self, transfer_id: str, error: str):
        """Handler für Transfer-Fehler."""
        try:
            status = self.transfer_coordinator.get_transfer_status(transfer_id)
            if status:
                source_drive = os.path.splitdrive(status['source'])[0]
                self.transfer_widget.remove_transfer(f"{source_drive}:{transfer_id}")
                
            # Zeige Fehlermeldung
            self.show_error("Transfer-Fehler", f"Fehler beim Transfer: {error}")
        except Exception as e:
            logger.error(f"Fehler beim Verarbeiten des Transfer-Fehlers: {e}")
            
    def on_transfer_started(self, transfer_id: str):
        """Handler für gestartete Transfers."""
        try:
            # Initialisiere Transfer-Status
            self.transfers[transfer_id] = {
                'filename': os.path.basename(transfer_id),
                'drive': os.path.splitdrive(transfer_id)[0],
                'progress': 0,
                'speed': 0,
                'total_bytes': 0,
                'transferred_bytes': 0,
                'start_time': time.time(),
                'eta': timedelta.max
            }
            
            # Füge Laufwerk zum Progress Widget hinzu falls noch nicht vorhanden
            drive_letter = self.transfers[transfer_id]['drive'].rstrip('\\').rstrip(':')
            if hasattr(self, 'transfer_widget'):
                if drive_letter not in self.transfer_widget.drive_groups:
                    self.transfer_widget.add_drive(drive_letter, f"Laufwerk {drive_letter}")
                
        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten des Transfer-Starts: {str(e)}")

    def on_transfer_progress(self, transfer_id: str, progress: float, speed: float):
        """Handler für Transfer-Fortschritt."""
        try:
            if transfer_id not in self.transfers:
                return
                
            transfer = self.transfers[transfer_id]
            transfer['progress'] = progress
            transfer['speed'] = speed
            
            # Aktualisiere Bytes-Statistiken
            source = os.path.join(transfer['drive'], transfer['filename'])
            if os.path.exists(source):
                transfer['total_bytes'] = os.path.getsize(source)
                transfer['transferred_bytes'] = int(transfer['total_bytes'] * (progress / 100))
                
                # Berechne ETA basierend auf aktueller Geschwindigkeit
                if speed > 0:
                    remaining_bytes = transfer['total_bytes'] - transfer['transferred_bytes']
                    eta_seconds = remaining_bytes / speed
                    transfer['eta'] = timedelta(seconds=int(eta_seconds))
                else:
                    transfer['eta'] = timedelta.max
                    
            # Aktualisiere Transfer im Progress Widget
            self.transfer_widget.update_transfer(
                transfer_id=transfer_id,
                filename=transfer['filename'],
                drive=transfer['drive'],
                progress=progress / 100,  # Normalisiere auf 0-1
                speed=speed,
                total_bytes=transfer['total_bytes'],
                transferred_bytes=transfer['transferred_bytes'],
                start_time=transfer['start_time'],
                eta=transfer['eta']
            )
            
            # Aktualisiere Laufwerksstatus
            drive_letter = transfer['drive'].rstrip('\\').rstrip(':')
            self.update_drive_status(drive_letter, speed)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren des Fortschritts: {str(e)}", exc_info=True)

    def on_transfer_completed(self, transfer_id: str):
        """Handler für abgeschlossene Transfers."""
        try:
            if transfer_id in self.transfers:
                # Entferne Transfer aus Progress Widget
                self.transfer_widget.remove_transfer(transfer_id)
                
                # Entferne aus Transfer-Status
                del self.transfers[transfer_id]
                
                self.logger.info(f"Transfer abgeschlossen: {transfer_id}")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Abschließen des Transfers: {str(e)}", exc_info=True)

    def on_transfer_error(self, transfer_id: str, error: str):
        """Handler für Transfer-Fehler."""
        try:
            # Zeige Fehlermeldung
            if transfer_id in self.transfers:
                filename = self.transfers[transfer_id]['filename']
                self.show_error("Fehler beim Kopieren", f"Fehler beim Kopieren von {filename}: {error}")
                
                # Entferne fehlgeschlagenen Transfer
                self.transfer_widget.remove_transfer(transfer_id)
                del self.transfers[transfer_id]
            
        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten des Transfer-Fehlers: {str(e)}", exc_info=True)
            
    def _setup_ui(self):
        """Initialisiert die UI-Komponenten."""
        try:
            # Hauptwidget und Layout
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            main_layout = QVBoxLayout(central_widget)
            main_layout.setContentsMargins(10, 10, 10, 10)
            main_layout.setSpacing(10)
            
            # Oberer Bereich: Einstellungen und Steuerung
            top_layout = QHBoxLayout()
            
            # Linke Seite: Laufwerke und Zuordnungen
            left_widget = QWidget()
            left_layout = QVBoxLayout(left_widget)
            left_layout.setContentsMargins(0, 0, 0, 0)
            
            # Laufwerksliste
            drives_group = QGroupBox("Verfügbare Laufwerke")
            drives_group.setStyleSheet(StyleHelper.get_group_box_style())
            drives_layout = QVBoxLayout(drives_group)
            drives_layout.addWidget(self.drives_list)
            left_layout.addWidget(drives_group)
            
            # Zuordnungen
            mappings_group = QGroupBox("Dateizuordnungen")
            mappings_group.setStyleSheet(StyleHelper.get_group_box_style())
            mappings_layout = QVBoxLayout(mappings_group)
            mappings_layout.addWidget(self.mappings_list)
            left_layout.addWidget(mappings_group)
            
            top_layout.addWidget(left_widget)
            
            # Rechte Seite: Fortschritt und Steuerung
            right_widget = QWidget()
            right_layout = QVBoxLayout(right_widget)
            right_layout.setContentsMargins(0, 0, 0, 0)
            
            # Fortschrittsanzeige
            self.transfer_widget.setMinimumHeight(400)
            right_layout.addWidget(self.transfer_widget, stretch=1)
            
            # Steuerungsbuttons
            button_layout = QHBoxLayout()
            button_layout.addWidget(self.start_button)
            button_layout.addWidget(self.cancel_button)
            button_layout.addWidget(self.abort_button)
            right_layout.addLayout(button_layout)
            
            top_layout.addWidget(right_widget, stretch=2)
            
            main_layout.addLayout(top_layout)
            
            # Statusleiste
            status_layout = QHBoxLayout()
            self.status_label = QLabel()
            self.status_label.setStyleSheet("color: white;")
            status_layout.addWidget(self.status_label)
            main_layout.addLayout(status_layout)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Initialisieren der UI: {str(e)}", exc_info=True)
        
    def setup_shortcuts(self):
        """Richtet Tastatur-Shortcuts ein."""
        # Existierende Shortcuts
        QShortcut(QKeySequence("Ctrl+S"), self, self.start_button.click)
        QShortcut(QKeySequence("Ctrl+C"), self, self.cancel_button.click)
        
        # Escape-Taste zum Entfernen von Einträgen
        QShortcut(QKeySequence("Esc"), self.mappings_list, self.event_handlers.on_remove_mapping_clicked)
        QShortcut(QKeySequence("Esc"), self.excluded_list, self.event_handlers.on_remove_excluded_clicked)
        
    def _on_drive_connected(self, drive_letter: str):
        """Handler für neue Laufwerksverbindung."""
        try:
            # Hole ausgeschlossene Laufwerke
            excluded_drives = []
            for i in range(self.excluded_list.count()):
                item = self.excluded_list.item(i)
                drive = item.text().strip()
                if drive:  # Nur nicht-leere Laufwerke hinzufügen
                    excluded_drives.append(drive)
            
            self.logger.debug(f"Ausgeschlossene Laufwerke: {excluded_drives}")
            
            if drive_letter not in excluded_drives:
                # Initialisiere Laufwerksgruppe im Progress Widget
                self.transfer_widget.update_transfer(
                    transfer_id=f"{drive_letter}:init",
                    filename="Initialisierung...",
                    drive=f"Laufwerk {drive_letter}",
                    progress=0,
                    speed=0,
                    total_bytes=0,
                    transferred_bytes=0
                )
                
                # Automatischer Start wenn aktiviert
                if self.auto_start_checkbox.isChecked():
                    self.start_copy(drive_letter)
                
        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten der Laufwerksverbindung: {str(e)}", exc_info=True)

    def _on_drive_disconnected(self, drive_letter):
        """Handler für getrennte Laufwerksverbindung."""
        try:
            # Entferne das Laufwerk aus der Liste
            self.drives_list.remove_drive(drive_letter)
            
            # Stoppe alle Kopiervorgänge von diesem Laufwerk
            affected_tasks = [task_id for task_id, copy in self.active_copies.items()
                             if copy["source_drive"] == drive_letter]
        
            for task_id in affected_tasks:
                self.transfer_coordinator.set_task_error(task_id, "Laufwerk getrennt")
                del self.active_copies[task_id]
                
            logger.warning(f"Laufwerk {drive_letter} wurde getrennt. "
                          f"{len(affected_tasks)} Kopiervorgänge abgebrochen.")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten der Laufwerkstrennung: {str(e)}", exc_info=True)
            
    def update_statistics(self, transfer: dict):
        """Aktualisiert die Statistiken für einen Transfer."""
        try:
            # Statistik-Updates deaktiviert
            pass
            
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren der Statistiken: {str(e)}")
        
    def get_current_settings(self) -> dict:
        """Gibt die aktuellen Einstellungen zurück."""
        return {
            'target_path': self.target_path_edit.text(),
            'auto_start': self.auto_start_checkbox.isChecked(),
            'excluded_paths': [
                self.excluded_list.item(i).text()
                for i in range(self.excluded_list.count())
            ],
            'mappings': self._get_mappings()
        }
        
    def _load_settings(self):
        """Lädt die gespeicherten Einstellungen."""
        try:
            # Lade Einstellungen
            settings = self.settings_manager.load_settings()
            self.logger.debug(f"Lade Einstellungen: {self.settings}")
            
            # Lade Zuordnungen
            if 'mappings' in self.settings:
                for file_type, target in self.settings['mappings'].items():
                    self.logger.debug(f"Zuordnung geladen: {file_type} -> {target}")
                    item = QListWidgetItem(f"{file_type} ➔ {target}")
                    self.mappings_list.addItem(item)
            
            # Lade ausgeschlossene Laufwerke
            self.excluded_drives = []  # Initialisiere Liste
            if 'excluded_drives' in self.settings:
                for drive in self.settings['excluded_drives']:
                    self.logger.debug(f"Ausgeschlossenes Laufwerk geladen: {drive}")
                    self.excluded_drives.append(drive)
                    item = QListWidgetItem(drive)
                    self.excluded_list.addItem(item)
            
            # Verarbeite Zuordnungen
            self._process_mappings()
            
            # Aktualisiere gefilterte Liste
            self.update_filtered_drives_list()
            
            # Speichere Einstellungen
            self.save_settings()
            self.logger.info("Einstellungen erfolgreich geladen")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Einstellungen: {e}", exc_info=True)
            
    def save_settings(self):
        """Speichert die aktuellen Einstellungen."""
        try:
            # Sammle aktuelle Einstellungen
            settings = {
                'mappings': {},
                'excluded_drives': []
            }
            
            # Speichere Zuordnungen
            for i in range(self.mappings_list.count()):
                item = self.mappings_list.item(i)
                text = item.text()
                if "➔" in text:
                    file_type, target = text.split("➔")
                    settings['mappings'][file_type.strip()] = target.strip()
                    
            # Speichere ausgeschlossene Laufwerke
            for i in range(self.excluded_list.count()):
                item = self.excluded_list.item(i)
                settings['excluded_drives'].append(item.text())
                
            # Speichere in Datei
            self.settings_manager.save_settings(settings)
            self.logger.info("Einstellungen gespeichert")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Einstellungen: {e}", exc_info=True)
            
    def closeEvent(self, event):
        """Wird aufgerufen, wenn das Fenster geschlossen wird."""
        try:
            # Stoppe den FileWatcher
            if hasattr(self, 'file_watcher_manager'):
                self.file_watcher_manager.stop()
            
            # Speichere die Einstellungen
            self.save_settings()
            
            # Akzeptiere das Schließen-Event
            event.accept()
            
            # Beende das Programm sauber
            sys.exit(0)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Beenden des Programms: {e}", exc_info=True)
            event.accept()  # Schließe trotzdem
            sys.exit(1)  # Beende mit Fehlercode
            
    def save_current_state(self):
        """Speichert den aktuellen Zustand temporär."""
        try:
            # Sammle Zuordnungen
            mappings = {}
            for i in range(self.mappings_list.count()):
                item = self.mappings_list.item(i)
                text = item.text()
                self.logger.debug(f"Verarbeite Zuordnung: {text}")
                
                # Unterstütze beide Formate: "*.mp4 ➔ Pfad" und ".mp4 -> Pfad"
                if "➔" in text:
                    file_type, target_path = text.split("➔")
                elif " -> " in text:
                    file_type, target_path = text.split(" -> ")
                else:
                    continue
                    
                # Bereinige Dateityp
                file_type = file_type.strip().lower()
                if file_type.startswith("*."):
                    file_type = "." + file_type[2:]  # Wandle "*.mp4" in ".mp4" um
                elif not file_type.startswith("."):
                    file_type = "." + file_type  # Stelle sicher, dass der Dateityp mit . beginnt
                    
                target_path = target_path.strip()
                
                # Füge nur gültige Zuordnungen hinzu
                if file_type and target_path:
                    mappings[file_type] = target_path
                    self.logger.debug(f"Zuordnung gefunden: {file_type} -> {target_path}")
                
            self.logger.debug(f"Gefundene Zuordnungen: {mappings}")
            
            # Sammle ausgeschlossene Laufwerke
            excluded_drives = []
            for i in range(self.excluded_list.count()):
                item = self.excluded_list.item(i)
                drive = item.text().strip()
                if drive:  # Nur nicht-leere Laufwerke hinzufügen
                    excluded_drives.append(drive)
            
            self.logger.debug(f"Ausgeschlossene Laufwerke: {excluded_drives}")
            
            # Aktuelle Einstellungen
            current_settings = {
                'excluded_drives': excluded_drives,
                'mappings': mappings,
                'parallel_copies': self.settings.get('parallel_copies', 2),
                'buffer_size': self.settings.get('buffer_size', 64*1024),
                'auto_start': self.auto_start_checkbox.isChecked(),
                'verify_copies': self.settings.get('verify_copies', False),
                'recursive_search': self.settings.get('recursive_search', True),
                'show_notifications': self.settings.get('show_notifications', True)
            }
            
            # Speichere in settings_manager
            self.settings_manager.save_settings(current_settings)
            self.settings = current_settings
            self.logger.debug(f"Aktueller Zustand gespeichert: {current_settings}")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Auto-Speichern: {e}", exc_info=True)
            
    def get_file_types(self):
        """Gibt eine Liste der verfügbaren Dateitypen zurück."""
        try:
            # Standard-Dateitypen
            file_types = [
                "*.jpg", "*.jpeg", "*.png", "*.gif", "*.bmp",
                "*.mp4", "*.mov", "*.avi", "*.mkv",
                "*.mp3", "*.wav", "*.flac",
                "*.doc", "*.docx", "*.pdf",
                "*.zip", "*.rar", "*.7z"
            ]
            
            # Benutzerdefinierte Dateitypen aus den Einstellungen
            custom_types = self.settings.get('custom_file_types', [])
            
            # Kombiniere und entferne Duplikate
            return sorted(list(set(file_types + custom_types)))
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Dateitypen: {e}")
            return []
        
    def get_source_files(self, source_drive: str) -> List[str]:
        """Gibt eine Liste der zu kopierenden Dateien zurück."""
        try:
            # Prüfe ob das Laufwerk in der Liste der verbundenen Laufwerke ist
            if source_drive not in self.drive_items:
                logger.warning(f"Laufwerk {source_drive} ist nicht in der Liste der verbundenen Laufwerke")
                self.ui_handlers.show_error(
                    "Fehler",
                    f"Laufwerk {source_drive} ist nicht verbunden."
                )
                return []
            
            # Prüfe ob das Laufwerk ausgeschlossen ist
            if self.drive_items[source_drive].is_excluded:
                logger.warning(f"Laufwerk {source_drive} ist ausgeschlossen")
                self.ui_handlers.show_error(
                    "Fehler",
                    f"Laufwerk {source_drive} ist ausgeschlossen."
                )
                return []

            # Prüfe ob das Laufwerk bereit ist
            drive_path = f"{source_drive}:\\"
            try:
                # Versuche einen Test-Zugriff auf das Laufwerk
                os.listdir(drive_path)
            except Exception as e:
                logger.warning(f"Laufwerk {source_drive} ist nicht bereit: {e}")
                self.ui_handlers.show_error(
                    "Fehler",
                    f"Laufwerk {source_drive} ist nicht bereit."
                )
                return []

            # Hole Dateitypen
            file_types = self.get_file_types()
            if not file_types:
                logger.warning("Keine Dateitypen ausgewählt")
                self.ui_handlers.show_warning(
                    "Warnung",
                    "Keine Dateitypen ausgewählt."
                )
                return []

            # Suche Dateien
            source_files = []
            try:
                for root, _, files in os.walk(drive_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if any(file.lower().endswith(ext.lower().replace("*", "")) for ext in file_types):
                            source_files.append(file_path)
            except PermissionError as pe:
                logger.error(f"Zugriff auf Laufwerk {source_drive} verweigert: {pe}")
                self.ui_handlers.show_error(
                    "Fehler",
                    f"Zugriff auf Laufwerk {source_drive} verweigert."
                )
                return []
            except Exception as e:
                logger.error(f"Fehler beim Durchsuchen von Laufwerk {source_drive}: {e}")
                self.ui_handlers.show_error(
                    "Fehler",
                    f"Fehler beim Durchsuchen von Laufwerk {source_drive}."
                )
                return []

            if not source_files:
                logger.info(f"Keine passenden Dateien auf Laufwerk {source_drive} gefunden")
                self.ui_handlers.show_warning(
                    "Keine Dateien gefunden",
                    f"Keine passenden Dateien auf Laufwerk {source_drive} gefunden."
                )

            return source_files

        except Exception as e:
            logger.error(f"Fehler beim Suchen der Quelldateien: {e}")
            self.ui_handlers.show_error(
                "Fehler",
                f"Fehler beim Suchen der Quelldateien: {e}"
            )
            return []

    def start_copy(self, source_drive, target_path):
        """Startet den Kopiervorgang."""
        try:
            source_files = self.get_source_files(source_drive)
            if not source_files:
                return
                
            for source_file in source_files:
                target_file = os.path.join(target_path, os.path.basename(source_file))
                
                # Prüfe ob Datei bereits existiert
                if os.path.exists(target_file):
                    base, ext = os.path.splitext(target_file)
                    counter = 1
                    while os.path.exists(target_file):
                        target_file = f"{base}_{counter}{ext}"
                        counter += 1
                
                # Erstelle Task ID und füge zur Warteschlange hinzu
                task_id = f"{source_file}->{target_file}"
                self.transfer_coordinator.start_copy_for_files([source_file], target_file)
                
        except Exception as e:
            logger.error(f"Fehler beim Starten des Kopiervorgangs: {e}")
            self.ui_handlers.show_error(
                "Fehler",
                f"Fehler beim Starten des Kopiervorgangs: {e}"
            )
            
    def on_drive_disconnected(self, drive_letter):
        """Wird aufgerufen, wenn ein Laufwerk getrennt wird."""
        # Entferne das Laufwerk aus der Liste
        self.drives_list.remove_drive(drive_letter)
        
        # Stoppe alle Kopiervorgänge von diesem Laufwerk
        affected_tasks = [task_id for task_id, copy in self.active_copies.items()
                         if copy["source_drive"] == drive_letter]
        
        for task_id in affected_tasks:
            self.transfer_coordinator.set_task_error(task_id, "Laufwerk getrennt")
            del self.active_copies[task_id]
            
        logger.warning(f"Laufwerk {drive_letter} wurde getrennt. "
                      f"{len(affected_tasks)} Kopiervorgänge abgebrochen.")
        
    def on_progress_updated(self, drive_letter: str, filename: str, progress: float, speed: float, total_size: int = None, transferred: int = None):
        """Wird aufgerufen, wenn sich der Fortschritt eines Kopiervorgangs ändert."""
        try:
            # Aktualisiere Fortschritt im UI
            if hasattr(self, 'transfer_widget'):
                self.transfer_widget.update_drive_progress(
                    drive_letter,
                    filename,
                    progress,
                    speed,  # Geschwindigkeit in MB/s
                    total_size,
                    transferred
                )
                
            # Aktualisiere Drive Status
            self.update_drive_status(drive_letter, speed)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren des Fortschritts: {e}")

    def update_drive_status(self, drive_letter: str, speed: float):
        """Aktualisiert die Statusanzeige eines Laufwerks."""
        try:
            # Finde alle aktiven Kopien für dieses Laufwerk
            active_count = 0
            if hasattr(self, 'transfer_widget'):
                # Prüfe ob das Laufwerk aktive Transfers hat
                if drive_letter in self.transfer_widget.drive_widgets:
                    active_count = len(self.transfer_widget.active_transfers)

            # Aktualisiere die Laufwerksanzeige
            if hasattr(self, 'drive_widget'):
                self.drive_widget.update_drive_status(drive_letter, active_count, speed)

        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren des Laufwerksstatus: {e}")

    def show_advanced_settings(self):
        """Zeigt den Dialog für erweiterte Einstellungen."""
        try:
            settings = {
                "buffer_size": 64,
                "parallel_copies": 2,
                "verify_mode": self.settings.get('verify_mode', 'none'),
                "auto_start": self.settings.get('auto_start', False),
                "schedule_enable": self.settings.get('schedule_enable', False),
                "start_time": self.settings.get('start_time', '22:00'),
                "batch_jobs": self.batch_manager.jobs if hasattr(self.batch_manager, 'jobs') else []
            }
            
            dialog = AdvancedSettingsDialog(
                self, settings,
                drives=self.drive_controller.get_drives(),
                file_types=self.get_file_types()
            )
            
            if dialog.exec_():
                new_settings = dialog.get_settings()
                
                # Aktualisiere Kopiereinstellungen
                
                # Speichere Batch-Jobs
                if hasattr(self.batch_manager, 'jobs'):
                    self.batch_manager.jobs = []
                    for job in new_settings["batch_jobs"]:
                        self.batch_manager.add_job(
                            job["source_drive"],
                            job["file_type"],
                            job["target_path"]
                        )
                    
                # Aktiviere/Deaktiviere Zeitsteuerung
                if new_settings["schedule_enable"]:
                    self.setup_scheduled_transfer(new_settings["start_time"])
                else:
                    self.disable_scheduled_transfer()
                    
        except Exception as e:
            logger.error(f"Fehler beim Öffnen der erweiterten Einstellungen: {e}")
            
    def setup_scheduled_transfer(self, start_time):
        """Richtet die zeitgesteuerte Übertragung ein."""
        time = datetime.strptime(start_time, "%H:%M").time()
        if not hasattr(self, "schedule_timer"):
            self.schedule_timer = QTimer(self)
            self.schedule_timer.timeout.connect(self.start_batch_processing)
            
        # Berechne die Zeit bis zum nächsten Start
        current_time = datetime.now().time()
        target_time = time
        
        if current_time > target_time:
            target_time = datetime.combine(datetime.now().date() + datetime.timedelta(days=1), time).time()
        else:
            target_time = datetime.combine(datetime.now().date(), time).time()
            
        seconds_until = (datetime.combine(datetime.now().date(), target_time) - datetime.now()).total_seconds()
        self.schedule_timer.start(int(seconds_until * 1000))
        
    def disable_scheduled_transfer(self):
        """Deaktiviert die zeitgesteuerte Übertragung."""
        if hasattr(self, "schedule_timer"):
            self.schedule_timer.stop()
            
    def start_batch_processing(self):
        """Startet die Batch-Verarbeitung."""
        next_job = self.batch_manager.get_next_job()
        if next_job:
            self.batch_manager.start_job(next_job)
            self.start_copy(next_job.source_drive, next_job.target_path)

    def _on_browse_clicked(self):
        """Öffnet einen Dialog zur Auswahl des Zielverzeichnisses."""
        # Hole den aktuellen Dateityp
        filetype = self.filetype_combo.currentText()
        if not filetype:
            self.ui_handlers.show_warning(
                self.i18n.get("ui.warning"),
                self.i18n.get("ui.select_filetype_first")
            )
            return
            
        # Öffne Verzeichnisauswahl-Dialog
        directory = QFileDialog.getExistingDirectory(
            self,
            self.i18n.get("ui.select_target_directory"),
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if directory:
            # Füge neue Zuordnung zur Liste hinzu
            mapping_text = f"{filetype} ➔ {directory}"
            self.mappings_list.addItem(mapping_text)
            
    def _on_add_mapping_clicked(self):
        """Fügt eine neue Zuordnung hinzu."""
        try:
            # Hole ausgewählten Dateityp und Zielpfad
            file_type = self.filetype_combo.currentText()
            target_path = self.target_path_edit.text().strip()
            
            if not file_type or not target_path:
                self.show_warning("Eingabe fehlt", "Bitte Dateityp und Zielpfad angeben")
                return
                
            # Erstelle Zuordnungstext
            mapping_text = f"{file_type} ➔ {target_path}"
            
            # Prüfe ob Zuordnung bereits existiert
            for i in range(self.mappings_list.count()):
                if self.mappings_list.item(i).text() == mapping_text:
                    self.show_warning("Doppelte Zuordnung", 
                                    "Diese Zuordnung existiert bereits")
                    return
            
            # Füge zur Liste hinzu
            self.mappings_list.addItem(mapping_text)
            self.logger.debug(f"Neue Zuordnung hinzugefügt: {mapping_text}")
            
            # Aktualisiere Einstellungen
            self.save_settings()
            
            # Aktualisiere FileWatcherManager
            if hasattr(self, 'file_watcher_manager'):
                self.file_watcher_manager.update_file_mappings()
                
            # Leere Eingabefelder
            self.target_path_edit.clear()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Hinzufügen der Zuordnung: {e}", 
                            exc_info=True)
            
    def _process_mappings(self):
        """Verarbeitet die gespeicherten Zuordnungen beim Laden der Einstellungen."""
        try:
            if not hasattr(self, 'mappings_list'):
                return
                
            self.mappings_list.clear()
            
            # Hole Zuordnungen aus den Einstellungen
            mappings = self.settings.get('mappings', {})
            
            # Füge Zuordnungen zur Liste hinzu
            for file_type, target in mappings.items():
                # Füge zur Liste hinzu
                item_text = f"{file_type} ➔ {target}"
                self.mappings_list.addItem(item_text)
                self.logger.debug(f"Zuordnung geladen: {file_type} -> {target}")
                
            # Aktualisiere FileWatcherManager
            if hasattr(self, 'file_watcher_manager'):
                self.file_watcher_manager.update_file_mappings()
                
            self.logger.debug(f"Zuordnungen verarbeitet: {mappings}")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten der Zuordnungen: {e}", exc_info=True)
            
    def _on_remove_mapping_clicked(self):
        """Entfernt die ausgewählte Zuordnung."""
        try:
            current_item = self.mappings_list.currentItem()
            if current_item:
                self.mappings_list.takeItem(
                    self.mappings_list.row(current_item)
                )
                self.save_settings()
                
        except Exception as e:
            self.logger.error(f"Fehler beim Entfernen der Zuordnung: {e}")
            
    def _on_add_excluded_path_clicked(self):
        """Öffnet einen Dialog zur Auswahl eines auszuschließenden Verzeichnisses."""
        try:
            directory = QFileDialog.getExistingDirectory(
                self,
                self.i18n.get("ui.select_directory"),
                os.path.expanduser("~")
            )
            if directory:
                # Prüfe ob das Verzeichnis bereits ausgeschlossen ist
                for i in range(self.excluded_list.count()):
                    if self.excluded_list.item(i).text() == directory:
                        self.ui_handlers.show_warning(
                            self.i18n.get("general.warning"),
                            self.i18n.get("ui.duplicate_excluded").format(directory=directory)
                        )
                        return
                
                self.excluded_list.addItem(directory)
                self.save_settings()
                
        except Exception as e:
            self.logger.error(f"Fehler beim Ausschließen des Verzeichnisses: {e}")
            
    def _on_remove_excluded_clicked(self):
        """Entfernt das ausgewählte ausgeschlossene Verzeichnis."""
        try:
            current_item = self.excluded_list.currentItem()
            if current_item:
                self.excluded_list.takeItem(
                    self.excluded_list.row(current_item)
                )
                self.save_settings()
                
        except Exception as e:
            self.logger.error(f"Fehler beim Entfernen des ausgeschlossenen Verzeichnisses: {e}")
            
    def _on_exclude_all_clicked(self):
        """Schließt alle verfügbaren Laufwerke aus."""
        try:
            # Leere die Liste
            self.excluded_list.clear()
            self.excluded_drives.clear()
            
            # Füge alle Laufwerksbuchstaben hinzu (außer D:)
            all_drives = ['A', 'B', 'C', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                         'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
            
            for drive in all_drives:
                if drive != 'D':
                    item = QListWidgetItem(drive)
                    self.excluded_list.addItem(item)
                    self.excluded_drives.append(drive)
            
            # Aktualisiere die gefilterte Liste
            self.update_filtered_drives_list()
            
            # Speichere die Einstellungen
            self.save_settings()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Ausschließen aller Laufwerke: {e}")
            
    def get_mapping_for_type(self, file_type: str) -> str:
        """Gibt die Zuordnung für einen Dateityp zurück.
        
        Args:
            file_type: Dateityp (z.B. '.mp4')
            
        Returns:
            Zielpfad für den Dateityp oder None wenn keine Zuordnung existiert
        """
        # Normalisiere den Dateityp (entferne Punkt am Anfang falls vorhanden)
        if file_type.startswith('.'):
            file_type = file_type[1:]
            
        # Suche nach beiden möglichen Formaten (*.ext und .ext)
        for i in range(self.mappings_list.count()):
            item = self.mappings_list.item(i)
            text = item.text()
            # Prüfe beide Formate
            if text.startswith(f"*.{file_type} ➔ ") or text.startswith(f".{file_type} ➔ "):
                target_dir = text.split(" ➔ ")[1].strip()
                self.logger.debug(f"Zuordnung gefunden für {file_type}: {target_dir}")
                return target_dir
                
        self.logger.debug(f"Keine Zuordnung gefunden für {file_type}")
        return None

    def _get_target_path(self, source_file: str, target_dir: str) -> str:
        """Erstellt den vollständigen Zielpfad für eine Datei.
        
        Args:
            source_file: Pfad zur Quelldatei
            target_dir: Zielverzeichnis
            
        Returns:
            Vollständiger Zielpfad für die Datei
        """
        if not source_file or not target_dir:
            return None
            
        # Extrahiere Dateinamen aus Quellpfad
        filename = os.path.basename(source_file)
        # Erstelle vollständigen Zielpfad
        return os.path.join(target_dir, filename)

    def start_copy_for_files(self, files: list):
        """Startet den Kopiervorgang für eine Liste von Dateien."""
        try:
            # Gruppiere Dateien nach Typ
            files_by_type = {}
            for file_path in files:
                _, ext = os.path.splitext(file_path)
                if ext:
                    # Stelle sicher, dass der Dateityp mit Punkt beginnt
                    file_type = f".{ext[1:].lower()}"
                    if file_type not in files_by_type:
                        files_by_type[file_type] = []
                    files_by_type[file_type].append(file_path)
                    
            # Starte Transfer für jede Dateigruppe
            for file_type, file_list in files_by_type.items():
                target_dir = self.get_mapping_for_type(file_type)
                if target_dir:
                    for source_file in file_list:
                        target_path = self._get_target_path(source_file, target_dir)
                        if target_path:
                            self.transfer_coordinator.start_transfer(source_file, target_path)
                        else:
                            self.logger.error(f"Konnte Zielpfad nicht erstellen für {source_file}")
                else:
                    self.logger.warning(f"Keine Zuordnung gefunden für Dateityp {file_type}")
                    
        except Exception as e:
            self.logger.error(f"Fehler beim Starten des Kopiervorgangs: {e}")
            self.show_error("Fehler", f"Fehler beim Starten des Kopiervorgangs:\n{str(e)}")
            
    def show_warning(self, title: str, message: str):
        """Zeigt eine Warnung an."""
        self.ui_handlers.show_warning(title, message)
        
    def show_error(self, title: str, message: str):
        """Zeigt einen Fehler an."""
        self.ui_handlers.show_error(title, message)

    def add_mapping(self, source: str, target: str):
        """Fügt eine neue Dateizuordnung hinzu.
        
        Args:
            source: Quellpfad oder Laufwerk
            target: Zielpfad für die Dateien
        """
        if not source or not target:
            return
            
        try:
            # Füge zur Liste hinzu
            item_text = f"{source} ➔ {target}"
            self.mappings_list.addItem(item_text)
            
            # Speichere in Einstellungen
            mappings = self.settings.get('mappings', {})
            mappings[source] = target
            self.settings['mappings'] = mappings
            self.settings_manager.save_settings(self.settings)
            
            logger.info(f"Neue Zuordnung hinzugefügt: {item_text}")
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen der Zuordnung: {e}")
            QMessageBox.warning(
                self,
                self.i18n.get("ui.error"),
                self.i18n.get("ui.mapping_error").format(error=str(e))
            )

    def get_file_types_and_mappings(self) -> tuple:
        """Holt die Dateitypen und Zuordnungen aus dem Zuordnungen-Widget.
        
        Returns:
            Tuple aus (file_types, mappings), wobei:
            - file_types: Liste der zu überwachenden Dateitypen
            - mappings: Dictionary mit Dateityp -> Zielpfad Zuordnungen
        """
        file_types = []
        mappings = {}
        
        try:
            # Lese alle Einträge aus der Zuordnungsliste
            for i in range(self.mappings_list.count()):
                item = self.mappings_list.item(i)
                if not item:
                    continue
                    
                text = item.text()
                self.logger.debug(f"Verarbeite Zuordnung: {text}")
                
                # Unterstütze beide Formate: "*.mp4 ➔ Pfad" und ".mp4 -> Pfad"
                if "➔" in text:
                    file_type, target_path = text.split("➔")
                elif " -> " in text:
                    file_type, target_path = text.split(" -> ")
                else:
                    continue
                    
                # Bereinige Dateityp
                file_type = file_type.strip().lower()
                if file_type.startswith("*."):
                    file_type = "." + file_type[2:]  # Wandle "*.mp4" in ".mp4" um
                elif not file_type.startswith("."):
                    file_type = "." + file_type  # Stelle sicher, dass der Dateityp mit . beginnt
                    
                target_path = target_path.strip()
                
                # Füge nur gültige Zuordnungen hinzu
                if file_type and target_path:
                    file_types.append(file_type)
                    mappings[file_type] = target_path
                    self.logger.debug(f"Zuordnung gefunden: {file_type} -> {target_path}")
                
            self.logger.debug(f"Gefundene Dateitypen: {file_types}")
            self.logger.debug(f"Gefundene Zuordnungen: {mappings}")
            return file_types, mappings
            
        except Exception as e:
            self.logger.error(f"Fehler beim Lesen der Zuordnungen: {e}", exc_info=True)
            return [], {}

    def update_filtered_drives_list(self):
        """Aktualisiert die gefilterte Laufwerksliste basierend auf Zuordnungen und Ausschlüssen."""
        try:
            self.filtered_drives_list.clear()
            
            # Hole aktuelle Zuordnungen
            file_types, mappings = self.get_file_types_and_mappings()
            self.logger.debug(f"Gefundene Dateitypen: {file_types}")
            self.logger.debug(f"Gefundene Zuordnungen: {mappings}")
            
            # Aktualisiere die Liste der ausgeschlossenen Laufwerke
            self.excluded_drives.clear()
            for i in range(self.excluded_list.count()):
                item = self.excluded_list.item(i)
                drive = item.text().strip()
                if drive:  # Nur nicht-leere Laufwerke hinzufügen
                    self.excluded_drives.append(drive)
            
            self.logger.debug(f"Ausgeschlossene Laufwerke: {self.excluded_drives}")
            
            # Aktualisiere Status aller Laufwerke
            for drive_letter, drive_item in self.drive_items.items():
                normalized_drive = drive_letter.rstrip(':\\')
                is_excluded = normalized_drive in self.excluded_drives
                
                # Aktualisiere den Status im DriveListItem
                drive_item.update_excluded_status(is_excluded)
                
                # Füge nicht ausgeschlossene Laufwerke zur gefilterten Liste hinzu
                if not is_excluded:
                    if hasattr(drive_item, 'label'):
                        new_item = self.filtered_drives_list.add_drive(
                            drive_letter, 
                            drive_item.label if hasattr(drive_item, 'label') else 'Unbekannt'
                        )
                        # Kopiere Status und andere Eigenschaften
                        if hasattr(drive_item, 'status'):
                            new_item.status = drive_item.status
                        if hasattr(drive_item, 'drive_type'):
                            new_item.drive_type = drive_item.drive_type
                        if hasattr(drive_item, 'is_mapped'):
                            new_item.is_mapped = drive_item.is_mapped
                        if hasattr(drive_item, 'is_excluded'):
                            new_item.is_excluded = drive_item.is_excluded
                        new_item._update_display()
            
            self.logger.debug(f"Gefilterte Laufwerksliste aktualisiert: {self.filtered_drives_list.count()} Laufwerke")
            
            # Speichere die Einstellungen
            self.save_settings()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren der gefilterten Laufwerksliste: {e}")
            
    def _has_matching_files(self, drive_letter: str) -> bool:
        """Prüft ob ein Laufwerk Dateien enthält, die den konfigurierten Zuordnungen entsprechen.
        
        Args:
            drive_letter: Laufwerksbuchstabe (z.B. 'C')
            
        Returns:
            True wenn das Laufwerk passende Dateien enthält, sonst False
        """
        try:
            # Hole aktuelle Zuordnungen
            file_types, _ = self.get_file_types_and_mappings()
            if not file_types:
                return False
                
            # Prüfe ob das Laufwerk existiert
            drive_path = f"{drive_letter}:\\"
            if not os.path.exists(drive_path):
                return False
                
            # Suche nach Dateien mit den konfigurierten Typen
            for root, _, files in os.walk(drive_path, topdown=True):
                for file in files:
                    file_ext = os.path.splitext(file)[1].lower()
                    if file_ext in file_types:
                        self.logger.debug(f"Passende Datei gefunden: {os.path.join(root, file)}")
                        return True
                        
            return False
            
        except Exception as e:
            self.logger.error(f"Fehler beim Prüfen auf passende Dateien: {e}")
            return False

    def toggle_watcher(self, enabled: bool):
        """Schaltet den Watcher ein oder aus."""
        try:
            self.is_watching = enabled
            
            # Aktualisiere Button-Text und Style
            if enabled:
                self.start_button.setText("⏹️ Stop")
                self.start_button.setStyleSheet("""
                    QPushButton {
                        background-color: #f44336;
                        color: white;
                        border: none;
                        padding: 5px;
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background-color: #da190b;
                    }
                    QPushButton:disabled {
                        background-color: #cccccc;
                    }
                """)
                
                # Deaktiviere UI-Elemente während der Watcher läuft
                self.mappings_list.setEnabled(False)
                self.add_mapping_button.setEnabled(False)
                self.remove_mapping_button.setEnabled(False)
                self.excluded_list.setEnabled(False)
                self.add_excluded_button.setEnabled(False)
                self.remove_excluded_button.setEnabled(False)
                self.exclude_all_button.setEnabled(False)
            else:
                self.start_button.setText("▶️ Start")
                self.start_button.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        padding: 5px;
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                    QPushButton:disabled {
                        background-color: #cccccc;
                    }
                """)
                
                # Aktiviere UI-Elemente wieder
                self.mappings_list.setEnabled(True)
                self.add_mapping_button.setEnabled(True)
                self.remove_mapping_button.setEnabled(True)
                self.excluded_list.setEnabled(True)
                self.add_excluded_button.setEnabled(True)
                self.remove_excluded_button.setEnabled(True)
                self.exclude_all_button.setEnabled(True)
            
            self.logger.debug(f"Watcher Status: {'Aktiv' if enabled else 'Inaktiv'}")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Umschalten des Watcher-Status: {e}", exc_info=True)
            
    def _on_start_clicked(self):
        """Interner Handler für Start/Stop Button."""
        try:
            if not self.is_watching:
                self.toggle_watcher(True)
                self.event_handlers.on_start_clicked()
            else:
                self.toggle_watcher(False)
                self.event_handlers.on_stop_clicked()
        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten des Start/Stop-Klicks: {e}")

    def _process_mapping(self, mapping_text: str) -> Tuple[str, str]:
        """Verarbeitet einen Zuordnungstext und gibt Dateityp und Zielpfad zurück."""
        try:
            # Trenne Dateityp und Pfad
            filetype, target = mapping_text.split('➔')
            
            # Bereinige die Strings
            filetype = filetype.strip().strip('*')
            target = target.strip()
            
            # Normalisiere den Pfad für Windows
            target = os.path.normpath(target)
            
            self.logger.debug(f"Verarbeite Zuordnung: {filetype} ➔ {target}")
            
            return filetype, target
            
        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten der Zuordnung '{mapping_text}': {e}")
            return None, None

    def _process_mappings(self):
        """Verarbeitet die gespeicherten Zuordnungen beim Laden der Einstellungen."""
        try:
            # Liste leeren bevor neue Einträge hinzugefügt werden
            self.mappings_list.clear()
            
            mappings = self.settings.get('mappings', {})
            for source, target in mappings.items():
                # Füge zur Liste hinzu
                item_text = f"{source} ➔ {target}"
                self.mappings_list.addItem(item_text)
                self.logger.debug(f"Zuordnung geladen: {source} -> {target}")
                
        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten der Zuordnungen: {e}", exc_info=True)
            raise

    @pyqtSlot(str)
    def log_message(self, message: str):
        """Fügt eine Nachricht zum Log hinzu."""
        try:
            self.logger.info(message)
            # Update status bar if it exists
            if hasattr(self, 'statusBar'):
                self.statusBar().showMessage(message, 3000)  # Show for 3 seconds
        except Exception as e:
            self.logger.error(f"Fehler beim Loggen der Nachricht: {str(e)}")

    def update_progress(self, filename: str, progress: float):
        """Aktualisiert den Fortschritt für eine Datei."""
        try:
            # Get drive letter from filename
            drive_letter = self.target_path_edit.text()[:1].upper()
            
            # Aktualisiere Progress Widget
            if hasattr(self, 'transfer_widget'):
                # Hole Dateigrößen
                source = os.path.join(drive_letter + ":", filename)
                if os.path.exists(source):
                    total_bytes = os.path.getsize(source)
                    transferred_bytes = int(total_bytes * (progress / 100))
                else:
                    total_bytes = 0
                    transferred_bytes = 0
                    
                # Generiere eindeutige Transfer-ID
                transfer_id = f"{drive_letter}:{filename}"
                
                # Aktualisiere Transfer
                self.transfer_widget.update_transfer(
                    transfer_id=transfer_id,
                    filename=filename,
                    drive=f"Laufwerk {drive_letter}",
                    progress=progress,
                    speed=0,
                    total_bytes=total_bytes,
                    transferred_bytes=transferred_bytes
                )
            
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren des Fortschritts: {str(e)}", exc_info=True)

    def _connect_signals(self):
        """Verbindet die Signal-Handler."""
        try:
            # Drive Handler Signale
            self.drive_handlers.drive_connected.connect(self._on_drive_connected)
            self.drive_handlers.drive_disconnected.connect(self._on_drive_disconnected)
            
            # Transfer Handler Signale
            self.transfer_coordinator.transfer_started.connect(self._on_transfer_started)
            self.transfer_coordinator.transfer_progress.connect(self._on_transfer_progress)
            self.transfer_coordinator.transfer_completed.connect(self._on_transfer_completed)
            self.transfer_coordinator.transfer_error.connect(self._on_transfer_error)
            
            # Button Signale
            self.start_button.clicked.connect(self._on_start_clicked)
            self.cancel_button.clicked.connect(self._on_cancel_clicked)
            self.target_select_button.clicked.connect(self._on_browse_clicked)
            
            self.logger.debug("Signale erfolgreich verbunden")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Verbinden der Signale: {e}", exc_info=True)
            raise  # Re-raise the exception after logging

    def showEvent(self, event):
        """Wird aufgerufen, wenn das Fenster angezeigt wird."""
        super().showEvent(event)
        if self._first_show:
            # Setze Position und Größe beim ersten Anzeigen
            screen = self.screen()
            screen_geometry = screen.geometry()
            x = (screen_geometry.width() - 1440) // 2
            y = (screen_geometry.height() - 1000) // 2
            self.setGeometry(x, y, 1440, 1000)
            self._first_show = False

    def update_drive_status(self, drive_letter: str, speed: float):
        """Aktualisiert die Statusanzeige eines Laufwerks."""
        try:
            # Finde alle aktiven Kopien für dieses Laufwerk
            active_count = 0
            if hasattr(self, 'transfer_widget'):
                # Prüfe ob das Laufwerk aktive Transfers hat
                if drive_letter in self.transfer_widget.drive_widgets:
                    active_count = len(self.transfer_widget.active_transfers)

            # Aktualisiere die Laufwerksanzeige
            if hasattr(self, 'drive_widget'):
                self.drive_widget.update_drive_status(drive_letter, active_count, speed)

        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren des Laufwerksstatus: {e}")

    def _setup_transfer_section(self):
        """Richtet die Transfer-Sektion ein."""
        # Transfer Widget
        self.transfer_widget = ModernTransferWidget()
        
        # Verbinde Transfer Coordinator
        self.transfer_coordinator.transfer_started.connect(
            self._on_transfer_started
        )
        self.transfer_coordinator.transfer_progress.connect(
            self._on_transfer_progress
        )
        self.transfer_coordinator.transfer_completed.connect(
            self._on_transfer_completed
        )
        self.transfer_coordinator.transfer_error.connect(
            self._on_transfer_error
        )
        
        # Verbinde Widget Signale
        self.transfer_widget.transfer_cancelled.connect(
            self.transfer_coordinator.cancel_transfer
        )
        self.transfer_widget.transfer_retry.connect(
            self.transfer_coordinator.retry_transfer
        )
        
        # Füge Widget zum Layout hinzu
        self.right_sidebar.addWidget(self.transfer_widget)
        
    def _on_transfer_started(self, transfer_id: str):
        """Handler für gestartete Transfers."""
        try:
            # Initialisiere Transfer im Widget
            self.transfer_widget.update_transfer(
                transfer_id=transfer_id,
                filename="",
                progress=0,
                speed=0,
                total_bytes=0,
                transferred_bytes=0,
                start_time=time.time(),
                eta=timedelta.max
            )
            
            # Zeige Statusmeldung
            self.show_status_message(
                f"Transfer gestartet: {transfer_id}",
                timeout=3000
            )
            
        except Exception as e:
            self.logger.error(f"Fehler beim Starten des Transfers: {e}")
            
    def _on_transfer_progress(self, transfer_id: str, progress: float, speed: float, eta: timedelta, total: int, transferred: int):
        """Handler für Transfer-Fortschritt."""
        try:
            # Hole Transfer-Info
            transfer = self.transfer_coordinator.get_transfer_status(transfer_id)
            if not transfer:
                return
                
            # Update Widget
            self.transfer_widget.update_transfer(
                transfer_id=transfer_id,
                filename=transfer['filename'],
                progress=progress,
                speed=speed,
                total_bytes=total,
                transferred_bytes=transferred,
                start_time=transfer['start_time'],
                eta=eta
            )
            
        except Exception as e:
            self.logger.error(f"Fehler beim Update des Transfers: {e}")
            
    def _on_transfer_completed(self, transfer_id: str):
        """Handler für abgeschlossene Transfers."""
        try:
            # Hole Transfer-Info
            transfer = self.transfer_coordinator.get_transfer_status(transfer_id)
            if not transfer:
                return
                
            # Entferne aus Widget
            self.transfer_widget.remove_transfer(transfer_id)
            
            # Zeige Erfolgsmeldung
            self.show_status_message(
                f"Transfer abgeschlossen: {transfer['filename']}",
                timeout=3000
            )
            
            # Aktualisiere UI
            self.refresh_current_view()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Abschließen des Transfers: {e}")
            
    def _on_transfer_error(self, transfer_id: str, error: str):
        """Handler für Transfer-Fehler."""
        try:
            # Hole Transfer-Info
            transfer = self.transfer_coordinator.get_transfer_status(transfer_id)
            if not transfer:
                return
                
            # Zeige Fehler im Widget
            self.transfer_widget.handle_error(
                transfer_id,
                error,
                error_type="error"
            )
            
            # Zeige Fehlermeldung
            self.show_error_message(
                f"Fehler beim Transfer von {transfer['filename']}: {error}"
            )
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Fehlerbehandlung: {e}")
            
    def show_status_message(self, message: str, timeout: int = 0):
        """Zeigt eine Statusmeldung in der Statusleiste an."""
        try:
            self.statusBar().showMessage(message, timeout)
        except Exception as e:
            self.logger.error(f"Fehler beim Anzeigen der Statusmeldung: {e}")
            
    def show_error_message(self, message: str):
        """Zeigt eine Fehlermeldung im Error Dialog an."""
        try:
            QMessageBox.critical(
                self,
                "Fehler",
                message,
                QMessageBox.Ok
            )
        except Exception as e:
            self.logger.error(f"Fehler beim Anzeigen der Fehlermeldung: {e}")

    def _setup_transfer_coordinator(self):
        """Richtet den TransferCoordinator ein."""
        self.logger.debug("Richte TransferCoordinator ein")
        try:
            # Erstelle TransferCoordinator
            self.transfer_coordinator = TransferCoordinator()
            
            # Verbinde Signale mit Qt.QueuedConnection
            self.transfer_coordinator.transfer_started.connect(
                self.transfer_widget.on_transfer_started,
                type=Qt.QueuedConnection
            )
            self.transfer_coordinator.transfer_progress.connect(
                self.transfer_widget.on_transfer_progress,
                type=Qt.QueuedConnection
            )
            self.transfer_coordinator.transfer_completed.connect(
                self.transfer_widget.on_transfer_completed,
                type=Qt.QueuedConnection
            )
            self.transfer_coordinator.transfer_error.connect(
                self.transfer_widget.on_transfer_error,
                type=Qt.QueuedConnection
            )
            self.transfer_coordinator.transfer_paused.connect(
                self.transfer_widget.on_transfer_paused,
                type=Qt.QueuedConnection
            )
            self.transfer_coordinator.transfer_resumed.connect(
                self.transfer_widget.on_transfer_resumed,
                type=Qt.QueuedConnection
            )
            self.transfer_coordinator.transfer_cancelled.connect(
                self.transfer_widget.on_transfer_cancelled,
                type=Qt.QueuedConnection
            )
            
            # Starte Queue-Verarbeitung
            self.transfer_coordinator.start()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Einrichten des TransferCoordinator: {e}", exc_info=True)

    def _connect_signals(self):
        """Verbindet die Signale der UI-Komponenten."""
        try:
            # Verbinde Transfer-Signale
            if hasattr(self.transfer_widget, 'on_transfer_started'):
                self.transfer_coordinator.transfer_started.connect(
                    self.transfer_widget.on_transfer_started,
                    type=Qt.QueuedConnection
                )
            
            if hasattr(self.transfer_widget, 'on_transfer_progress'):
                self.transfer_coordinator.transfer_progress.connect(
                    self.transfer_widget.on_transfer_progress,
                    type=Qt.QueuedConnection
                )
            
            if hasattr(self.transfer_widget, 'on_transfer_completed'):
                self.transfer_coordinator.transfer_completed.connect(
                    self.transfer_widget.on_transfer_completed,
                    type=Qt.QueuedConnection
                )
            
            if hasattr(self.transfer_widget, 'on_transfer_error'):
                self.transfer_coordinator.transfer_error.connect(
                    self.transfer_widget.on_transfer_error,
                    type=Qt.QueuedConnection
                )
            
            if hasattr(self.transfer_widget, 'on_transfer_paused'):
                self.transfer_coordinator.transfer_paused.connect(
                    self.transfer_widget.on_transfer_paused,
                    type=Qt.QueuedConnection
                )
            
            if hasattr(self.transfer_widget, 'on_transfer_resumed'):
                self.transfer_coordinator.transfer_resumed.connect(
                    self.transfer_widget.on_transfer_resumed,
                    type=Qt.QueuedConnection
                )
            
            if hasattr(self.transfer_widget, 'on_transfer_cancelled'):
                self.transfer_coordinator.transfer_cancelled.connect(
                    self.transfer_widget.on_transfer_cancelled,
                    type=Qt.QueuedConnection
                )
            
            # Verbinde Batch-Signale
            if hasattr(self.transfer_widget, 'on_batch_started'):
                self.transfer_coordinator.batch_started.connect(
                    self.transfer_widget.on_batch_started,
                    type=Qt.QueuedConnection
                )
            
            if hasattr(self.transfer_widget, 'on_batch_progress'):
                self.transfer_coordinator.batch_progress.connect(
                    self.transfer_widget.on_batch_progress,
                    type=Qt.QueuedConnection
                )
            
            if hasattr(self.transfer_widget, 'on_batch_completed'):
                self.transfer_coordinator.batch_completed.connect(
                    self.transfer_widget.on_batch_completed,
                    type=Qt.QueuedConnection
                )
            
            if hasattr(self.transfer_widget, 'on_batch_error'):
                self.transfer_coordinator.batch_error.connect(
                    self.transfer_widget.on_batch_error,
                    type=Qt.QueuedConnection
                )
            
            self.logger.debug("Signale erfolgreich verbunden")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Verbinden der Signale: {e}", exc_info=True)
            raise  # Re-raise the exception after logging

    def _connect_signals(self):
        """Verbindet die Signale der UI-Komponenten."""
        try:
            # Verbinde Transfer-Signale
            if hasattr(self.transfer_widget, 'on_transfer_started'):
                self.transfer_coordinator.transfer_started.connect(
                    self.transfer_widget.on_transfer_started,
                    type=Qt.QueuedConnection
                )
            
            if hasattr(self.transfer_widget, 'on_transfer_progress'):
                self.transfer_coordinator.transfer_progress.connect(
                    self.transfer_widget.on_transfer_progress,
                    type=Qt.QueuedConnection
                )
            
            if hasattr(self.transfer_widget, 'on_transfer_completed'):
                self.transfer_coordinator.transfer_completed.connect(
                    self.transfer_widget.on_transfer_completed,
                    type=Qt.QueuedConnection
                )
            
            if hasattr(self.transfer_widget, 'on_transfer_error'):
                self.transfer_coordinator.transfer_error.connect(
                    self.transfer_widget.on_transfer_error,
                    type=Qt.QueuedConnection
                )
            
            if hasattr(self.transfer_widget, 'on_transfer_paused'):
                self.transfer_coordinator.transfer_paused.connect(
                    self.transfer_widget.on_transfer_paused,
                    type=Qt.QueuedConnection
                )
            
            if hasattr(self.transfer_widget, 'on_transfer_resumed'):
                self.transfer_coordinator.transfer_resumed.connect(
                    self.transfer_widget.on_transfer_resumed,
                    type=Qt.QueuedConnection
                )
            
            if hasattr(self.transfer_widget, 'on_transfer_cancelled'):
                self.transfer_coordinator.transfer_cancelled.connect(
                    self.transfer_widget.on_transfer_cancelled,
                    type=Qt.QueuedConnection
                )
            
            # Verbinde Batch-Signale
            if hasattr(self.transfer_widget, 'on_batch_started'):
                self.transfer_coordinator.batch_started.connect(
                    self.transfer_widget.on_batch_started,
                    type=Qt.QueuedConnection
                )
            
            if hasattr(self.transfer_widget, 'on_batch_progress'):
                self.transfer_coordinator.batch_progress.connect(
                    self.transfer_widget.on_batch_progress,
                    type=Qt.QueuedConnection
                )
            
            if hasattr(self.transfer_widget, 'on_batch_completed'):
                self.transfer_coordinator.batch_completed.connect(
                    self.transfer_widget.on_batch_completed,
                    type=Qt.QueuedConnection
                )
            
            if hasattr(self.transfer_widget, 'on_batch_error'):
                self.transfer_coordinator.batch_error.connect(
                    self.transfer_widget.on_batch_error,
                    type=Qt.QueuedConnection
                )
            
            self.logger.debug("Signale erfolgreich verbunden")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Verbinden der Signale: {e}", exc_info=True)
            raise  # Re-raise the exception after logging
