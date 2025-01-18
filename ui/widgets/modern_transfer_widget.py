#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Ein modernes Widget zur Anzeige des Übertragungsfortschritts."""

import time
import logging
import os
from datetime import timedelta
from dataclasses import dataclass
from typing import Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QListWidget,
    QListWidgetItem, QScrollArea, QAbstractItemView,
    QSizePolicy
)
from PyQt5.QtCore import (
    Qt, pyqtSignal, pyqtSlot, QMutex, 
    QMutexLocker, QTimer
)
from PyQt5.QtGui import QPalette, QColor

from core.transfer.status import TransferStatus
from core.transfer.transfer_coordinator import TransferInfo
from ui.style_helper import StyleHelper

@dataclass
class TransferItemData:
    """Daten für ein Transfer-Item in der Liste."""
    transfer_id: str
    filename: str
    status: TransferStatus
    progress: float = 0.0
    speed: float = 0.0
    eta: Optional[timedelta] = None
    total_bytes: int = 0
    transferred_bytes: int = 0
    error_message: Optional[str] = None

class ModernTransferWidget(QWidget):
    """Ein modernes Widget zur Anzeige und Verwaltung von Dateitransfers."""

    # Interne Signale für Thread-Sicherheit
    _update_transfer_signal = pyqtSignal(object)
    _remove_transfer_signal = pyqtSignal(str)
    
    # Externe Signale für Transfer-Steuerung
    request_retry = pyqtSignal(str)  # transfer_id
    request_cancel = pyqtSignal(str)  # transfer_id
    request_pause = pyqtSignal(str)  # transfer_id
    request_resume = pyqtSignal(str)  # transfer_id
    
    # Status-Update Signale
    transfer_started = pyqtSignal(str, str)  # transfer_id, filename
    transfer_progress = pyqtSignal(str, float, float, timedelta, int, int)  # transfer_id, progress, speed, eta, total_bytes, transferred_bytes
    transfer_completed = pyqtSignal(str)  # transfer_id
    transfer_error = pyqtSignal(str, str)  # transfer_id, error_message
    transfer_paused = pyqtSignal(str)  # transfer_id
    transfer_resumed = pyqtSignal(str)  # transfer_id
    transfer_cancelled = pyqtSignal(str)  # transfer_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.mutex = QMutex()
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_total_progress)
        self.timer.start(1000)  # Update jede Sekunde
        self.setup_ui()
        
        # Initialisiere Datenstrukturen
        self._transfer_items = {}  # Dict[str, QListWidgetItem]
        self._last_update_times = {}  # Für Update-Debouncing
        self._transfers = {}  # Für Transfer-Daten
        
        # Verbinde interne Signale
        self._update_transfer_signal.connect(
            self._update_transfer_internal,
            type=Qt.DirectConnection
        )
        self._remove_transfer_signal.connect(
            self._remove_transfer_internal,
            type=Qt.DirectConnection
        )
        
        self.logger.debug("ModernTransferWidget initialisiert")

    def setup_ui(self):
        """Richtet das UI des Widgets ein."""
        # Hauptlayout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Gesamt-Fortschrittsbalken
        self._total_progress = QProgressBar()
        self._total_progress.setObjectName("total_progress")
        self._total_progress.setRange(0, 100)
        self._total_progress.setValue(0)
        self._total_progress.setTextVisible(True)
        self._total_progress.setFormat("Gesamt: %p%")
        self._total_progress.setFixedHeight(16)
        self._total_progress.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: {StyleHelper.SURFACE_LIGHT};
                border-radius: 2px;
                text-align: center;
                margin: 0;
                padding: 2px;
                font-size: 10px;
                color: {StyleHelper.TEXT_SECONDARY};
            }}
            QProgressBar::chunk {{
                background-color: {StyleHelper.SUCCESS};
                border-radius: 2px;
            }}
        """)
        main_layout.addWidget(self._total_progress)
        
        # Scroll Area für die Transfer-Items
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background-color: #666;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        # Container Widget für die Transfer-Items
        self.transfers_container = QWidget()
        self.transfers_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.transfers_layout = QVBoxLayout(self.transfers_container)
        self.transfers_layout.setContentsMargins(0, 0, 0, 10)  # 10px Padding am unteren Rand
        self.transfers_layout.setSpacing(0)
        self.transfers_layout.addStretch()
        
        # Setze den Container als Widget für die Scroll Area
        self.scroll_area.setWidget(self.transfers_container)
        
        # Platzhalter-Label für leere Liste
        self._empty_label = QLabel("Keine aktiven Transfers")
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 14px;
                margin-top: 8px;
            }
        """)
        
        # Füge Widgets zum Layout hinzu
        main_layout.addWidget(self._empty_label)
        main_layout.addWidget(self.scroll_area)
        
        # Setze Minimalgröße für das Widget
        self.setMinimumHeight(400)
        
        # Initial Empty State prüfen
        self._check_empty_state()
        
    def update_transfer(self, data: TransferItemData):
        """Aktualisiert einen bestehenden Transfer oder erstellt einen neuen."""
        try:
            current_time = time.time()
            
            # Debounce Updates - aber nicht für wichtige Status-Updates
            if data.status == TransferStatus.RUNNING:
                if data.transfer_id in self._last_update_times:
                    if current_time - self._last_update_times[data.transfer_id] < 0.1:  # 100ms debounce
                        return
                        
            self._last_update_times[data.transfer_id] = current_time
            
            # Cleanup alte Updates
            self._last_update_times = {k: v for k, v in self._last_update_times.items() 
                                     if current_time - v < 1.0}
            
            # Stelle sicher, dass ein Dateiname vorhanden ist
            if not data.filename:
                data.filename = self._get_filename(data.transfer_id)
                
            # Update über Signal aufrufen
            self._update_transfer_signal.emit(data)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Update des Transfer-Items: {e}", exc_info=True)

    def remove_transfer(self, transfer_id: str):
        """Entfernt einen Transfer aus dem Widget."""
        self.logger.debug(f"Entferne Transfer: {transfer_id}")
        self._remove_transfer_signal.emit(transfer_id)

    @pyqtSlot(object)
    def _update_transfer_internal(self, data: TransferItemData):
        """Interne Methode für thread-sicheres Update."""
        try:
            self.logger.debug(f"Internes Update für Transfer {data.transfer_id}")
            
            with QMutexLocker(self.mutex):
                if data.transfer_id not in self._transfer_items:
                    self.logger.info(f"Erstelle neues Transfer-Item für {data.transfer_id}")
                    self._create_transfer_item(data)
                else:
                    self.logger.debug(f"Aktualisiere Transfer-Item {data.transfer_id}")
                    self._update_transfer_item(data)
                    
                # Aktualisiere den Gesamtfortschritt
                self._update_total_progress()
                
        except Exception as e:
            self.logger.error(f"Fehler beim internen Update des Transfer-Items: {e}", exc_info=True)

    def _create_transfer_item(self, data: TransferItemData):
        """Erstellt ein neues Transfer-Item in der GUI."""
        try:
            # Container für das gesamte Transfer-Item
            container = QWidget()
            container.setObjectName(f"transfer_container_{data.transfer_id}")
            container.setStyleSheet(f"""
                QWidget#transfer_container_{data.transfer_id} {{
                    background-color: {StyleHelper.SURFACE};
                    border: 1px solid {StyleHelper.BORDER};
                    border-radius: 4px;
                    margin: 2px 4px;
                }}
            """)
            
            # Layout für das Transfer-Item
            layout = QHBoxLayout(container)
            layout.setContentsMargins(12, 8, 12, 8)
            layout.setSpacing(8)
            
            # Linke Seite (Dateiname und Fortschritt)
            left_widget = QWidget()
            left_layout = QVBoxLayout(left_widget)
            left_layout.setContentsMargins(0, 0, 0, 0)
            left_layout.setSpacing(0)
            
            # Dateiname
            filename = os.path.basename(data.transfer_id)
            filename_label = QLabel(filename)
            filename_label.setObjectName(f"filename_label_{data.transfer_id}")
            filename_label.setStyleSheet(f"""
                QLabel {{
                    color: {StyleHelper.TEXT};
                    font-size: 13px;
                    font-weight: bold;
                }}
            """)
            left_layout.addWidget(filename_label)
            
            # Progress Container
            progress_container = QWidget()
            progress_container.setFixedHeight(16)  # Noch etwas reduzierte Höhe
            progress_container_layout = QVBoxLayout(progress_container)
            progress_container_layout.setContentsMargins(0, 4, 0, 4)  # Reduziertes Padding
            progress_container_layout.setSpacing(0)
            progress_container_layout.setAlignment(Qt.AlignVCenter)
            
            # Fortschrittsbalken
            progress_bar = QProgressBar()
            progress_bar.setObjectName(f"progress_bar_{data.transfer_id}")
            progress_bar.setFixedHeight(2)
            progress_bar.setTextVisible(False)
            progress_bar.setRange(0, 100)
            progress_bar.setValue(0)  # Initialer Wert
            progress_bar.setMinimum(0)
            progress_bar.setMaximum(100)
            progress_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            
            # Setze die Farbe basierend auf dem Status
            bar_color = StyleHelper.PRIMARY if data.status == TransferStatus.RUNNING else StyleHelper.SUCCESS
            progress_bar.setStyleSheet(f"""
                QProgressBar {{
                    min-height: 2px;
                    max-height: 2px;
                    background-color: {StyleHelper.SURFACE_LIGHT};
                    border: none;
                    border-radius: 1px;
                    margin: 0px;
                    padding: 0px;
                }}
                QProgressBar::chunk {{
                    background-color: {bar_color};
                    border-radius: 1px;
                }}
            """)
            progress_container_layout.addWidget(progress_bar)
            
            left_layout.addWidget(progress_container)
            layout.addWidget(left_widget, stretch=1)
            
            # Rechte Seite (Status und Geschwindigkeit)
            right_widget = QWidget()
            right_widget.setStyleSheet("background: transparent;")
            right_layout = QHBoxLayout(right_widget)
            right_layout.setContentsMargins(0, 0, 0, 0)
            right_layout.setSpacing(16)
            
            # Status
            status_label = QLabel()
            status_label.setObjectName(f"status_label_{data.transfer_id}")
            status_label.setStyleSheet(f"""
                QLabel {{
                    color: {StyleHelper.TEXT_SECONDARY};
                    font-size: 12px;
                    background: transparent;
                    padding: 4px 8px;
                    border-radius: 2px;
                }}
            """)
            right_layout.addWidget(status_label)
            
            # Geschwindigkeit
            speed_label = QLabel()
            speed_label.setObjectName(f"speed_label_{data.transfer_id}")
            speed_label.setStyleSheet(f"""
                QLabel {{
                    color: {StyleHelper.TEXT_SECONDARY};
                    font-size: 12px;
                    background: transparent;
                    padding: 4px 8px;
                    border-radius: 2px;
                }}
            """)
            right_layout.addWidget(speed_label)
            
            layout.addWidget(right_widget)
            
            # Füge das Transfer-Item zum Layout hinzu
            self.transfers_layout.insertWidget(self.transfers_layout.count() - 1, container)
            
            # Item speichern
            self._transfer_items[data.transfer_id] = container
            
            # Initial update durchführen
            self._update_transfer_item(data)
            
            # Empty State aktualisieren
            self._check_empty_state()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen des Transfer-Items: {e}", exc_info=True)

    def _update_transfer_item(self, data: TransferItemData):
        """Aktualisiert ein bestehendes Transfer-Item in der GUI."""
        try:
            if data.transfer_id not in self._transfer_items:
                self.logger.warning(f"Transfer-Item nicht gefunden: {data.transfer_id}")
                return
                
            item = self._transfer_items[data.transfer_id]
            
            if not item:
                self.logger.warning(f"Widget für Transfer {data.transfer_id} nicht gefunden")
                return

            # Status aktualisieren
            status_label = item.findChild(QLabel, f"status_label_{data.transfer_id}")
            if status_label:
                status_text = self._get_status_text(data.status)
                status_label.setText(status_text)
                # Setze Hintergrundfarbe basierend auf Status
                if data.status == TransferStatus.COMPLETED:
                    status_label.setStyleSheet(f"""
                        QLabel {{
                            color: {StyleHelper.SUCCESS};
                            background-color: {StyleHelper.SUCCESS}33;
                            border-radius: 2px;
                            padding: 2px 8px;
                            font-size: 12px;
                        }}
                    """)
                else:
                    status_label.setStyleSheet(f"""
                        QLabel {{
                            color: {StyleHelper.TEXT_SECONDARY};
                            background-color: transparent;
                            border-radius: 2px;
                            padding: 4px 8px;
                            font-size: 12px;
                        }}
                    """)

            # Fortschritt aktualisieren (auf 100% begrenzen)
            progress_bar = item.findChild(QProgressBar, f"progress_bar_{data.transfer_id}")
            if progress_bar:
                # Begrenze den Fortschritt auf maximal 100%
                progress = min(max(data.progress if data.progress is not None else 0, 0), 1.0) * 100
                progress_bar.setValue(int(progress))
                
                # Aktualisiere die Farbe basierend auf dem Status
                bar_color = StyleHelper.PRIMARY if data.status == TransferStatus.RUNNING else StyleHelper.SUCCESS
                progress_bar.setStyleSheet(f"""
                    QProgressBar {{
                        min-height: 2px;
                        max-height: 2px;
                        background-color: {StyleHelper.SURFACE_LIGHT};
                        border: none;
                        border-radius: 1px;
                        margin: 0px;
                        padding: 0px;
                    }}
                    QProgressBar::chunk {{
                        background-color: {bar_color};
                        border-radius: 1px;
                    }}
                """)

            # Geschwindigkeit aktualisieren
            speed_label = item.findChild(QLabel, f"speed_label_{data.transfer_id}")
            if speed_label:
                if data.status == TransferStatus.RUNNING and data.speed is not None:
                    speed = min(data.speed, 99999.9)
                    speed_text = f"{speed:.1f} MB/s"
                    speed_label.setText(speed_text)
                    speed_label.show()
                else:
                    speed_label.hide()

            # Sicherstellen, dass das Widget sichtbar bleibt
            item.setVisible(True)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren des Transfer-Items: {e}", exc_info=True)

    @pyqtSlot(str)
    def _remove_transfer_internal(self, transfer_id: str):
        """Interne Methode für thread-sicheres Entfernen."""
        self.logger.debug(f"Entferne Transfer-Item: {transfer_id}")
        try:
            with QMutexLocker(self.mutex):
                if transfer_id in self._transfer_items:
                    item = self._transfer_items.pop(transfer_id)
                    self.transfers_layout.removeWidget(item)
                    item.deleteLater()
                    self.logger.info(f"Transfer-Item entfernt: {transfer_id}")
                else:
                    self.logger.warning(f"Transfer-Item nicht gefunden: {transfer_id}")
                    
        except Exception as e:
            self.logger.error(f"Fehler beim Entfernen des Transfer-Items: {e}", exc_info=True)

    def _update_status_style(self, label: QLabel, status: TransferStatus):
        """Aktualisiert den Style des Status-Labels."""
        if status == TransferStatus.COMPLETED:
            label.setStyleSheet(f"""
                QLabel {{
                    color: {StyleHelper.SUCCESS};
                    background-color: {StyleHelper.SUCCESS}33;
                    border-radius: 2px;
                    padding: 2px 8px;
                    font-size: 12px;
                }}
            """)
        elif status == TransferStatus.RUNNING:
            label.setStyleSheet(f"""
                QLabel {{
                    color: {StyleHelper.PRIMARY};
                    background-color: {StyleHelper.SURFACE_LIGHT};
                    border-radius: 2px;
                    padding: 2px 8px;
                    font-size: 12px;
                }}
            """)
            # Auch den Fortschrittsbalken blau färben
            widget = label.parent()
            if widget:
                progress_bar = widget.findChild(QProgressBar)
                if progress_bar:
                    progress_bar.setStyleSheet(f"""
                        QProgressBar {{
                            border: none;
                            background-color: {StyleHelper.SURFACE_LIGHT};
                            border-radius: 1px;
                            margin: 0;
                            padding: 0;
                        }}
                        QProgressBar::chunk {{
                            background-color: {StyleHelper.PRIMARY};
                            border-radius: 1px;
                        }}
                    """)
        elif status == TransferStatus.ERROR:
            label.setStyleSheet(f"""
                QLabel {{
                    color: {StyleHelper.ERROR};
                    background-color: {StyleHelper.SURFACE_LIGHT};
                    border-radius: 2px;
                    padding: 2px 8px;
                    font-size: 12px;
                }}
            """)
        elif status == TransferStatus.PAUSED:
            label.setStyleSheet(f"""
                QLabel {{
                    color: {StyleHelper.WARNING};
                    background-color: {StyleHelper.SURFACE_LIGHT};
                    border-radius: 2px;
                    padding: 2px 8px;
                    font-size: 12px;
                }}
            """)
        elif status == TransferStatus.QUEUED:
            label.setStyleSheet(f"""
                QLabel {{
                    color: {StyleHelper.TEXT_SECONDARY};
                    background-color: {StyleHelper.SURFACE_LIGHT};
                    border-radius: 2px;
                    padding: 2px 8px;
                    font-size: 12px;
                }}
            """)
        elif status == TransferStatus.CANCELLED:
            label.setStyleSheet(f"""
                QLabel {{
                    color: {StyleHelper.TEXT_SECONDARY};
                    background-color: {StyleHelper.SURFACE_LIGHT};
                    border-radius: 2px;
                    padding: 2px 8px;
                    font-size: 12px;
                }}
            """)

    def _get_status_text(self, status: TransferStatus) -> str:
        """Gibt den Status-Text basierend auf dem Status zurück."""
        status_map = {
            TransferStatus.QUEUED: "Warte",
            TransferStatus.RUNNING: "Kopiere",
            TransferStatus.COMPLETED: "Fertig",
            TransferStatus.ERROR: "Fehler",
            TransferStatus.CANCELLED: "Abgebrochen",
            TransferStatus.PAUSED: "Pausiert"
        }
        return status_map.get(status, str(status))

    def _get_filename(self, transfer_id: str) -> str:
        """Holt den Dateinamen für einen Transfer."""
        try:
            item = self._transfer_items.get(transfer_id)
            if item:
                filename_label = item.findChild(QLabel)
                if filename_label:
                    return filename_label.text()
                        
            # Wenn kein Dateiname gefunden wurde, versuche den Dateinamen aus der Transfer-ID zu extrahieren
            if os.path.sep in transfer_id:
                return os.path.basename(transfer_id)
                
        except Exception as e:
            self.logger.error(f"Fehler beim Holen des Dateinamens: {e}", exc_info=True)
            
        # Fallback: Generiere einen generischen Namen
        return f"Transfer {transfer_id[:8]}"

    def _get_progress(self, transfer_id: str) -> float:
        """Holt den Fortschritt für einen Transfer."""
        try:
            item = self._transfer_items.get(transfer_id)
            if item:
                progress_bar = item.findChild(QProgressBar, f"progress_bar_{transfer_id}")
                if progress_bar:
                    return progress_bar.value() / 100.0
        except Exception as e:
            self.logger.error(f"Fehler beim Holen des Fortschritts: {e}", exc_info=True)
        return 0.0

    @pyqtSlot(str, str)
    def on_transfer_started(self, transfer_id: str, filename: str):
        """Handler für gestartete Transfers.
        
        Args:
            transfer_id: ID des Transfers
            filename: Name der Datei
        """
        self.logger.info(f"Transfer gestartet: {transfer_id} - {filename}")
        try:
            # Stelle sicher, dass ein Dateiname vorhanden ist
            if not filename and os.path.sep in transfer_id:
                filename = os.path.basename(transfer_id)
            elif not filename:
                filename = f"Transfer {transfer_id[:8]}"
                
            # Erstelle TransferItemData
            data = TransferItemData(
                transfer_id=transfer_id,
                filename=filename,
                status=TransferStatus.RUNNING,
                progress=0.0,
                speed=0.0,
                total_bytes=0,
                transferred_bytes=0
            )
            
            # Update über Signal aufrufen
            self._update_transfer_signal.emit(data)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen des Transfer-Items: {e}", exc_info=True)

    @pyqtSlot(str, float, float, timedelta, int, int)
    def on_transfer_progress(self, transfer_id: str, progress: float,
                           speed: float, eta: timedelta,
                           total_bytes: int, transferred_bytes: int):
        """Handler für Transfer-Fortschritt."""
        try:
            filename = self._get_filename(transfer_id)
            if not filename:
                self.logger.warning(f"Kein Dateiname für Transfer {transfer_id} gefunden")
                filename = f"Transfer {transfer_id}"
            
            data = TransferItemData(
                transfer_id=transfer_id,
                filename=filename,
                status=TransferStatus.RUNNING,
                progress=progress,
                speed=speed,
                eta=eta,
                total_bytes=total_bytes,
                transferred_bytes=transferred_bytes
            )
            
            # Update über Signal aufrufen
            self._update_transfer_signal.emit(data)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren des Fortschritts: {e}", exc_info=True)

    @pyqtSlot(str)
    def on_transfer_completed(self, transfer_id: str):
        """Handler für abgeschlossene Transfers."""
        try:
            filename = self._get_filename(transfer_id)
            if not filename:
                self.logger.warning(f"Kein Dateiname für Transfer {transfer_id} gefunden")
                filename = f"Transfer {transfer_id}"
            
            # Hole aktuelle Transfer-Daten
            current_item = self._transfer_items.get(transfer_id)
            total_bytes = 0
            if current_item:
                progress_bar = current_item.findChild(QProgressBar, f"progress_bar_{transfer_id}")
                if progress_bar:
                    total_bytes = progress_bar.property("total_bytes") or 0
            
            data = TransferItemData(
                transfer_id=transfer_id,
                filename=filename,
                status=TransferStatus.COMPLETED,
                progress=1.0,
                speed=0.0,
                total_bytes=total_bytes,
                transferred_bytes=total_bytes
            )
            
            # Update über Signal aufrufen
            self._update_transfer_signal.emit(data)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Abschließen des Transfers: {e}", exc_info=True)

    @pyqtSlot(str, str)
    def on_transfer_error(self, transfer_id: str, error_message: str):
        """Handler für Transfer-Fehler.
        
        Args:
            transfer_id: ID des Transfers
            error_message: Fehlermeldung
        """
        self.logger.debug(f"Transfer Fehler: {transfer_id} - {error_message}")
        try:
            filename = self._get_filename(transfer_id)
            if not filename:
                self.logger.warning(f"Kein Dateiname für Transfer {transfer_id} gefunden")
                filename = f"Transfer {transfer_id}"
            
            data = TransferItemData(
                transfer_id=transfer_id,
                filename=filename,
                status=TransferStatus.ERROR,
                progress=0.0,
                speed=0.0,
                error_message=error_message
            )
            self.update_transfer(data)
        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten des Transfer-Fehlers: {e}", exc_info=True)

    @pyqtSlot(str)
    def on_transfer_paused(self, transfer_id: str):
        """Handler für pausierte Transfers.
        
        Args:
            transfer_id: ID des Transfers
        """
        self.logger.debug(f"Transfer pausiert: {transfer_id}")
        try:
            filename = self._get_filename(transfer_id)
            if not filename:
                self.logger.warning(f"Kein Dateiname für Transfer {transfer_id} gefunden")
                filename = f"Transfer {transfer_id}"
            
            data = TransferItemData(
                transfer_id=transfer_id,
                filename=filename,
                status=TransferStatus.PAUSED,
                progress=self._get_progress(transfer_id),
                speed=0.0
            )
            self.update_transfer(data)
        except Exception as e:
            self.logger.error(f"Fehler beim Pausieren des Transfers: {e}", exc_info=True)

    @pyqtSlot(str)
    def on_transfer_resumed(self, transfer_id: str):
        """Handler für fortgesetzte Transfers.
        
        Args:
            transfer_id: ID des Transfers
        """
        self.logger.debug(f"Transfer fortgesetzt: {transfer_id}")
        try:
            filename = self._get_filename(transfer_id)
            if not filename:
                self.logger.warning(f"Kein Dateiname für Transfer {transfer_id} gefunden")
                filename = f"Transfer {transfer_id}"
            
            data = TransferItemData(
                transfer_id=transfer_id,
                filename=filename,
                status=TransferStatus.RUNNING,
                progress=self._get_progress(transfer_id),
                speed=0.0
            )
            self.update_transfer(data)
        except Exception as e:
            self.logger.error(f"Fehler beim Fortsetzen des Transfers: {e}", exc_info=True)

    @pyqtSlot(str)
    def on_transfer_cancelled(self, transfer_id: str):
        """Handler für abgebrochene Transfers.
        
        Args:
            transfer_id: ID des Transfers
        """
        self.logger.debug(f"Transfer abgebrochen: {transfer_id}")
        try:
            filename = self._get_filename(transfer_id)
            if not filename:
                self.logger.warning(f"Kein Dateiname für Transfer {transfer_id} gefunden")
                filename = f"Transfer {transfer_id}"
            
            data = TransferItemData(
                transfer_id=transfer_id,
                filename=filename,
                status=TransferStatus.CANCELLED,
                progress=self._get_progress(transfer_id),
                speed=0.0
            )
            self.update_transfer(data)
        except Exception as e:
            self.logger.error(f"Fehler beim Abbrechen des Transfers: {e}", exc_info=True)

    def transfer_completed(self, transfer_id: str):
        """Wird aufgerufen, wenn ein Transfer abgeschlossen ist."""
        self.logger.debug(f"Transfer abgeschlossen: {transfer_id}")
        data = TransferItemData(
            transfer_id=transfer_id,
            filename=self._get_filename(transfer_id),
            status=TransferStatus.COMPLETED,
            progress=1.0
        )
        self.update_transfer(data)

    def transfer_error(self, transfer_id: str, error_message: str):
        """Wird aufgerufen, wenn ein Fehler beim Transfer auftritt."""
        self.logger.debug(f"Transfer-Fehler: {transfer_id} - {error_message}")
        data = TransferItemData(
            transfer_id=transfer_id,
            filename=self._get_filename(transfer_id),
            status=TransferStatus.ERROR,
            progress=0.0
        )
        self.update_transfer(data)

    def transfer_paused(self, transfer_id: str):
        """Wird aufgerufen, wenn ein Transfer pausiert wurde."""
        self.logger.debug(f"Transfer pausiert: {transfer_id}")
        data = TransferItemData(
            transfer_id=transfer_id,
            filename=self._get_filename(transfer_id),
            status=TransferStatus.PAUSED
        )
        self.update_transfer(data)

    def transfer_resumed(self, transfer_id: str):
        """Wird aufgerufen, wenn ein Transfer fortgesetzt wurde."""
        self.logger.debug(f"Transfer fortgesetzt: {transfer_id}")
        data = TransferItemData(
            transfer_id=transfer_id,
            filename=self._get_filename(transfer_id),
            status=TransferStatus.RUNNING
        )
        self.update_transfer(data)

    def transfer_cancelled(self, transfer_id: str):
        """Wird aufgerufen, wenn ein Transfer abgebrochen wurde."""
        self.logger.debug(f"Transfer abgebrochen: {transfer_id}")
        data = TransferItemData(
            transfer_id=transfer_id,
            filename=self._get_filename(transfer_id),
            status=TransferStatus.CANCELLED
        )
        self.update_transfer(data)

    def update_transfer_started(self, transfer_id: str, filename: str):
        """Wird aufgerufen, wenn ein Transfer gestartet wurde."""
        self.logger.debug(f"Transfer gestartet: {transfer_id} - {filename}")
        data = TransferItemData(
            transfer_id=transfer_id,
            filename=filename,
            status=TransferStatus.RUNNING,
            progress=0.0,
            speed=0.0,
            eta=timedelta(0),
            total_bytes=0,
            transferred_bytes=0
        )
        self.update_transfer(data)

    def update_transfer_progress(self, transfer_id: str, progress: float,
                               speed: float, eta: timedelta,
                               total_bytes: int, transferred_bytes: int):
        """Wird aufgerufen, wenn sich der Fortschritt eines Transfers ändert."""
        self.logger.debug(f"Transfer Fortschritt: {transfer_id} - {progress:.1%} @ {speed:.1f} MB/s")
        
        # Hole den bestehenden Dateinamen
        filename = self._get_filename(transfer_id)
        if not filename:
            self.logger.warning(f"Kein Dateiname für Transfer {transfer_id} gefunden")
            filename = os.path.basename(transfer_id)
            
        data = TransferItemData(
            transfer_id=transfer_id,
            filename=filename,
            status=TransferStatus.RUNNING,
            progress=progress,
            speed=speed,
            eta=eta,
            total_bytes=total_bytes,
            transferred_bytes=transferred_bytes
        )
        self.update_transfer(data)

    @pyqtSlot(str, str)
    def on_transfer_started(self, transfer_id: str, filename: str):
        """Wird aufgerufen, wenn ein Transfer gestartet wurde."""
        self.logger.debug(f"Transfer gestartet: {transfer_id} - {filename}")
        try:
            data = TransferItemData(
                transfer_id=transfer_id,
                filename=filename,
                status=TransferStatus.QUEUED,
                progress=0.0,
                speed=0.0
            )
            self.update_transfer(data)
        except Exception as e:
            self.logger.error(f"Fehler beim Starten des Transfers: {e}", exc_info=True)

    @pyqtSlot(str, float, float, timedelta, int, int)
    def on_transfer_progress(self, transfer_id: str, progress: float,
                           speed: float, eta: timedelta,
                           total_bytes: int, transferred_bytes: int):
        """Wird aufgerufen, wenn sich der Fortschritt eines Transfers ändert."""
        self.logger.debug(f"Transfer Fortschritt: {transfer_id} - {progress:.1%} @ {speed:.1f} MB/s")
        try:
            filename = self._get_filename(transfer_id)
            if not filename:
                self.logger.warning(f"Kein Dateiname für Transfer {transfer_id} gefunden")
                filename = f"Transfer {transfer_id}"
            
            data = TransferItemData(
                transfer_id=transfer_id,
                filename=filename,
                status=TransferStatus.RUNNING,
                progress=progress,
                speed=speed,
                eta=eta,
                total_bytes=total_bytes,
                transferred_bytes=transferred_bytes
            )
            self.update_transfer(data)
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren des Fortschritts: {e}", exc_info=True)

    @pyqtSlot(str)
    def on_transfer_completed(self, transfer_id: str):
        """Wird aufgerufen, wenn ein Transfer abgeschlossen ist."""
        self.logger.debug(f"Transfer abgeschlossen: {transfer_id}")
        try:
            filename = self._get_filename(transfer_id)
            if not filename:
                self.logger.warning(f"Kein Dateiname für Transfer {transfer_id} gefunden")
                filename = f"Transfer {transfer_id}"
            
            data = TransferItemData(
                transfer_id=transfer_id,
                filename=filename,
                status=TransferStatus.COMPLETED,
                progress=1.0,
                speed=0.0
            )
            self.update_transfer(data)
        except Exception as e:
            self.logger.error(f"Fehler beim Abschließen des Transfers: {e}", exc_info=True)

    @pyqtSlot(str, str)
    def on_transfer_error(self, transfer_id: str, error_message: str):
        """Wird aufgerufen, wenn ein Fehler beim Transfer auftritt."""
        self.logger.debug(f"Transfer Fehler: {transfer_id} - {error_message}")
        try:
            filename = self._get_filename(transfer_id)
            if not filename:
                self.logger.warning(f"Kein Dateiname für Transfer {transfer_id} gefunden")
                filename = f"Transfer {transfer_id}"
            
            data = TransferItemData(
                transfer_id=transfer_id,
                filename=filename,
                status=TransferStatus.ERROR,
                progress=0.0,
                speed=0.0,
                error_message=error_message
            )
            self.update_transfer(data)
        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten des Transfer-Fehlers: {e}", exc_info=True)

    @pyqtSlot(str)
    def on_transfer_paused(self, transfer_id: str):
        """Wird aufgerufen, wenn ein Transfer pausiert wurde."""
        self.logger.debug(f"Transfer pausiert: {transfer_id}")
        try:
            filename = self._get_filename(transfer_id)
            if not filename:
                self.logger.warning(f"Kein Dateiname für Transfer {transfer_id} gefunden")
                filename = f"Transfer {transfer_id}"
            
            data = TransferItemData(
                transfer_id=transfer_id,
                filename=filename,
                status=TransferStatus.PAUSED,
                progress=self._get_progress(transfer_id),
                speed=0.0
            )
            self.update_transfer(data)
        except Exception as e:
            self.logger.error(f"Fehler beim Pausieren des Transfers: {e}", exc_info=True)

    @pyqtSlot(str)
    def on_transfer_resumed(self, transfer_id: str):
        """Wird aufgerufen, wenn ein Transfer fortgesetzt wurde."""
        self.logger.debug(f"Transfer fortgesetzt: {transfer_id}")
        try:
            filename = self._get_filename(transfer_id)
            if not filename:
                self.logger.warning(f"Kein Dateiname für Transfer {transfer_id} gefunden")
                filename = f"Transfer {transfer_id}"
            
            data = TransferItemData(
                transfer_id=transfer_id,
                filename=filename,
                status=TransferStatus.RUNNING,
                progress=self._get_progress(transfer_id),
                speed=0.0
            )
            self.update_transfer(data)
        except Exception as e:
            self.logger.error(f"Fehler beim Fortsetzen des Transfers: {e}", exc_info=True)

    @pyqtSlot(str)
    def on_transfer_cancelled(self, transfer_id: str):
        """Wird aufgerufen, wenn ein Transfer abgebrochen wurde."""
        self.logger.debug(f"Transfer abgebrochen: {transfer_id}")
        try:
            filename = self._get_filename(transfer_id)
            if not filename:
                self.logger.warning(f"Kein Dateiname für Transfer {transfer_id} gefunden")
                filename = f"Transfer {transfer_id}"
            
            data = TransferItemData(
                transfer_id=transfer_id,
                filename=filename,
                status=TransferStatus.CANCELLED,
                progress=self._get_progress(transfer_id),
                speed=0.0
            )
            self.update_transfer(data)
        except Exception as e:
            self.logger.error(f"Fehler beim Abbrechen des Transfers: {e}", exc_info=True)

    def _update_total_progress(self):
        """Aktualisiert den Gesamtfortschritt basierend auf allen aktiven Transfers."""
        try:
            total_progress = 0
            active_count = 0
            
            for i in range(self.transfers_layout.count() - 1):  # -1 für den Stretch
                item = self.transfers_layout.itemAt(i)
                if not item:
                    continue
                    
                widget = item.widget()
                if not widget:
                    continue
                    
                status_label = widget.findChild(QLabel)
                progress_bar = widget.findChild(QProgressBar)
                
                if not status_label or not progress_bar:
                    continue
                    
                status_text = status_label.text()
                if status_text in ["Kopiere", "Pausiert"]:
                    total_progress += progress_bar.value()
                    active_count += 1
                elif status_text == "Fertig":
                    total_progress += 100
                    active_count += 1
                    
            if active_count > 0:
                self._total_progress.setValue(int(total_progress / active_count))
            else:
                self._total_progress.setValue(0)
                
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren des Gesamtfortschritts: {e}", exc_info=True)

    def _check_empty_state(self):
        """Überprüft, ob die Liste leer ist und aktualisiert den Empty-State."""
        try:
            count = self.transfers_layout.count() - 1  # -1 für den Stretch
            self.logger.debug(f"Prüfe Empty State - Anzahl Items: {count}")
            
            if count == 0:
                self._empty_label.show()
                self.transfers_container.hide()
                self.logger.debug("Liste leer - zeige Empty Label")
            else:
                self._empty_label.hide()
                self.transfers_container.show()
                self.logger.debug(f"Liste enthält {count} Items - zeige Transfer-Liste")
                
            # Aktualisiere Layout
            self.transfers_layout.activate()
            self.transfers_container.update()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren des Empty State: {e}", exc_info=True)