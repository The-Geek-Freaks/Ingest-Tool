from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QSpinBox, QCheckBox, QLineEdit, QPushButton,
                             QFormLayout, QGroupBox)
from PyQt5.QtCore import pyqtSignal

class NetworkSettingsDialog(QDialog):
    """Dialog für Netzwerkeinstellungen."""
    
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, current_settings: dict, parent=None):
        super().__init__(parent)
        self.current_settings = current_settings
        self.setWindowTitle("Netzwerk-Einstellungen")
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Richtet das UI des Dialogs ein."""
        layout = QVBoxLayout()
        
        # Bandbreitengruppe
        bandwidth_group = QGroupBox("Bandbreitenlimit")
        bandwidth_layout = QFormLayout()
        
        self.enable_limit_cb = QCheckBox("Bandbreitenlimit aktivieren")
        self.limit_spinbox = QSpinBox()
        self.limit_spinbox.setRange(1, 1000)
        self.limit_spinbox.setSuffix(" MB/s")
        
        bandwidth_layout.addRow(self.enable_limit_cb)
        bandwidth_layout.addRow("Limit:", self.limit_spinbox)
        bandwidth_group.setLayout(bandwidth_layout)
        
        # E-Mail-Benachrichtigungen
        email_group = QGroupBox("E-Mail-Benachrichtigungen")
        email_layout = QFormLayout()
        
        self.enable_email_cb = QCheckBox("E-Mail-Benachrichtigungen aktivieren")
        self.smtp_server = QLineEdit()
        self.smtp_port = QSpinBox()
        self.smtp_port.setRange(1, 65535)
        self.smtp_port.setValue(587)
        self.email_address = QLineEdit()
        
        email_layout.addRow(self.enable_email_cb)
        email_layout.addRow("SMTP-Server:", self.smtp_server)
        email_layout.addRow("SMTP-Port:", self.smtp_port)
        email_layout.addRow("E-Mail-Adresse:", self.email_address)
        email_group.setLayout(email_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Speichern")
        cancel_button = QPushButton("Abbrechen")
        
        save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        # Hauptlayout
        layout.addWidget(bandwidth_group)
        layout.addWidget(email_group)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def load_settings(self):
        """Lädt die aktuellen Einstellungen."""
        bandwidth = self.current_settings.get('bandwidth', {})
        email = self.current_settings.get('email', {})
        
        self.enable_limit_cb.setChecked(bandwidth.get('enabled', False))
        self.limit_spinbox.setValue(bandwidth.get('limit', 100))
        
        self.enable_email_cb.setChecked(email.get('enabled', False))
        self.smtp_server.setText(email.get('smtp_server', ''))
        self.smtp_port.setValue(email.get('smtp_port', 587))
        self.email_address.setText(email.get('address', ''))
        
    def get_settings(self) -> dict:
        """Gibt die aktuellen Einstellungen zurück."""
        return {
            'bandwidth': {
                'enabled': self.enable_limit_cb.isChecked(),
                'limit': self.limit_spinbox.value()
            },
            'email': {
                'enabled': self.enable_email_cb.isChecked(),
                'smtp_server': self.smtp_server.text(),
                'smtp_port': self.smtp_port.value(),
                'address': self.email_address.text()
            }
        }
        
    def accept(self):
        """Handler für den Speichern-Button."""
        settings = self.get_settings()
        self.settings_changed.emit(settings)
        super().accept()
