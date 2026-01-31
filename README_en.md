# Claude Code Recall

**A GUI tool for browsing and managing Claude Code session history across all projects**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Mac%20%7C%20Linux-lightgrey.svg)]()

[日本語](README.md) | English | [한국어](README_ko.md) | [Deutsch](README_de.md) | [Français](README_fr.md) | [Português](README_pt-BR.md) | [Español](README_es.md)

## Overview

Claude Code Recall is a desktop application that allows you to search, browse, and manage session history across all [Claude Code](https://docs.anthropic.com/en/docs/claude-code) projects.

**Features not available in the official tool:**
- Cross-project session search
- One-click session resume
- Delete unwanted sessions

## Features

| Feature | Description |
|---------|-------------|
| **Session List** | Display all project sessions in chronological order |
| **Search** | Filter by project name or message content |
| **Filters** | Exclude system sessions and slash commands |
| **Conversation Preview** | Display conversations with color-coded formatting |
| **Activity Graph** | Visualize prompt counts over the last 30 days |
| **Resume Session** | Right-click to resume a session in a new terminal |
| **Delete Session** | Delete unwanted sessions |
| **Copy Text** | Select and copy conversation content |
| **Auto-reload** | Automatically refresh session list every 10 minutes |

## Screenshot

![Claude Code Recall Screenshot](assets/screenshot.png)

## Requirements

- **OS**: Windows 10/11, macOS, Linux
- **Python**: 3.9 or higher
- **Dependencies**: tkinter (Python standard library)

## Installation

### Method 1: Clone the repository

```bash
git clone https://github.com/QuatrexEX/claude-code-recall.git
cd claude-code-recall
python claude_code_recall.py
```

### Method 2: Download the file

1. Download `claude_code_recall.py`
2. Run in terminal:
   ```bash
   python claude_code_recall.py
   ```

### Windows

Double-click `claude_code_recall.bat` to launch.

## Usage

### Basic Operations

1. Launch the app to see a list of all project sessions
2. Click a session to view its conversation content on the right
3. Use the search box to filter by project name or message content

### Context Menu

**Right-click on session list:**
- **Resume Session** - Open a new terminal and resume the Claude Code session
- **Delete Session** - Delete the session file (with confirmation dialog)

**Right-click on conversation area:**
- **Copy** - Copy selected text to clipboard

### Filters

- **Exclude system sessions**: Hide Warmup and sub-agent sessions
- **Exclude slash commands**: Hide sessions with only commands like `/exit`

## Notes

- **Unofficial tool**: This tool is not affiliated with Anthropic or Claude Code
- **Deletion is permanent**: Session deletion cannot be undone. Please be careful
- **Session file location**: Reads files from `~/.claude/projects/`

## Disclaimer

This software is provided "as is" without warranty of any kind, express or implied. The author is not responsible for any damages arising from the use of this software.

## License

MIT License

Copyright (c) 2026 Quatrex

See [LICENSE](LICENSE) file for details.

## Author

**Quatrex**

- X (Twitter): [@Quatrex](https://x.com/Quatrex)
- GitHub: [QuatrexEX](https://github.com/QuatrexEX)

## Contributing

Issues and Pull Requests are welcome.

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Create a Pull Request

---

**Made with Claude Code** 🤖
