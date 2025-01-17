#!/usr/bin/env python3
"""
Hauptdatei der Ingest Tool Anwendung.
"""
import os
import sys
import logging
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QMetaType
from PyQt5.QtGui import QTextCursor, QIcon
from config.constants import (
    PROGRAMM_VERZEICHNIS, EINSTELLUNGEN_DATEI, LOG_VERZEICHNIS,
    TRANSLATIONS_VERZEICHNIS, LOG_DATEI, STANDARD_DATEITYPEN
)
from ui.qt_init import register_metatypes

# Konfiguriere Logging
def setup_logging():
    """Konfiguriert das Logging-System."""
    # Erstelle Logs-Verzeichnis wenn es nicht existiert
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Log-Datei mit Datum
    log_file = os.path.join(log_dir, f'ingest_tool_{datetime.now().strftime("%Y%m%d")}.log')
    
    # Formatierung
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter(log_format, date_format)
    
    # Root Logger konfigurieren
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Bestehende Handler entfernen
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # File Handler für alle Logs
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Console Handler für INFO und höher
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Wichtige Module auf DEBUG setzen
    debug_loggers = [
        'ui.widgets.modern_transfer_widget',
        'core.transfer.transfer_coordinator',
        'core.transfer.manager',
        'ui.handlers.transfer_event_handlers'
    ]
    
    for logger_name in debug_loggers:
        module_logger = logging.getLogger(logger_name)
        module_logger.setLevel(logging.DEBUG)
        # Stelle sicher, dass der Logger die Handler nicht propagiert
        module_logger.propagate = True
    
    # PyQt Debug-Logging
    if os.environ.get('PYQT_DEBUG_LOGGING'):
        logging.getLogger('PyQt5').setLevel(logging.DEBUG)
    else:
        logging.getLogger('PyQt5').setLevel(logging.WARNING)
    
    # Test-Log um zu verifizieren dass alles funktioniert
    root_logger.info("Logging-System initialisiert")
    for logger_name in debug_loggers:
        logging.getLogger(logger_name).debug(f"Debug-Logging aktiviert für {logger_name}")

# Globale QApplication-Instanz
app: QApplication = None

def create_app():
    """Erstellt die QApplication wenn noch nicht vorhanden."""
    global app
    if app is None:
        # Registriere alle benötigten Qt-Metatypen
        register_metatypes()
        
        app = QApplication(sys.argv)
    return app

def show_error_dialog(title: str, message: str):
    """Zeigt einen Fehlerdialog an."""
    from PyQt5.QtWidgets import QMessageBox
    create_app()  # Stelle sicher dass QApplication existiert
    QMessageBox.critical(None, title, message)

def check_requirements():
    """Überprüft und installiert benötigte Pakete."""
    try:
        from utils.requirements_checker import RequirementsChecker
        
        # Finde requirements.txt relativ zum Skript
        script_dir = os.path.dirname(os.path.abspath(__file__))
        requirements_file = os.path.join(script_dir, "requirements.txt")
        
        # Überprüfe Requirements
        checker = RequirementsChecker(requirements_file)
        if not checker.check_and_install():
            show_error_dialog(
                "Fehler",
                "Konnte benötigte Pakete nicht installieren.\n"
                "Bitte installieren Sie die Pakete manuell:\n"
                f"pip install -r {requirements_file}"
            )
            sys.exit(1)
            
    except Exception as e:
        show_error_dialog(
            "Fehler",
            f"Fehler beim Überprüfen der Abhängigkeiten:\n{e}\n\n"
            "Bitte stellen Sie sicher, dass pip installiert ist."
        )
        sys.exit(1)

def init_directories():
    """Initialisiert benötigte Verzeichnisse."""
    # Erstelle Einstellungs-Verzeichnis
    settings_dir = os.path.dirname(EINSTELLUNGEN_DATEI)
    os.makedirs(settings_dir, exist_ok=True)
    
    # Erstelle Log-Verzeichnis
    os.makedirs(LOG_VERZEICHNIS, exist_ok=True)
    
    # Erstelle Übersetzungs-Verzeichnis
    os.makedirs(TRANSLATIONS_VERZEICHNIS, exist_ok=True)
    
    dirs = [
        os.path.join(PROGRAMM_VERZEICHNIS, "config"),
        os.path.join(PROGRAMM_VERZEICHNIS, "temp")
    ]
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d)

def setup_dark_mode(app: 'QApplication'):
    """Richtet Dark Mode für die Anwendung ein."""
    app.setStyleSheet("""
        QMainWindow, QDialog {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        
        QGroupBox {
            background-color: #2d2d2d;
            border: 1px solid #3d3d3d;
            border-radius: 4px;
            margin-top: 0.5em;
            padding-top: 0.5em;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 3px 0 3px;
            color: #ffffff;
        }
        
        QListWidget, QTextEdit {
            background-color: #1e1e1e;
            border: 1px solid #3d3d3d;
            color: #ffffff;
        }
        
        QPushButton {
            background-color: #0078d4;
            border: none;
            border-radius: 2px;
            color: white;
            padding: 5px 15px;
        }
        
        QPushButton:hover {
            background-color: #1084d8;
        }
        
        QPushButton:pressed {
            background-color: #006cbd;
        }
        
        QComboBox {
            background-color: #1e1e1e;
            border: 1px solid #3d3d3d;
            border-radius: 2px;
            color: white;
            padding: 5px;
        }
        
        QComboBox::drop-down {
            border: none;
        }
        
        QComboBox::down-arrow {
            image: none;
            border: none;
        }
        
        QCheckBox {
            color: white;
        }
        
        QCheckBox::indicator {
            width: 13px;
            height: 13px;
        }
        
        QLabel {
            color: white;
        }
    """)

def main():
    """Hauptfunktion der Anwendung."""
    try:
        # Richte Logging ein
        setup_logging()
        logger = logging.getLogger(__name__)
        
        # Initialisiere Verzeichnisse
        init_directories()
        
        # Überprüfe Requirements
        check_requirements()
        
        # Starte Qt-Anwendung
        app = create_app()
        
        # Programm-Icon setzen
        app.setWindowIcon(QIcon("C:/Users/Shadow-PC/CascadeProjects/Ingest-Tool/ressourcen/icon.png"))
        
        # Initialisiere die Anwendung
        app.setStyle('Fusion')
        app.setApplicationName('Ingest Tool')
        
        # Importiere MainWindow erst nach Logging-Setup
        from ui.main_window import MainWindow
        
        # Dark Mode
        setup_dark_mode(app)
        
        # Erstelle und zeige das Hauptfenster
        window = MainWindow(app)
        window.show()
        
        # Setze die finale Größe nach dem Anzeigen
        window.resize(1440, 1230)
        
        # Führe Event-Loop aus und beende sauber
        return sys.exit(app.exec_())
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Unerwarteter Fehler: {str(e)}", exc_info=True)
        show_error_dialog(
            "Fehler",
            f"Ein unerwarteter Fehler ist aufgetreten:\n{e}"
        )
        return sys.exit(1)

if __name__ == "__main__":
    main()
