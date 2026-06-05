#!/usr/bin/env python3
"""
Claude Code Recall - セッション履歴ビューア
全プロジェクトのClaude Codeセッション履歴を横断的に閲覧・管理できるGUIツール

Copyright (c) 2026
License: MIT
"""

from __future__ import annotations

import atexit
import json
import locale
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import tkinter as tk
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any, Optional, TypedDict

# ============================================================================
# 定数
# ============================================================================

APP_NAME = "Claude Code Recall"
APP_VERSION = "1.2.0"
DEFAULT_WINDOW_SIZE = "1200x800"

# Colors
COLOR_TEXT_MUTED = "#666666"
COLOR_TEXT_DARK = "#333333"
COLOR_BAR_NORMAL = "#4a90d9"
COLOR_BAR_HIGHLIGHT = "#ff6600"
COLOR_BAR_ZERO = "#e0e0e0"
COLOR_BG_LIGHT = "#f8f8f8"
COLOR_USER = "#0066cc"
COLOR_ASSISTANT = "#009933"
COLOR_SEPARATOR = "#cccccc"

# Fonts
FONT_SMALL = ("", 8)
FONT_XSMALL = ("", 7)
FONT_MEDIUM = ("", 10, "bold")
FONT_MONO = ("Consolas", 10)
FONT_MONO_BOLD = ("Consolas", 10, "bold")
FONT_MONO_SMALL = ("Consolas", 9)

# Timing
AUTO_RELOAD_INTERVAL_MS = 600_000  # 10 minutes
SEARCH_DEBOUNCE_MS = 200

# Chart layout
CHART_DAYS = 30
CHART_HEIGHT_PX = 120
CHART_MARGIN_LEFT = 30
CHART_MARGIN_RIGHT = 10
CHART_MARGIN_TOP = 10
CHART_MARGIN_BOTTOM = 25
CHART_X_LABEL_TARGETS = 5
CHART_BAR_MIN_WIDTH = 2
CHART_BAR_GAP = 1

# Display
FIRST_MESSAGE_DISPLAY_LENGTH = 50
SHORT_PROJECT_DEPTH = 2
SEPARATOR_LENGTH = 80

# Limits
MAX_SESSION_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

# Validation
SESSION_ID_PATTERN = re.compile(r"^[0-9a-fA-F-]{36}$")

# i18n
I18N_DIR = Path(__file__).resolve().parent / "i18n"
SUPPORTED_LANGUAGES = ("ja", "en", "ko", "de", "fr", "pt-BR", "es")
DEFAULT_LANGUAGE = "en"
_current_language = DEFAULT_LANGUAGE

# OS言語コード -> アプリ言語コード
_LANGUAGE_MAP = {
    "ja": "ja",
    "en": "en",
    "ko": "ko",
    "de": "de",
    "fr": "fr",
    "pt": "pt-BR",
    "es": "es",
}


# ============================================================================
# 型定義
# ============================================================================

class SessionMessage(TypedDict):
    type: str
    content: str
    timestamp: Any
    is_meta: bool
    is_slash_command: bool


class SessionInfo(TypedDict):
    file_path: Path
    project_name: str
    session_id: str
    timestamp: datetime
    first_message: str
    messages: list[SessionMessage]
    is_human_session: bool
    has_normal_messages: bool


# ============================================================================
# i18n
# ============================================================================

@lru_cache(maxsize=None)
def _load_translation(lang: str) -> dict[str, str]:
    """指定言語のJSON翻訳ファイルを読み込む（キャッシュあり）。"""
    path = I18N_DIR / f"{lang}.json"
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def get_text(key: str, **kwargs: Any) -> str:
    """翻訳テキストを取得する。

    現在言語に存在しないキーはデフォルト言語にフォールバックし、
    それもなければキー自体を返す。
    """
    text = _load_translation(_current_language).get(key)
    if text is None:
        text = _load_translation(DEFAULT_LANGUAGE).get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text


def set_language(lang: str) -> None:
    """言語を設定する。サポート対象外なら無視。"""
    global _current_language
    if lang in SUPPORTED_LANGUAGES:
        _current_language = lang


def _get_windows_language() -> Optional[str]:
    """Windows API でユーザー UI 言語を取得する。"""
    if sys.platform != "win32":
        return None
    try:
        import ctypes

        WINDOWS_LANG_MAP = {
            0x11: "ja",
            0x09: "en",
            0x12: "ko",
            0x07: "de",
            0x0C: "fr",
            0x16: "pt-BR",
            0x0A: "es",
        }
        kernel32 = ctypes.windll.kernel32
        lang_id = kernel32.GetUserDefaultUILanguage()
        primary_lang = lang_id & 0x3FF
        return WINDOWS_LANG_MAP.get(primary_lang)
    except Exception:
        return None


