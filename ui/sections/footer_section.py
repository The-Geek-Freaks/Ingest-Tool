from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QPushButton, QDialog, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, QSize, QDateTime
from PyQt5.QtGui import QIcon, QPixmap
from ..widgets import CustomButton

class FAQDialog(QDialog):
    """Dialog für häufig gestellte Fragen."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Häufig gestellte Fragen")
        self.setMinimumSize(600, 400)
        self.setup_ui()
        
    def setup_ui(self):
        """Richtet die UI des Dialogs ein."""
        layout = QVBoxLayout(self)
        
        # Scrollbereich für FAQ-Einträge
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        # Container für FAQ-Einträge
        container = QWidget()
        faq_layout = QVBoxLayout(container)
        faq_layout.setSpacing(20)
        
        # FAQ-Einträge
        faqs = [
            ("Wie füge ich neue Laufwerke hinzu?",
             "Schließen Sie ein Laufwerk an Ihren Computer an. Das Tool erkennt automatisch neue Laufwerke und zeigt sie in der Liste an."),
            
            ("Wie richte ich Dateitypzuordnungen ein?",
             "Klicken Sie auf den 'Zuordnung hinzufügen' Button und wählen Sie einen Dateityp (z.B. *.mp4) sowie ein Zielverzeichnis aus."),
            
            ("Was bedeuten die verschiedenen Log-Level?",
             "DEBUG: Detaillierte Informationen für Entwickler\n"
             "INFO: Allgemeine Informationen über den Programmablauf\n"
             "WARNING: Warnungen, die Ihre Aufmerksamkeit erfordern\n"
             "ERROR: Fehler, die den normalen Ablauf stören"),
            
            ("Wie kann ich Dateien umbenennen?",
             "Nutzen Sie die Batch-Rename Funktion in den erweiterten Einstellungen. Dort können Sie Muster und Regeln für die automatische Umbenennung festlegen."),
            
            ("Was tun bei Übertragungsfehlern?",
             "1. Prüfen Sie die Verbindung zum Laufwerk\n"
             "2. Kontrollieren Sie den verfügbaren Speicherplatz\n"
             "3. Schauen Sie im Protokoll nach detaillierten Fehlermeldungen\n"
             "4. Versuchen Sie die Übertragung mit weniger parallelen Kopien"),
             
            ("Wie funktioniert die automatische Überwachung?",
             "Das Tool überwacht die ausgewählten Laufwerke auf neue Dateien. Sobald eine Datei erkannt wird, die den konfigurierten Typen entspricht, wird sie automatisch in das zugeordnete Verzeichnis kopiert.")
        ]
        
        for question, answer in faqs:
            # Frage
            q_label = QLabel(f"<b>{question}</b>")
            q_label.setTextFormat(Qt.RichText)
            q_label.setWordWrap(True)
            faq_layout.addWidget(q_label)
            
            # Antwort
            a_label = QLabel(answer)
            a_label.setWordWrap(True)
            a_label.setStyleSheet("color: #666;")
            faq_layout.addWidget(a_label)
            
            # Trennlinie
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setStyleSheet("background-color: #404040;")
            faq_layout.addWidget(line)
            
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        # Schließen-Button
        close_btn = QPushButton("Schließen")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

class FooterSection(QWidget):
    """Footer-Sektion des Hauptfensters."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Richtet das UI der Footer-Sektion ein."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 0)
        
        # Status und Progress
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_label = QLabel("Bereit")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #2ecc71;
                font-size: 10pt;
            }
        """)
        
        self.speed_label = QLabel("0 MB/s")
        self.speed_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 10pt;
            }
        """)
        
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.speed_label)
        
        layout.addWidget(status_widget)
        
        # Fortschrittsbalken
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid gray;
                border-radius: 3px;
                background-color: #3d3d3d;
                text-align: center;
                color: white;
                font-size: 10pt;
            }
            QProgressBar::chunk {
                background-color: rgb(13, 71, 161);
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Buttons
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        self.start_button = CustomButton(
            "Start",
            tooltip="Transfer starten (Strg+Enter)"
        )
        
        self.stop_button = CustomButton(
            "Transfer abbrechen",
            tooltip="Transfer abbrechen (Strg+Esc)"
        )
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: black;
                border: 1px solid gray;
                padding: 8px 15px;
                font-size: 10pt;
                min-width: 120px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        
        layout.addWidget(button_widget)
        
        # Copyright und FAQ
        copyright_widget = QWidget()
        copyright_layout = QHBoxLayout(copyright_widget)
        copyright_layout.setContentsMargins(0, 0, 0, 0)
        
        copyright_label = QLabel("TheGeekFreaks - Alexander Zuber-Jatzke 2025")
        copyright_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 9pt;
            }
        """)
        copyright_label.setAlignment(Qt.AlignCenter)
        
        faq_button = QPushButton("FAQ")
        faq_button.setIcon(QIcon(QPixmap("ressourcen/icons/help.png")))
        faq_button.clicked.connect(self.show_faq)
        
        copyright_layout.addWidget(copyright_label)
        copyright_layout.addStretch()
        copyright_layout.addWidget(faq_button)
        
        layout.addWidget(copyright_widget)
        
    def show_faq(self):
        """Zeigt den FAQ-Dialog."""
        dialog = FAQDialog(self)
        dialog.exec_()
