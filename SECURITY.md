# 🔒 Sicherheitsrichtlinie

## 🛡️ Unterstützte Versionen

| Version | Unterstützt          | Unterstützung bis |
| ------- | ------------------- | ----------------- |
| 0.1.x   | :white_check_mark: | 31.12.2025       |
| < 0.1.0 | :x:                | -                 |

## 🔍 Sicherheitslücken melden

Die Sicherheit unserer Nutzer hat höchste Priorität. Wir sind dankbar für jeden Hinweis auf mögliche Sicherheitslücken.

### ✉️ Meldeprozess

1. **Vertrauliche Meldung**:
   - E-Mail an: security@thegeekfreaks.de
   - PGP-Key: [security_pgp.asc](./security_pgp.asc)
   - Alternativ: Über unseren [Security Advisory](https://github.com/The-Geek-Freaks/Ingest-Tool/security/advisories/new)

2. **Erforderliche Informationen**:
   - Detaillierte Beschreibung der Schwachstelle
   - Schritte zur Reproduktion
   - Mögliche Auswirkungen
   - Version des Ingest-Tools
   - Betriebssystem und Version

3. **Antwortzeit**:
   - Erste Rückmeldung: innerhalb von 48 Stunden
   - Statusupdates: mindestens alle 5 Werktage
   - Behebung: je nach Schweregrad (siehe unten)

### ⏱️ Bearbeitungszeiten nach Schweregrad

| Schweregrad | Beschreibung | Reaktionszeit | Behebungszeit |
|-------------|--------------|---------------|---------------|
| Kritisch    | RCE, Datenverlust | < 24h | < 7 Tage |
| Hoch        | Lokale Ausführung | < 48h | < 14 Tage |
| Mittel      | DoS, Funktionsstörung | < 72h | < 30 Tage |
| Niedrig     | UI/UX Probleme | < 7 Tage | < 60 Tage |

## 🔒 Sicherheitsmaßnahmen

### 📦 Code-Sicherheit
- Automatische Dependency-Updates via Dependabot
- Code-Scanning mit CodeQL
- Regelmäßige Sicherheitsaudits
- Signierte Releases

### 🛡️ Datenverarbeitung
- Verschlüsselte Datenübertragung (AES-256)
- Keine Speicherung sensibler Daten
- Lokale Verarbeitung priorisiert
- Sichere Temporärdateien-Handhabung

### 🔑 Best Practices
- Principle of Least Privilege
- Defense in Depth
- Secure by Default
- Fail Secure

## 📜 Verantwortungsvolle Offenlegung

Wir folgen dem Prinzip der verantwortungsvollen Offenlegung:

1. **Meldung**: Sicherheitslücke wird gemeldet
2. **Bestätigung**: Wir bestätigen den Eingang
3. **Untersuchung**: Problem wird analysiert
4. **Behebung**: Fix wird entwickelt und getestet
5. **Veröffentlichung**: Nach Behebung wird CVE erstellt
6. **Anerkennung**: Finder wird in Hall of Fame gelistet


## 📋 Checkliste für Sicherheitsmeldungen

```markdown
### Beschreibung
- [ ] Detaillierte Beschreibung der Schwachstelle
- [ ] Betroffene Komponenten identifiziert
- [ ] Mögliche Auswirkungen beschrieben

### Reproduktion
- [ ] Schritte zur Reproduktion dokumentiert
- [ ] Proof of Concept (PoC) bereitgestellt
- [ ] Betroffene Versionen angegeben

### Umgebung
- [ ] Betriebssystem und Version
- [ ] Ingest-Tool Version
- [ ] Relevante Konfigurationen

### Zusätzlich
- [ ] Screenshots/Videos (falls zutreffend)
- [ ] Vorgeschlagene Behebung (optional)
- [ ] CVE-ID (falls vorhanden)
```

## 📞 Kontakt

- Security Team: security@thegeekfreaks.de
- PGP Key: [security_pgp.asc](./security_pgp.asc)
- Discord: [TGF Security](https://tgf.click/discord)
- Twitter: [@TGFSecurity](https://twitter.com/TGFSecurity)

---

Letzte Aktualisierung: 13.01.2025
