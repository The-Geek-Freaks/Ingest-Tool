# Ingest Tool

Ein leistungsfähiges Tool zur automatisierten Dateiübertragung und -organisation von verschiedenen Laufwerken.

## 🌟 Features

- **Intelligente Laufwerkserkennung**
  - Automatische Erkennung von lokalen, USB- und Netzwerklaufwerken
  - Echtzeit-Status-Updates für verbundene Laufwerke
  - Visuelle Unterscheidung verschiedener Laufwerkstypen (💾 USB, 💿 Lokal, ☁️ Netzwerk)

- **Flexible Dateiübertragung**
  - Regelbasierte Dateiorganisation
  - Parallele Dateiübertragungen für höhere Geschwindigkeit
  - Fortschrittsanzeige in Echtzeit
  - Pause/Fortsetzen-Funktion

- **Erweiterte Verwaltung**
  - Ausschluss bestimmter Laufwerke
  - Voreinstellungen für häufig verwendete Konfigurationen
  - Detaillierte Protokollierung aller Vorgänge

## 🚀 Installation

1. Stellen Sie sicher, dass Python 3.8 oder höher installiert ist
2. Klonen Sie das Repository:
   ```bash
   git clone https://github.com/yourusername/ingest-tool.git
   cd ingest-tool
   ```
3. Installieren Sie die Abhängigkeiten:
   ```bash
   pip install -r requirements.txt
   ```

## 🛠️ Konfiguration

Die Konfiguration erfolgt über die `config.json` Datei im Hauptverzeichnis:

```json
{
  "language": "de",
  "default_filetype": "all",
  "parallel_transfers": 2,
  "auto_start": false
}
```

### Verfügbare Einstellungen:
- `language`: Sprache der Benutzeroberfläche (de, en)
- `default_filetype`: Standard-Dateityp-Filter
- `parallel_transfers`: Anzahl paralleler Übertragungen
- `auto_start`: Automatischer Start bei Laufwerkserkennung

## 🖥️ Verwendung

1. Starten Sie das Tool:
   ```bash
   python ingest_tool.py
   ```

2. Hauptfunktionen:
   - **Laufwerke**: Zeigt alle verfügbaren Laufwerke mit Status
   - **Zuordnungen**: Verwaltet Regeln für Dateiübertragungen
   - **Filter**: Wählt Dateitypen für die Übertragung
   - **Presets**: Speichert und lädt häufig verwendete Einstellungen

## 🏗️ Projektstruktur

```
ingest-tool/
├── core/                 # Kernfunktionalität
│   ├── drive_controller/    # Laufwerksverwaltung
│   └── transfer/           # Dateiübertragung
├── ui/                  # Benutzeroberfläche
│   ├── widgets/           # UI-Komponenten
│   ├── handlers/          # Event-Handler
│   └── layouts/           # Layout-Definitionen
├── utils/               # Hilfsfunktionen
├── config/              # Konfigurationsdateien
└── translations/        # Sprachdateien
```

## 🔧 Entwicklung

### Voraussetzungen
- Python 3.8+
- PyQt5
- pytest für Tests

### Tests ausführen
```bash
pytest tests/
```

### Code-Stil
- PEP 8 Konventionen
- Docstrings für alle Klassen und Methoden
- Typisierung mit Python Type Hints

## 📝 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert. Siehe [LICENSE](LICENSE) für Details.

## 🤝 Mitwirken

1. Fork des Repositories
2. Feature-Branch erstellen (`git checkout -b feature/AmazingFeature`)
3. Änderungen committen (`git commit -m 'Add some AmazingFeature'`)
4. Branch pushen (`git push origin feature/AmazingFeature`)
5. Pull Request erstellen

## 🐛 Bekannte Probleme

- Einige Netzwerklaufwerke werden möglicherweise nicht korrekt erkannt
- Große Dateien können bei der Vorschau zu Verzögerungen führen

## 📞 Support

Bei Fragen oder Problemen:
1. Überprüfen Sie die [Issues](https://github.com/yourusername/ingest-tool/issues)
2. Erstellen Sie ein neues Issue mit detaillierter Beschreibung
3. Kontaktieren Sie das Entwicklerteam

## 🙏 Danksagung

- PyQt5 Team für das großartige UI-Framework
- Alle Mitwirkenden und Tester
