import unittest
import tempfile
import os
import shutil
from datetime import datetime
from core.optimized_copy_engine import OptimizedCopyEngine
from core.transfer.transfer_coordinator import TransferCoordinator
from PyQt5.QtCore import QCoreApplication
import sys

class TestBatchTransfers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # QApplication für Signal/Slot-Tests
        cls.app = QCoreApplication(sys.argv)
        
    def setUp(self):
        self.coordinator = TransferCoordinator()
        self.test_dir = tempfile.mkdtemp()
        self.source_files = []
        self.progress_updates = []
        
        # Verbinde Signale
        self.coordinator.batch_progress.connect(self._on_batch_progress)
        self.coordinator.batch_completed.connect(self._on_batch_completed)
        self.coordinator.batch_error.connect(self._on_batch_error)
        
    def tearDown(self):
        # Aufräumen
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
    def _create_test_file(self, size_mb):
        """Erstellt eine Testdatei mit gegebener Größe."""
        path = os.path.join(self.test_dir, f"test_file_{size_mb}mb.dat")
        with open(path, 'wb') as f:
            f.write(b'0' * (size_mb * 1024 * 1024))
        self.source_files.append(path)
        return path
        
    def _on_batch_progress(self, batch_id, progress, speed, eta):
        self.progress_updates.append({
            'time': datetime.now(),
            'batch_id': batch_id,
            'progress': progress,
            'speed': speed,
            'eta': eta
        })
        
    def _on_batch_completed(self, batch_id):
        self.batch_completed = True
        
    def _on_batch_error(self, batch_id, error):
        self.batch_error = error
        
    def test_large_batch_transfer(self):
        """Testet Batch-Transfer mit verschiedenen Dateigrößen."""
        # Erstelle Testdateien
        file_sizes = [1, 10, 50]  # MB
        target_dir = os.path.join(self.test_dir, "target")
        os.makedirs(target_dir)
        
        transfers = []
        for size in file_sizes:
            source = self._create_test_file(size)
            target = os.path.join(target_dir, os.path.basename(source))
            transfers.append((source, target))
            
        # Starte Batch-Transfer
        self.batch_completed = False
        self.batch_error = None
        batch_id = self.coordinator.start_batch_transfer(transfers)
        
        # Warte auf Abschluss (in echtem Code würde man einen Event Loop verwenden)
        timeout = 30  # Sekunden
        start_time = datetime.now()
        while not self.batch_completed and not self.batch_error:
            QCoreApplication.processEvents()
            if (datetime.now() - start_time).total_seconds() > timeout:
                self.fail("Timeout beim Warten auf Batch-Abschluss")
                
        # Prüfe Ergebnis
        self.assertIsNone(self.batch_error, f"Batch-Transfer fehlgeschlagen: {self.batch_error}")
        self.assertTrue(self.batch_completed)
        
        # Prüfe ob alle Dateien kopiert wurden
        for source, target in transfers:
            self.assertTrue(os.path.exists(target))
            self.assertEqual(os.path.getsize(source), os.path.getsize(target))
            
        # Prüfe Fortschrittsupdates
        self.assertGreater(len(self.progress_updates), 0)
        self.assertEqual(self.progress_updates[-1]['progress'], 100.0)
        
    def test_batch_cancellation(self):
        """Testet das Abbrechen eines Batch-Transfers."""
        # Erstelle große Testdateien
        transfers = []
        target_dir = os.path.join(self.test_dir, "target")
        os.makedirs(target_dir)
        
        # Erstelle 3 große Dateien (100MB)
        for i in range(3):
            source = self._create_test_file(100)
            target = os.path.join(target_dir, os.path.basename(source))
            transfers.append((source, target))
            
        # Starte Batch-Transfer
        self.batch_completed = False
        self.batch_error = None
        batch_id = self.coordinator.start_batch_transfer(transfers)
        
        # Warte kurz und breche dann ab
        QCoreApplication.processEvents()
        self.coordinator.cancel_batch(batch_id)
        
        # Prüfe ob alle temporären Dateien aufgeräumt wurden
        for _, target in transfers:
            self.assertFalse(os.path.exists(target + ".tmp"))
            
if __name__ == '__main__':
    unittest.main()
