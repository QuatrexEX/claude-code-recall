# Claude Code Recall

**Un outil GUI pour parcourir et gérer l'historique des sessions Claude Code sur tous les projets**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Mac%20%7C%20Linux-lightgrey.svg)]()

[日本語](README.md) | [English](README_en.md) | [한국어](README_ko.md) | [Deutsch](README_de.md) | Français | [Português](README_pt-BR.md) | [Español](README_es.md)

## Aperçu

Claude Code Recall est une application de bureau qui vous permet de rechercher, parcourir et gérer l'historique des sessions de tous les projets [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

**Fonctionnalités non disponibles dans l'outil officiel :**
- Recherche de sessions multi-projets
- Reprise de session en un clic
- Suppression des sessions indésirables

## Fonctionnalités

| Fonctionnalité | Description |
|----------------|-------------|
| **Liste des sessions** | Afficher toutes les sessions de projets par ordre chronologique |
| **Recherche** | Filtrer par nom de projet ou contenu du message |
| **Filtres** | Exclure les sessions système et les commandes slash |
| **Aperçu des conversations** | Afficher les conversations avec un formatage coloré |
| **Graphique d'activité** | Visualiser le nombre de prompts sur les 30 derniers jours |
| **Reprendre une session** | Clic droit pour reprendre une session dans un nouveau terminal |
| **Supprimer une session** | Supprimer les sessions indésirables |
| **Copier le texte** | Sélectionner et copier le contenu des conversations |
| **Actualisation auto** | Actualiser automatiquement la liste des sessions toutes les 10 minutes |

## Capture d'écran

![Capture d'écran Claude Code Recall](assets/screenshot.png)

## Configuration requise

- **OS** : Windows 10/11, macOS, Linux
- **Python** : 3.9 ou supérieur
- **Dépendances** : tkinter (bibliothèque standard Python)

## Installation

### Méthode 1 : Cloner le dépôt

```bash
git clone https://github.com/QuatrexEX/claude-code-recall.git
cd claude-code-recall
python claude_code_recall.py
```

### Méthode 2 : Télécharger le fichier

1. Téléchargez `claude_code_recall.py`
2. Exécutez dans le terminal :
   ```bash
   python claude_code_recall.py
   ```

### Windows

Double-cliquez sur `claude_code_recall.bat` pour lancer.

## Utilisation

### Opérations de base

1. Lancez l'application pour voir la liste de toutes les sessions de projets
2. Cliquez sur une session pour afficher son contenu à droite
3. Utilisez la barre de recherche pour filtrer par nom de projet ou contenu du message

### Menu contextuel

**Clic droit sur la liste des sessions :**
- **Reprendre la session** - Ouvrir un nouveau terminal et reprendre la session Claude Code
- **Supprimer la session** - Supprimer le fichier de session (avec dialogue de confirmation)

**Clic droit sur la zone de conversation :**
- **Copier** - Copier le texte sélectionné dans le presse-papiers

### Filtres

- **Exclure les sessions système** : Masquer les sessions Warmup et sous-agent
- **Exclure les commandes slash** : Masquer les sessions contenant uniquement des commandes comme `/exit`

## Remarques

- **Outil non officiel** : Cet outil n'est pas affilié à Anthropic ou Claude Code
- **La suppression est permanente** : La suppression de session ne peut pas être annulée. Soyez prudent
- **Emplacement des fichiers de session** : Lit les fichiers depuis `~/.claude/projects/`

## Avertissement

Ce logiciel est fourni "tel quel" sans aucune garantie, expresse ou implicite. L'auteur n'est pas responsable des dommages résultant de l'utilisation de ce logiciel.

## Licence

MIT License

Copyright (c) 2026 Quatrex

Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## Auteur

**Quatrex**

- X (Twitter) : [@Quatrex](https://x.com/Quatrex)
- GitHub : [QuatrexEX](https://github.com/QuatrexEX)

## Contribution

Les Issues et Pull Requests sont les bienvenues.

1. Forkez ce dépôt
2. Créez une branche de fonctionnalité (`git checkout -b feature/amazing-feature`)
3. Committez vos modifications (`git commit -m 'Add amazing feature'`)
4. Poussez vers la branche (`git push origin feature/amazing-feature`)
5. Créez une Pull Request

---

**Made with Claude Code** 🤖
