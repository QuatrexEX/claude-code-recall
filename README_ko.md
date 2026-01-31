# Claude Code Recall

**모든 프로젝트의 Claude Code 세션 기록을 탐색하고 관리할 수 있는 GUI 도구**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Mac%20%7C%20Linux-lightgrey.svg)]()

[日本語](README.md) | [English](README_en.md) | 한국어 | [Deutsch](README_de.md) | [Français](README_fr.md) | [Português](README_pt-BR.md) | [Español](README_es.md)

## 개요

Claude Code Recall은 모든 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) 프로젝트의 세션 기록을 검색, 탐색 및 관리할 수 있는 데스크톱 애플리케이션입니다.

**공식 도구에 없는 기능을 제공합니다:**
- 전체 프로젝트 세션 검색
- 원클릭 세션 재개
- 불필요한 세션 삭제

## 기능

| 기능 | 설명 |
|------|------|
| **세션 목록** | 모든 프로젝트 세션을 시간순으로 표시 |
| **검색** | 프로젝트 이름 또는 메시지 내용으로 필터링 |
| **필터** | 시스템 세션 및 슬래시 명령어 제외 |
| **대화 미리보기** | 색상으로 구분된 대화 내용 표시 |
| **활동 그래프** | 최근 30일간 프롬프트 수를 막대 그래프로 시각화 |
| **세션 재개** | 우클릭으로 새 터미널에서 세션 재개 |
| **세션 삭제** | 불필요한 세션 삭제 |
| **텍스트 복사** | 대화 내용 선택 및 복사 |
| **자동 새로고침** | 10분마다 세션 목록 자동 갱신 |

## 스크린샷

![Claude Code Recall 스크린샷](assets/screenshot.png)

## 시스템 요구사항

- **OS**: Windows 10/11, macOS, Linux
- **Python**: 3.9 이상
- **의존성**: tkinter (Python 표준 라이브러리)

## 설치

### 방법 1: 저장소 클론

```bash
git clone https://github.com/QuatrexEX/claude-code-recall.git
cd claude-code-recall
python claude_code_recall.py
```

### 방법 2: 파일 다운로드

1. `claude_code_recall.py` 다운로드
2. 터미널에서 실행:
   ```bash
   python claude_code_recall.py
   ```

### Windows의 경우

`claude_code_recall.bat`을 더블클릭하여 실행할 수 있습니다.

## 사용법

### 기본 조작

1. 앱을 실행하면 모든 프로젝트의 세션 목록이 표시됩니다
2. 세션을 클릭하면 오른쪽에 대화 내용이 표시됩니다
3. 검색 상자에서 프로젝트 이름이나 메시지 내용으로 필터링할 수 있습니다

### 우클릭 메뉴

**세션 목록에서 우클릭:**
- **세션 재개** - 새 터미널에서 Claude Code를 실행하고 세션 재개
- **세션 삭제** - 세션 파일 삭제 (확인 대화상자 있음)

**대화 표시 영역에서 우클릭:**
- **복사** - 선택한 텍스트를 클립보드에 복사

### 필터

- **시스템 세션 제외**: Warmup, 서브 에이전트 세션 숨기기
- **슬래시 명령어 제외**: `/exit` 등의 명령어만 있는 세션 숨기기

## 주의사항

- **비공식 도구**: 이 도구는 Anthropic 및 Claude Code와 관련이 없는 비공식 도구입니다
- **삭제는 영구적입니다**: 세션 삭제는 취소할 수 없습니다. 신중하게 조작하세요
- **세션 파일 위치**: `~/.claude/projects/` 아래의 파일을 읽습니다

## 면책 조항

이 소프트웨어는 명시적이든 묵시적이든 어떠한 보증 없이 "있는 그대로" 제공됩니다. 이 소프트웨어 사용으로 인해 발생하는 어떠한 손해에 대해서도 작성자는 책임을 지지 않습니다.

## 라이선스

MIT License

Copyright (c) 2026 Quatrex

자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 작성자

**Quatrex**

- X (Twitter): [@Quatrex](https://x.com/Quatrex)
- GitHub: [QuatrexEX](https://github.com/QuatrexEX)

## 기여

Issue 및 Pull Request를 환영합니다.

1. 이 저장소를 포크
2. 기능 브랜치 생성 (`git checkout -b feature/amazing-feature`)
3. 변경 사항 커밋 (`git commit -m 'Add amazing feature'`)
4. 브랜치에 푸시 (`git push origin feature/amazing-feature`)
5. Pull Request 생성

---

**Made with Claude Code** 🤖
