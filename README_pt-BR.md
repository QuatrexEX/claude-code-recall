# Claude Code Recall

**Uma ferramenta GUI para navegar e gerenciar o histórico de sessões do Claude Code em todos os projetos**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Mac%20%7C%20Linux-lightgrey.svg)]()

[日本語](README.md) | [English](README_en.md) | [한국어](README_ko.md) | [Deutsch](README_de.md) | [Français](README_fr.md) | Português | [Español](README_es.md)

## Visão Geral

Claude Code Recall é um aplicativo de desktop que permite pesquisar, navegar e gerenciar o histórico de sessões de todos os projetos [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

**Recursos não disponíveis na ferramenta oficial:**
- Pesquisa de sessões entre projetos
- Retomar sessão com um clique
- Excluir sessões indesejadas

## Recursos

| Recurso | Descrição |
|---------|-----------|
| **Lista de Sessões** | Exibir todas as sessões de projetos em ordem cronológica |
| **Pesquisa** | Filtrar por nome do projeto ou conteúdo da mensagem |
| **Filtros** | Excluir sessões do sistema e comandos slash |
| **Visualização de Conversas** | Exibir conversas com formatação colorida |
| **Gráfico de Atividade** | Visualizar contagem de prompts nos últimos 30 dias |
| **Retomar Sessão** | Clique direito para retomar uma sessão em um novo terminal |
| **Excluir Sessão** | Excluir sessões indesejadas |
| **Copiar Texto** | Selecionar e copiar conteúdo da conversa |
| **Auto-atualização** | Atualizar automaticamente a lista de sessões a cada 10 minutos |

## Captura de Tela

![Captura de tela do Claude Code Recall](assets/screenshot.png)

## Requisitos

- **SO**: Windows 10/11, macOS, Linux
- **Python**: 3.9 ou superior
- **Dependências**: tkinter (biblioteca padrão do Python)

## Instalação

### Método 1: Clonar o repositório

```bash
git clone https://github.com/QuatrexEX/claude-code-recall.git
cd claude-code-recall
python claude_code_recall.py
```

### Método 2: Baixar o arquivo

1. Baixe `claude_code_recall.py`
2. Execute no terminal:
   ```bash
   python claude_code_recall.py
   ```

### Windows

Clique duas vezes em `claude_code_recall.bat` para iniciar.

## Uso

### Operações Básicas

1. Inicie o aplicativo para ver uma lista de todas as sessões de projetos
2. Clique em uma sessão para visualizar o conteúdo da conversa à direita
3. Use a caixa de pesquisa para filtrar por nome do projeto ou conteúdo da mensagem

### Menu de Contexto

**Clique direito na lista de sessões:**
- **Retomar Sessão** - Abrir um novo terminal e retomar a sessão do Claude Code
- **Excluir Sessão** - Excluir o arquivo de sessão (com diálogo de confirmação)

**Clique direito na área de conversa:**
- **Copiar** - Copiar texto selecionado para a área de transferência

### Filtros

- **Excluir sessões do sistema**: Ocultar sessões de Warmup e sub-agente
- **Excluir comandos slash**: Ocultar sessões com apenas comandos como `/exit`

## Observações

- **Ferramenta não oficial**: Esta ferramenta não é afiliada à Anthropic ou ao Claude Code
- **A exclusão é permanente**: A exclusão de sessão não pode ser desfeita. Por favor, tenha cuidado
- **Localização dos arquivos de sessão**: Lê arquivos de `~/.claude/projects/`

## Aviso Legal

Este software é fornecido "como está", sem garantia de qualquer tipo, expressa ou implícita. O autor não é responsável por quaisquer danos decorrentes do uso deste software.

## Licença

MIT License

Copyright (c) 2026 Quatrex

Veja o arquivo [LICENSE](LICENSE) para detalhes.

## Autor

**Quatrex**

- X (Twitter): [@Quatrex](https://x.com/Quatrex)
- GitHub: [QuatrexEX](https://github.com/QuatrexEX)

## Contribuição

Issues e Pull Requests são bem-vindos.

1. Faça um fork deste repositório
2. Crie uma branch de recurso (`git checkout -b feature/amazing-feature`)
3. Faça commit das suas alterações (`git commit -m 'Add amazing feature'`)
4. Faça push para a branch (`git push origin feature/amazing-feature`)
5. Crie um Pull Request

---

**Made with Claude Code** 🤖
