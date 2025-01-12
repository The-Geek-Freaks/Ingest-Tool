# 🚀 TheGeekFreaks Ingest-Tool

Ein professionelles Dateimanagement-Tool für automatisierte Dateiübertragungen zwischen Laufwerken. Ideal für Fotografen, Videografen und Content Creator.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

## ✨ Hauptfunktionen

### 📁 Intelligentes Dateimanagement
- **Automatische Laufwerkserkennung**: Sofortige Erkennung von USB-Sticks, SD-Karten und Netzwerklaufwerken
- **Smart-Sorting**: Automatische Sortierung nach Dateitypen in konfigurierbare Zielverzeichnisse
- **Echtzeit-Überwachung**: Sofortige Verarbeitung neuer Dateien auf überwachten Laufwerken

### 🔄 Leistungsstarke Übertragung
- **Parallele Transfers**: Mehrere Dateien gleichzeitig übertragen
- **Fortschrittsanzeige**: Detaillierte Statusanzeige für jeden Transfer
- **Abbruch-Funktion**: Flexibler Stop einzelner oder aller Transfers
- **Quellschutz**: Optional können Quelldateien nach erfolgreicher Übertragung automatisch gelöscht werden

### ⚙️ Anpassbare Konfiguration
- **Dateityp-Filter**: Fokussierung auf relevante Dateiformate (z.B. RAW, JPG, MP4)
- **Laufwerks-Blacklist**: Ausschluss bestimmter Laufwerke von der Überwachung
- **Zielverzeichnis-Mapping**: Flexible Zuordnung von Dateitypen zu Zielordnern

## 🎯 Anwendungsfälle

- **Fotografie**: Automatischer Import von Fotos von SD-Karten
- **Videoproduktion**: Organisierte Ablage von Footage nach Projekten
- **Backup**: Automatische Sicherung wichtiger Dateien auf NAS oder externe Festplatten

## 💻 Schnellstart

1. **Download & Installation**
   ```bash
   git clone https://github.com/thegeekfreaks/ingest-tool.git
   cd ingest-tool
   pip install -r requirements.txt
   ```

2. **Erste Schritte**
   ```bash
   python main.py
   ```
   - Klicken Sie auf "Einstellungen" zum Konfigurieren der Dateitypen
   - Wählen Sie Ihre Zielverzeichnisse
   - Drücken Sie "Start" zum Beginnen der Überwachung

## 🛠️ Konfiguration

### Grundeinstellungen
- Wählen Sie zu überwachende Laufwerke
- Definieren Sie Dateityp-Filter (*.raw, *.jpg, *.mp4)
- Legen Sie Zielverzeichnisse fest

### Erweiterte Optionen
```json
{
  "delete_source": false,        // Quelldateien nach Transfer löschen
  "parallel_transfers": 2,       // Anzahl gleichzeitiger Transfers
  "check_interval": 5,          // Überprüfungsintervall in Sekunden
  "auto_start": false           // Automatischer Start beim Programmstart
}
```

## 🎮 Bedienung

### Hauptfenster
- **Start/Stop**: Überwachung starten oder beenden
- **Abbrechen**: Aktive Transfers stoppen
- **Status**: Echtzeit-Übersicht aller Transfers
- **Laufwerke**: Liste verfügbarer und ausgeschlossener Laufwerke

### Transfer-Steuerung
- Fortschrittsanzeige pro Transfer
- Geschwindigkeitsanzeige in MB/s
- Abbruch-Option für einzelne Transfers
- Gesamtfortschritt aller Transfers

## 🔧 Fehlerbehebung

### Häufige Probleme
- **Laufwerk nicht erkannt**: USB-Verbindung prüfen
- **Transfer stockt**: Zielverzeichnis auf freien Speicherplatz prüfen
- **Programm reagiert nicht**: Log-Dateien unter `logs/` prüfen

### Log-Dateien
- Detaillierte Logs unter `logs/ingest.log`
- Fehlerberichte unter `logs/error.log`

## 📱 Support & Kontakt

- **GitHub Issues**: Bug-Reports und Feature-Requests
- **E-Mail**: support@thegeekfreaks.de
- **Discord**: [TheGeekFreaks Community](https://discord.gg/thegeekfreaks)

## 🤝 Mitwirken

Wir freuen uns über Beiträge! Bitte beachten Sie unsere Contribution Guidelines:
1. Fork des Repositories
2. Feature-Branch erstellen
3. Code dokumentieren
4. Pull Request einreichen

## 📄 Lizenz

GPL 3.0 License - Siehe [LICENSE](LICENSE) für Details

---
Entwickelt mit ❤️ von TheGeekFreaks
