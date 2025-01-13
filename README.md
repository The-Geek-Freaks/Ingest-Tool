# 🚀 TheGeekFreaks Ingest-Tool

Ein modernes und effizientes Dateimanagement-Tool für professionelle Dateiübertragungen zwischen Laufwerken. Optimiert für Fotografen, Videografen und Content Creator.

![Version](https://img.shields.io/github/v/release/The-Geek-Freaks/Ingest-Tool?include_prereleases)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![Qt](https://img.shields.io/badge/Qt-6.5+-purple.svg)
![License](https://img.shields.io/github/license/The-Geek-Freaks/Ingest-Tool)
[![GitHub issues](https://img.shields.io/github/issues/The-Geek-Freaks/Ingest-Tool)](https://github.com/The-Geek-Freaks/Ingest-Tool/issues)
[![GitHub stars](https://img.shields.io/github/stars/The-Geek-Freaks/Ingest-Tool)](https://github.com/The-Geek-Freaks/Ingest-Tool/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/The-Geek-Freaks/Ingest-Tool)](https://github.com/The-Geek-Freaks/Ingest-Tool/network)
[![GitHub last commit](https://img.shields.io/github/last-commit/The-Geek-Freaks/Ingest-Tool)](https://github.com/The-Geek-Freaks/Ingest-Tool/commits/main)
[![Downloads](https://img.shields.io/github/downloads/The-Geek-Freaks/Ingest-Tool/total)](https://github.com/The-Geek-Freaks/Ingest-Tool/releases)
[![Repo size](https://img.shields.io/github/repo-size/The-Geek-Freaks/Ingest-Tool)](https://github.com/The-Geek-Freaks/Ingest-Tool)
[![Contributors](https://img.shields.io/github/contributors/The-Geek-Freaks/Ingest-Tool)](https://github.com/The-Geek-Freaks/Ingest-Tool/graphs/contributors)
[![Activity](https://img.shields.io/github/commit-activity/m/The-Geek-Freaks/Ingest-Tool)](https://github.com/The-Geek-Freaks/Ingest-Tool/graphs/commit-activity)

## ✨ Hauptfunktionen

### 📁 Moderne Benutzeroberfläche
- **Drag & Drop Support**: Einfaches Ziehen und Ablegen von Dateien
- **Dark Mode**: Augenschonende dunkle Benutzeroberfläche
- **Responsive Design**: Dynamische Anpassung an verschiedene Fenstergrößen
- **Intuitive Bedienung**: Klare und übersichtliche Benutzerführung

### 🔄 Intelligentes Dateimanagement
- **Automatische Laufwerkserkennung**: Sofortige Erkennung von USB-Sticks, SD-Karten und Netzwerklaufwerken
- **Smart-Sorting**: Automatische Sortierung nach Dateitypen
- **Echtzeit-Überwachung**: Sofortige Verarbeitung neuer Dateien
- **Parallele Verarbeitung**: Effiziente Nutzung der System-Ressourcen

### 🔄 Leistungsstarke Übertragung
- **Parallele Transfers**: Mehrere Dateien gleichzeitig übertragen
- **Fortschrittsanzeige**: Detaillierte Statusanzeige für jeden Transfer
- **Laufwerks-Management**: Flexible Verwaltung von Quell- und Ziellaufwerken
- **Fehlerbehandlung**: Robuste Fehlerbehandlung und Wiederaufnahme
- **Logging**: Umfangreiche Protokollierung aller Aktivitäten

## 🎯 Anwendungsfälle

- **Fotografie**: Automatischer Import von Fotos von SD-Karten
- **Videoproduktion**: Organisierte Ablage von Footage nach Projekten
- **Backup**: Automatische Sicherung wichtiger Dateien auf NAS oder externe Festplatten

## 💻 Systemanforderungen

- **Betriebssystem**: Windows 10/11
- **Python**: 3.11 oder höher
- **Arbeitsspeicher**: Mindestens 4GB RAM
- **Festplattenspeicher**: 100MB freier Speicherplatz

## 🚀 Installation

## 💻 Schnellstart

1. **Download & Installation**
   ```bash
   pip install -r requirements.txt
   ```

2. **Erste Schritte**
   ```bash
   python main.py
   ```
   - Klicken Sie auf "Einstellungen" zum Konfigurieren der Dateitypen
   - Wählen Sie Ihre Zielverzeichnisse in den Zuordnungswidget
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

### Bekannte Probleme
- **Laufwerkserkennung**: Stellen Sie sicher, dass die Laufwerke korrekt eingebunden sind
- **Performance**: Überprüfen Sie die Systemauslastung bei vielen parallelen Transfers
- **Berechtigungen**: Administratorrechte können für bestimmte Funktionen erforderlich sein

### Logs
- Programm-Logs: `logs/ingest.log`
- Error-Logs: `logs/error.log`

## 📱 Support

- **GitHub Issues**: [Bug-Reports und Feature-Requests](https://github.com/The-Geek-Freaks/Ingest-Tool/issues)
- **E-Mail**: support@thegeekfreaks.de
- **Discord**: [TheGeekFreaks Community](https://discord.gg/thegeekfreaks)

## 📄 Lizenz

Dieses Projekt ist unter der GNU General Public License v3.0 (GPLv3) lizenziert - siehe [LICENSE](LICENSE) für Details.

Diese Lizenz garantiert Ihnen folgende Freiheiten:
- Die Software für jeden Zweck auszuführen
- Die Software zu studieren und zu modifizieren
- Kopien der Software weiterzugeben
- Modifizierte Versionen der Software zu verbreiten

Unter der Bedingung, dass:
- Der Quellcode aller abgeleiteten Werke unter der GPLv3 veröffentlicht wird
- Alle Änderungen dokumentiert werden
- Die vollständige Lizenz und Copyright-Hinweise beibehalten werden

Für die vollständige Lizenz siehe: [GNU GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html)

---
Entwickelt mit ❤️ von TheGeekFreaks
