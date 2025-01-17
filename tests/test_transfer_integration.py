#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Integrationstests für das Transfer-System.
"""

import os
import sys
import shutil
import tempfile
import unittest
import time
from datetime import datetime, timedelta
from PyQt5.QtCore import QObject, QTimer, QEventLoop
from PyQt5.QtWidgets import QApplication

from core.transfer.transfer_coordinator import TransferCoordinator
from core.transfer.exceptions import TransferError

class TestTransferIntegration(unittest.TestCase):
    """Integrationstests für das Transfer-System."""
    
    @classmethod
    def setUpClass(cls):
        """Klassen-Setup."""
        # Initialisiere QApplication für alle Tests
        cls.app = QApplication.instance()
        if not cls.app:
            cls.app = QApplication(sys.argv)
    
    def setUp(self):
        """Test-Setup."""
        self.test_dir = tempfile.mkdtemp()
        self.source_dir = os.path.join(self.test_dir, 'source')
        self.target_dir = os.path.join(self.test_dir, 'target')
        
        # Erstelle Test-Verzeichnisse
        os.makedirs(self.source_dir)
        os.makedirs(self.target_dir)
        
        # Erstelle Test-Dateien
        self.test_files = []
        for i in range(2):
            source_file = os.path.join(self.source_dir, f'test_file_{i}.txt')
            with open(source_file, 'w') as f:
                f.write(f'Test content {i}')
            self.test_files.append(source_file)
            
        # Initialisiere TransferCoordinator
        self.coordinator = TransferCoordinator()
        
        # Signal-Tracking
        self.signals_received = {
            'transfer_started': [],
            'transfer_completed': [],
            'transfer_error': [],
            'batch_started': [],
            'batch_completed': [],
            'batch_error': []
        }
        
        # Event Loop für asynchrone Signale
        self.loop = QEventLoop()
        self.timer = QTimer()
        self.timer.setInterval(5000)  # 5 Sekunden Timeout
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._on_timeout)
        
        # Verbinde Signale
        self._connect_signals()
            
    def tearDown(self):
        """Test-Cleanup."""
        shutil.rmtree(self.test_dir)
        self._disconnect_signals()
        
    def _connect_signals(self):
        """Verbindet alle Signale."""
        self.coordinator.transfer_started.connect(
            lambda transfer_id: self._handle_signal('transfer_started', transfer_id))
        self.coordinator.transfer_completed.connect(
            lambda transfer_id: self._handle_signal('transfer_completed', transfer_id))
        self.coordinator.transfer_error.connect(
            lambda transfer_id, error: self._handle_signal('transfer_error', (transfer_id, error)))
        self.coordinator.batch_started.connect(
            lambda batch_id: self._handle_signal('batch_started', batch_id))
        self.coordinator.batch_completed.connect(
            lambda batch_id: self._handle_signal('batch_completed', batch_id))
        self.coordinator.batch_error.connect(
            lambda batch_id, error: self._handle_signal('batch_error', (batch_id, error)))
            
    def _disconnect_signals(self):
        """Trennt alle Signal-Verbindungen."""
        try:
            self.coordinator.transfer_started.disconnect()
            self.coordinator.transfer_completed.disconnect()
            self.coordinator.transfer_error.disconnect()
            self.coordinator.batch_started.disconnect()
            self.coordinator.batch_completed.disconnect()
            self.coordinator.batch_error.disconnect()
        except:
            pass
            
    def _handle_signal(self, signal_name: str, data):
        """Verarbeitet empfangene Signale."""
        self.signals_received[signal_name].append(data)
        self.loop.quit()
            
    def _on_timeout(self):
        """Wird aufgerufen wenn der Timer abläuft."""
        self.loop.quit()
        self.fail("Timeout beim Warten auf Signal")
            
    def _wait_for_signal(self, signal_name: str, expected_id: str, timeout: int = 5000):
        """Wartet auf ein bestimmtes Signal."""
        if expected_id not in self.signals_received[signal_name]:
            self.timer.start(timeout)
            self.loop.exec_()
            QApplication.processEvents()
            
            # Prüfe ob das Signal empfangen wurde
            self.assertIn(expected_id, self.signals_received[signal_name],
                         f"Signal {signal_name} für ID {expected_id} nicht empfangen")
        
    def test_single_transfer(self):
        """Testet einen einzelnen Transfer."""
        source_file = self.test_files[0]
        target_file = os.path.join(self.target_dir, os.path.basename(source_file))
        
        # Starte Transfer
        transfer_id = self.coordinator.start_transfer(source_file, target_file)
        
        # Warte auf Start-Signal
        self._wait_for_signal('transfer_started', transfer_id)
        
        # Warte auf Abschluss-Signal
        self._wait_for_signal('transfer_completed', transfer_id)
        
        # Prüfe Ergebnis
        self.assertTrue(transfer_id in self.signals_received['transfer_started'])
        self.assertTrue(transfer_id in self.signals_received['transfer_completed'])
        self.assertTrue(os.path.exists(target_file))
        
    def test_batch_transfer(self):
        """Testet einen Batch-Transfer."""
        transfers = []
        for source_file in self.test_files:
            target_file = os.path.join(self.target_dir, os.path.basename(source_file))
            transfers.append((source_file, target_file))
            
        # Starte Batch
        batch_id = self.coordinator.start_batch_transfer(transfers)
        
        # Warte auf Batch-Start
        self._wait_for_signal('batch_started', batch_id)
        
        # Warte auf Batch-Abschluss
        self._wait_for_signal('batch_completed', batch_id)
        
        # Prüfe Ergebnis
        self.assertTrue(batch_id in self.signals_received['batch_started'])
        self.assertTrue(batch_id in self.signals_received['batch_completed'])
        
        # Prüfe, ob alle Dateien übertragen wurden
        for source_file in self.test_files:
            target_file = os.path.join(self.target_dir, os.path.basename(source_file))
            self.assertTrue(os.path.exists(target_file))
            
    def test_transfer_error(self):
        """Testet Fehlerbehandlung bei Transfers."""
        # Nicht existierende Quelldatei
        source_file = os.path.join(self.source_dir, 'non_existent.txt')
        target_file = os.path.join(self.target_dir, 'non_existent.txt')
        
        # Starte Transfer
        transfer_id = self.coordinator.start_transfer(source_file, target_file)
        
        # Warte auf Start-Signal
        self._wait_for_signal('transfer_started', transfer_id)
        
        # Warte auf Fehler-Signal
        self._wait_for_signal('transfer_error', transfer_id)
        
        # Prüfe Ergebnis
        error_transfers = [t[0] for t in self.signals_received['transfer_error']]
        self.assertTrue(transfer_id in error_transfers)
        self.assertFalse(os.path.exists(target_file))
        
if __name__ == '__main__':
    unittest.main()
