"""
Widget zur Anzeige und Verwaltung von Laufwerken.
"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QPainter, QColor, QPen
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QFrame, QPushButton, QMenu
)

from core.drive.status import DriveStatus
from utils.i18n import I18n

class DriveWidget(QWidget):
    """Widget zur Anzeige eines einzelnen Laufwerks."""
    
    # Signale
    selected = pyqtSignal(bool)  # True wenn ausgewählt, False wenn abgewählt
    eject = pyqtSignal()  # Auswerfen angefordert
    
    def __init__(self, drive_info: dict, i18n: I18n, parent=None):
        super().__init__(parent)
        self.drive_info = drive_info
        self.i18n = i18n
        self.is_selected = False
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
        
        # Obere Zeile: Icon und Laufwerksname
        top_row = QHBoxLayout()
        
        # Icon basierend auf Laufwerkstyp
        icon = QIcon("assets/icons/usb-drive.png" if self.drive_info['type'] == 'removable'
                    else "assets/icons/hard-drive.png")
        icon_label = QLabel()
        icon_label.setPixmap(icon.pixmap(24, 24))
        top_row.addWidget(icon_label)
        
        # Laufwerksname und Buchstabe
        name_label = QLabel(f"{self.drive_info['label']} ({self.drive_info['letter']})")
        name_label.setStyleSheet("font-weight: bold; color: white;")
        top_row.addWidget(name_label)
        
        # Status-Indikator
        self.status_label = QLabel()
        self.update_status(self.drive_info.get('status', DriveStatus.READY.value))
        top_row.addWidget(self.status_label)
        
        top_row.addStretch()
        
        # Auswerfen-Button für Wechseldatenträger
        if self.drive_info['type'] == 'removable':
            eject_btn = QPushButton()
            eject_btn.setIcon(QIcon("assets/icons/eject.png"))
            eject_btn.setToolTip(self.i18n.get('drive.eject'))
            eject_btn.clicked.connect(self.eject.emit)
            eject_btn.setStyleSheet("""
                QPushButton {
                    border: none;
                    padding: 4px;
                    border-radius: 2px;
                }
                QPushButton:hover {
                    background-color: #404040;
                }
            """)
            top_row.addWidget(eject_btn)
            
        frame_layout.addLayout(top_row)
        
        # Mittlere Zeile: Speichernutzung
        usage_layout = QHBoxLayout()
        
        # Speicherbalken
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.update_usage()
        usage_layout.addWidget(self.progress_bar)
        
        frame_layout.addLayout(usage_layout)
        
        # Untere Zeile: Detailinformationen
        bottom_row = QHBoxLayout()
        
        # Freier/Gesamtspeicher
        size_label = QLabel(self._format_size(self.drive_info['size']))
        size_label.setStyleSheet("color: #888;")
        bottom_row.addWidget(size_label)
        
        free_label = QLabel(f"Frei: {self._format_size(self.drive_info['free'])}")
        free_label.setStyleSheet("color: #888;")
        bottom_row.addWidget(free_label)
        
        bottom_row.addStretch()
        
        frame_layout.addLayout(bottom_row)
        
        frame.setLayout(frame_layout)
        layout.addWidget(frame)
        self.setLayout(layout)
        
        # Mausklick-Events
        self.setMouseTracking(True)
        
    def update_status(self, status: str):
        """Aktualisiert den Status des Laufwerks."""
        color_map = {
            DriveStatus.READY.value: "#2ecc71",      # Grün
            DriveStatus.BUSY.value: "#f1c40f",       # Gelb
            DriveStatus.ERROR.value: "#e74c3c",      # Rot
            DriveStatus.DISCONNECTED.value: "#95a5a6" # Grau
        }
        
        status_text = {
            DriveStatus.READY.value: self.i18n.get('drive.status.ready'),
            DriveStatus.BUSY.value: self.i18n.get('drive.status.busy'),
            DriveStatus.ERROR.value: self.i18n.get('drive.status.error'),
            DriveStatus.DISCONNECTED.value: self.i18n.get('drive.status.disconnected')
        }
        
        color = color_map.get(status, "#95a5a6")
        text = status_text.get(status, self.i18n.get('drive.status.unknown'))
        
        self.status_label.setStyleSheet(f"""
            color: {color};
            padding: 2px 6px;
            border: 1px solid {color};
            border-radius: 2px;
            font-size: 8pt;
        """)
        self.status_label.setText(text)
        
    def update_usage(self):
        """Aktualisiert die Speichernutzungsanzeige."""
        if self.drive_info['size'] > 0:
            used = self.drive_info['size'] - self.drive_info['free']
            percentage = (used / self.drive_info['size']) * 100
            
            # Setze Farbe basierend auf Nutzung
            if percentage >= 90:
                color = "#e74c3c"  # Rot
            elif percentage >= 75:
                color = "#f1c40f"  # Gelb
            else:
                color = "#2ecc71"  # Grün
                
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
            
            self.progress_bar.setValue(int(percentage))
            
    def _format_size(self, size: int) -> str:
        """Formatiert eine Größe in Bytes in lesbare Form."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"
        
    def mousePressEvent(self, event):
        """Handler für Mausklick-Events."""
        if event.button() == Qt.LeftButton:
            self.is_selected = not self.is_selected
            self.selected.emit(self.is_selected)
            self.update_selection_style()
            
    def update_selection_style(self):
        """Aktualisiert den Stil basierend auf Auswahl-Status."""
        if self.is_selected:
            self.setStyleSheet("""
                QFrame {
                    background-color: #1a237e;
                    border: 2px solid #303f9f;
                }
                QFrame:hover {
                    background-color: #283593;
                    border: 2px solid #3949ab;
                }
            """)
        else:
            self.setStyleSheet("")
            
    def update_drive_status(self, drive_letter: str, active_count: int, speed: float):
        """Aktualisiert den Status eines Laufwerks."""
        try:
            # Formatiere Geschwindigkeit
            if speed > 0:
                speed_text = f"{speed:.1f} MB/s"  # Speed ist bereits in MB/s
            else:
                speed_text = "0 B/s"
            
            # Erstelle Statustext
            if active_count > 0:
                status_text = f"{active_count} {'Kopie' if active_count == 1 else 'Kopien'} ({speed_text})"
            else:
                status_text = "Bereit"
            
            # Aktualisiere Label
            if drive_letter in self.drive_labels:
                self.drive_labels[drive_letter].setText(status_text)
                
        except Exception as e:
            logging.error(f"Fehler beim Aktualisieren des Laufwerksstatus: {e}")
