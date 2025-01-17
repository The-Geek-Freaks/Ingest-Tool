#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Integration test for the transfer signal chain."""

import os
import shutil
import uuid
import tempfile
from datetime import timedelta
import pytest
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

# Global PyQt app for tests
if not QApplication.instance():
    app = QApplication([])

from core.file_watcher_manager import FileWatcherManager
from core.transfer.transfer_coordinator import TransferCoordinator
from core.optimized_copy_engine import OptimizedCopyEngine
from ui.widgets.modern_transfer_widget import ModernTransferWidget, TransferStatus, TransferItemData

class SignalSpy:
    """Helper class to record signals."""
    def __init__(self):
        self.signals = []
        
    def slot(self, *args):
        """Store signal parameters."""
        self.signals.append(args)
        
    def clear(self):
        """Clear all recorded signals."""
        self.signals = []

@pytest.fixture
def temp_dirs():
    """Create temporary directories for source and target."""
    source_dir = tempfile.mkdtemp()
    target_dir = tempfile.mkdtemp()
    
    # Create a test file
    test_file = os.path.join(source_dir, "test.mp4")
    with open(test_file, "wb") as f:
        f.write(os.urandom(1024 * 1024))  # 1 MB test file
        
    yield source_dir, target_dir, test_file
    
    # Cleanup
    shutil.rmtree(source_dir)
    try:
        shutil.rmtree(target_dir)
    except FileNotFoundError:
        pass  # Ignore if directory already deleted

@pytest.fixture
def components(temp_dirs):
    """Create and connect all components."""
    source_dir, target_dir, test_file = temp_dirs
    
    # Create components
    file_watcher = FileWatcherManager(None)  # None as main_window for tests
    copy_engine = OptimizedCopyEngine()
    coordinator = TransferCoordinator()
    widget = ModernTransferWidget()
    
    # Connect signals
    coordinator.transfer_started.connect(lambda transfer_id, filename: 
        widget.update_transfer(TransferItemData(
            transfer_id=transfer_id, 
            filename=filename, 
            status=TransferStatus.RUNNING,
            progress=0.0,
            speed=0.0,
            eta=timedelta(seconds=0),
            total_bytes=0,
            transferred_bytes=0
        ))
    )
    
    coordinator.transfer_progress.connect(lambda transfer_id, filename, progress, speed, eta, total_bytes, transferred_bytes:
        widget.update_transfer(TransferItemData(
            transfer_id=transfer_id, 
            filename=filename, 
            status=TransferStatus.RUNNING, 
            progress=progress, 
            speed=speed, 
            eta=eta,
            total_bytes=total_bytes,
            transferred_bytes=transferred_bytes
        ))
    )
    
    coordinator.transfer_completed.connect(lambda transfer_id:
        widget.update_transfer(TransferItemData(
            transfer_id=transfer_id, 
            filename="", 
            status=TransferStatus.COMPLETED, 
            progress=1.0,
            speed=0.0,
            eta=timedelta(seconds=0),
            total_bytes=0,
            transferred_bytes=0
        ))
    )
    
    coordinator.transfer_error.connect(lambda transfer_id, error_message:
        widget.update_transfer(TransferItemData(
            transfer_id=transfer_id, 
            filename="", 
            status=TransferStatus.ERROR, 
            progress=0.0,
            speed=0.0,
            eta=timedelta(seconds=0),
            total_bytes=0,
            transferred_bytes=0,
            error_message=error_message
        ))
    )

    return {
        'file_watcher': file_watcher,
        'copy_engine': copy_engine,
        'coordinator': coordinator,
        'widget': widget,
        'source_dir': source_dir,
        'target_dir': target_dir,
        'test_file': test_file
    }

def test_transfer_signal_chain(components, temp_dirs):
    """Test that all signals propagate correctly through the chain."""
    source_dir, target_dir, test_file = temp_dirs
    
    # Spy on signals
    progress_spy = SignalSpy()
    components['coordinator'].transfer_progress.connect(progress_spy.slot)
    
    # Start transfer directly via copy engine
    target_file = os.path.join(target_dir, "test.mp4")
    transfer_id = str(uuid.uuid4())
    
    # Send transfer start signal
    components['coordinator'].transfer_started.emit(transfer_id, os.path.basename(test_file))
    
    def progress_callback(progress: float, speed: float, total_bytes: int, transferred_bytes: int):
        components['coordinator'].transfer_progress.emit(
            transfer_id,
            os.path.basename(test_file),
            progress,
            speed,
            timedelta(seconds=0),  # ETA not calculated in tests
            total_bytes,
            transferred_bytes
        )

    components['copy_engine'].set_progress_callback(progress_callback)
    components['copy_engine'].copy_file(test_file, target_file)
    
    # Send transfer complete signal
    components['coordinator'].transfer_completed.emit(transfer_id)
    
    # Wait for signals
    QTimer.singleShot(1000, lambda: app.quit())
    app.exec_()
    
    # Check signals
    assert len(progress_spy.signals) > 0, "No progress signals received"

def test_error_signal_chain(components, temp_dirs):
    """Test that error signals propagate correctly through the chain."""
    source_dir, target_dir, test_file = temp_dirs
    
    # Spy on signals
    error_spy = SignalSpy()
    components['coordinator'].transfer_error.connect(error_spy.slot)
    
    # Delete target directory to provoke error
    shutil.rmtree(target_dir)
    
    # Start transfer directly via copy engine
    target_file = os.path.join(target_dir, "test.mp4")
    transfer_id = str(uuid.uuid4())
    
    # Send transfer start signal
    components['coordinator'].transfer_started.emit(transfer_id, os.path.basename(test_file))
    
    try:
        components['copy_engine'].copy_file(test_file, target_file)
    except FileNotFoundError as e:
        # Error expected since target directory doesn't exist
        components['coordinator'].transfer_error.emit(transfer_id, str(e))
    
    # Wait for signals
    QTimer.singleShot(1000, lambda: app.quit())
    app.exec_()
    
    # Check if error signal was received
    assert len(error_spy.signals) > 0, "No error signal received"
