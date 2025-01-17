import unittest
import os
import tempfile
import time
from datetime import datetime
from core.optimized_copy_engine import OptimizedCopyEngine, TransferStats
from unittest.mock import patch
import logging

logger = logging.getLogger(__name__)

class TestOptimizedCopyEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Konfiguriert Logging für Tests."""
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def setUp(self):
        self.engine = OptimizedCopyEngine()
        self.progress_updates = []
        self.engine.set_progress_callback(self._on_progress)
        
    def _on_progress(self, transfer_id: str, progress: float, speed: float):
        """Callback für Fortschrittsupdates."""
        logger.debug(f"Progress Update: {transfer_id} - {progress:.1f}% - {speed/1024/1024:.1f}MB/s")
        self.progress_updates.append({
            'transfer_id': transfer_id,
            'progress': progress,
            'speed': speed,
            'time': datetime.now()
        })
        
    def _cleanup_temp_dir(self, temp_dir: str):
        """Räumt ein temporäres Verzeichnis auf.
        
        Args:
            temp_dir: Pfad zum temporären Verzeichnis
        """
        try:
            # Versuche alle Dateien und Verzeichnisse zu löschen
            for root, dirs, files in os.walk(temp_dir, topdown=False):
                for name in files:
                    try:
                        os.chmod(os.path.join(root, name), 0o777)
                        os.remove(os.path.join(root, name))
                    except Exception as e:
                        logger.warning(f"Fehler beim Löschen von {name}: {e}")
                        
                for name in dirs:
                    try:
                        dir_path = os.path.join(root, name)
                        os.chmod(dir_path, 0o777)
                        os.rmdir(dir_path)
                    except Exception as e:
                        logger.warning(f"Fehler beim Löschen von {name}: {e}")
                        
            # Lösche das Hauptverzeichnis
            os.chmod(temp_dir, 0o777)
            os.rmdir(temp_dir)
            
        except Exception as e:
            logger.warning(f"Fehler beim Aufräumen von {temp_dir}: {e}")
            
    def test_progress_rate_limiting(self):
        # Create a test file
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp.write(b'0' * (10 * 1024 * 1024))  # 10MB file
            source_path = temp.name
            
        target_path = source_path + '.copy'
        transfer_id = 'test_transfer'
        
        try:
            # Start the transfer
            future = self.engine.copy_file(source_path, target_path, transfer_id)
            future.result()  # Wait for completion
            
            # Verify progress updates
            self.assertTrue(len(self.progress_updates) > 0)
            
            # Check rate limiting (excluding first and last updates)
            for i in range(2, len(self.progress_updates) - 1):
                time_diff = (self.progress_updates[i]['time'] - 
                           self.progress_updates[i-1]['time']).total_seconds()
                self.assertGreaterEqual(time_diff, self.engine._min_progress_interval)
                
            # Verify first update is at start
            self.assertEqual(self.progress_updates[0]['progress'], 0.0)
                
            # Verify final progress is 100%
            self.assertEqual(self.progress_updates[-1]['progress'], 100.0)
            
        finally:
            # Cleanup
            for path in [source_path, target_path]:
                if os.path.exists(path):
                    os.remove(path)
                    
    def test_error_handling(self):
        """Testet die Fehlerbehandlung bei verschiedenen Szenarien."""
        # Test: Nicht existierende Quelldatei
        with self.assertRaises(FileNotFoundError):
            future = self.engine.copy_file("nicht_existent.txt", "ziel.txt", "test_transfer")
            future.result()
            
        # Test: Keine Schreibrechte im Zielverzeichnis
        temp_dir = tempfile.mkdtemp()
        try:
            # Erstelle Testdatei
            source_path = os.path.join(temp_dir, "source.txt")
            with open(source_path, 'w') as f:
                f.write("test")
                
            # Erstelle Zielverzeichnis ohne Schreibrechte
            target_dir = os.path.join(temp_dir, "no_write")
            os.makedirs(target_dir)
            
            # Entferne Schreibrechte
            if os.name == 'nt':  # Windows
                import win32security
                import ntsecuritycon as con
                import win32file
                
                # Hole Security-Descriptor
                sd = win32security.GetFileSecurity(
                    target_dir, win32security.DACL_SECURITY_INFORMATION
                )
                
                # Hole DACL
                dacl = sd.GetSecurityDescriptorDacl()
                
                # Entferne alle Rechte
                dacl.DeleteAce(0)  # Lösche alle ACEs
                
                # Setze nur Leserechte für Everyone
                everyone = win32security.ConvertStringSidToSid("S-1-1-0")
                dacl.AddAccessAllowedAce(
                    win32security.ACL_REVISION,
                    con.FILE_GENERIC_READ | con.FILE_LIST_DIRECTORY,
                    everyone
                )
                
                # Hole aktuellen Besitzer
                handle = win32file.CreateFile(
                    target_dir,
                    con.WRITE_OWNER | con.READ_CONTROL,
                    win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE,
                    None,
                    win32file.OPEN_EXISTING,
                    win32file.FILE_FLAG_BACKUP_SEMANTICS,
                    None
                )
                
                try:
                    owner_sid = win32security.GetSecurityInfo(
                        handle,
                        win32security.SE_FILE_OBJECT,
                        win32security.OWNER_SECURITY_INFORMATION
                    ).GetSecurityDescriptorOwner()
                    
                    # Setze explizit Deny-Rechte für den Besitzer
                    dacl.AddAccessDeniedAce(
                        win32security.ACL_REVISION,
                        con.FILE_WRITE_DATA | con.FILE_ADD_FILE | con.FILE_WRITE_EA |
                        con.FILE_WRITE_ATTRIBUTES | con.FILE_DELETE_CHILD,
                        owner_sid
                    )
                    
                finally:
                    win32file.CloseHandle(handle)
                    
                # Setze neuen Security-Descriptor
                sd.SetSecurityDescriptorDacl(1, dacl, 0)
                win32security.SetFileSecurity(
                    target_dir,
                    win32security.DACL_SECURITY_INFORMATION,
                    sd
                )
                
                # Warte kurz, damit die Berechtigungen übernommen werden
                time.sleep(0.1)
                
            else:  # Unix
                os.chmod(target_dir, 0o444)  # Nur Leserechte
                
            # Führe Test durch
            with self.assertRaises(PermissionError):
                future = self.engine.copy_file(
                    source_path,
                    os.path.join(target_dir, "test.txt"),
                    "test_transfer"
                )
                future.result()
                
        finally:
            # Aufräumen
            self._cleanup_temp_dir(temp_dir)
            
    def test_checksum_verification(self):
        """Testet die Prüfsummenberechnung und -verifikation."""
        # Erstelle Testdatei
        test_data = b'0' * 1024  # 1KB Testdaten
        with tempfile.NamedTemporaryFile(delete=False) as source:
            source.write(test_data)
            source_path = source.name
            
        target_path = source_path + '.copy'
        transfer_id = 'test_transfer'
        
        try:
            # Kopiere Datei
            future = self.engine.copy_file(source_path, target_path, transfer_id)
            future.result()
            
            # Berechne und vergleiche Prüfsummen
            source_checksum = self.engine._calculate_checksum(source_path)
            target_checksum = self.engine._calculate_checksum(target_path)
            self.assertEqual(source_checksum, target_checksum)
            
        finally:
            # Aufräumen
            for path in [source_path, target_path]:
                if os.path.exists(path):
                    os.remove(path)
                    
    def test_copy_strategies(self):
        """Testet die Auswahl der Kopierstrategien."""
        test_cases = [
            (5 * 1024 * 1024, 'small'),      # 5MB
            (50 * 1024 * 1024, 'medium'),    # 50MB
            (2 * 1024 * 1024 * 1024, 'large')# 2GB
        ]
        
        for size, expected_strategy in test_cases:
            strategy = self.engine._get_optimal_strategy(size)
            self.assertEqual(strategy, expected_strategy,
                           f"Falsche Strategie für {size} Bytes")

    def test_adaptive_chunk_size(self):
        """Testet die adaptive Chunk-Größen-Anpassung."""
        # Test für kleine Datei
        small_size = 5 * 1024 * 1024  # 5MB
        chunk_size = self.engine._get_optimal_chunk_size(small_size)
        self.assertLessEqual(chunk_size, small_size // 4)
        self.assertGreaterEqual(chunk_size, self.engine._min_chunk_size)
        
        # Test für mittlere Datei
        medium_size = 100 * 1024 * 1024  # 100MB
        chunk_size = self.engine._get_optimal_chunk_size(medium_size)
        self.assertGreaterEqual(chunk_size, self.engine._min_chunk_size)
        self.assertLessEqual(chunk_size, self.engine._max_chunk_size)
        
        # Test für große Datei
        large_size = 2 * 1024 * 1024 * 1024  # 2GB
        chunk_size = self.engine._get_optimal_chunk_size(large_size)
        self.assertGreaterEqual(chunk_size, self.engine._min_chunk_size)
        self.assertLessEqual(chunk_size, self.engine._max_chunk_size)
        
    def test_copy_performance(self):
        """Testet die Kopier-Performance mit verschiedenen Dateigrößen."""
        # Erstelle temporäres Verzeichnis
        temp_dir = tempfile.mkdtemp()
        try:
            # Teste verschiedene Dateigrößen
            sizes = {
                'small': 5 * 1024 * 1024,  # 5 MB
                'medium': 50 * 1024 * 1024,  # 50 MB
                'large': 200 * 1024 * 1024  # 200 MB
            }
            
            for size_type, size in sizes.items():
                # Erstelle Quelldatei
                source_path = os.path.join(temp_dir, f"source_{size_type}.dat")
                target_path = os.path.join(temp_dir, f"target_{size_type}.dat")
                
                # Erstelle Testdatei mit zufälligen Daten
                with open(source_path, 'wb') as f:
                    f.write(os.urandom(size))
                    
                try:
                    # Kopiere Datei
                    future = self.engine.copy_file(
                        source_path,
                        target_path,
                        f"test_transfer_{size_type}"
                    )
                    
                    # Warte auf Abschluss mit Timeout
                    result = future.result(timeout=60)  # Erhöhe Timeout auf 60 Sekunden
                    
                    # Warte kurz um sicherzustellen, dass die Finalisierung abgeschlossen ist
                    time.sleep(0.1)
                    
                    # Prüfe ob Zieldatei existiert
                    self.assertTrue(os.path.exists(target_path), 
                                 f"Zieldatei {target_path} existiert nicht")
                    
                    # Prüfe Dateigröße
                    source_size = os.path.getsize(source_path)
                    target_size = os.path.getsize(target_path)
                    self.assertEqual(
                        source_size,
                        target_size,
                        f"Falsche Dateigröße: {target_size} != {source_size}"
                    )
                    
                    # Prüfe Dateiinhalt
                    with open(source_path, 'rb') as src, open(target_path, 'rb') as dst:
                        self.assertEqual(src.read(), dst.read(), 
                                     "Dateiinhalt stimmt nicht überein")
                        
                except Exception as e:
                    self.fail(f"Fehler beim Kopieren von {size_type} Datei: {e}")
                    
        finally:
            # Räume auf
            self._cleanup_temp_dir(temp_dir)

if __name__ == '__main__':
    unittest.main()