def detect_system_language() -> str:
    """システム言語を検出してアプリでサポートする言語コードを返す。

    Note:
        副作用のあるlocale.setlocale()は呼ばない。getlocale()のみ使用。
    """
    if sys.platform == "win32":
        win_lang = _get_windows_language()
        if win_lang:
            return win_lang

    system_locale: Optional[str] = None
    try:
        for env_var in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
            env_value = os.environ.get(env_var)
            if env_value and env_value not in ("C", "POSIX"):
                system_locale = env_value
                break

        if not system_locale:
            loc = locale.getlocale()
            if loc and loc[0]:
                system_locale = loc[0]
    except Exception:
        pass

    if system_locale:
        system_locale = system_locale.split(".")[0]
        if system_locale.lower().startswith("pt_br"):
            return "pt-BR"
        lang_code = system_locale.split("_")[0].lower()
        if lang_code in _LANGUAGE_MAP:
            return _LANGUAGE_MAP[lang_code]

    return DEFAULT_LANGUAGE


# ============================================================================
# タイムゾーン（OSのタイムゾーン設定を起動時にキャプチャ）
# ============================================================================
#
# datetime.astimezone() は引数なしでもOSのタイムゾーンを使うが、ロケール経由で
# Pythonが TZ を誤推論するリスクを避けるため、起動時にOSのタイムゾーンを取得して
# 固定化する。これにより表示言語の変更とタイムゾーンは完全に独立する。

def _get_local_timezone() -> Optional[Any]:
    """OSのタイムゾーンを取得する（表示言語とは無関係）。"""
    try:
        return datetime.now(timezone.utc).astimezone().tzinfo
    except Exception:
        return None


LOCAL_TZ = _get_local_timezone()


def now_local() -> datetime:
    """OSタイムゾーンでの現在時刻（naive）を返す。"""
    if LOCAL_TZ is not None:
        return datetime.now(LOCAL_TZ).replace(tzinfo=None)
    return datetime.now()


# ============================================================================
# ユーティリティ関数
# ============================================================================

def get_claude_projects_dir() -> Path:
    """Claude Codeのプロジェクトディレクトリ ~/.claude/projects を返す。"""
    if sys.platform == "win32":
        home_str = os.environ.get("USERPROFILE") or os.environ.get("HOME")
        home = Path(home_str) if home_str else Path.home()
    else:
        home = Path.home()
    return home / ".claude" / "projects"


def is_safe_path(base_path: Path, target_path: Path) -> bool:
    """target_path が base_path 配下にあるか検証（パストラバーサル防止）。"""
    try:
        return target_path.resolve().is_relative_to(base_path.resolve())
    except (OSError, ValueError):
        return False


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """テキストを max_length で切り詰める。"""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def get_short_project_name(full_path: str, depth: int = SHORT_PROJECT_DEPTH) -> str:
    """プロジェクトパスを末端 depth 階層に短縮する。"""
    normalized = full_path.replace("/", "\\")
    parts = normalized.split("\\")
    if len(parts) >= depth:
        return "\\".join(parts[-depth:])
    return parts[-1] if parts else full_path


def to_local_datetime(ts: Any) -> Optional[datetime]:
    """ISO文字列またはUnixミリ秒を、OSタイムゾーンのnaive datetimeに変換。

    LOCAL_TZ (起動時にキャプチャしたOSのタイムゾーン) を使うため、
    表示言語やロケール変更の影響を受けない。
    """
    if ts is None:
        return None
    try:
        if isinstance(ts, str):
            dt_utc = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        elif isinstance(ts, (int, float)):
            dt_utc = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
        else:
            return None
        if LOCAL_TZ is not None:
            return dt_utc.astimezone(LOCAL_TZ).replace(tzinfo=None)
        return dt_utc.astimezone().replace(tzinfo=None)
    except (ValueError, OSError):
        return None


# ============================================================================
# メインアプリケーション
# ============================================================================

