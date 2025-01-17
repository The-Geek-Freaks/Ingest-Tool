import os
import pytest
import logging
from unittest.mock import MagicMock, patch
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QListWidgetItem
from PyQt5.Qt import Qt
from datetime import timedelta

from ui.main_window import MainWindow
from ui.widgets.modern_transfer_widget import ModernTransferWidget, TransferItemData, TransferStatus
from core.transfer.transfer_coordinator import TransferCoordinator
from ui.widgets.drive_list_item import DriveListItem

@pytest.fixture
def app(qtbot):
    """Fixture für die QApplication."""
    return QApplication.instance() or QApplication([])

@pytest.fixture
def main_window(app, qtbot):
    """Fixture für das MainWindow."""
    window = MainWindow(app)
    qtbot.addWidget(window)
    return window

@pytest.fixture
def mock_filesystem():
    """Mock für das Dateisystem."""
    with patch('os.path.exists') as mock_exists, \
         patch('os.path.isfile') as mock_isfile, \
         patch('os.walk') as mock_walk, \
         patch('os.path.getsize') as mock_getsize:
        
        # Simuliere existierende Dateien
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_getsize.return_value = 1024  # 1 KB
        mock_walk.return_value = [
            ("D:\\", [], ["test1.mp4", "test2.mp4"]),
        ]
        yield

def test_transfer_signal_chain(main_window, mock_filesystem, qtbot, caplog):
    """Testet die komplette Signal-Kette vom Start-Button bis zum ModernTransferWidget."""
    caplog.set_level(logging.DEBUG)
    
    # Setze Test-Konfiguration
    main_window.target_path_edit.setText("E:/target")
    main_window.filetype_combo.addItem(".mp4")
    main_window.filetype_combo.setCurrentText(".mp4")
    
    # Setze alle Laufwerke außer D: auf ausgeschlossen
    main_window.excluded_list.clear()
    main_window.excluded_drives = ['A', 'B', 'C', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                                 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    
    # Aktualisiere die ausgeschlossenen Laufwerke in der UI
    for drive in main_window.excluded_drives:
        item = QListWidgetItem(drive)
        main_window.excluded_list.addItem(item)
    
    # Mock für DriveList
    mock_drive = DriveListItem("D:", "Test Drive", "local")
    mock_drive._setup_ui()  # Initialisiere das UI
    main_window.drives_list.addItem(mock_drive)
    main_window.drives_list.setCurrentItem(mock_drive)
    
    # Füge eine Zuordnung hinzu
    mapping_item = QListWidgetItem(".mp4 ➔ E:/target")
    main_window.mappings_list.addItem(mapping_item)
    
    # Aktualisiere die Zuordnungen
    main_window.file_watcher_manager.update_file_mappings()
    
    # Aktualisiere die gefilterte Liste
    main_window.update_filtered_drives_list()
    
    # Spy auf ModernTransferWidget
    widget_spy = qtbot.createSignalSpy(main_window.transfer_progress._update_transfer_signal)
    
    # Spy auf TransferCoordinator Signale
    coordinator_started_spy = qtbot.createSignalSpy(main_window.transfer_coordinator.transfer_started)
    coordinator_progress_spy = qtbot.createSignalSpy(main_window.transfer_coordinator.transfer_progress)
    coordinator_completed_spy = qtbot.createSignalSpy(main_window.transfer_coordinator.transfer_completed)
    
    # Klicke Start-Button
    qtbot.mouseClick(main_window.start_button, Qt.LeftButton)
    
    # Warte bis der FileWatcher gestartet ist
    qtbot.wait(100)
    
    # Simuliere neue Datei
    test_file = "D:\\test1.mp4"
    main_window.file_watcher_manager._handle_new_file(test_file)
    
    # Warte auf Signale
    def verify_signals():
        # Überprüfe TransferCoordinator Signale
        assert len(coordinator_started_spy) > 0, "Kein transfer_started Signal empfangen"
        assert len(coordinator_progress_spy) > 0, "Kein transfer_progress Signal empfangen"
        
        # Überprüfe ModernTransferWidget Signale
        assert len(widget_spy) > 0, "Kein _update_transfer_signal im Widget empfangen"
        
        # Analysiere die empfangenen Daten
        started_data = coordinator_started_spy[0]
        progress_data = coordinator_progress_spy[0]
        widget_data = widget_spy[0][0]  # [0][0] weil wir das erste Signal und dessen erste Argument wollen
        
        # Logge die Daten für Analyse
        logging.debug(f"TransferCoordinator started signal: {started_data}")
        logging.debug(f"TransferCoordinator progress signal: {progress_data}")
        logging.debug(f"ModernTransferWidget update signal: {widget_data}")
        
        # Überprüfe Datenfluss
        assert isinstance(widget_data, TransferItemData), "Widget erhielt keine TransferItemData"
        assert widget_data.transfer_id == started_data[0], "Transfer ID stimmt nicht überein"
        assert widget_data.status in [TransferStatus.RUNNING, TransferStatus.COMPLETED], "Unerwarteter Transfer-Status"
    
    # Warte auf Signal-Verarbeitung
    qtbot.waitUntil(verify_signals, timeout=5000)
    
    # Analysiere Debug-Logs
    for record in caplog.records:
        print(f"{record.levelname}: {record.message}")
