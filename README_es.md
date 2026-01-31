# Claude Code Recall

**Una herramienta GUI para explorar y gestionar el historial de sesiones de Claude Code en todos los proyectos**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Mac%20%7C%20Linux-lightgrey.svg)]()

[日本語](README.md) | [English](README_en.md) | [한국어](README_ko.md) | [Deutsch](README_de.md) | [Français](README_fr.md) | [Português](README_pt-BR.md) | Español

## Descripción General

Claude Code Recall es una aplicación de escritorio que te permite buscar, explorar y gestionar el historial de sesiones de todos los proyectos de [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

**Funciones no disponibles en la herramienta oficial:**
- Búsqueda de sesiones entre proyectos
- Reanudar sesión con un clic
- Eliminar sesiones no deseadas

## Características

| Característica | Descripción |
|----------------|-------------|
| **Lista de Sesiones** | Mostrar todas las sesiones de proyectos en orden cronológico |
| **Búsqueda** | Filtrar por nombre de proyecto o contenido del mensaje |
| **Filtros** | Excluir sesiones del sistema y comandos slash |
| **Vista Previa de Conversaciones** | Mostrar conversaciones con formato de colores |
| **Gráfico de Actividad** | Visualizar el conteo de prompts en los últimos 30 días |
| **Reanudar Sesión** | Clic derecho para reanudar una sesión en una nueva terminal |
| **Eliminar Sesión** | Eliminar sesiones no deseadas |
| **Copiar Texto** | Seleccionar y copiar contenido de la conversación |
| **Auto-actualización** | Actualizar automáticamente la lista de sesiones cada 10 minutos |

## Captura de Pantalla

![Captura de pantalla de Claude Code Recall](assets/screenshot.png)

## Requisitos

- **SO**: Windows 10/11, macOS, Linux
- **Python**: 3.9 o superior
- **Dependencias**: tkinter (biblioteca estándar de Python)

## Instalación

### Método 1: Clonar el repositorio

```bash
git clone https://github.com/QuatrexEX/claude-code-recall.git
cd claude-code-recall
python claude_code_recall.py
```

### Método 2: Descargar el archivo

1. Descarga `claude_code_recall.py`
2. Ejecuta en la terminal:
   ```bash
   python claude_code_recall.py
   ```

### Windows

Haz doble clic en `claude_code_recall.bat` para iniciar.

## Uso

### Operaciones Básicas

1. Inicia la aplicación para ver una lista de todas las sesiones de proyectos
2. Haz clic en una sesión para ver el contenido de la conversación a la derecha
3. Usa el cuadro de búsqueda para filtrar por nombre de proyecto o contenido del mensaje

### Menú Contextual

**Clic derecho en la lista de sesiones:**
- **Reanudar Sesión** - Abrir una nueva terminal y reanudar la sesión de Claude Code
- **Eliminar Sesión** - Eliminar el archivo de sesión (con diálogo de confirmación)

**Clic derecho en el área de conversación:**
- **Copiar** - Copiar el texto seleccionado al portapapeles

### Filtros

- **Excluir sesiones del sistema**: Ocultar sesiones de Warmup y sub-agente
- **Excluir comandos slash**: Ocultar sesiones con solo comandos como `/exit`

## Notas

- **Herramienta no oficial**: Esta herramienta no está afiliada con Anthropic o Claude Code
- **La eliminación es permanente**: La eliminación de sesiones no se puede deshacer. Por favor, ten cuidado
- **Ubicación de archivos de sesión**: Lee archivos de `~/.claude/projects/`

## Descargo de Responsabilidad

Este software se proporciona "tal cual" sin garantía de ningún tipo, expresa o implícita. El autor no es responsable de ningún daño que surja del uso de este software.

## Licencia

MIT License

Copyright (c) 2026 Quatrex

Ver archivo [LICENSE](LICENSE) para más detalles.

## Autor

**Quatrex**

- X (Twitter): [@Quatrex](https://x.com/Quatrex)
- GitHub: [QuatrexEX](https://github.com/QuatrexEX)

## Contribuir

Los Issues y Pull Requests son bienvenidos.

1. Haz fork de este repositorio
2. Crea una rama de característica (`git checkout -b feature/amazing-feature`)
3. Haz commit de tus cambios (`git commit -m 'Add amazing feature'`)
4. Haz push a la rama (`git push origin feature/amazing-feature`)
5. Crea un Pull Request

---

**Made with Claude Code** 🤖
