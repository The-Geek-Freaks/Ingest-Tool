"""
Hilfsfunktionen für Netzwerkoperationen.
"""
import os
import time
import socket
import logging
import subprocess
from typing import Optional, Dict, Tuple
from pathlib import Path

def get_network_interfaces() -> Dict[str, Dict]:
    """Ermittelt verfügbare Netzwerkschnittstellen."""
    try:
        import psutil
        interfaces = {}
        for name, stats in psutil.net_if_stats().items():
            if stats.isup:
                addrs = psutil.net_if_addrs().get(name, [])
                ipv4 = next((addr.address for addr in addrs 
                           if addr.family == socket.AF_INET), None)
                interfaces[name] = {
                    'speed': stats.speed,
                    'mtu': stats.mtu,
                    'ipv4': ipv4
                }
        return interfaces
    except ImportError:
        logging.warning("psutil nicht verfügbar")
        return {}

def measure_bandwidth(interface: Optional[str] = None,
                     duration: int = 1) -> float:
    """Misst die verfügbare Bandbreite einer Schnittstelle."""
    try:
        import psutil
        if interface:
            counters = {interface: psutil.net_io_counters(pernic=True)[interface]}
        else:
            counters = psutil.net_io_counters(pernic=True)
            
        time.sleep(duration)
        
        if interface:
            counters2 = {interface: psutil.net_io_counters(pernic=True)[interface]}
        else:
            counters2 = psutil.net_io_counters(pernic=True)
            
        total_bytes = 0
        for name in counters:
            bytes_sent = counters2[name].bytes_sent - counters[name].bytes_sent
            bytes_recv = counters2[name].bytes_recv - counters[name].bytes_recv
            total_bytes += bytes_sent + bytes_recv
            
        return total_bytes / duration
        
    except (ImportError, KeyError):
        return 0

def calculate_buffer_size(file_size: int,
                         bandwidth: Optional[float] = None) -> int:
    """Berechnet optimale Puffergröße basierend auf Dateigröße und Bandbreite."""
    if bandwidth is None:
        bandwidth = measure_bandwidth()
        
    # Minimale und maximale Puffergrößen
    MIN_BUFFER = 64 * 1024      # 64 KB
    MAX_BUFFER = 16 * 1024 * 1024  # 16 MB
    
    # Basis-Puffergröße: 0.1 Sekunden Übertragungszeit
    buffer_size = int(max(bandwidth * 0.1, MIN_BUFFER))
    
    # Für kleine Dateien: Maximal 1/4 der Dateigröße
    if file_size < MAX_BUFFER * 4:
        buffer_size = min(buffer_size, file_size // 4)
        
    return min(max(buffer_size, MIN_BUFFER), MAX_BUFFER)

def set_qos_policy(path: str, qos_level: int):
    """Setzt Windows QoS-Policy für einen Pfad."""
    try:
        import win32net
        import win32netcon
        
        # QoS-Policy erstellen/aktualisieren
        policy_data = {
            'name': f'IngestTool_{Path(path).name}',
            'comment': 'Automatisch erstellt durch IngestTool',
            'priority': qos_level
        }
        
        try:
            win32net.NetQosAdd(None, 1, policy_data)
        except:
            win32net.NetQosSet(None, 1, policy_data)
            
    except ImportError:
        logging.warning("win32net nicht verfügbar - QoS deaktiviert")
        
def parse_robocopy_progress(line: str) -> Optional[Dict]:
    """Analysiert Robocopy-Fortschrittsausgabe."""
    import re
    
    # Verschiedene Fortschrittsformate
    patterns = [
        # 50.2% - 1.23 GB kopiert
        r'(\d+\.?\d*)%.+?(\d+\.?\d*)\s*([KMG]B)',
        # Datei 123 von 456
        r'File\s+(\d+)\s+of\s+(\d+)',
        # Geschwindigkeit: 123.4 MB/s
        r'Speed:\s+(\d+\.?\d*)\s+([KMG]B)/s'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, line)
        if match:
            return {
                'line': line,
                'groups': match.groups()
            }
    return None
    
def parse_rsync_progress(line: str) -> Optional[Dict]:
    """Analysiert rsync-Fortschrittsausgabe."""
    import re
    
    # Beispiel: 23,456 100%  123.45MB/s    0:00:01
    pattern = r'(\d+)\s+(\d+)%\s+(\d+\.?\d*\w+)/s\s+(\d+:\d+:\d+)'
    
    match = re.search(pattern, line)
    if match:
        return {
            'line': line,
            'groups': match.groups()
        }
    return None
