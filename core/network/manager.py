"""
Netzwerk-Manager für allgemeine Netzwerkoperationen.
"""
import os
import time
import socket
import logging
import threading
from typing import Optional, Dict, Tuple
from pathlib import Path
from queue import Queue, Empty

from .types import NetworkPath, NetworkStats, QoSLevel
from .errors import NetworkError, ConnectionError, TransferError
from .utils import (
    get_network_interfaces,
    measure_bandwidth,
    calculate_buffer_size,
    set_qos_policy
)

class NetworkManager:
    """Verwaltet Netzwerkoperationen und -verbindungen."""
    
    def __init__(self):
        self.connections = {}
        self.bandwidth_limits = {}
        self.qos_settings = {}
        self.retry_settings = {
            'max_retries': 3,
            'base_delay': 5,
            'max_delay': 300
        }
        self._lock = threading.Lock()
        self._connection_cache = {}
        self._cache_lifetime = 60  # Sekunden
        
        # Optimale Puffergrößen
        self.NETWORK_BUFFER = 4 * 1024 * 1024   # 4MB für Netzwerk
        self.LOCAL_BUFFER = 16 * 1024 * 1024    # 16MB für lokale Kopien
        
        # E-Mail-Benachrichtigungen
        self.email_notification = False
        self.email_settings = {
            'smtp_server': '',
            'smtp_port': 587,
            'username': '',
            'password': '',
            'from_addr': '',
            'to_addr': ''
        }
        
        # Erweiterte Fehlerbehandlung
        self.error_log = []
        self.recovery_mode = False
        
        # Priorisierung
        self.priority_files = set()
        self.priority_types = set()
        
    def connect(self, server: str, share: str,
                username: Optional[str] = None,
                password: Optional[str] = None) -> bool:
        """Stellt eine Netzwerkverbindung her."""
        try:
            import win32wnet
            import win32netcon
            
            # Prüfe Cache
            cache_key = f"{server}\\{share}"
            if cache_key in self._connection_cache:
                timestamp, _ = self._connection_cache[cache_key]
                if time.time() - timestamp < self._cache_lifetime:
                    return True
                    
            # Verbindungsaufbau
            if username and password:
                win32wnet.WNetAddConnection2(
                    win32netcon.RESOURCETYPE_DISK,
                    None,
                    f"\\\\{server}\\{share}",
                    None,
                    username,
                    password,
                    0
                )
            else:
                win32wnet.WNetAddConnection2(
                    win32netcon.RESOURCETYPE_DISK,
                    None,
                    f"\\\\{server}\\{share}",
                    None
                )
                
            # Cache aktualisieren
            self._connection_cache[cache_key] = (time.time(), True)
            return True
            
        except Exception as e:
            logging.error(f"Verbindungsfehler: {e}")
            raise ConnectionError(f"Verbindung zu {server}\\{share} fehlgeschlagen")
            
    def disconnect(self, server: str, share: str):
        """Trennt eine Netzwerkverbindung."""
        try:
            import win32wnet
            win32wnet.WNetCancelConnection2(f"\\\\{server}\\{share}", 0, 0)
            
            # Cache löschen
            cache_key = f"{server}\\{share}"
            if cache_key in self._connection_cache:
                del self._connection_cache[cache_key]
                
        except Exception as e:
            logging.error(f"Fehler beim Trennen: {e}")
            
    def set_bandwidth_limit(self, interface: str, limit: int):
        """Setzt Bandbreitenlimit für eine Schnittstelle."""
        self.bandwidth_limits[interface] = limit
        
    def set_qos_level(self, path: str, level: QoSLevel):
        """Setzt QoS-Level für einen Pfad."""
        self.qos_settings[path] = level.value
        set_qos_policy(path, level.value)
        
    def get_network_stats(self, interface: Optional[str] = None) -> NetworkStats:
        """Ermittelt Netzwerkstatistiken."""
        return NetworkStats.measure()
        
    def send_notification(self, subject: str, message: str):
        """Sendet E-Mail-Benachrichtigung."""
        if not self.email_notification:
            return
            
        try:
            import smtplib
            from email.message import EmailMessage
            
            msg = EmailMessage()
            msg.set_content(message)
            msg['Subject'] = subject
            msg['From'] = self.email_settings['from_addr']
            msg['To'] = self.email_settings['to_addr']
            
            with smtplib.SMTP(
                self.email_settings['smtp_server'],
                self.email_settings['smtp_port']
            ) as server:
                server.starttls()
                server.login(
                    self.email_settings['username'],
                    self.email_settings['password']
                )
                server.send_message(msg)
                
        except Exception as e:
            logging.error(f"E-Mail-Fehler: {e}")
            
    def add_priority_file(self, filepath: str):
        """Fügt eine Datei zur Prioritätsliste hinzu."""
        self.priority_files.add(filepath)
        
    def add_priority_type(self, extension: str):
        """Fügt einen Dateityp zur Prioritätsliste hinzu."""
        if not extension.startswith('.'):
            extension = '.' + extension
        self.priority_types.add(extension.lower())
        
    def is_priority(self, filepath: str) -> bool:
        """Prüft ob eine Datei priorisiert ist."""
        if filepath in self.priority_files:
            return True
            
        ext = os.path.splitext(filepath)[1].lower()
        return ext in self.priority_types
        
    def clear_error_log(self):
        """Leert das Fehlerprotokoll."""
        self.error_log.clear()
        
    def enable_recovery_mode(self, enabled: bool = True):
        """Aktiviert/Deaktiviert den Wiederherstellungsmodus."""
        self.recovery_mode = enabled
