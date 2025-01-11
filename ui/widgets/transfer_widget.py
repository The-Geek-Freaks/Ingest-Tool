"""
Widget zur Anzeige und Steuerung von Dateitransfers.
"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QFrame, QPushButton, QMenu
)

from core.network.types import TransferStatus, QoSLevel
from utils.i18n import I18n

class TransferWidget(QWidget):
    """Widget zur Anzeige eines einzelnen Transfers."""
    
    # Signale
    cancel = pyqtSignal()  # Transfer abbrechen
    retry = pyqtSignal()   # Transfer wiederholen
    
    def __init__(self, transfer_info: dict, i18n: I18n, parent=None):
        super().__init__(parent)
        self.transfer_info = transfer_info
        self.i18n = i18n
        self.setup_ui()
        
    def setup_ui(self):
        """Richtet das UI des Widgets ein."""
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # Hauptframe
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        frame.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 4px;
            }
            QFrame:hover {
                background-color: #353535;
                border: 1px solid #505050;
            }
        """)
        
        # Layout für Frame-Inhalt
        frame_layout = QVBoxLayout()
        frame_layout.setContentsMargins(12, 12, 12, 12)
        frame_layout.setSpacing(8)
        
        # Obere Zeile: Dateiname und Status
        top_row = QHBoxLayout()
        
        # Icon basierend auf Dateityp
        icon = self._get_file_icon()
        icon_label = QLabel()
        icon_label.setPixmap(icon.pixmap(24, 24))
        top_row.addWidget(icon_label)
        
        # Dateiname
        name_label = QLabel(self.transfer_info['filename'])
        name_label.setStyleSheet("font-weight: bold; color: white;")
        top_row.addWidget(name_label)
        
        # Status-Indikator
        self.status_label = QLabel()
        self.update_status(self.transfer_info.get('status', TransferStatus.PENDING))
        top_row.addWidget(self.status_label)
        
        top_row.addStretch()
        
        # QoS-Level
        qos_label = QLabel()
        qos_level = self.transfer_info.get('qos_level', QoSLevel.NORMAL)
        qos_label.setStyleSheet(f"""
            padding: 2px 6px;
            border-radius: 2px;
            font-size: 8pt;
            background-color: {self._get_qos_color(qos_level)};
            color: white;
        """)
        qos_label.setText(qos_level.name.capitalize())
        top_row.addWidget(qos_label)
        
        # Abbrechen/Wiederholen Button
        self.action_btn = QPushButton()
        self.action_btn.setStyleSheet("""
            QPushButton {
                border: none;
                padding: 4px;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #404040;
            }
        """)
        self.update_action_button()
        top_row.addWidget(self.action_btn)
        
        frame_layout.addLayout(top_row)
        
        # Mittlere Zeile: Fortschrittsbalken
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.update_progress(self.transfer_info.get('progress', 0))
        frame_layout.addWidget(self.progress_bar)
        
        # Untere Zeile: Details
        bottom_row = QHBoxLayout()
        
        # Übertragungsrate
        self.speed_label = QLabel()
        self.speed_label.setStyleSheet("color: #888;")
        self.update_speed(self.transfer_info.get('speed', 0))
        bottom_row.addWidget(self.speed_label)
        
        # Verbleibende Zeit
        self.time_label = QLabel()
        self.time_label.setStyleSheet("color: #888;")
        self.update_time(self.transfer_info.get('remaining_time', 0))
        bottom_row.addWidget(self.time_label)
        
        bottom_row.addStretch()
        
        # Dateigröße
        size_label = QLabel(self._format_size(self.transfer_info.get('size', 0)))
        size_label.setStyleSheet("color: #888;")
        bottom_row.addWidget(size_label)
        
        frame_layout.addLayout(bottom_row)
        
        frame.setLayout(frame_layout)
        layout.addWidget(frame)
        self.setLayout(layout)
        
    def update_status(self, status: TransferStatus):
        """Aktualisiert den Status des Transfers."""
        color_map = {
            TransferStatus.PENDING: "#3498db",    # Blau
            TransferStatus.ACTIVE: "#2ecc71",     # Grün
            TransferStatus.PAUSED: "#f1c40f",     # Gelb
            TransferStatus.COMPLETED: "#27ae60",  # Dunkelgrün
            TransferStatus.ERROR: "#e74c3c",      # Rot
            TransferStatus.CANCELLED: "#95a5a6"   # Grau
        }
        
        color = color_map.get(status, "#95a5a6")
        
        self.status_label.setStyleSheet(f"""
            color: {color};
            padding: 2px 6px;
            border: 1px solid {color};
            border-radius: 2px;
            font-size: 8pt;
        """)
        self.status_label.setText(
            self.i18n.get(f'transfer.status.{status.name.lower()}')
        )
        self.update_action_button()
        
    def update_progress(self, progress: float):
        """Aktualisiert den Fortschrittsbalken."""
        # Setze Farbe basierend auf Status
        status = self.transfer_info.get('status', TransferStatus.PENDING)
        color = {
            TransferStatus.ACTIVE: "#2ecc71",     # Grün
            TransferStatus.PAUSED: "#f1c40f",     # Gelb
            TransferStatus.COMPLETED: "#27ae60",  # Dunkelgrün
            TransferStatus.ERROR: "#e74c3c",      # Rot
            TransferStatus.CANCELLED: "#95a5a6"   # Grau
        }.get(status, "#3498db")  # Standard: Blau
        
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #404040;
                border-radius: 2px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {color};
            }}
        """)
        
        self.progress_bar.setValue(int(progress))
        
    def update_speed(self, speed: float):
        """Aktualisiert die Übertragungsrate."""
        self.speed_label.setText(
            self.i18n.get('transfer.speed', speed=self._format_speed(speed))
        )
        
    def update_time(self, seconds: int):
        """Aktualisiert die verbleibende Zeit."""
        if seconds < 60:
            text = f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            text = f"{minutes}min"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            text = f"{hours}h {minutes}min"
            
        self.time_label.setText(
            self.i18n.get('transfer.remaining_time', time=text)
        )
        
    def update_action_button(self):
        """Aktualisiert den Aktions-Button basierend auf Status."""
        status = self.transfer_info.get('status', TransferStatus.PENDING)
        
        if status in [TransferStatus.PENDING, TransferStatus.ACTIVE]:
            self.action_btn.setIcon(QIcon("assets/icons/cancel.png"))
            self.action_btn.setToolTip(self.i18n.get('general.cancel'))
            self.action_btn.clicked.connect(self.cancel.emit)
        elif status in [TransferStatus.ERROR, TransferStatus.CANCELLED]:
            self.action_btn.setIcon(QIcon("assets/icons/retry.png"))
            self.action_btn.setToolTip(self.i18n.get('general.retry'))
            self.action_btn.clicked.connect(self.retry.emit)
        else:
            self.action_btn.hide()
            
    def _get_file_icon(self) -> QIcon:
        """Ermittelt das passende Icon für den Dateityp."""
        ext = self.transfer_info.get('extension', '').lower()
        
        if ext in ['.jpg', '.jpeg', '.png', '.gif']:
            return QIcon("assets/icons/image.png")
        elif ext in ['.mp4', '.avi', '.mov']:
            return QIcon("assets/icons/video.png")
        elif ext in ['.mp3', '.wav', '.ogg']:
            return QIcon("assets/icons/audio.png")
        elif ext in ['.doc', '.docx', '.pdf']:
            return QIcon("assets/icons/document.png")
        else:
            return QIcon("assets/icons/file.png")
            
    def _get_qos_color(self, level: QoSLevel) -> str:
        """Ermittelt die Farbe für ein QoS-Level."""
        return {
            QoSLevel.HIGH: "#e74c3c",    # Rot
            QoSLevel.NORMAL: "#3498db",  # Blau
            QoSLevel.LOW: "#95a5a6"      # Grau
        }.get(level, "#95a5a6")
        
    def _format_size(self, size: int) -> str:
        """Formatiert eine Größe in Bytes in lesbare Form."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"
        
    def _format_speed(self, speed: float) -> str:
        """Formatiert eine Übertragungsrate in lesbare Form."""
        return self._format_size(int(speed))
