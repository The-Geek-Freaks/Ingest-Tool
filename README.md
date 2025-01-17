<div align="center">
  <img src="docs/assets/banner.png" alt="TheGeekFreaks Ingest-Tool Banner" width="100%"/>
  <h1>🚀 TheGeekFreaks Ingest-Tool</h1>
  <p>Ein modernes und effizientes Dateimanagement-Tool für professionelle Dateiübertragungen zwischen Laufwerken.</p>
  <p>Optimiert für Fotografen, Videografen und Content Creator.</p>

  ![Status](https://img.shields.io/badge/Status-Beta-yellow)
  ![Version](https://img.shields.io/github/v/release/The-Geek-Freaks/Ingest-Tool?include_prereleases)
  ![Python](https://img.shields.io/badge/python-3.11+-green.svg)
  ![Qt](https://img.shields.io/badge/Qt-6.5+-purple.svg)
  ![Windows](https://img.shields.io/badge/Windows-10%2F11-blue)
  ![License](https://img.shields.io/badge/License-GPLv3-blue.svg)
  [![GitHub issues](https://img.shields.io/github/issues/The-Geek-Freaks/Ingest-Tool)](https://github.com/The-Geek-Freaks/Ingest-Tool/issues)
  [![GitHub stars](https://img.shields.io/github/stars/The-Geek-Freaks/Ingest-Tool)](https://github.com/The-Geek-Freaks/Ingest-Tool/stargazers)
  ![Contributors](https://img.shields.io/github/contributors/The-Geek-Freaks/Ingest-Tool)
  ![Downloads](https://img.shields.io/github/downloads/The-Geek-Freaks/Ingest-Tool/total)
  [![Discord](https://img.shields.io/discord/397127284114325504?label=Discord&logo=discord)](https://tgf.click/discord)
</div>

## 📑 Inhaltsverzeichnis
- [✨ Hauptfunktionen](#-hauptfunktionen)
- [🎯 Anwendungsfälle](#-anwendungsfälle)
- [💻 Installation](#-installation)
- [🛠️ Konfiguration](#️-konfiguration)
- [🎮 Bedienung](#-bedienung)
- [⚡ Performance](#-performance)
- [🗺️ Roadmap](#️-roadmap)
- [🔧 Fehlerbehebung](#-fehlerbehebung)
- [📄 Lizenz](#-lizenz)

<div align="center">
  <img src="docs/assets/demo.gif" alt="Ingest-Tool Demo" width="80%"/>
</div>

## ⭐ Highlights

<div align="center">
  <table>
    <tr>
      <td align="center">
        <img src="docs/assets/feature1.png" width="200px" /><br/>
        <b>Intelligentes Mapping</b>
      </td>
      <td align="center">
        <img src="docs/assets/feature2.png" width="200px" /><br/>
        <b>Echtzeit-Monitoring</b>
      </td>
      <td align="center">
        <img src="docs/assets/feature3.png" width="200px" /><br/>
        <b>Schnelle Transfers</b>
      </td>
    </tr>
  </table>
</div>

## ✨ Hauptfunktionen

### 📁 Moderne Benutzeroberfläche
- **Drag & Drop Support**: Einfaches Ziehen und Ablegen von Dateien
- **Dark/Light Mode**: Augenschonende Themes für Tag und Nacht
- **Responsive Design**: Dynamische Anpassung an Fenstergrößen
- **Intuitive Bedienung**: Klare und übersichtliche Benutzerführung
- **Multi-Monitor Support**: Optimiert für mehrere Bildschirme
- **Customizable Layout**: Anpassbare Arbeitsbereiche
- **Schnellzugriff-Leiste**: Häufig genutzte Funktionen direkt erreichbar
- **Kontextmenüs**: Rechtskick-Optionen für schnelle Aktionen

### 🔄 Intelligentes Dateimanagement
- **Automatische Laufwerkserkennung**: Sofortige Erkennung von:
  - USB-Sticks und externe Festplatten
  - SD-Karten und Speichermedien
  - Netzwerklaufwerke (SMB/NFS)
  - Cloud-Speicher Integration
- **Smart-Sorting**: Automatische Sortierung nach:
  - Dateityp und -format
  - Aufnahmedatum (EXIF)
  - Projektstruktur
  - Benutzerdefinierten Regeln
- **Echtzeit-Überwachung**:
  - Live-Vorschau der Dateien
  - Automatische Verarbeitung
  - Änderungserkennung
  - Fehlerbenachrichtigungen
- **Duplikaterkennung**:
  - MD5/SHA Prüfsummen
  - Intelligente Namensgebung
  - Versionskontrolle
  - Konfliktlösung

### 🚀 Leistungsstarke Übertragung
- **Hochgeschwindigkeits-Transfer**:
  - Parallele Übertragungen
  - Gepufferte Schreibvorgänge
  - Optimierte Chunk-Größen
  - SSD-optimierte Transfers
- **Sicherheitsfunktionen**:
  - Automatische Backups
  - Checksummen-Verifikation
  - Wiederaufnahme nach Abbruch
  - Verschlüsselte Übertragung
- **Fortschrittsüberwachung**:
  - Detaillierte Statistiken
  - Geschwindigkeitsanzeige
  - Restzeit-Berechnung
  - Transfer-Logs

### 🛠️ Profi-Werkzeuge
- **Batch-Verarbeitung**:
  - Massenumbenennungen
  - Metadaten-Bearbeitung
  - Format-Konvertierung
  - Filter und Sortierung
- **Workflow-Automation**:
  - Benutzerdefinierte Regeln
  - Zeitgesteuerte Aufgaben
  - Event-basierte Aktionen
- **Datei-Analyse**:
  - EXIF-Daten Auswertung
  - Dateityp-Erkennung
  - Größenanalyse
  - Integritätsprüfung
- **Reporting**:
  - Transfer-Berichte
  - Fehlerprotokolle
  - Nutzungsstatistiken
  - Export-Funktionen


## ⚡ Performance

### Optimierte Dateiübertragung
- Parallele Verarbeitung für große Dateimengen
- Intelligentes Chunk-Management
- Fortgeschrittene Fehlerbehandlung
- Automatische Wiederaufnahme bei Unterbrechungen

### Ressourcennutzung
- Dynamische Speicherverwaltung
- Effiziente CPU-Nutzung
- Optimierte I/O-Operationen

| Operation | Geschwindigkeit |
|-----------|----------------|
| Kopieren (SSD → SSD) | ~500 MB/s |
| Kopieren (HDD → SSD) | ~120 MB/s |
| Kopieren (NVMe → NVMe) | ~2000 MB/s |
| Dateianalyse | ~10.000 Dateien/s |

## 🚀 Installation

### Windows Installer
⬇️ [Neueste Version herunterladen](https://github.com/The-Geek-Freaks/Ingest-Tool/releases/latest)

### Manuelle Installation
   ```bash
# Repository klonen
   git clone https://github.com/The-Geek-Freaks/Ingest-Tool.git

# Ins Verzeichnis wechseln
   cd Ingest-Tool

# Abhängigkeiten installieren
   pip install -r requirements.txt
   ```
5. Anwendung starten:
   ```bash
   python ingest_tool.py
   ```

### Development Setup
Für Entwickler empfehlen wir zusätzlich:
```bash
pip install -r requirements-dev.txt
```

Dies installiert:
- pytest für Unit Tests
- black für Code-Formatierung
- mypy für statische Typ-Überprüfung

## 🛠️ Konfiguration

### Umgebungsvariablen
Erstellen Sie eine `.env` Datei im Root-Verzeichnis:
```env
DEBUG=False
LOG_LEVEL=INFO
THEME=dark
```

### Logging
Logs werden standardmäßig in `./logs` gespeichert. Das Log-Level kann in der `.env` Datei konfiguriert werden.

## 🔧 Fehlerbehebung

### Bekannte Probleme
- UI kann bei sehr großen Dateimengen (>100GB) verzögert reagieren
- Netzwerkverbindungen können bei instabiler Verbindung neu aufgebaut werden müssen

### Debugging
1. Debug-Modus aktivieren in `.env`:
   ```env
   DEBUG=True
   LOG_LEVEL=DEBUG
   ```
2. Log-Dateien prüfen unter `./logs`
3. Bei Bedarf Issue auf GitHub erstellen

## 🗺️ Roadmap

- [x] Basis-Funktionalität
- [x] Drag & Drop Support
- [x] Intelligente Dateizuordnung
- [x] Fortschrittsanzeige
- [ ] Profi-Funktionen
  - [ ] Erweiterte Filteroptionen
  - [x] Backup-Strategien
  - [x] Automatisierte Workflows
- [ ] Crossplattform
  - [ ] Linux Support
  - [ ] macOS Support
- [ ] Rechtsklickintegration
- [ ] API für Entwickler

## 👥 Community

[![Discord](https://img.shields.io/discord/XXXXX?label=Discord&logo=discord)](https://discord.gg/thegeekfreaks)
[![Twitter](https://img.shields.io/twitter/follow/thegeekfreaks?style=social)](https://twitter.com/thegeekfreaks)

- 🤝 [Wie du beitragen kannst](CONTRIBUTING.md)
- 💬 [Community-Richtlinien](CODE_OF_CONDUCT.md)
- 🌟 [Hall of Fame](https://github.com/The-Geek-Freaks/Ingest-Tool/graphs/contributors)

## 🔧 Fehlerbehebung

### Bekannte Probleme
- **Submenü funktionslos**: Einige Submenüpunkte noch nicht implementiert
- **Themewahl**: Themeauswahl noch nicht implementiert
- **Sprachwahl**: Sprachwahl noch nicht funktionsfähig

### Support
- **GitHub Issues**: [Bug-Reports und Feature-Requests](https://github.com/The-Geek-Freaks/Ingest-Tool/issues)
- **E-Mail**: support@thegeekfreaks.de
- **Discord**: [TheGeekFreaks Community](https://discord.gg/thegeekfreaks)

### Logs
- Programm-Logs: `logs/ingest.log`
- Error-Logs: `logs/error.log`
- Transfer-Logs: `logs/transfer.log`

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

## 📝 Changelog

Eine detaillierte Liste aller Änderungen finden Sie in der [CHANGELOG.md](CHANGELOG.md) Datei.

---
<div align="center">
  <p>Entwickelt mit ❤️ von TheGeekFreaks</p>
  <p>Copyright © 2025 TheGeekFreaks. Alle Rechte vorbehalten.</p>
</div>
