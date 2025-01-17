import unittest
from unittest.mock import MagicMock, patch
from PyQt5.QtCore import QCoreApplication
import sys
from datetime import datetime
from core.transfer.transfer_coordinator import TransferCoordinator

class TestTransferCoordinator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # QApplication für Signal/Slot-Tests
        cls.app = QCoreApplication(sys.argv)
        
    def setUp(self):
        self.coordinator = TransferCoordinator()
        self.signal_received = []
        
    def _on_transfer_started(self, transfer_id):
        self.signal_received.append(('started', transfer_id))
        
    def _on_transfer_progress(self, transfer_id, progress, speed):
        self.signal_received.append(('progress', transfer_id, progress, speed))
        
    def _on_transfer_completed(self, transfer_id):
        self.signal_received.append(('completed', transfer_id))
        
    def test_signal_emission_order(self):
        """Testet die korrekte Reihenfolge der Signal-Emissionen."""
        # Verbinde Signale
        self.coordinator.transfer_started.connect(self._on_transfer_started)
        self.coordinator.transfer_progress.connect(self._on_transfer_progress)
        self.coordinator.transfer_completed.connect(self._on_transfer_completed)
        
        # Starte Test-Transfer
        transfer_id = "test_transfer"
        source = "test_source.txt"
        target = "test_target.txt"
        
        with patch('core.transfer.transfer_coordinator.CopyEngineAdapter') as mock_engine:
            # Mock Engine-Verhalten
            mock_engine.return_value.start_transfer.return_value.result.return_value = True
            
            # Führe Transfer aus
            self.coordinator.start_transfer(source, target)
            
            # Prüfe Signal-Reihenfolge
            self.assertTrue(len(self.signal_received) >= 3)
            self.assertEqual(self.signal_received[0][0], 'started')
            self.assertEqual(self.signal_received[-1][0], 'completed')
            
    def test_concurrent_transfers(self):
        """Testet das Verhalten bei gleichzeitigen Transfers."""
        transfers = [
            ("source1.txt", "target1.txt"),
            ("source2.txt", "target2.txt"),
            ("source3.txt", "target3.txt")
        ]
        
        with patch('core.transfer.transfer_coordinator.CopyEngineAdapter') as mock_engine:
            # Mock Engine-Verhalten
            mock_engine.return_value.start_transfer.return_value.result.return_value = True
            
            # Starte mehrere Transfers
            transfer_ids = []
            for source, target in transfers:
                transfer_id = self.coordinator.start_transfer(source, target)
                transfer_ids.append(transfer_id)
                
            # Prüfe ob alle Transfers gestartet wurden
            self.assertEqual(len(self.coordinator._active_transfers), len(transfers))
            
    def test_error_handling(self):
        """Testet die Fehlerbehandlung bei Transfer-Fehlern."""
        self.error_received = False
        
        def on_error(transfer_id, error):
            self.error_received = True
            
        self.coordinator.transfer_error.connect(on_error)
        
        with patch('core.transfer.transfer_coordinator.CopyEngineAdapter') as mock_engine:
            # Simuliere Fehler
            mock_engine.return_value.start_transfer.side_effect = Exception("Test Error")
            
            # Starte Transfer
            self.coordinator.start_transfer("source.txt", "target.txt")
            
            # Prüfe ob Fehler-Signal empfangen wurde
            self.assertTrue(self.error_received)
            
    def test_batch_operations(self):
        """Testet Batch-Transfer Operationen."""
        batch_started = False
        batch_completed = False
        
        def on_batch_started(batch_id):
            nonlocal batch_started
            batch_started = True
            
        def on_batch_completed(batch_id):
            nonlocal batch_completed
            batch_completed = True
            
        self.coordinator.batch_started.connect(on_batch_started)
        self.coordinator.batch_completed.connect(on_batch_completed)
        
        # Erstelle Batch
        files = [("source1.txt", "target1.txt"), ("source2.txt", "target2.txt")]
        
        with patch('core.transfer.transfer_coordinator.CopyEngineAdapter') as mock_engine:
            mock_engine.return_value.start_transfer.return_value.result.return_value = True
            
            # Starte Batch-Transfer
            self.coordinator.start_batch_transfer(files)
            
            # Prüfe Batch-Signale
            self.assertTrue(batch_started)
            self.assertTrue(batch_completed)

if __name__ == '__main__':
    unittest.main()
