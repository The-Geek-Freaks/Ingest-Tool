"""
Typdefinitionen für Netzwerkoperationen.
"""
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Dict, Any

class QoSLevel(Enum):
    """Quality of Service Level."""
    HIGH = 7
    NORMAL = 4
    LOW = 1

@dataclass
class NetworkPath:
    """Repräsentiert einen Netzwerkpfad."""
    path: str
    is_network: bool
    server: Optional[str] = None
    share: Optional[str] = None
    
    @classmethod
    def from_path(cls, path: str) -> 'NetworkPath':
        """Erstellt NetworkPath aus einem Pfadstring."""
        import re
        # UNC-Pfad-Erkennung
        unc_match = re.match(r'\\\\([^\\]+)\\([^\\]+)(?:\\|$)', path)
        if unc_match:
            return cls(
                path=path,
                is_network=True,
                server=unc_match.group(1),
                share=unc_match.group(2)
            )
        # Netzlaufwerk-Erkennung
        if len(path) >= 2 and path[1] == ':':
            import win32wnet
            try:
                netpath = win32wnet.WNetGetUniversalName(
                    path,
                    win32wnet.UNIVERSAL_NAME_INFO_LEVEL
                )
                unc_match = re.match(r'\\\\([^\\]+)\\([^\\]+)(?:\\|$)', netpath)
                if unc_match:
                    return cls(
                        path=path,
                        is_network=True,
                        server=unc_match.group(1),
                        share=unc_match.group(2)
                    )
            except:
                pass
        return cls(path=path, is_network=False)

@dataclass
class TransferStatus:
    """Status einer Dateiübertragung."""
    source: str
    target: str
    bytes_total: int
    bytes_transferred: int
    speed: float  # Bytes/Sekunde
    eta: float    # Geschätzte verbleibende Zeit in Sekunden
    status: str   # 'running', 'paused', 'completed', 'error'
    error: Optional[str] = None

@dataclass
class NetworkStats:
    """Netzwerkstatistiken."""
    bandwidth: float  # Bytes/Sekunde
    latency: float   # Millisekunden
    packet_loss: float  # Prozent
    interface: Optional[str] = None
    
    @classmethod
    def measure(cls, host: str = '8.8.8.8') -> 'NetworkStats':
        """Misst aktuelle Netzwerkstatistiken."""
        import subprocess
        import re
        
        # Ping für Latenz und Paketverlust
        try:
            ping = subprocess.run(
                ['ping', '-n', '10', host],
                capture_output=True,
                text=True
            )
            latency_match = re.search(r'Minimum = (\d+)ms', ping.stdout)
            loss_match = re.search(r'(\d+)% Verlust', ping.stdout)
            
            latency = float(latency_match.group(1)) if latency_match else 0
            loss = float(loss_match.group(1)) if loss_match else 0
        except:
            latency = 0
            loss = 0
            
        # Bandbreite (vereinfacht)
        try:
            import psutil
            net_io = psutil.net_io_counters()
            time.sleep(1)
            net_io2 = psutil.net_io_counters()
            bandwidth = (net_io2.bytes_sent + net_io2.bytes_recv -
                       net_io.bytes_sent - net_io.bytes_recv)
        except:
            bandwidth = 0
            
        return cls(
            bandwidth=bandwidth,
            latency=latency,
            packet_loss=loss
        )
