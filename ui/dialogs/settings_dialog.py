"""
Dialog für die Anwendungseinstellungen.
"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QSpinBox, QCheckBox, QGroupBox,
    QDialogButtonBox, QTabWidget, QWidget,
    QLineEdit, QPushButton, QFileDialog
)

from core.network.types import QoSLevel
from utils.settings import Settings
from utils.i18n import I18n

class SettingsDialog(QDialog):
    """Dialog für die Anwendungseinstellungen."""
    
    # Signale
    settings_changed = pyqtSignal(dict)  # Einstellungen wurden geändert
    
    def __init__(self, settings: Settings, i18n: I18n, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.i18n = i18n
        self.current_settings = settings.load()
        
        self.setWindowTitle(self.i18n.get('settings.title'))
        self.setMinimumWidth(500)
        self.setup_ui()
        
    def setup_ui(self):
        """Richtet das UI des Dialogs ein."""
        layout = QVBoxLayout()
        
        # Tab-Widget für verschiedene Einstellungskategorien
        tabs = QTabWidget()
        
        # Allgemeine Einstellungen
        general_tab = QWidget()
        general_layout = QVBoxLayout()
        
        # Sprache
        language_group = QGroupBox(self.i18n.get('settings.general.language'))
        language_layout = QVBoxLayout()
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Deutsch", "English"])
        self.language_combo.setCurrentText(
            self.current_settings.get('language', 'Deutsch')
        )
        language_layout.addWidget(self.language_combo)
        
        language_group.setLayout(language_layout)
        general_layout.addWidget(language_group)
        
        # Dateitypen
        filetypes_group = QGroupBox("Dateitypen")
        filetypes_layout = QVBoxLayout()
        
        # Button für Dateityp-Verwaltung
        manage_filetypes_btn = QPushButton("Dateitypen verwalten...")
        manage_filetypes_btn.clicked.connect(self.show_filetypes_dialog)
        filetypes_layout.addWidget(manage_filetypes_btn)
        
        filetypes_group.setLayout(filetypes_layout)
        general_layout.addWidget(filetypes_group)
        
        # Verhalten
        behavior_group = QGroupBox(self.i18n.get('settings.general.behavior'))
        behavior_layout = QVBoxLayout()
        
        self.delete_source_check = QCheckBox(
            self.i18n.get('settings.general.delete_source')
        )
        self.delete_source_check.setChecked(
            self.current_settings.get('delete_source', False)
        )
        behavior_layout.addWidget(self.delete_source_check)
        
        self.show_notifications_check = QCheckBox(
            self.i18n.get('settings.general.show_notifications')
        )
        self.show_notifications_check.setChecked(
            self.current_settings.get('show_notifications', True)
        )
        behavior_layout.addWidget(self.show_notifications_check)
        
        self.minimize_to_tray_check = QCheckBox(
            self.i18n.get('settings.general.minimize_to_tray')
        )
        self.minimize_to_tray_check.setChecked(
            self.current_settings.get('minimize_to_tray', True)
        )
        behavior_layout.addWidget(self.minimize_to_tray_check)
        
        behavior_group.setLayout(behavior_layout)
        general_layout.addWidget(behavior_group)
        
        general_layout.addStretch()
        general_tab.setLayout(general_layout)
        tabs.addTab(general_tab, self.i18n.get('settings.general.title'))
        
        # Netzwerk-Einstellungen
        network_tab = QWidget()
        network_layout = QVBoxLayout()
        
        # Transfer
        transfer_group = QGroupBox(self.i18n.get('settings.network.transfer'))
        transfer_layout = QVBoxLayout()
        
        # QoS-Level
        qos_layout = QHBoxLayout()
        qos_label = QLabel(self.i18n.get('settings.network.default_priority'))
        self.qos_combo = QComboBox()
        self.qos_combo.addItems([level.name.capitalize() for level in QoSLevel])
        self.qos_combo.setCurrentText(
            self.current_settings.get('network', {}).get(
                'qos_level',
                QoSLevel.NORMAL.name
            ).capitalize()
        )
        qos_layout.addWidget(qos_label)
        qos_layout.addWidget(self.qos_combo)
        transfer_layout.addLayout(qos_layout)
        
        # Bandbreitenlimit
        bandwidth_layout = QHBoxLayout()
        bandwidth_label = QLabel(self.i18n.get('settings.network.bandwidth_limit'))
        self.bandwidth_spin = QSpinBox()
        self.bandwidth_spin.setRange(0, 1000)  # 0 = unbegrenzt
        self.bandwidth_spin.setValue(
            self.current_settings.get('network', {}).get('bandwidth_limit', 0) 
            // (1024 * 1024)  # Konvertiere B/s in MB/s
        )
        bandwidth_layout.addWidget(bandwidth_label)
        bandwidth_layout.addWidget(self.bandwidth_spin)
        transfer_layout.addLayout(bandwidth_layout)
        
        # Parallele Transfers
        parallel_layout = QHBoxLayout()
        parallel_label = QLabel(self.i18n.get('settings.network.parallel_transfers'))
        self.parallel_spin = QSpinBox()
        self.parallel_spin.setRange(1, 16)
        self.parallel_spin.setValue(
            self.current_settings.get('network', {}).get('parallel_transfers', 4)
        )
        parallel_layout.addWidget(parallel_label)
        parallel_layout.addWidget(self.parallel_spin)
        transfer_layout.addLayout(parallel_layout)
        
        transfer_group.setLayout(transfer_layout)
        network_layout.addWidget(transfer_group)
        
        # Proxy
        proxy_group = QGroupBox(self.i18n.get('settings.network.proxy.title'))
        proxy_layout = QVBoxLayout()
        
        self.use_proxy_check = QCheckBox(
            self.i18n.get('settings.network.proxy.use_proxy')
        )
        self.use_proxy_check.setChecked(
            self.current_settings.get('network', {}).get('use_proxy', False)
        )
        self.use_proxy_check.toggled.connect(self.on_use_proxy_toggled)
        proxy_layout.addWidget(self.use_proxy_check)
        
        proxy_settings_layout = QVBoxLayout()
        
        # Proxy-Host
        host_layout = QHBoxLayout()
        host_label = QLabel(self.i18n.get('settings.network.proxy.host'))
        self.proxy_host_edit = QLineEdit()
        self.proxy_host_edit.setText(
            self.current_settings.get('network', {}).get('proxy_host', '')
        )
        host_layout.addWidget(host_label)
        host_layout.addWidget(self.proxy_host_edit)
        proxy_settings_layout.addLayout(host_layout)
        
        # Proxy-Port
        port_layout = QHBoxLayout()
        port_label = QLabel(self.i18n.get('settings.network.proxy.port'))
        self.proxy_port_spin = QSpinBox()
        self.proxy_port_spin.setRange(1, 65535)
        self.proxy_port_spin.setValue(
            self.current_settings.get('network', {}).get('proxy_port', 8080)
        )
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.proxy_port_spin)
        proxy_settings_layout.addLayout(port_layout)
        
        proxy_layout.addLayout(proxy_settings_layout)
        proxy_group.setLayout(proxy_layout)
        network_layout.addWidget(proxy_group)
        
        network_layout.addStretch()
        network_tab.setLayout(network_layout)
        tabs.addTab(network_tab, self.i18n.get('settings.network.title'))
        
        # Pfade
        paths_tab = QWidget()
        paths_layout = QVBoxLayout()
        
        # Zielverzeichnisse
        targets_group = QGroupBox(self.i18n.get('settings.paths.targets.title'))
        targets_layout = QVBoxLayout()
        
        # Standard-Zielverzeichnis
        default_target_layout = QHBoxLayout()
        default_target_label = QLabel(
            self.i18n.get('settings.paths.targets.default_target')
        )
        self.default_target_edit = QLineEdit()
        self.default_target_edit.setText(
            self.current_settings.get('paths', {}).get('default_target', '')
        )
        default_target_btn = QPushButton(self.i18n.get('general.browse'))
        default_target_btn.clicked.connect(self.on_default_target_clicked)
        default_target_layout.addWidget(default_target_label)
        default_target_layout.addWidget(self.default_target_edit)
        default_target_layout.addWidget(default_target_btn)
        targets_layout.addLayout(default_target_layout)
        
        targets_group.setLayout(targets_layout)
        paths_layout.addWidget(targets_group)
        
        # Temporäre Dateien
        temp_group = QGroupBox(self.i18n.get('settings.paths.temp.title'))
        temp_layout = QVBoxLayout()
        
        # Temp-Verzeichnis
        temp_dir_layout = QHBoxLayout()
        temp_dir_label = QLabel(self.i18n.get('settings.paths.temp.temp_dir'))
        self.temp_dir_edit = QLineEdit()
        self.temp_dir_edit.setText(
            self.current_settings.get('paths', {}).get('temp_dir', '')
        )
        temp_dir_btn = QPushButton(self.i18n.get('general.browse'))
        temp_dir_btn.clicked.connect(self.on_temp_dir_clicked)
        temp_dir_layout.addWidget(temp_dir_label)
        temp_dir_layout.addWidget(self.temp_dir_edit)
        temp_dir_layout.addWidget(temp_dir_btn)
        temp_layout.addLayout(temp_dir_layout)
        
        # Temp-Dateien aufräumen
        self.cleanup_temp_check = QCheckBox(
            self.i18n.get('settings.paths.temp.cleanup_temp')
        )
        self.cleanup_temp_check.setChecked(
            self.current_settings.get('paths', {}).get('cleanup_temp', True)
        )
        temp_layout.addWidget(self.cleanup_temp_check)
        
        temp_group.setLayout(temp_layout)
        paths_layout.addWidget(temp_group)
        
        paths_layout.addStretch()
        paths_tab.setLayout(paths_layout)
        tabs.addTab(paths_tab, self.i18n.get('settings.paths.title'))
        
        layout.addWidget(tabs)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        # Übersetze Button-Texte
        buttons.button(QDialogButtonBox.Ok).setText(self.i18n.get('general.ok'))
        buttons.button(QDialogButtonBox.Cancel).setText(
            self.i18n.get('general.cancel')
        )
        
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
        # Initialer Zustand
        self.on_use_proxy_toggled(self.use_proxy_check.isChecked())
        
    def on_use_proxy_toggled(self, checked: bool):
        """Handler für Proxy aktivieren/deaktivieren."""
        self.proxy_host_edit.setEnabled(checked)
        self.proxy_port_spin.setEnabled(checked)
        
    def on_default_target_clicked(self):
        """Handler für Standard-Zielverzeichnis auswählen."""
        directory = QFileDialog.getExistingDirectory(
            self,
            self.i18n.get('settings.paths.targets.default_target'),
            self.default_target_edit.text()
        )
        if directory:
            self.default_target_edit.setText(directory)
            
    def on_temp_dir_clicked(self):
        """Handler für Temp-Verzeichnis auswählen."""
        directory = QFileDialog.getExistingDirectory(
            self,
            self.i18n.get('settings.paths.temp.temp_dir'),
            self.temp_dir_edit.text()
        )
        if directory:
            self.temp_dir_edit.setText(directory)
            
    def show_filetypes_dialog(self):
        """Zeigt den Dialog zur Dateityp-Verwaltung."""
        from ui.components.dialogs import FileTypesDialog
        
        # Hole aktuelle Dateitypen aus den Einstellungen
        current_types = self.current_settings.get('file_types', {
            'IMAGE': ['.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif'],
            'VIDEO': ['.mp4', '.mov', '.avi', '.mkv', '.mxf', '.m4v'],
            'AUDIO': ['.mp3', '.wav', '.aac', '.flac', '.ogg'],
            'DOCUMENT': ['.pdf', '.doc', '.docx', '.txt']
        })
        
        dialog = FileTypesDialog(self, current_types)
        if dialog.exec_() == QDialog.Accepted:
            # Speichere die neuen Dateitypen
            self.current_settings['file_types'] = dialog.get_file_types()
            self.settings_changed.emit(self.current_settings)
            
    def accept(self):
        """Handler für OK-Button."""
        # Sammle alle Einstellungen
        settings = {
            'language': self.language_combo.currentText(),
            'delete_source': self.delete_source_check.isChecked(),
            'show_notifications': self.show_notifications_check.isChecked(),
            'minimize_to_tray': self.minimize_to_tray_check.isChecked(),
            'network': {
                'qos_level': self.qos_combo.currentText().upper(),
                'bandwidth_limit': self.bandwidth_spin.value() * 1024 * 1024,
                'parallel_transfers': self.parallel_spin.value(),
                'use_proxy': self.use_proxy_check.isChecked(),
                'proxy_host': self.proxy_host_edit.text(),
                'proxy_port': self.proxy_port_spin.value()
            },
            'paths': {
                'default_target': self.default_target_edit.text(),
                'temp_dir': self.temp_dir_edit.text(),
                'cleanup_temp': self.cleanup_temp_check.isChecked()
            }
        }
        
        # Speichere Einstellungen
        self.settings.save(settings)
        
        # Emittiere Signal
        self.settings_changed.emit(settings)
        
        super().accept()
