"""
Transfer-Sektion der UI.
"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QProgressBar, QLabel, QScrollArea, QFrame, QSpinBox,
    QComboBox
)
from PyQt5.QtCore import Qt
from core.transfer_controller import TransferController
from .widgets.custom_button import CustomButton
from ui.controllers.transfer_controller import TransferController
from core.network.types import QoSLevel

class TransferSection(QWidget):
    """Sektion für die Transfer-Steuerung."""
    
    def __init__(self, transfer_controller: TransferController, parent=None):
        super().__init__(parent)
        self.transfer_controller = transfer_controller
        self.active_transfers = {}
        self.setup_ui()
        
    def setup_ui(self):
        """Richtet das UI der Sektion ein."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Transfer Controls
        controls_layout = QHBoxLayout()
        
        # Start/Stop Buttons
        self.start_button = CustomButton(
            "Start",
            tooltip="Startet den Transfervorgang"
        )
        self.start_button.clicked.connect(self.on_start_clicked)
        controls_layout.addWidget(self.start_button)
        
        self.stop_button = CustomButton(
            "Stop",
            tooltip="Stoppt den Transfervorgang"
        )
        self.stop_button.clicked.connect(self.on_stop_clicked)
        self.stop_button.setEnabled(False)
        controls_layout.addWidget(self.stop_button)
        
        # QoS-Level Auswahl
        qos_label = QLabel("Priorität:")
        qos_label.setStyleSheet("color: white;")
        controls_layout.addWidget(qos_label)
        
        self.qos_combo = QComboBox()
        self.qos_combo.addItems([level.name.capitalize() for level in QoSLevel])
        self.qos_combo.setCurrentText(QoSLevel.NORMAL.name.capitalize())
        self.qos_combo.currentTextChanged.connect(self.on_qos_changed)
        controls_layout.addWidget(self.qos_combo)
        
        # Bandbreitenlimit
        bandwidth_label = QLabel("Bandbreitenlimit (MB/s):")
        bandwidth_label.setStyleSheet("color: white;")
        controls_layout.addWidget(bandwidth_label)
        
        self.bandwidth_spin = QSpinBox()
        self.bandwidth_spin.setRange(0, 1000)  # 0 = unbegrenzt
        self.bandwidth_spin.setValue(0)
        self.bandwidth_spin.valueChanged.connect(self.on_bandwidth_changed)
        controls_layout.addWidget(self.bandwidth_spin)
        
        controls_layout.addStretch()
        
        # Status-Label
        self.status_label = QLabel("Bereit")
        self.status_label.setStyleSheet("color: #2ecc71; font-size: 10pt;")
        controls_layout.addWidget(self.status_label)
        
        layout.addLayout(controls_layout)
        
        # Scroll-Bereich für Transfer-Widgets
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameStyle(QFrame.NoFrame)
        
        # Container für Transfer-Widgets
        self.transfers_container = QWidget()
        self.transfers_layout = QVBoxLayout()
        self.transfers_layout.setContentsMargins(0, 0, 0, 0)
        self.transfers_layout.setSpacing(8)
        self.transfers_layout.addStretch()
        
        self.transfers_container.setLayout(self.transfers_layout)
        scroll.setWidget(self.transfers_container)
        
        layout.addWidget(scroll)
        self.setLayout(layout)
        
    def on_start_clicked(self):
        """Handler für Start-Button."""
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText("Übertragung läuft...")
        self.status_label.setStyleSheet("color: #3498db;")
        
    def on_stop_clicked(self):
        """Handler für Stop-Button."""
        self.stop_button.setEnabled(False)
        self.start_button.setEnabled(True)
        self.status_label.setText("Übertragung gestoppt")
        self.status_label.setStyleSheet("color: #e74c3c;")
        
    def on_qos_changed(self, text: str):
        """Handler für QoS-Level Änderung."""
        level = QoSLevel[text.upper()]
        self.transfer_controller.network_manager.set_qos_level("*", level)
        
    def on_bandwidth_changed(self, value: int):
        """Handler für Bandbreitenlimit Änderung."""
        # Konvertiere MB/s in B/s
        limit = value * 1024 * 1024 if value > 0 else None
        self.transfer_controller.network_manager.bandwidth_limit = limit
        
    def add_transfer(self, transfer_info: dict):
        """Fügt einen neuen Transfer hinzu."""
        widget = TransferWidget(transfer_info)
        widget.cancel.connect(lambda: self.on_transfer_cancel(transfer_info['id']))
        widget.retry.connect(lambda: self.on_transfer_retry(transfer_info['id']))
        
        # Füge Widget vor dem Stretch ein
        self.transfers_layout.insertWidget(
            self.transfers_layout.count() - 1,
            widget
        )
        self.active_transfers[transfer_info['id']] = widget
        
    def update_transfer(self, transfer_id: str, progress: float,
                       speed: float = None, remaining: int = None):
        """Aktualisiert den Fortschritt eines Transfers."""
        if transfer_id in self.active_transfers:
            widget = self.active_transfers[transfer_id]
            widget.update_progress(progress)
            
            if speed is not None:
                widget.update_speed(speed)
            if remaining is not None:
                widget.update_time(remaining)
                
    def complete_transfer(self, transfer_id: str, success: bool):
        """Markiert einen Transfer als abgeschlossen."""
        if transfer_id in self.active_transfers:
            widget = self.active_transfers[transfer_id]
            widget.transfer_info['status'] = (
                TransferStatus.COMPLETED if success
                else TransferStatus.ERROR
            )
            widget.update_status(widget.transfer_info['status'])
            
    def on_transfer_cancel(self, transfer_id: str):
        """Handler für Transfer-Abbruch."""
        if transfer_id in self.active_transfers:
            widget = self.active_transfers[transfer_id]
            widget.transfer_info['status'] = TransferStatus.CANCELLED
            widget.update_status(TransferStatus.CANCELLED)
            
    def on_transfer_retry(self, transfer_id: str):
        """Handler für Transfer-Wiederholung."""
        if transfer_id in self.active_transfers:
            widget = self.active_transfers[transfer_id]
            widget.transfer_info['status'] = TransferStatus.PENDING
            widget.update_status(TransferStatus.PENDING)
            # Starte Transfer neu
            self.transfer_controller.retry_transfer(transfer_id)
