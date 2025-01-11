"""
Netzwerk-Kopier-Manager für Dateiübertragungen.
"""
import os
import time
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from queue import Queue

from .types import NetworkPath, TransferStatus, QoSLevel
from .errors import CopyAborted, CopyVerificationError
from .utils import (
    calculate_buffer_size,
    parse_robocopy_progress,
    parse_rsync_progress
)

class NetworkCopyManager:
    """Verwaltet Netzwerk-Kopieroperationen."""
    
    def __init__(self, progress_callback: Optional[Callable] = None,
                 error_callback: Optional[Callable] = None):
        self.progress_callback = progress_callback
        self.error_callback = error_callback
        self.abort_requested = False
        
        # Optimale Puffergrößen
        self.NETWORK_BUFFER = 4 * 1024 * 1024   # 4MB für Netzwerk
        self.LOCAL_BUFFER = 16 * 1024 * 1024    # 16MB für lokale Kopien
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 2  # Sekunden
        
        self._network_path_cache: Dict[str, tuple] = {}
        self._cache_lifetime = 300  # Cache-Gültigkeit in Sekunden
        
        # Erweiterte Konfiguration
        self.max_parallel_transfers = 4
        self.bandwidth_limit = None  # in KB/s, None = unbegrenzt
        self.enable_qos = False
        
        # Fehlerbehandlung
        self.error_log = []
        self.recovery_mode = False
        
        # QoS Einstellungen
        self.qos_settings = {
            'high': QoSLevel.HIGH,
            'normal': QoSLevel.NORMAL,
            'low': QoSLevel.LOW
        }
        
        # Standard Robocopy-Argumente
        self.default_robocopy_args = [
            '/E',           # Kopiert Unterverzeichnisse, auch leere
            '/Z',           # Kopiert im Wiederaufnahme-Modus
            '/R:3',         # 3 Wiederholungsversuche
            '/W:5',         # 5 Sekunden Wartezeit zwischen Versuchen
            '/MT:8',        # 8 Threads
            '/NFL',         # Keine Dateiliste
            '/NDL'          # Keine Verzeichnisliste
        ]
        
        # Standard rsync-Argumente
        self.default_rsync_args = [
            '-av',          # Archiv-Modus und ausführliche Ausgabe
            '--progress',   # Zeigt Fortschritt
            '--partial',    # Behält teilweise übertragene Dateien
            '--stats'       # Zeigt Übertragungsstatistik
        ]
        
    def copy_file(self, source: str, target: str,
                 bandwidth_limit: Optional[int] = None,
                 qos_level: Optional[QoSLevel] = None) -> bool:
        """Kopiert eine Datei mit optimaler Methode."""
        source_path = NetworkPath.from_path(source)
        target_path = NetworkPath.from_path(target)
        
        # Bestimme optimale Kopiermethode
        if os.name == 'nt' and (source_path.is_network or target_path.is_network):
            return self.copy_with_robocopy(source, target,
                                         bandwidth_limit, qos_level)
        elif os.name != 'nt' and (source_path.is_network or target_path.is_network):
            return self.copy_with_rsync(source, target,
                                      bandwidth_limit, qos_level)
        else:
            return self._copy_with_python(source, target,
                                        bandwidth_limit, qos_level)
            
    def copy_with_robocopy(self, source: str, target: str,
                          bandwidth_limit: Optional[int] = None,
                          qos_level: Optional[QoSLevel] = None) -> bool:
        """Kopiert Dateien mit Robocopy."""
        args = self.default_robocopy_args.copy()
        
        # Bandbreitenlimit
        if bandwidth_limit:
            args.append(f'/IPG:{int(1000/bandwidth_limit)}')  # IPG in ms
            
        # QoS-Level
        if qos_level and self.enable_qos:
            from .utils import set_qos_policy
            set_qos_policy(source, qos_level.value)
            
        # Führe Robocopy aus
        cmd = ['robocopy', source, target] + args
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Überwache Fortschritt
            while True:
                if self.abort_requested:
                    process.terminate()
                    raise CopyAborted("Kopiervorgang abgebrochen")
                    
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                    
                progress = parse_robocopy_progress(line)
                if progress and self.progress_callback:
                    self.progress_callback(progress)
                    
            return process.returncode in [0, 1]  # 0=OK, 1=OK mit Änderungen
            
        except Exception as e:
            if self.error_callback:
                self.error_callback(str(e))
            return False
            
    def copy_with_rsync(self, source: str, target: str,
                        bandwidth_limit: Optional[int] = None,
                        qos_level: Optional[QoSLevel] = None) -> bool:
        """Kopiert Dateien mit rsync."""
        args = self.default_rsync_args.copy()
        
        # Bandbreitenlimit (KB/s)
        if bandwidth_limit:
            args.append(f'--bwlimit={bandwidth_limit}')
            
        # QoS-Level (via ionice)
        ionice_cmd = []
        if qos_level and self.enable_qos:
            ionice_cmd = ['ionice', '-c2', f'-n{qos_level.value}']
            
        # Führe rsync aus
        cmd = ionice_cmd + ['rsync'] + args + [source, target]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Überwache Fortschritt
            while True:
                if self.abort_requested:
                    process.terminate()
                    raise CopyAborted("Kopiervorgang abgebrochen")
                    
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                    
                progress = parse_rsync_progress(line)
                if progress and self.progress_callback:
                    self.progress_callback(progress)
                    
            return process.returncode == 0
            
        except Exception as e:
            if self.error_callback:
                self.error_callback(str(e))
            return False
            
    def _copy_with_python(self, source: str, target: str,
                         bandwidth_limit: Optional[int] = None,
                         qos_level: Optional[QoSLevel] = None) -> bool:
        """Kopiert Dateien mit Python."""
        try:
            # Erstelle Zielverzeichnis
            os.makedirs(os.path.dirname(target), exist_ok=True)
            
            # Bestimme Puffergröße
            file_size = os.path.getsize(source)
            buffer_size = calculate_buffer_size(file_size, bandwidth_limit)
            
            # Kopiere Datei
            copied = 0
            start_time = time.time()
            
            with open(source, 'rb') as src, open(target, 'wb') as dst:
                while True:
                    if self.abort_requested:
                        raise CopyAborted("Kopiervorgang abgebrochen")
                        
                    chunk = src.read(buffer_size)
                    if not chunk:
                        break
                        
                    dst.write(chunk)
                    copied += len(chunk)
                    
                    # Fortschritt melden
                    if self.progress_callback:
                        elapsed = time.time() - start_time
                        speed = copied / elapsed if elapsed > 0 else 0
                        progress = {
                            'total': file_size,
                            'copied': copied,
                            'percent': (copied / file_size) * 100,
                            'speed': speed
                        }
                        self.progress_callback(progress)
                        
                    # Bandbreitenlimit
                    if bandwidth_limit:
                        elapsed = time.time() - start_time
                        expected = copied / bandwidth_limit
                        if expected > elapsed:
                            time.sleep(expected - elapsed)
                            
            # Verifiziere Kopie
            if not self._verify_copy(source, target):
                raise CopyVerificationError("Verifizierung fehlgeschlagen")
                
            return True
            
        except Exception as e:
            if self.error_callback:
                self.error_callback(str(e))
            return False
            
    def _verify_copy(self, source: str, target: str) -> bool:
        """Verifiziert eine Kopie durch Größen- und Hash-Vergleich."""
        if os.path.getsize(source) != os.path.getsize(target):
            return False
            
        # Schneller Hash-Vergleich
        import hashlib
        
        def quick_hash(path: str) -> str:
            sha256 = hashlib.sha256()
            with open(path, 'rb') as f:
                # Lies nur Anfang und Ende
                start = f.read(8192)
                f.seek(-8192, 2)
                end = f.read()
                sha256.update(start + end)
            return sha256.hexdigest()
            
        return quick_hash(source) == quick_hash(target)
        
    def abort(self):
        """Bricht laufende Kopieroperationen ab."""
        self.abort_requested = True
        
    def reset(self):
        """Setzt den Manager zurück."""
        self.abort_requested = False
        self.error_log.clear()
