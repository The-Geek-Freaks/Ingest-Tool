#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""FAQ Widget für das Hauptfenster."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton,
    QLabel, QScrollArea, QFrame, QDialog,
    QDialogButtonBox, QHBoxLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor

class FAQDialog(QDialog):
    """Dialog zur Anzeige von häufig gestellten Fragen."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Erstellt das UI des FAQ Dialogs."""
        self.setWindowTitle("Häufig gestellte Fragen")
        self.setMinimumSize(800, 800)
        
        # Dark Mode Palette
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#1e1e1e"))
        palette.setColor(QPalette.WindowText, QColor("#ffffff"))
        palette.setColor(QPalette.Base, QColor("#2d2d2d"))
        palette.setColor(QPalette.AlternateBase, QColor("#353535"))
        palette.setColor(QPalette.Text, QColor("#ffffff"))
        palette.setColor(QPalette.Button, QColor("#353535"))
        palette.setColor(QPalette.ButtonText, QColor("#ffffff"))
        self.setPalette(palette)
        
        # Hauptlayout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border-bottom: 1px solid #404040;
            }
        """)
        header.setMinimumHeight(100)
        header_layout = QVBoxLayout(header)
        
        # Titel
        title = QLabel("Häufig gestellte Fragen (FAQ)")
        title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 24px;
                font-weight: bold;
                padding: 10px;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)
        
        # Untertitel
        subtitle = QLabel("Hier finden Sie Antworten auf die häufigsten Fragen zum Ingest Tool")
        subtitle.setStyleSheet("""
            QLabel {
                color: #b0b0b0;
                font-size: 14px;
            }
        """)
        subtitle.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(subtitle)
        
        layout.addWidget(header)
        
        # Content Container
        content_container = QWidget()
        content_container.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
            }
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #404040;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4a4a4a;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background-color: #2d2d2d;
            }
        """)
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(10)
        
        # FAQ Einträge
        faqs = [
            {
                "category": " Allgemein",
                "items": [
                    {
                        "question": "Was ist das Ingest Tool?",
                        "answer": "Das Ingest Tool ist eine professionelle Anwendung zur automatischen Übertragung von Dateien von angeschlossenen Laufwerken zu definierten Zielordnern. Es wurde speziell für Fotografen, Videografen und Medienproduktionen entwickelt, um den Workflow bei der Dateiübertragung zu optimieren."
                    },
                    {
                        "question": "Für wen ist das Tool geeignet?",
                        "answer": "Das Tool ist ideal für:\n- Fotografen und Videografen\n- Medienproduktionen\n- Content Creator\n- Alle, die regelmäßig große Datenmengen von Speicherkarten übertragen"
                    },
                    {
                        "question": "Wie starte ich die Überwachung?",
                        "answer": "1. Klicken Sie auf den 'Start' Button im unteren Bereich\n2. Das Tool beginnt die Überwachung der Laufwerke\n3. Neue Laufwerke werden automatisch erkannt\n4. Der Status wird in der Statusleiste angezeigt"
                    }
                ]
            },
            {
                "category": " Laufwerke und Übertragung",
                "items": [
                    {
                        "question": "Wie füge ich ein neues Laufwerk hinzu?",
                        "answer": "1. Schließen Sie ein USB-Laufwerk oder eine Speicherkarte an\n2. Das Tool erkennt es automatisch\n3. Das Laufwerk erscheint in der Liste der verbundenen Laufwerke\n4. Die Erkennung erfolgt in der Regel innerhalb weniger Sekunden"
                    },
                    {
                        "question": "Wie erstelle ich eine neue Zuordnung?",
                        "answer": "1. Klicken Sie auf 'Hinzufügen' im Zuordnungen-Bereich\n2. Wählen Sie den gewünschten Dateityp aus (z.B. .RAW, .MP4)\n3. Wählen Sie den Zielordner\n4. Optional: Aktivieren Sie 'Unterordner erstellen'\n5. Bestätigen Sie mit 'OK'"
                    },
                    {
                        "question": "Welche Dateitypen werden unterstützt?",
                        "answer": "Das Tool unterstützt alle gängigen Medienformate:\n- Fotos: RAW, ARW, CR2, CR3, NEF, DNG, JPG, TIFF\n- Videos: MP4, MOV, MXF, AVI, MTS\n- Audio: WAV, MP3, AAC\n- Dokumente: PDF, TXT, XML"
                    }
                ]
            },
            {
                "category": " Einstellungen und Konfiguration",
                "items": [
                    {
                        "question": "Was sind Presets?",
                        "answer": "Presets sind vordefinierte Einstellungen für:\n- Dateityp-Zuordnungen\n- Zielverzeichnisse\n- Benennungsregeln\n- Automatisierungsoptionen\n\nSie können mehrere Presets erstellen und zwischen ihnen wechseln."
                    },
                    {
                        "question": "Wie konfiguriere ich automatische Unterordner?",
                        "answer": "1. Öffnen Sie die erweiterten Einstellungen\n2. Wählen Sie 'Ordnerstruktur'\n3. Aktivieren Sie 'Automatische Unterordner'\n4. Wählen Sie das gewünschte Format:\n   - Datum (YYYY-MM-DD)\n   - Projekt\n   - Benutzerdefiniert"
                    },
                    {
                        "question": "Wie funktioniert die Plugin-Verwaltung?",
                        "answer": "1. Öffnen Sie die erweiterten Einstellungen\n2. Wechseln Sie zum Tab 'Plugins'\n3. Hier können Sie:\n   - Neue Plugins installieren\n   - Vorhandene Plugins aktivieren/deaktivieren\n   - Plugin-Einstellungen anpassen\n   - Plugins aktualisieren"
                    }
                ]
            },
            {
                "category": " Überwachung und Status",
                "items": [
                    {
                        "question": "Welche Statusanzeigen gibt es?",
                        "answer": "Das Tool zeigt folgende Status an:\n- Bereit: Wartet auf neue Transfers\n- Übertragung läuft\n- Warnung: Aufmerksamkeit erforderlich\n- Fehler: Problem aufgetreten"
                    },
                    {
                        "question": "Wie funktioniert die Fortschrittsanzeige?",
                        "answer": "Die Fortschrittsanzeige zeigt:\n1. Gesamtfortschritt aller Transfers\n2. Einzelfortschritt pro Datei\n3. Übertragungsgeschwindigkeit\n4. Geschätzte Restzeit\n5. Bereits übertragene Datenmenge"
                    }
                ]
            },
            {
                "category": " Protokollierung und Berichte",
                "items": [
                    {
                        "question": "Welche Protokollierungsoptionen gibt es?",
                        "answer": "Das Tool bietet verschiedene Protokollierungsebenen:\n1. INFO: Normale Aktivitäten\n2. DEBUG: Detaillierte Informationen\n3. WARNING: Warnungen\n4. ERROR: Fehlermeldungen\n\nProtokolle können gespeichert und exportiert werden."
                    },
                    {
                        "question": "Wie erstelle ich einen Transferbericht?",
                        "answer": "1. Klicken Sie nach dem Transfer auf 'Bericht erstellen'\n2. Wählen Sie den Berichtszeitraum\n3. Wählen Sie die gewünschten Details:\n   - Übertragene Dateien\n   - Fehler und Warnungen\n   - Statistiken\n4. Exportieren Sie den Bericht als PDF oder CSV"
                    }
                ]
            },
            {
                "category": " Fehlerbehebung und Support",
                "items": [
                    {
                        "question": "Ein Laufwerk wird nicht erkannt, was kann ich tun?",
                        "answer": "Folgen Sie diesen Schritten:\n1. Prüfen Sie die physische Verbindung\n2. Prüfen Sie in Windows:\n   - Datenträgerverwaltung\n   - Geräte-Manager\n3. Verwenden Sie einen anderen USB-Port\n4. Starten Sie das Tool neu\n5. Prüfen Sie die Protokolle"
                    },
                    {
                        "question": "Wie optimiere ich die Übertragungsgeschwindigkeit?",
                        "answer": "Tipps für maximale Geschwindigkeit:\n1. Verwenden Sie USB 3.0/3.1 Ports (blau)\n2. Schließen Sie andere Programme\n3. Defragmentieren Sie Ziellaufwerke\n4. Aktivieren Sie den Hochleistungsmodus\n5. Prüfen Sie die Festplattenauslastung"
                    },
                    {
                        "question": "Wo finde ich Support?",
                        "answer": "Support-Optionen:\n1. Online-Dokumentation: docs.geekfreaks.de\n2. Support-Forum: forum.geekfreaks.de\n3. E-Mail: support@geekfreaks.de\n4. Live-Chat: Während der Geschäftszeiten\n5. Remote-Support: Nach Vereinbarung"
                    }
                ]
            }
        ]
        
        # FAQ-Einträge nach Kategorien hinzufügen
        for category in faqs:
            # Kategorie-Container
            category_container = QWidget()
            category_container.setStyleSheet("""
                QWidget {
                    background-color: #2d2d2d;
                    border-radius: 8px;
                    padding: 10px;
                }
            """)
            category_layout = QVBoxLayout(category_container)
            category_layout.setSpacing(10)
            
            # Kategorie-Header
            category_header = QWidget()
            header_layout = QHBoxLayout(category_header)
            header_layout.setContentsMargins(0, 0, 0, 0)
            
            # Kategorie-Label
            category_label = QLabel(category["category"])
            category_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
            category_label.setStyleSheet("color: #2196F3;")
            header_layout.addWidget(category_label)
            
            # Linie
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)
            line.setStyleSheet("background-color: #e9ecef;")
            header_layout.addWidget(line)
            
            category_layout.addWidget(category_header)
            
            # FAQ-Einträge der Kategorie
            for item in category["items"]:
                faq_entry = FAQEntry(item["question"], item["answer"])
                category_layout.addWidget(faq_entry)
            
            content_layout.addWidget(category_container)
        
        # Scrollbereich
        scroll = QScrollArea()
        scroll.setWidget(content_container)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        layout.addWidget(scroll)
        
        # Footer
        footer = QWidget()
        footer.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border-top: 1px solid #404040;
            }
            QPushButton {
                background-color: #404040;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #353535;
            }
        """)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 10, 20, 10)
        
        # Copyright
        copyright = QLabel(" 2025 TheGeekFreaks. Alle Rechte vorbehalten.")
        copyright.setStyleSheet("color: #b0b0b0;")
        footer_layout.addWidget(copyright)
        
        # Schließen Button
        close_button = QPushButton("Schließen")
        close_button.setFixedWidth(120)
        close_button.clicked.connect(self.close)
        footer_layout.addWidget(close_button)
        
        layout.addWidget(footer)

class FAQEntry(QWidget):
    """Ein einzelner FAQ-Eintrag mit Frage und Antwort."""
    
    def __init__(self, question, answer, parent=None):
        super().__init__(parent)
        self.question = question
        self.answer = answer
        self.is_expanded = False
        self.setup_ui()
        
    def setup_ui(self):
        """Erstellt das UI des FAQ-Eintrags."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Container für den FAQ-Eintrag
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border-radius: 4px;
                border: 1px solid #404040;
            }
            QFrame:hover {
                border-color: #4a4a4a;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(15, 15, 15, 15)
        container_layout.setSpacing(10)
        
        # Frage Button
        self.question_button = QPushButton(self.question)
        self.question_button.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px;
                background-color: transparent;
                color: #ffffff;
                border: none;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #2196F3;
            }
        """)
        self.question_button.clicked.connect(self.toggle_answer)
        container_layout.addWidget(self.question_button)
        
        # Antwort Label
        self.answer_label = QLabel(self.answer)
        self.answer_label.setWordWrap(True)
        self.answer_label.setStyleSheet("""
            QLabel {
                color: #b0b0b0;
                padding: 8px;
                background-color: #353535;
                border-radius: 4px;
            }
        """)
        self.answer_label.hide()
        container_layout.addWidget(self.answer_label)
        
        layout.addWidget(container)
        
    def toggle_answer(self):
        """Zeigt oder versteckt die Antwort."""
        self.is_expanded = not self.is_expanded
        self.answer_label.setVisible(self.is_expanded)
        # Ändere den Pfeil je nach Zustand
        self.question_button.setText(f"{'▼' if self.is_expanded else '▶'} {self.question}")
