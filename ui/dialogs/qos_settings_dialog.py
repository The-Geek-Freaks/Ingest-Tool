from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QCheckBox, QPushButton, QTableWidget,
                             QTableWidgetItem, QGroupBox, QFormLayout)
from PyQt5.QtCore import pyqtSignal

class QoSSettingsDialog(QDialog):
    """Dialog für QoS-Einstellungen (Quality of Service)."""
    
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, current_settings: dict, parent=None):
        super().__init__(parent)
        self.current_settings = current_settings
        self.setWindowTitle("QoS-Einstellungen")
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Richtet das UI des Dialogs ein."""
        layout = QVBoxLayout()
        
        # QoS-Aktivierung
        self.enable_qos = QCheckBox("QoS-Optimierung aktivieren")
        
        # Prioritätseinstellungen
        priority_group = QGroupBox("Dateityp-Prioritäten")
        priority_layout = QVBoxLayout()
        
        self.priority_table = QTableWidget()
        self.priority_table.setColumnCount(2)
        self.priority_table.setHorizontalHeaderLabels(["Dateityp", "Priorität"])
        
        # Vordefinierte Dateitypen und Prioritäten
        self.default_types = [
            (".jpg", "Hoch"),
            (".png", "Hoch"),
            (".mp4", "Mittel"),
            (".pdf", "Niedrig"),
            (".txt", "Niedrig")
        ]
        
        self.priority_table.setRowCount(len(self.default_types))
        for row, (ext, prio) in enumerate(self.default_types):
            type_item = QTableWidgetItem(ext)
            self.priority_table.setItem(row, 0, type_item)
            
            prio_combo = QComboBox()
            prio_combo.addItems(["Hoch", "Mittel", "Niedrig"])
            prio_combo.setCurrentText(prio)
            self.priority_table.setCellWidget(row, 1, prio_combo)
        
        priority_layout.addWidget(self.priority_table)
        priority_group.setLayout(priority_layout)
        
        # Netzwerkoptimierung
        network_group = QGroupBox("Netzwerkoptimierung")
        network_layout = QFormLayout()
        
        self.buffer_size = QComboBox()
        self.buffer_size.addItems(["4 MB", "8 MB", "16 MB", "32 MB"])
        
        self.retry_count = QComboBox()
        self.retry_count.addItems(["1", "3", "5", "10"])
        
        network_layout.addRow("Puffergröße:", self.buffer_size)
        network_layout.addRow("Max. Wiederholungen:", self.retry_count)
        network_group.setLayout(network_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Speichern")
        cancel_button = QPushButton("Abbrechen")
        
        save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        # Hauptlayout
        layout.addWidget(self.enable_qos)
        layout.addWidget(priority_group)
        layout.addWidget(network_group)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def load_settings(self):
        """Lädt die aktuellen Einstellungen."""
        qos = self.current_settings.get('qos', {})
        
        self.enable_qos.setChecked(qos.get('enabled', False))
        
        # Lade Prioritäten
        priorities = qos.get('priorities', {})
        for row in range(self.priority_table.rowCount()):
            ext = self.priority_table.item(row, 0).text()
            combo = self.priority_table.cellWidget(row, 1)
            if ext in priorities:
                combo.setCurrentText(priorities[ext])
        
        # Lade Netzwerkeinstellungen
        network = qos.get('network', {})
        self.buffer_size.setCurrentText(f"{network.get('buffer_size', 4)} MB")
        self.retry_count.setCurrentText(str(network.get('retry_count', 3)))
        
    def get_settings(self) -> dict:
        """Gibt die aktuellen Einstellungen zurück."""
        priorities = {}
        for row in range(self.priority_table.rowCount()):
            ext = self.priority_table.item(row, 0).text()
            combo = self.priority_table.cellWidget(row, 1)
            priorities[ext] = combo.currentText()
        
        buffer_size = int(self.buffer_size.currentText().split()[0])
        retry_count = int(self.retry_count.currentText())
        
        return {
            'qos': {
                'enabled': self.enable_qos.isChecked(),
                'priorities': priorities,
                'network': {
                    'buffer_size': buffer_size,
                    'retry_count': retry_count
                }
            }
        }
        
    def accept(self):
        """Handler für den Speichern-Button."""
        settings = self.get_settings()
        self.settings_changed.emit(settings)
        super().accept()
