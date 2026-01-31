# Claude Code Recall

**Ein GUI-Tool zum Durchsuchen und Verwalten des Claude Code Sitzungsverlaufs über alle Projekte hinweg**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Mac%20%7C%20Linux-lightgrey.svg)]()

[日本語](README.md) | [English](README_en.md) | [한국어](README_ko.md) | Deutsch | [Français](README_fr.md) | [Português](README_pt-BR.md) | [Español](README_es.md)

## Überblick

Claude Code Recall ist eine Desktop-Anwendung, mit der Sie den Sitzungsverlauf aller [Claude Code](https://docs.anthropic.com/en/docs/claude-code)-Projekte durchsuchen, ansehen und verwalten können.

**Funktionen, die im offiziellen Tool nicht verfügbar sind:**
- Projektübergreifende Sitzungssuche
- Sitzung mit einem Klick fortsetzen
- Unerwünschte Sitzungen löschen

## Funktionen

| Funktion | Beschreibung |
|----------|--------------|
| **Sitzungsliste** | Alle Projektsitzungen chronologisch anzeigen |
| **Suche** | Nach Projektname oder Nachrichteninhalt filtern |
| **Filter** | Systemsitzungen und Slash-Befehle ausblenden |
| **Gesprächsvorschau** | Gespräche mit farbcodierter Formatierung anzeigen |
| **Aktivitätsdiagramm** | Prompt-Anzahl der letzten 30 Tage visualisieren |
| **Sitzung fortsetzen** | Rechtsklick, um eine Sitzung in einem neuen Terminal fortzusetzen |
| **Sitzung löschen** | Unerwünschte Sitzungen löschen |
| **Text kopieren** | Gesprächsinhalt auswählen und kopieren |
| **Auto-Aktualisierung** | Sitzungsliste alle 10 Minuten automatisch aktualisieren |

## Screenshot

![Claude Code Recall Screenshot](assets/screenshot.png)

## Voraussetzungen

- **Betriebssystem**: Windows 10/11, macOS, Linux
- **Python**: 3.9 oder höher
- **Abhängigkeiten**: tkinter (Python-Standardbibliothek)

## Installation

### Methode 1: Repository klonen

```bash
git clone https://github.com/QuatrexEX/claude-code-recall.git
cd claude-code-recall
python claude_code_recall.py
```

### Methode 2: Datei herunterladen

1. `claude_code_recall.py` herunterladen
2. Im Terminal ausführen:
   ```bash
   python claude_code_recall.py
   ```

### Windows

Doppelklicken Sie auf `claude_code_recall.bat` zum Starten.

## Verwendung

### Grundlegende Bedienung

1. Starten Sie die App, um eine Liste aller Projektsitzungen zu sehen
2. Klicken Sie auf eine Sitzung, um den Gesprächsinhalt rechts anzuzeigen
3. Verwenden Sie das Suchfeld zum Filtern nach Projektname oder Nachrichteninhalt

### Kontextmenü

**Rechtsklick auf Sitzungsliste:**
- **Sitzung fortsetzen** - Öffnet ein neues Terminal und setzt die Claude Code Sitzung fort
- **Sitzung löschen** - Löscht die Sitzungsdatei (mit Bestätigungsdialog)

**Rechtsklick auf Gesprächsbereich:**
- **Kopieren** - Ausgewählten Text in die Zwischenablage kopieren

### Filter

- **Systemsitzungen ausblenden**: Warmup- und Sub-Agent-Sitzungen verbergen
- **Slash-Befehle ausblenden**: Sitzungen mit nur Befehlen wie `/exit` verbergen

## Hinweise

- **Inoffizielles Tool**: Dieses Tool ist nicht mit Anthropic oder Claude Code verbunden
- **Löschung ist dauerhaft**: Das Löschen von Sitzungen kann nicht rückgängig gemacht werden. Bitte seien Sie vorsichtig
- **Speicherort der Sitzungsdateien**: Liest Dateien aus `~/.claude/projects/`

## Haftungsausschluss

Diese Software wird "wie besehen" ohne jegliche ausdrückliche oder stillschweigende Garantie bereitgestellt. Der Autor ist nicht verantwortlich für Schäden, die durch die Verwendung dieser Software entstehen.

## Lizenz

MIT License

Copyright (c) 2026 Quatrex

Siehe [LICENSE](LICENSE) Datei für Details.

## Autor

**Quatrex**

- X (Twitter): [@Quatrex](https://x.com/Quatrex)
- GitHub: [QuatrexEX](https://github.com/QuatrexEX)

## Mitwirken

Issues und Pull Requests sind willkommen.

1. Dieses Repository forken
2. Feature-Branch erstellen (`git checkout -b feature/amazing-feature`)
3. Änderungen committen (`git commit -m 'Add amazing feature'`)
4. Branch pushen (`git push origin feature/amazing-feature`)
5. Pull Request erstellen

---

**Made with Claude Code** 🤖