class ClaudeCodeRecall:
    """Claude Code Recallメインアプリケーションクラス。"""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(get_text("app_title"))
        self.root.geometry(DEFAULT_WINDOW_SIZE)

        self.projects_dir = get_claude_projects_dir()

        self.sessions: list[SessionInfo] = []
        self.current_session: Optional[SessionInfo] = None
        self._cached_filtered_sessions: list[SessionInfo] = []
        self._cached_chart_counts: dict[str, int] = {}

        self.filter_system_sessions = tk.BooleanVar(value=True)
        self.filter_slash_commands = tk.BooleanVar(value=True)

        self.chart_canvas: Optional[tk.Canvas] = None
        self.chart_bars: dict[str, int] = {}
        self.selected_date: Optional[str] = None

        self.last_updated: Optional[datetime] = None

        logging.basicConfig(level=logging.WARNING)
        self.logger = logging.getLogger(__name__)

        self._temp_files: list[str] = []
        atexit.register(self._cleanup_temp_files)

        self._auto_reload_id: Optional[str] = None
        self._search_after_id: Optional[str] = None

        self._setup_ui()
        self._setup_text_context_menu()

        self._load_all_sessions()
        self._schedule_auto_reload()

    # ------------------------------------------------------------------
    # UI 構築
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        self.paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._setup_left_panel()
        self._setup_right_panel()

    def _setup_left_panel(self) -> None:
        left_frame = ttk.Frame(self.paned)
        self.paned.add(left_frame, weight=1)

        top_frame = ttk.Frame(left_frame)
        top_frame.pack(fill=tk.BOTH, expand=True)

        self._setup_search_bar(top_frame)
        self._setup_filter_bar(top_frame)
        self._setup_status_bar(top_frame)
        self._setup_session_tree(top_frame)
        self._setup_chart_panel(left_frame)

    def _setup_search_bar(self, parent: ttk.Frame) -> None:
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(search_frame, text=get_text("search")).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._on_search_change())
        ttk.Entry(search_frame, textvariable=self.search_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0)
        )

    def _setup_filter_bar(self, parent: ttk.Frame) -> None:
        filter_frame = ttk.Frame(parent)
        filter_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Checkbutton(
            filter_frame,
            text=get_text("filter_system"),
            variable=self.filter_system_sessions,
            command=self._filter_sessions,
        ).pack(side=tk.LEFT)
        ttk.Checkbutton(
            filter_frame,
            text=get_text("filter_slash"),
            variable=self.filter_slash_commands,
            command=self._on_slash_filter_change,
        ).pack(side=tk.LEFT, padx=(10, 0))

    def _setup_status_bar(self, parent: ttk.Frame) -> None:
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X)
        self.count_label = ttk.Label(status_frame, text="")
        self.count_label.pack(side=tk.LEFT)
        self.updated_label = ttk.Label(
            status_frame, text="", foreground=COLOR_TEXT_MUTED
        )
        self.updated_label.pack(side=tk.RIGHT)

    def _setup_session_tree(self, parent: ttk.Frame) -> None:
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("project", "date", "first_message")
        self.session_tree = ttk.Treeview(
            list_frame, columns=columns, show="headings", selectmode="browse"
        )
        self.session_tree.heading("project", text=get_text("col_project"))
        self.session_tree.heading("date", text=get_text("col_date"))
        self.session_tree.heading("first_message", text=get_text("col_first_message"))
        self.session_tree.column("project", width=150, minwidth=100)
        self.session_tree.column("date", width=130, minwidth=100)
        self.session_tree.column("first_message", width=200, minwidth=100)

        scrollbar = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self.session_tree.yview
        )
        self.session_tree.configure(yscrollcommand=scrollbar.set)
        self.session_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.session_tree.bind("<<TreeviewSelect>>", self._on_session_select)

        self.session_context_menu = tk.Menu(self.root, tearoff=0)
        self.session_context_menu.add_command(
            label=get_text("menu_resume"), command=self._resume_selected_session
        )
        self.session_context_menu.add_separator()
        self.session_context_menu.add_command(
            label=get_text("menu_delete"), command=self._delete_selected_session
        )
        self.session_tree.bind("<Button-3>", self._on_session_right_click)

    def _setup_chart_panel(self, parent: ttk.Frame) -> None:
        chart_frame = ttk.LabelFrame(parent, text=get_text("chart_title"))
        chart_frame.pack(fill=tk.BOTH, pady=(5, 0), ipady=5)
        self.chart_canvas = tk.Canvas(
            chart_frame,
            height=CHART_HEIGHT_PX,
            bg=COLOR_BG_LIGHT,
            highlightthickness=0,
        )
        self.chart_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.chart_canvas.bind("<Configure>", lambda e: self._draw_chart())

    def _setup_right_panel(self) -> None:
        right_frame = ttk.Frame(self.paned)
        self.paned.add(right_frame, weight=2)

        self.session_info_label = ttk.Label(
            right_frame, text=get_text("select_session"), font=FONT_MEDIUM
        )
        self.session_info_label.pack(anchor=tk.W, pady=(0, 5))

        text_frame = ttk.Frame(right_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.conversation_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=FONT_MONO,
            state=tk.DISABLED,
            padx=10,
            pady=10,
        )
        text_scrollbar = ttk.Scrollbar(
            text_frame, orient=tk.VERTICAL, command=self.conversation_text.yview
        )
        self.conversation_text.configure(yscrollcommand=text_scrollbar.set)
        self.conversation_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.conversation_text.tag_configure(
            "user", foreground=COLOR_USER, font=FONT_MONO_BOLD
        )
        self.conversation_text.tag_configure("assistant", foreground=COLOR_ASSISTANT)
        self.conversation_text.tag_configure(
            "timestamp", foreground=COLOR_TEXT_MUTED, font=FONT_MONO_SMALL
        )
        self.conversation_text.tag_configure("separator", foreground=COLOR_SEPARATOR)

    def _setup_text_context_menu(self) -> None:
        self.text_context_menu = tk.Menu(self.root, tearoff=0)
        self.text_context_menu.add_command(
            label=get_text("menu_copy"), command=self._copy_selected_text
        )
        self.conversation_text.bind("<Button-3>", self._on_text_right_click)

    # ------------------------------------------------------------------
    # 検索デバウンス
    # ------------------------------------------------------------------

    def _on_search_change(self) -> None:
        if self._search_after_id is not None:
            try:
                self.root.after_cancel(self._search_after_id)
            except tk.TclError:
                pass
        self._search_after_id = self.root.after(
            SEARCH_DEBOUNCE_MS, self._filter_sessions
        )

    # ------------------------------------------------------------------
    # 自動再読み込み
    # ------------------------------------------------------------------

    def _schedule_auto_reload(self) -> None:
        self._auto_reload_id = self.root.after(
            AUTO_RELOAD_INTERVAL_MS, self._auto_reload
        )

    def _auto_reload(self) -> None:
        try:
            selected_session_id: Optional[str] = None
            if self.session_tree.selection() and self.current_session:
                selected_session_id = self.current_session.get("session_id")

            self._load_all_sessions()

            if selected_session_id:
                for idx, session in enumerate(self._cached_filtered_sessions):
                    if session.get("session_id") == selected_session_id:
                        iid = str(idx)
                        self.session_tree.selection_set(iid)
                        self.session_tree.see(iid)
                        break

            self._schedule_auto_reload()
        except tk.TclError:
            # ウィンドウ破棄済み
            pass

    # ------------------------------------------------------------------
    # セッション読み込み
    # ------------------------------------------------------------------

    def _load_all_sessions(self) -> None:
        self.sessions = []
        self.last_updated = now_local()

        if not self.projects_dir.exists():
            self._filter_sessions()
            return

        for project_dir in self.projects_dir.iterdir():
            try:
                if not project_dir.is_dir():
                    continue

                project_name_fallback = project_dir.name.replace(
                    "--", ":/", 1
                ).replace("-", "/")

                for session_file in project_dir.glob("*.jsonl"):
                    if not session_file.is_file():
                        continue
                    session_info = self._parse_session_file(
                        session_file, project_name_fallback
                    )
                    if session_info:
                        self.sessions.append(session_info)
            except (OSError, PermissionError) as e:
                self.logger.warning(f"Skipping directory {project_dir}: {e}")

        self.sessions.sort(key=lambda x: x["timestamp"], reverse=True)
        self._filter_sessions()

    def _parse_session_file(
        self, file_path: Path, project_name_fallback: str
    ) -> Optional[SessionInfo]:
        try:
            if file_path.stat().st_size > MAX_SESSION_FILE_SIZE:
                self.logger.warning(f"Skipping large session file: {file_path}")
                return None
        except OSError:
            return None

        try:
            messages, first_user_message, latest_timestamp, actual_cwd = (
                self._read_session_jsonl(file_path)
            )
        except Exception as e:
            self.logger.warning(f"Error parsing {file_path}: {e}")
            return None

        if not messages:
            return None

        is_human_session = self._is_human_session(file_path, first_user_message)
        has_normal_messages = any(
            m["type"] == "user" and not m["is_slash_command"] for m in messages
        )

        return {
            "file_path": file_path,
            "project_name": actual_cwd or project_name_fallback,
            "session_id": file_path.stem,
            "timestamp": latest_timestamp or datetime.min,
            "first_message": first_user_message or get_text("slash_command_only"),
            "messages": messages,
            "is_human_session": is_human_session,
            "has_normal_messages": has_normal_messages,
        }

    def _read_session_jsonl(
        self, file_path: Path
    ) -> tuple[list[SessionMessage], str, Optional[datetime], Optional[str]]:
        """JSONLファイルを読み込み (messages, first_user_message, latest_ts, cwd) を返す。"""
        messages: list[SessionMessage] = []
        first_user_message = ""
        latest_timestamp: Optional[datetime] = None
        actual_cwd: Optional[str] = None

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if actual_cwd is None and "cwd" in data:
                    actual_cwd = data["cwd"]

                latest_timestamp = self._update_latest_timestamp(
                    data.get("timestamp"), latest_timestamp
                )

                msg_info = self._extract_message(data)
                if msg_info:
                    messages.append(msg_info)
                    if (
                        msg_info["type"] == "user"
                        and not first_user_message
                        and not msg_info["is_slash_command"]
                    ):
                        first_user_message = msg_info["content"].replace("\n", " ")

        return messages, first_user_message, latest_timestamp, actual_cwd

    @staticmethod
    def _update_latest_timestamp(
        ts: Any, current_latest: Optional[datetime]
    ) -> Optional[datetime]:
        dt = to_local_datetime(ts)
        if dt is not None and (current_latest is None or dt > current_latest):
            return dt
        return current_latest

    @staticmethod
    def _extract_message(data: dict[str, Any]) -> Optional[SessionMessage]:
        msg_type = data.get("type")
        if msg_type not in ("user", "assistant"):
            return None

        message = data.get("message", {})
        content = ""
        is_meta = data.get("isMeta", False)

        if isinstance(message, dict):
            raw_content = message.get("content", "")
            if isinstance(raw_content, str):
                content = raw_content
            elif isinstance(raw_content, list):
                for item in raw_content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        content += item.get("text", "")
                    elif isinstance(item, str):
                        content += item

        if not content:
            return None

        stripped = content.strip()
        is_slash_command = (
            is_meta
            or stripped.startswith("<command-name>")
            or stripped.startswith("<local-command-stdout>")
            or stripped.startswith("<local-command-caveat>")
        )

        return {
            "type": msg_type,
            "content": content,
            "timestamp": data.get("timestamp"),
            "is_meta": is_meta,
            "is_slash_command": is_slash_command,
        }

    @staticmethod
    def _is_human_session(file_path: Path, first_message: str) -> bool:
        if file_path.stem.startswith("agent-"):
            return False
        if first_message.strip().lower() == "warmup":
            return False
        return True

    # ------------------------------------------------------------------
    # フィルター・キャッシュ
    # ------------------------------------------------------------------

    def _filter_sessions(self) -> None:
        """フィルタ結果とチャート集計を再計算してUI更新。"""
        self._cached_filtered_sessions = self._compute_filtered_sessions()
        self._cached_chart_counts = self._compute_prompt_counts_by_date()
        self._populate_session_list()
        self._draw_chart()

    def _compute_filtered_sessions(self) -> list[SessionInfo]:
        query = self.search_var.get().lower()
        exclude_system = self.filter_system_sessions.get()
        exclude_slash = self.filter_slash_commands.get()

        filtered = self.sessions
        if exclude_system:
            filtered = [s for s in filtered if s.get("is_human_session", True)]
        if exclude_slash:
            filtered = [s for s in filtered if s.get("has_normal_messages", True)]
        if query:
            filtered = [
                s
                for s in filtered
                if query in s["project_name"].lower()
                or query in s["first_message"].lower()
            ]
        return filtered

    def _compute_prompt_counts_by_date(self) -> dict[str, int]:
        """過去 CHART_DAYS 日間のユーザープロンプト数を日別集計。"""
        counts: dict[str, int] = {}
        today = now_local().date()
        exclude_slash = self.filter_slash_commands.get()

        for i in range(CHART_DAYS):
            date = today - timedelta(days=CHART_DAYS - 1 - i)
            counts[date.strftime("%Y-%m-%d")] = 0

        for session in self._cached_filtered_sessions:
            for msg in session.get("messages", []):
                if msg["type"] != "user":
                    continue
                if exclude_slash and msg["is_slash_command"]:
                    continue
                msg_date = to_local_datetime(msg["timestamp"])
                if msg_date:
                    date_str = msg_date.strftime("%Y-%m-%d")
                    if date_str in counts:
                        counts[date_str] += 1
        return counts

    def _populate_session_list(self) -> None:
        self.session_tree.delete(*self.session_tree.get_children())

        for idx, session in enumerate(self._cached_filtered_sessions):
            project = get_short_project_name(session["project_name"])
            if session["timestamp"] != datetime.min:
                date_str = session["timestamp"].strftime("%Y-%m-%d %H:%M")
            else:
                date_str = "-"
            first_msg = truncate_text(
                session["first_message"], FIRST_MESSAGE_DISPLAY_LENGTH
            )
            self.session_tree.insert(
                "", tk.END, iid=str(idx), values=(project, date_str, first_msg)
            )

        self.count_label.config(
            text=get_text(
                "session_count",
                displayed=len(self._cached_filtered_sessions),
                total=len(self.sessions),
            )
        )

        if self.last_updated:
            time_str = self.last_updated.strftime("%Y-%m-%d %H:%M")
            self.updated_label.config(text=get_text("last_updated", time=time_str))

    def _on_slash_filter_change(self) -> None:
        self._filter_sessions()
        if self.current_session:
            self._display_conversation(self.current_session)

    def _get_selected_session(self) -> Optional[SessionInfo]:
        selection = self.session_tree.selection()
        if not selection:
            return None
        try:
            idx = int(selection[0])
            if 0 <= idx < len(self._cached_filtered_sessions):
                return self._cached_filtered_sessions[idx]
        except (ValueError, IndexError):
            pass
        return None

    def _on_session_select(self, event: tk.Event) -> None:
        session = self._get_selected_session()
        if session:
            self._display_conversation(session)
            self._update_chart_highlight(session)

    def _on_session_right_click(self, event: tk.Event) -> None:
        item = self.session_tree.identify_row(event.y)
        if item:
            self.session_tree.selection_set(item)
            self.session_context_menu.post(event.x_root, event.y_root)

    # ------------------------------------------------------------------
    # 会話表示
    # ------------------------------------------------------------------

    def _display_conversation(self, session: SessionInfo) -> None:
        self.current_session = session
        self.session_info_label.config(
            text=get_text(
                "project_label",
                path=session["project_name"],
                session_id=session["session_id"],
            )
        )

        self.conversation_text.config(state=tk.NORMAL)
        try:
            self.conversation_text.delete(1.0, tk.END)
            exclude_slash = self.filter_slash_commands.get()
            for msg in session["messages"]:
                if exclude_slash and msg["is_slash_command"]:
                    continue
                self._render_message(msg)
        finally:
            self.conversation_text.config(state=tk.DISABLED)
        self.conversation_text.see(1.0)

    def _render_message(self, msg: SessionMessage) -> None:
        msg_type = msg["type"]
        content = msg["content"]
        ts_str = self._format_timestamp(msg.get("timestamp"))

        label_key = "user_label" if msg_type == "user" else "assistant_label"
        tag = "user" if msg_type == "user" else "assistant"
        self.conversation_text.insert(tk.END, get_text(label_key), tag)

        if ts_str:
            self.conversation_text.insert(tk.END, f"  [{ts_str}]", "timestamp")
        self.conversation_text.insert(tk.END, "\n")
        self.conversation_text.insert(tk.END, content + "\n", tag)
        self.conversation_text.insert(
            tk.END, "─" * SEPARATOR_LENGTH + "\n\n", "separator"
        )

    @staticmethod
    def _format_timestamp(timestamp: Any) -> str:
        if not timestamp:
            return ""
        dt = to_local_datetime(timestamp)
        if dt is not None:
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        return str(timestamp)

    # ------------------------------------------------------------------
    # チャート描画
    # ------------------------------------------------------------------

    def _draw_chart(self) -> None:
        if self.chart_canvas is None:
            return
        self.chart_canvas.delete("all")
        self.chart_bars = {}

        counts = self._cached_chart_counts
        if not counts:
            return

        canvas_width = self.chart_canvas.winfo_width()
        canvas_height = self.chart_canvas.winfo_height()
        if canvas_width <= 1 or canvas_height <= 1:
            return

        layout = self._compute_chart_layout(canvas_width, canvas_height, len(counts))
        if layout is None:
            return

        max_count = max(max(counts.values(), default=0), 1)
        self._draw_chart_axis(layout, max_count)
        self._draw_chart_bars(counts, layout, max_count)
        self._draw_chart_x_labels(counts, layout)

    @staticmethod
    def _compute_chart_layout(
        canvas_width: int, canvas_height: int, num_bars: int
    ) -> Optional[dict[str, float]]:
        chart_width = canvas_width - CHART_MARGIN_LEFT - CHART_MARGIN_RIGHT
        chart_height = canvas_height - CHART_MARGIN_TOP - CHART_MARGIN_BOTTOM
        if chart_width <= 0 or chart_height <= 0 or num_bars == 0:
            return None
        bar_width = max(
            CHART_BAR_MIN_WIDTH, (chart_width - num_bars) / num_bars
        )
        return {
            "chart_width": chart_width,
            "chart_height": chart_height,
            "bar_width": bar_width,
            "gap": CHART_BAR_GAP,
        }

    def _draw_chart_axis(self, layout: dict[str, float], max_count: int) -> None:
        assert self.chart_canvas is not None
        self.chart_canvas.create_text(
            CHART_MARGIN_LEFT - 5,
            CHART_MARGIN_TOP,
            text=str(max_count),
            anchor="e",
            font=FONT_SMALL,
            fill=COLOR_TEXT_MUTED,
        )
        self.chart_canvas.create_text(
            CHART_MARGIN_LEFT - 5,
            CHART_MARGIN_TOP + layout["chart_height"],
            text="0",
            anchor="e",
            font=FONT_SMALL,
            fill=COLOR_TEXT_MUTED,
        )

    def _draw_chart_bars(
        self,
        counts: dict[str, int],
        layout: dict[str, float],
        max_count: int,
    ) -> None:
        assert self.chart_canvas is not None
        bar_width = layout["bar_width"]
        gap = layout["gap"]
        chart_height = layout["chart_height"]
        y2 = CHART_MARGIN_TOP + chart_height

        for i, date_str in enumerate(sorted(counts.keys())):
            count = counts[date_str]
            bar_height = (count / max_count) * chart_height
            x1 = CHART_MARGIN_LEFT + i * (bar_width + gap)
            x2 = x1 + bar_width
            y1 = y2 - bar_height

            if self.selected_date == date_str:
                color = COLOR_BAR_HIGHLIGHT
            elif count > 0:
                color = COLOR_BAR_NORMAL
            else:
                color = COLOR_BAR_ZERO

            bar_id = self.chart_canvas.create_rectangle(
                x1, y1, x2, y2, fill=color, outline=""
            )
            self.chart_bars[date_str] = bar_id

            self.chart_canvas.tag_bind(
                bar_id,
                "<Enter>",
                lambda e, d=date_str, c=count: self._show_chart_tooltip(e, d, c),
            )
            self.chart_canvas.tag_bind(
                bar_id, "<Leave>", lambda e: self._hide_chart_tooltip()
            )

    def _draw_chart_x_labels(
        self, counts: dict[str, int], layout: dict[str, float]
    ) -> None:
        assert self.chart_canvas is not None
        dates = sorted(counts.keys())
        num_bars = len(dates)
        bar_width = layout["bar_width"]
        gap = layout["gap"]
        label_interval = max(1, num_bars // CHART_X_LABEL_TARGETS)
        y = CHART_MARGIN_TOP + layout["chart_height"] + 12

        for i, date_str in enumerate(dates):
            if i % label_interval == 0 or i == num_bars - 1:
                x = CHART_MARGIN_LEFT + i * (bar_width + gap) + bar_width / 2
                self.chart_canvas.create_text(
                    x,
                    y,
                    text=date_str[5:],  # MM-DD
                    font=FONT_XSMALL,
                    fill=COLOR_TEXT_MUTED,
                )

    def _show_chart_tooltip(
        self, event: tk.Event, date_str: str, count: int
    ) -> None:
        if self.chart_canvas is None:
            return
        self.chart_canvas.delete("tooltip")
        text = f"{date_str}: {get_text('chart_prompts', count=count)}"
        x, y = event.x, event.y - 20
        bbox_id = self.chart_canvas.create_rectangle(
            x - 40,
            y - 10,
            x + 40,
            y + 10,
            fill=COLOR_TEXT_DARK,
            outline="",
            tags="tooltip",
        )
        text_id = self.chart_canvas.create_text(
            x, y, text=text, fill="white", font=FONT_SMALL, tags="tooltip"
        )
        bbox = self.chart_canvas.bbox(text_id)
        if bbox:
            self.chart_canvas.coords(
                bbox_id, bbox[0] - 5, bbox[1] - 3, bbox[2] + 5, bbox[3] + 3
            )

    def _hide_chart_tooltip(self) -> None:
        if self.chart_canvas is not None:
            self.chart_canvas.delete("tooltip")

    def _update_chart_highlight(self, session: Optional[SessionInfo]) -> None:
        if self.chart_canvas is None:
            return

        new_selected_date: Optional[str] = None
        if session:
            ts = session.get("timestamp")
            if ts and ts != datetime.min:
                new_selected_date = ts.date().strftime("%Y-%m-%d")

        if new_selected_date == self.selected_date:
            return

        old_date = self.selected_date
        self.selected_date = new_selected_date

        # キャッシュ済みのcountsを使う（再集計しない）
        counts = self._cached_chart_counts

        if old_date and old_date in self.chart_bars:
            bar_id = self.chart_bars[old_date]
            color = COLOR_BAR_NORMAL if counts.get(old_date, 0) > 0 else COLOR_BAR_ZERO
            self.chart_canvas.itemconfig(bar_id, fill=color)

        if new_selected_date and new_selected_date in self.chart_bars:
            self.chart_canvas.itemconfig(
                self.chart_bars[new_selected_date], fill=COLOR_BAR_HIGHLIGHT
            )

    # ------------------------------------------------------------------
    # テキスト右クリック
    # ------------------------------------------------------------------

    def _on_text_right_click(self, event: tk.Event) -> None:
        try:
            if self.conversation_text.selection_get():
                self.text_context_menu.post(event.x_root, event.y_root)
        except tk.TclError:
            pass

    def _copy_selected_text(self) -> None:
        try:
            text = self.conversation_text.selection_get()
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
        except tk.TclError:
            pass

    # ------------------------------------------------------------------
    # セッション再開
    # ------------------------------------------------------------------

    def _resume_selected_session(self) -> None:
        session = self._get_selected_session()
        if not session:
            return
        try:
            session_id = session["session_id"]
            project_path = session["project_name"]

            # ホワイトリスト検証（UUID形式）
            if not SESSION_ID_PATTERN.match(session_id):
                raise ValueError(f"Invalid session ID format: {session_id}")

            if sys.platform == "win32":
                self._resume_session_windows(project_path, session_id)
            elif sys.platform == "darwin":
                self._resume_session_macos(project_path, session_id)
            else:
                self._resume_session_linux(project_path, session_id)
        except Exception as e:
            messagebox.showerror(
                get_text("error_title"), get_text("error_resume", error=str(e))
            )

    def _resume_session_windows(self, project_path: str, session_id: str) -> None:
        """Windowsでセッションを再開（一時バッチを生成して新コンソールで起動）。

        セキュリティ:
            session_id は呼び出し側でUUID検証済み。
            project_path は %, " をバッチ用にエスケープ。
            エンコーディングは locale.getpreferredencoding() で決定（ロケール非依存）。
        """
        try:
            resolved_path = Path(project_path).resolve(strict=False)
        except (OSError, ValueError):
            resolved_path = Path(project_path)

        # batch内エスケープ: % -> %%, " -> ""
        safe_path = str(resolved_path).replace("%", "%%").replace('"', '""')

        batch_content = (
            f"@echo off\r\n"
            f'cd /d "{safe_path}"\r\n'
            f"claude --resume {session_id}\r\n"
            f"pause\r\n"
        )

        encoding = locale.getpreferredencoding(False) or "mbcs"
        try:
            encoded = batch_content.encode(encoding)
        except (UnicodeEncodeError, LookupError):
            encoded = batch_content.encode("utf-8")

        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".bat", delete=False
        ) as f:
            f.write(encoded)
            batch_path = f.name

        self._temp_files.append(batch_path)
        # ShellExecute経由で .bat を新コンソールで実行
        os.startfile(batch_path)

    def _resume_session_macos(self, project_path: str, session_id: str) -> None:
        """macOSでセッションを再開（osascript で Terminal にコマンド送信）。"""
        safe_path = shlex.quote(project_path)
        safe_id = shlex.quote(session_id)
        cmd = f"cd {safe_path} && claude --resume {safe_id}"
        # AppleScript の二重引用符内エスケープ
        escaped = cmd.replace("\\", "\\\\").replace('"', '\\"')
        applescript = f'tell application "Terminal" to do script "{escaped}"'
        subprocess.Popen(["osascript", "-e", applescript])

    @staticmethod
    def _resume_session_linux(project_path: str, session_id: str) -> None:
        """Linuxでセッションを再開（一般的なターミナルエミュレータを順に試行）。"""
        safe_path = shlex.quote(project_path)
        safe_id = shlex.quote(session_id)
        script = f"cd {safe_path} && claude --resume {safe_id}; exec bash"

        terminals = [
            ["gnome-terminal", "--", "bash", "-c", script],
            ["konsole", "-e", "bash", "-c", script],
            ["xterm", "-e", "bash", "-c", script],
        ]
        for term_cmd in terminals:
            try:
                subprocess.Popen(term_cmd)
                return
            except FileNotFoundError:
                continue
        raise RuntimeError("No suitable terminal emulator found")

    # ------------------------------------------------------------------
    # セッション削除
    # ------------------------------------------------------------------

    def _delete_selected_session(self) -> None:
        session = self._get_selected_session()
        if not session:
            return

        try:
            file_path: Path = session["file_path"]
            first_msg = truncate_text(
                session["first_message"], FIRST_MESSAGE_DISPLAY_LENGTH
            )

            # パストラバーサル防止（削除はユーザ要求外パスへの書き込みなので必須）
            if not is_safe_path(self.projects_dir, file_path):
                raise ValueError("Invalid file path")

            if not messagebox.askyesno(
                get_text("confirm_delete_title"),
                get_text(
                    "confirm_delete_message",
                    project=session["project_name"],
                    message=first_msg,
                ),
            ):
                return

            if file_path.exists():
                file_path.unlink()

            related_dir = file_path.with_suffix("")
            if (
                related_dir.exists()
                and related_dir.is_dir()
                and is_safe_path(self.projects_dir, related_dir)
            ):
                shutil.rmtree(related_dir)

            self.sessions = [
                s for s in self.sessions if s["file_path"] != file_path
            ]

            if (
                self.current_session
                and self.current_session["file_path"] == file_path
            ):
                self.current_session = None
                self.session_info_label.config(text=get_text("select_session"))
                self.conversation_text.config(state=tk.NORMAL)
                self.conversation_text.delete(1.0, tk.END)
                self.conversation_text.config(state=tk.DISABLED)

            self._filter_sessions()
            messagebox.showinfo(
                get_text("delete_success_title"),
                get_text("delete_success_message"),
            )
        except Exception as e:
            messagebox.showerror(
                get_text("error_title"), get_text("error_delete", error=str(e))
            )

    # ------------------------------------------------------------------
    # クリーンアップ
    # ------------------------------------------------------------------

    def _cleanup_temp_files(self) -> None:
        for path in self._temp_files:
            try:
                os.unlink(path)
            except OSError:
                pass
        self._temp_files.clear()


# ============================================================================
# エントリーポイント
# ============================================================================

def main() -> None:
    set_language(detect_system_language())
    root = tk.Tk()
    ClaudeCodeRecall(root)
    root.mainloop()


if __name__ == "__main__":
    main()
