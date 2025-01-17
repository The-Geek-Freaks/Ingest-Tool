#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tests für das ModernTransferWidget."""

import sys
import pytest
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Initialisiere QApplication vor den Imports
app = QApplication(sys.argv)

from ui.widgets.modern_transfer_widget import ModernTransferWidget, TransferStatus, TransferItemData

@pytest.fixture(scope="session")
def qapp():
    return app

@pytest.fixture
def widget(qapp):
    return ModernTransferWidget()

def test_create_transfer(widget):
    """Test, dass ein neuer Transfer korrekt erstellt wird."""
    # Arrange
    transfer_id = "test-1"
    filename = "test.mp4"
    status = TransferStatus.RUNNING
    progress = 0.0
    speed = 1024 * 1024  # 1 MB/s
    eta = timedelta(minutes=1)
    
    # Act
    widget.update_transfer(
        transfer_id=transfer_id,
        filename=filename,
        status=status,
        progress=progress,
        speed=speed,
        eta=eta
    )
    
    # Assert
    assert transfer_id in widget._transfer_data
    data = widget._transfer_data[transfer_id]
    assert data.filename == filename
    assert data.progress == progress
    assert data.speed == speed

def test_update_transfer_progress(widget):
    """Test, dass der Fortschritt korrekt aktualisiert wird."""
    # Arrange
    transfer_id = "test-2"
    filename = "test.mp4"
    status = TransferStatus.RUNNING
    
    # Initial transfer
    widget.update_transfer(
        transfer_id=transfer_id,
        filename=filename,
        status=status,
        progress=0.0,
        speed=1024 * 1024,
        eta=timedelta(minutes=1)
    )
    
    # Update progress
    widget.update_transfer(
        transfer_id=transfer_id,
        filename=filename,
        status=status,
        progress=0.5,
        speed=2048 * 1024,
        eta=timedelta(seconds=30)
    )
    
    # Assert
    assert transfer_id in widget._transfer_data
    data = widget._transfer_data[transfer_id]
    assert data.progress == 0.5
    assert data.speed == 2048 * 1024

def test_handle_error(widget):
    """Test, dass Fehler korrekt behandelt werden."""
    # Arrange
    transfer_id = "test-3"
    filename = "test.mp4"
    
    # Initial transfer
    widget.update_transfer(
        transfer_id=transfer_id,
        filename=filename,
        status=TransferStatus.RUNNING,
        progress=0.0,
        speed=1024 * 1024,
        eta=timedelta(minutes=1)
    )
    
    # Update with error
    widget.update_transfer(
        transfer_id=transfer_id,
        filename=filename,
        status=TransferStatus.ERROR,
        progress=0.3,
        speed=0,
        eta=None,
        error_message="Test error"
    )
    
    # Assert
    assert transfer_id in widget._transfer_data
    data = widget._transfer_data[transfer_id]
    assert data.status == TransferStatus.ERROR
    assert data.error_message == "Test error"

def test_remove_transfer(widget):
    """Test, dass Transfers korrekt entfernt werden."""
    # Arrange
    transfer_id = "test-4"
    filename = "test.mp4"
    
    widget.update_transfer(
        transfer_id=transfer_id,
        filename=filename,
        status=TransferStatus.RUNNING,
        progress=0.0,
        speed=1024 * 1024,
        eta=timedelta(minutes=1)
    )
    
    # Act
    widget.remove_transfer(transfer_id)
    
    # Assert
    assert transfer_id not in widget._transfer_data
    assert transfer_id not in widget._transfer_widgets

def test_multiple_transfers(widget):
    """Test, dass mehrere Transfers parallel verarbeitet werden können."""
    # Arrange
    transfers = [
        ("test-5", "video1.mp4"),
        ("test-6", "video2.mp4"),
        ("test-7", "video3.mp4")
    ]
    
    # Act
    for transfer_id, filename in transfers:
        widget.update_transfer(
            transfer_id=transfer_id,
            filename=filename,
            status=TransferStatus.RUNNING,
            progress=0.0,
            speed=1024 * 1024,
            eta=timedelta(minutes=1)
        )
        
    # Assert
    assert len(widget._transfer_widgets) == len(transfers)
    for transfer_id, _ in transfers:
        assert transfer_id in widget._transfer_data

def test_recursion_prevention(widget):
    """Test, dass keine Rekursion bei schnellen Updates auftritt."""
    # Arrange
    transfer_id = "test-recursive"
    filename = "test.mp4"
    status = TransferStatus.RUNNING
    progress = 0.0
    speed = 1024 * 1024  # 1 MB/s
    eta = timedelta(minutes=1)
    
    # Act - Versuche schnelle Updates durchzuführen
    for i in range(10):
        progress = i / 10.0
        widget.update_transfer(
            transfer_id=transfer_id,
            filename=filename,
            status=status,
            progress=progress,
            speed=speed,
            eta=eta
        )
        
    # Assert
    assert widget._is_updating is False  # Flag sollte am Ende False sein
    assert transfer_id in widget._transfer_data
    data = widget._transfer_data[transfer_id]
    assert data.progress == 0.9  # Letzter Update sollte durchgekommen sein

def test_signal_connections(widget, qtbot):
    """Test, dass Signale korrekt verbunden sind und keine Rekursion verursachen."""
    # Arrange
    transfer_id = "test-signals"
    filename = "test.mp4"
    status = TransferStatus.RUNNING
    progress = 0.5
    
    # Act - Verbinde einen Signal-Handler
    signals_received = []
    def on_transfer_retry(tid):
        signals_received.append(tid)
        # Versuche während der Signal-Verarbeitung ein Update durchzuführen
        widget.update_transfer(
            transfer_id=tid,
            filename=filename,
            status=status,
            progress=progress,
            speed=1024 * 1024,
            eta=timedelta(minutes=1)
        )
    
    widget.transfer_retry.connect(on_transfer_retry)
    
    # Emittiere das Signal
    widget.transfer_retry.emit(transfer_id)
    
    # Assert
    assert len(signals_received) == 1  # Signal sollte genau einmal empfangen worden sein
    assert signals_received[0] == transfer_id
    assert widget._is_updating is False  # Flag sollte am Ende False sein
