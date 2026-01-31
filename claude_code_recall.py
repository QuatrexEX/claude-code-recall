#!/usr/bin/env python3
"""
Claude Code Recall - セッション履歴ビューア
全プロジェクトのClaude Codeセッション履歴を横断的に閲覧・管理できるGUIツール

Copyright (c) 2026
License: MIT
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import tkinter as tk
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any, Optional

# ============================================================================
# 定数
# ============================================================================

APP_NAME = "Claude Code Recall"
APP_VERSION = "1.1.0"
DEFAULT_WINDOW_SIZE = "1200x800"

# ============================================================================
# 多言語対応（i18n）
# ============================================================================

TRANSLATIONS = {
    "ja": {
        "app_title": "Claude Code Recall - セッション履歴ビューア",
        "search": "検索:",
        "filter_system": "システムセッション除外",
        "filter_slash": "スラッシュコマンド除外",
        "session_count": "セッション数: {displayed} / {total}",
        "col_project": "プロジェクト",
        "col_date": "日時",
        "col_first_message": "最初のメッセージ",
        "select_session": "セッションを選択してください",
        "project_label": "プロジェクト: {path}\nセッションID: {session_id}",
        "menu_resume": "セッションを再開",
        "menu_delete": "セッションを削除",
        "menu_copy": "コピー",
        "confirm_delete_title": "セッション削除の確認",
        "confirm_delete_message": "以下のセッションを削除しますか？\n\nプロジェクト: {project}\nメッセージ: {message}...\n\nこの操作は取り消せません。",
        "delete_success_title": "削除完了",
        "delete_success_message": "セッションを削除しました。",
        "error_title": "エラー",
        "error_delete": "セッションの削除に失敗しました:\n{error}",
        "error_resume": "セッションの再開に失敗しました:\n{error}",
        "slash_command_only": "(スラッシュコマンドのみ)",
        "user_label": "👤 User",
        "assistant_label": "🤖 Assistant",
        "chart_title": "過去30日間のプロンプト数",
        "chart_prompts": "{count}件",
        "last_updated": "最終更新: {time}",
    },
    "en": {
        "app_title": "Claude Code Recall - Session History Viewer",
        "search": "Search:",
        "filter_system": "Exclude system sessions",
        "filter_slash": "Exclude slash commands",
        "session_count": "Sessions: {displayed} / {total}",
        "col_project": "Project",
        "col_date": "Date",
        "col_first_message": "First Message",
        "select_session": "Select a session",
        "project_label": "Project: {path}\nSession ID: {session_id}",
        "menu_resume": "Resume Session",
        "menu_delete": "Delete Session",
        "menu_copy": "Copy",
        "confirm_delete_title": "Confirm Deletion",
        "confirm_delete_message": "Delete this session?\n\nProject: {project}\nMessage: {message}...\n\nThis action cannot be undone.",
        "delete_success_title": "Deleted",
        "delete_success_message": "Session deleted successfully.",
        "error_title": "Error",
        "error_delete": "Failed to delete session:\n{error}",
        "error_resume": "Failed to resume session:\n{error}",
        "slash_command_only": "(Slash commands only)",
        "user_label": "👤 User",
        "assistant_label": "🤖 Assistant",
        "chart_title": "Prompts in the last 30 days",
        "chart_prompts": "{count}",
        "last_updated": "Last updated: {time}",
    },
}

# 現在の言語（デフォルト: 日本語）
_current_language = "ja"


def get_text(key: str, **kwargs: Any) -> str:
    """翻訳テキストを取得する。

    Args:
        key: 翻訳キー
        **kwargs: フォーマット用の引数

    Returns:
        翻訳されたテキスト
    """
    text = TRANSLATIONS.get(_current_language, TRANSLATIONS["ja"]).get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except KeyError:
            return text
    return text


def set_language(lang: str) -> None:
    """言語を設定する。

    Args:
        lang: 言語コード（"ja", "en" など）
    """
    global _current_language
    if lang in TRANSLATIONS:
        _current_language = lang


# ============================================================================
# ユーティリティ関数
# ============================================================================

def get_claude_projects_dir() -> Path:
    """Claude Codeのプロジェクトディレクトリを取得する。

    Returns:
        プロジェクトディレクトリのPath

    Note:
        Windows: ~/.claude/projects
        Mac/Linux: ~/.claude/projects
    """
    if sys.platform == "win32":
        # Windowsの場合、HOMEまたはUSERPROFILEを使用
        home = Path(os.environ.get("USERPROFILE", os.environ.get("HOME", "")))
    else:
        home = Path.home()

    return home / ".claude" / "projects"


def is_safe_path(base_path: Path, target_path: Path) -> bool:
    """パストラバーサル攻撃を防ぐためのパス検証。

    Args:
        base_path: 基準となるディレクトリ
        target_path: 検証するパス

    Returns:
        パスが安全な場合True
    """
    try:
        # 絶対パスに変換して比較
        base_resolved = base_path.resolve()
        target_resolved = target_path.resolve()
        return str(target_resolved).startswith(str(base_resolved))
    except (OSError, ValueError):
        return False


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """テキストを指定長で切り詰める。

    Args:
        text: 対象テキスト
        max_length: 最大長
        suffix: 切り詰め時に追加する文字列

    Returns:
        切り詰められたテキスト
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def get_short_project_name(full_path: str, depth: int = 2) -> str:
    """プロジェクトパスを短縮表示用に変換する。

    Args:
        full_path: フルパス
        depth: 表示するディレクトリ階層の深さ

    Returns:
        短縮されたパス（例: "CC\\CCV"）
    """
    # パス区切り文字を統一
    normalized = full_path.replace("/", "\\")
    parts = normalized.split("\\")

    if len(parts) >= depth:
        return "\\".join(parts[-depth:])
    return parts[-1] if parts else full_path


# ============================================================================
# メインアプリケーション
# ============================================================================

class ClaudeCodeRecall:
    """Claude Code Recallメインアプリケーションクラス。"""

    def __init__(self, root: tk.Tk) -> None:
        """アプリケーションを初期化する。

        Args:
            root: Tkinterのルートウィンドウ
        """
        self.root = root
        self.root.title(get_text("app_title"))
        self.root.geometry(DEFAULT_WINDOW_SIZE)

        # ディレクトリ設定
        self.projects_dir = get_claude_projects_dir()

        # データ
        self.sessions: list[dict[str, Any]] = []
        self.current_session: Optional[dict[str, Any]] = None

        # フィルター設定
        self.filter_system_sessions = tk.BooleanVar(value=True)
        self.filter_slash_commands = tk.BooleanVar(value=True)

        # 棒グラフ関連
        self.chart_canvas: Optional[tk.Canvas] = None
        self.chart_bars: dict[str, int] = {}  # date_str -> canvas item id
        self.selected_date: Optional[str] = None

        # 最終更新日時
        self.last_updated: Optional[datetime] = None

        # UI構築
        self._setup_ui()
        self._setup_text_context_menu()

        # セッション読み込み
        self._load_all_sessions()

        # ログ設定
        logging.basicConfig(level=logging.WARNING)
        self.logger = logging.getLogger(__name__)

        # 自動再読み込みタイマー開始（10分間隔）
        self._schedule_auto_reload()

    def _setup_ui(self) -> None:
        """UIを構築する。"""
        # メインのPanedWindow（左右分割）
        self.paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self._setup_left_panel()
        self._setup_right_panel()

    def _setup_left_panel(self) -> None:
        """左パネル（セッションリスト + 棒グラフ）を構築する。"""
        left_frame = ttk.Frame(self.paned)
        self.paned.add(left_frame, weight=1)

        # 上部フレーム（セッションリスト）- 3/4
        top_frame = ttk.Frame(left_frame)
        top_frame.pack(fill=tk.BOTH, expand=True)

        # 検索バー
        search_frame = ttk.Frame(top_frame)
        search_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(search_frame, text=get_text("search")).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._filter_sessions())
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        # フィルターオプション
        filter_frame = ttk.Frame(top_frame)
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

        # セッション数・最終更新日時表示
        status_frame = ttk.Frame(top_frame)
        status_frame.pack(fill=tk.X)

        self.count_label = ttk.Label(status_frame, text="")
        self.count_label.pack(side=tk.LEFT)

        self.updated_label = ttk.Label(status_frame, text="", foreground="#666666")
        self.updated_label.pack(side=tk.RIGHT)

        # セッションリスト（Treeview）
        list_frame = ttk.Frame(top_frame)
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

        # 右クリックメニュー（セッションリスト用）
        self.session_context_menu = tk.Menu(self.root, tearoff=0)
        self.session_context_menu.add_command(
            label=get_text("menu_resume"), command=self._resume_selected_session
        )
        self.session_context_menu.add_separator()
        self.session_context_menu.add_command(
            label=get_text("menu_delete"), command=self._delete_selected_session
        )
        self.session_tree.bind("<Button-3>", self._on_session_right_click)

        # 下部フレーム（棒グラフ）- 1/4
        self._setup_chart_panel(left_frame)

    def _setup_chart_panel(self, parent: ttk.Frame) -> None:
        """棒グラフパネルを構築する。

        Args:
            parent: 親フレーム
        """
        chart_frame = ttk.LabelFrame(parent, text=get_text("chart_title"))
        chart_frame.pack(fill=tk.BOTH, pady=(5, 0), ipady=5)

        # Canvas for chart (height fixed to ~1/4 of typical window)
        self.chart_canvas = tk.Canvas(
            chart_frame,
            height=120,
            bg="#f8f8f8",
            highlightthickness=0,
        )
        self.chart_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Bind resize event
        self.chart_canvas.bind("<Configure>", lambda e: self._draw_chart())

    def _get_prompt_counts_by_date(self) -> dict[str, int]:
        """過去30日間の日別プロンプト数（Userメッセージ数）を取得する。

        Returns:
            日付文字列をキー、プロンプト数を値とする辞書
        """
        counts: dict[str, int] = {}
        today = datetime.now().date()
        exclude_slash = self.filter_slash_commands.get()

        # Initialize all 30 days with 0
        for i in range(30):
            date = today - timedelta(days=29 - i)
            date_str = date.strftime("%Y-%m-%d")
            counts[date_str] = 0

        # Count user prompts (filtered)
        filtered = self._get_filtered_sessions()
        for session in filtered:
            messages = session.get("messages", [])
            for msg in messages:
                # Count only user messages
                if msg.get("type") != "user":
                    continue
                # Exclude slash commands if filter is enabled
                if exclude_slash and msg.get("is_slash_command", False):
                    continue

                ts = msg.get("timestamp")
                if ts:
                    msg_date = self._timestamp_to_date(ts)
                    if msg_date:
                        date_str = msg_date.strftime("%Y-%m-%d")
                        if date_str in counts:
                            counts[date_str] += 1

        return counts

    def _timestamp_to_date(self, ts: Any) -> Optional[datetime]:
        """タイムスタンプを日付に変換する。

        Args:
            ts: タイムスタンプ値

        Returns:
            datetime オブジェクト、または None
        """
        try:
            if isinstance(ts, str):
                dt_utc = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                return dt_utc.astimezone().replace(tzinfo=None)
            elif isinstance(ts, (int, float)):
                dt_utc = datetime.utcfromtimestamp(ts / 1000)
                dt_aware = dt_utc.replace(tzinfo=timezone.utc)
                return dt_aware.astimezone().replace(tzinfo=None)
        except (ValueError, OSError):
            pass
        return None

    def _draw_chart(self) -> None:
        """棒グラフを描画する。"""
        if self.chart_canvas is None:
            return

        self.chart_canvas.delete("all")
        self.chart_bars = {}

        counts = self._get_prompt_counts_by_date()
        if not counts:
            return

        # Canvas dimensions
        canvas_width = self.chart_canvas.winfo_width()
        canvas_height = self.chart_canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            return

        # Chart margins
        margin_left = 30
        margin_right = 10
        margin_top = 10
        margin_bottom = 25

        chart_width = canvas_width - margin_left - margin_right
        chart_height = canvas_height - margin_top - margin_bottom

        if chart_width <= 0 or chart_height <= 0:
            return

        # Get sorted dates
        dates = sorted(counts.keys())
        num_bars = len(dates)
        max_count = max(counts.values()) if counts.values() else 1
        max_count = max(max_count, 1)  # Avoid division by zero

        # Bar dimensions
        bar_width = max(2, (chart_width - num_bars) / num_bars)
        gap = 1

        # Draw Y-axis scale
        self.chart_canvas.create_text(
            margin_left - 5,
            margin_top,
            text=str(max_count),
            anchor="e",
            font=("", 8),
            fill="#666666",
        )
        self.chart_canvas.create_text(
            margin_left - 5,
            margin_top + chart_height,
            text="0",
            anchor="e",
            font=("", 8),
            fill="#666666",
        )

        # Draw bars
        for i, date_str in enumerate(dates):
            count = counts[date_str]
            bar_height = (count / max_count) * chart_height if max_count > 0 else 0

            x1 = margin_left + i * (bar_width + gap)
            x2 = x1 + bar_width
            y2 = margin_top + chart_height
            y1 = y2 - bar_height

            # Determine color
            if self.selected_date == date_str:
                fill_color = "#ff6600"  # Highlight color (orange)
            elif count > 0:
                fill_color = "#4a90d9"  # Normal bar color (blue)
            else:
                fill_color = "#e0e0e0"  # Zero count color (light gray)

            bar_id = self.chart_canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=fill_color,
                outline="",
            )
            self.chart_bars[date_str] = bar_id

            # Bind tooltip
            self.chart_canvas.tag_bind(
                bar_id,
                "<Enter>",
                lambda e, d=date_str, c=count: self._show_chart_tooltip(e, d, c),
            )
            self.chart_canvas.tag_bind(
                bar_id, "<Leave>", lambda e: self._hide_chart_tooltip()
            )

        # Draw X-axis labels (show only a few dates)
        label_interval = max(1, num_bars // 5)
        for i, date_str in enumerate(dates):
            if i % label_interval == 0 or i == num_bars - 1:
                x = margin_left + i * (bar_width + gap) + bar_width / 2
                y = margin_top + chart_height + 12
                # Show only month/day
                label = date_str[5:]  # "MM-DD"
                self.chart_canvas.create_text(
                    x, y,
                    text=label,
                    font=("", 7),
                    fill="#666666",
                )

    def _show_chart_tooltip(self, event: tk.Event, date_str: str, count: int) -> None:
        """棒グラフのツールチップを表示する。

        Args:
            event: イベントオブジェクト
            date_str: 日付文字列
            count: セッション数
        """
        if self.chart_canvas is None:
            return

        # Remove existing tooltip
        self.chart_canvas.delete("tooltip")

        text = f"{date_str}: {get_text('chart_prompts', count=count)}"
        x = event.x
        y = event.y - 20

        # Background
        bbox_id = self.chart_canvas.create_rectangle(
            x - 40, y - 10, x + 40, y + 10,
            fill="#333333",
            outline="",
            tags="tooltip",
        )
        text_id = self.chart_canvas.create_text(
            x, y,
            text=text,
            fill="white",
            font=("", 8),
            tags="tooltip",
        )

        # Adjust background size to text
        bbox = self.chart_canvas.bbox(text_id)
        if bbox:
            self.chart_canvas.coords(
                bbox_id,
                bbox[0] - 5, bbox[1] - 3, bbox[2] + 5, bbox[3] + 3
            )

    def _hide_chart_tooltip(self) -> None:
        """棒グラフのツールチップを非表示にする。"""
        if self.chart_canvas is not None:
            self.chart_canvas.delete("tooltip")

    def _update_chart_highlight(self, session: Optional[dict[str, Any]]) -> None:
        """選択されたセッションに対応する棒をハイライトする。

        Args:
            session: 選択されたセッション（Noneの場合はハイライト解除）
        """
        if self.chart_canvas is None:
            return

        # Get date of selected session
        new_selected_date: Optional[str] = None
        if session:
            ts = session.get("timestamp")
            if ts and ts != datetime.min:
                new_selected_date = ts.date().strftime("%Y-%m-%d")

        # Update only if selection changed
        if new_selected_date == self.selected_date:
            return

        old_date = self.selected_date
        self.selected_date = new_selected_date

        # Update bar colors
        counts = self._get_prompt_counts_by_date()

        # Reset old highlight
        if old_date and old_date in self.chart_bars:
            bar_id = self.chart_bars[old_date]
            count = counts.get(old_date, 0)
            color = "#4a90d9" if count > 0 else "#e0e0e0"
            self.chart_canvas.itemconfig(bar_id, fill=color)

        # Set new highlight
        if new_selected_date and new_selected_date in self.chart_bars:
            bar_id = self.chart_bars[new_selected_date]
            self.chart_canvas.itemconfig(bar_id, fill="#ff6600")

    def _setup_right_panel(self) -> None:
        """右パネル（会話表示）を構築する。"""
        right_frame = ttk.Frame(self.paned)
        self.paned.add(right_frame, weight=2)

        # セッション情報
        self.session_info_label = ttk.Label(
            right_frame, text=get_text("select_session"), font=("", 10, "bold")
        )
        self.session_info_label.pack(anchor=tk.W, pady=(0, 5))

        # 会話表示（Text）
        text_frame = ttk.Frame(right_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.conversation_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
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

        # タグ設定（色分け）
        self.conversation_text.tag_configure(
            "user", foreground="#0066cc", font=("Consolas", 10, "bold")
        )
        self.conversation_text.tag_configure("assistant", foreground="#009933")
        self.conversation_text.tag_configure(
            "timestamp", foreground="#666666", font=("Consolas", 9)
        )
        self.conversation_text.tag_configure("separator", foreground="#cccccc")

    def _setup_text_context_menu(self) -> None:
        """テキスト表示エリアの右クリックメニューを設定する。"""
        self.text_context_menu = tk.Menu(self.root, tearoff=0)
        self.text_context_menu.add_command(
            label=get_text("menu_copy"), command=self._copy_selected_text
        )
        self.conversation_text.bind("<Button-3>", self._on_text_right_click)

    def _on_text_right_click(self, event: tk.Event) -> None:
        """テキストエリア右クリック時の処理。

        Args:
            event: イベントオブジェクト
        """
        # 選択されたテキストがある場合のみメニューを表示
        try:
            if self.conversation_text.selection_get():
                self.text_context_menu.post(event.x_root, event.y_root)
        except tk.TclError:
            # 選択がない場合は何もしない
            pass

    def _copy_selected_text(self) -> None:
        """選択されたテキストをクリップボードにコピーする。"""
        try:
            selected_text = self.conversation_text.selection_get()
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
        except tk.TclError:
            pass

    def _schedule_auto_reload(self) -> None:
        """自動再読み込みタイマーをスケジュールする。"""
        # 10分 = 600,000ミリ秒
        self.root.after(600000, self._auto_reload)

    def _auto_reload(self) -> None:
        """自動再読み込みを実行する。"""
        # 現在の選択状態を保存
        selection = self.session_tree.selection()
        selected_session_id: Optional[str] = None
        if selection and self.current_session:
            selected_session_id = self.current_session.get("session_id")

        # セッションを再読み込み
        self._load_all_sessions()

        # 選択状態を復元
        if selected_session_id:
            filtered = self._get_filtered_sessions()
            for idx, session in enumerate(filtered):
                if session.get("session_id") == selected_session_id:
                    self.session_tree.selection_set(str(idx))
                    self.session_tree.see(str(idx))
                    break

        # 次のタイマーをスケジュール
        self._schedule_auto_reload()

    def _load_all_sessions(self) -> None:
        """全プロジェクトのセッションを読み込む。"""
        self.sessions = []
        self.last_updated = datetime.now()

        if not self.projects_dir.exists():
            self._filter_sessions()
            return

        for project_dir in self.projects_dir.iterdir():
            if not project_dir.is_dir():
                continue

            # セキュリティチェック
            if not is_safe_path(self.projects_dir, project_dir):
                continue

            # プロジェクト名をデコード（フォールバック用）
            project_name_fallback = project_dir.name.replace("--", ":/", 1).replace(
                "-", "/"
            )

            for session_file in project_dir.glob("*.jsonl"):
                if not session_file.is_file():
                    continue

                # セキュリティチェック
                if not is_safe_path(project_dir, session_file):
                    continue

                session_info = self._parse_session_file(
                    session_file, project_name_fallback
                )
                if session_info:
                    self.sessions.append(session_info)

        # 日時でソート（新しい順）
        self.sessions.sort(key=lambda x: x["timestamp"], reverse=True)

        self._filter_sessions()

    def _parse_session_file(
        self, file_path: Path, project_name_fallback: str
    ) -> Optional[dict[str, Any]]:
        """セッションファイルをパースして情報を抽出する。

        Args:
            file_path: セッションファイルのパス
            project_name_fallback: cwdが取得できない場合のフォールバック名

        Returns:
            セッション情報の辞書、または None
        """
        try:
            messages: list[dict[str, Any]] = []
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

                    # cwdを取得（最初に見つかったものを使用）
                    if actual_cwd is None and "cwd" in data:
                        actual_cwd = data["cwd"]

                    # タイムスタンプを取得
                    latest_timestamp = self._parse_timestamp(
                        data.get("timestamp"), latest_timestamp
                    )

                    # メッセージを抽出
                    msg_info = self._extract_message(data)
                    if msg_info:
                        messages.append(msg_info)
                        if (
                            msg_info["type"] == "user"
                            and not first_user_message
                            and not msg_info["is_slash_command"]
                        ):
                            first_user_message = msg_info["content"][:100].replace(
                                "\n", " "
                            )

            if not messages:
                return None

            # セッション属性を判定
            is_human_session = self._is_human_session(file_path, first_user_message)
            has_normal_messages = any(
                m["type"] == "user" and not m.get("is_slash_command", False)
                for m in messages
            )

            return {
                "file_path": file_path,
                "project_name": actual_cwd or project_name_fallback,
                "session_id": file_path.stem,
                "timestamp": latest_timestamp or datetime.min,
                "first_message": first_user_message
                or get_text("slash_command_only"),
                "messages": messages,
                "is_human_session": is_human_session,
                "has_normal_messages": has_normal_messages,
            }

        except Exception as e:
            self.logger.warning(f"Error parsing {file_path}: {e}")
            return None

    def _parse_timestamp(
        self, ts: Any, current_latest: Optional[datetime]
    ) -> Optional[datetime]:
        """タイムスタンプをパースしてローカルタイムゾーンに変換する。

        Args:
            ts: タイムスタンプ値
            current_latest: 現在の最新タイムスタンプ

        Returns:
            更新されたタイムスタンプ（ローカルタイムゾーン）
        """
        if ts is None:
            return current_latest

        try:
            if isinstance(ts, str):
                # ISO format (UTC) -> local timezone
                dt_utc = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                dt = dt_utc.astimezone().replace(tzinfo=None)
            elif isinstance(ts, (int, float)):
                # Unix timestamp in milliseconds (UTC) -> local timezone
                dt_utc = datetime.utcfromtimestamp(ts / 1000)
                # Convert UTC naive to aware, then to local
                dt_aware = dt_utc.replace(tzinfo=timezone.utc)
                dt = dt_aware.astimezone().replace(tzinfo=None)
            else:
                return current_latest

            if current_latest is None or dt > current_latest:
                return dt
        except (ValueError, OSError):
            pass

        return current_latest

    def _extract_message(self, data: dict[str, Any]) -> Optional[dict[str, Any]]:
        """メッセージデータを抽出する。

        Args:
            data: JSONデータ

        Returns:
            メッセージ情報の辞書、または None
        """
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

        # スラッシュコマンドかどうかを判定
        content_stripped = content.strip()
        is_slash_command = (
            is_meta
            or content_stripped.startswith("<command-name>")
            or content_stripped.startswith("<local-command-stdout>")
            or content_stripped.startswith("<local-command-caveat>")
        )

        return {
            "type": msg_type,
            "content": content,
            "timestamp": data.get("timestamp"),
            "is_meta": is_meta,
            "is_slash_command": is_slash_command,
        }

    def _is_human_session(self, file_path: Path, first_message: str) -> bool:
        """人間が開始したセッションかどうかを判定する。

        Args:
            file_path: セッションファイルのパス
            first_message: 最初のユーザーメッセージ

        Returns:
            人間が開始したセッションの場合 True
        """
        # agent-で始まるファイル名はサブエージェントセッション
        if file_path.stem.startswith("agent-"):
            return False

        # 最初のメッセージが"Warmup"のものはウォームアップセッション
        if first_message.strip().lower() == "warmup":
            return False

        return True

    def _populate_session_list(
        self, sessions: Optional[list[dict[str, Any]]] = None
    ) -> None:
        """セッションリストを表示する。

        Args:
            sessions: 表示するセッションリスト（Noneの場合は全セッション）
        """
        self.session_tree.delete(*self.session_tree.get_children())

        display_sessions = sessions if sessions is not None else self.sessions

        for idx, session in enumerate(display_sessions):
            project = get_short_project_name(session["project_name"])

            if session["timestamp"] != datetime.min:
                date_str = session["timestamp"].strftime("%Y-%m-%d %H:%M")
            else:
                date_str = "-"

            first_msg = truncate_text(session["first_message"], 50)

            self.session_tree.insert(
                "", tk.END, iid=str(idx), values=(project, date_str, first_msg)
            )

        self.count_label.config(
            text=get_text(
                "session_count",
                displayed=len(display_sessions),
                total=len(self.sessions),
            )
        )

        # 最終更新日時を更新
        if self.last_updated:
            time_str = self.last_updated.strftime("%Y-%m-%d %H:%M")
            self.updated_label.config(text=get_text("last_updated", time=time_str))

    def _filter_sessions(self) -> None:
        """検索フィルタを適用する。"""
        filtered = self._get_filtered_sessions()
        self._populate_session_list(filtered)
        self._draw_chart()

    def _on_slash_filter_change(self) -> None:
        """スラッシュコマンドフィルター変更時の処理。"""
        self._filter_sessions()
        if self.current_session:
            self._display_conversation(self.current_session)

    def _get_filtered_sessions(self) -> list[dict[str, Any]]:
        """現在のフィルター条件でセッションリストを取得する。

        Returns:
            フィルタリングされたセッションリスト
        """
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

    def _on_session_select(self, event: tk.Event) -> None:
        """セッション選択時の処理。

        Args:
            event: イベントオブジェクト
        """
        selection = self.session_tree.selection()
        if not selection:
            return

        try:
            idx = int(selection[0])
            filtered = self._get_filtered_sessions()
            if idx < len(filtered):
                session = filtered[idx]
                self._display_conversation(session)
                self._update_chart_highlight(session)
        except (ValueError, IndexError):
            pass

    def _on_session_right_click(self, event: tk.Event) -> None:
        """セッションリスト右クリック時の処理。

        Args:
            event: イベントオブジェクト
        """
        item = self.session_tree.identify_row(event.y)
        if item:
            self.session_tree.selection_set(item)
            self.session_context_menu.post(event.x_root, event.y_root)

    def _display_conversation(self, session: dict[str, Any]) -> None:
        """会話を表示する。

        Args:
            session: セッション情報
        """
        self.current_session = session

        self.session_info_label.config(
            text=get_text(
                "project_label",
                path=session["project_name"],
                session_id=session["session_id"],
            )
        )

        self.conversation_text.config(state=tk.NORMAL)
        self.conversation_text.delete(1.0, tk.END)

        exclude_slash = self.filter_slash_commands.get()

        for msg in session["messages"]:
            if exclude_slash and msg.get("is_slash_command", False):
                continue

            self._render_message(msg)

        self.conversation_text.config(state=tk.DISABLED)
        self.conversation_text.see(1.0)

    def _render_message(self, msg: dict[str, Any]) -> None:
        """メッセージを描画する。

        Args:
            msg: メッセージ情報
        """
        msg_type = msg["type"]
        content = msg["content"]
        timestamp = msg.get("timestamp", "")

        # タイムスタンプをフォーマット
        ts_str = self._format_timestamp(timestamp)

        # ロール表示
        if msg_type == "user":
            self.conversation_text.insert(tk.END, get_text("user_label"), "user")
        else:
            self.conversation_text.insert(
                tk.END, get_text("assistant_label"), "assistant"
            )

        if ts_str:
            self.conversation_text.insert(tk.END, f"  [{ts_str}]", "timestamp")

        self.conversation_text.insert(tk.END, "\n")

        # 内容表示
        tag = "user" if msg_type == "user" else "assistant"
        self.conversation_text.insert(tk.END, content + "\n", tag)

        # 区切り線
        self.conversation_text.insert(tk.END, "─" * 80 + "\n\n", "separator")

    def _format_timestamp(self, timestamp: Any) -> str:
        """タイムスタンプをローカルタイムゾーンで文字列にフォーマットする。

        Args:
            timestamp: タイムスタンプ値

        Returns:
            フォーマットされた文字列（ローカルタイムゾーン）
        """
        if not timestamp:
            return ""

        try:
            if isinstance(timestamp, str):
                # ISO format (UTC) -> local timezone
                dt_utc = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                dt = dt_utc.astimezone().replace(tzinfo=None)
            elif isinstance(timestamp, (int, float)):
                # Unix timestamp in milliseconds (UTC) -> local timezone
                dt_utc = datetime.utcfromtimestamp(timestamp / 1000)
                dt_aware = dt_utc.replace(tzinfo=timezone.utc)
                dt = dt_aware.astimezone().replace(tzinfo=None)
            else:
                return ""
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, OSError):
            return str(timestamp) if timestamp else ""

    def _resume_selected_session(self) -> None:
        """選択されたセッションを再開する。"""
        selection = self.session_tree.selection()
        if not selection:
            return

        try:
            idx = int(selection[0])
            filtered = self._get_filtered_sessions()
            if idx >= len(filtered):
                return

            session = filtered[idx]
            session_id = session["session_id"]
            project_path = session["project_name"]

            # プラットフォームに応じた処理
            if sys.platform == "win32":
                self._resume_session_windows(project_path, session_id)
            else:
                self._resume_session_unix(project_path, session_id)

        except Exception as e:
            messagebox.showerror(
                get_text("error_title"), get_text("error_resume", error=str(e))
            )

    def _resume_session_windows(self, project_path: str, session_id: str) -> None:
        """Windowsでセッションを再開する。

        Args:
            project_path: プロジェクトパス
            session_id: セッションID
        """
        batch_content = (
            f'@echo off\n'
            f'cd /d "{project_path}"\n'
            f'claude --resume {session_id}\n'
            f'pause'
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".bat", delete=False, encoding="cp932"
        ) as f:
            f.write(batch_content)
            batch_path = f.name

        subprocess.Popen(f'start cmd /k "{batch_path}"', shell=True)

    def _resume_session_unix(self, project_path: str, session_id: str) -> None:
        """Unix系OSでセッションを再開する。

        Args:
            project_path: プロジェクトパス
            session_id: セッションID
        """
        script_content = (
            f'cd "{project_path}" && claude --resume {session_id}; exec bash'
        )

        # 一般的なターミナルエミュレータを試す
        terminals = [
            ["gnome-terminal", "--", "bash", "-c", script_content],
            ["xterm", "-e", f"bash -c '{script_content}'"],
            ["open", "-a", "Terminal", project_path],  # macOS
        ]

        for terminal_cmd in terminals:
            try:
                subprocess.Popen(terminal_cmd)
                return
            except FileNotFoundError:
                continue

        raise RuntimeError("No suitable terminal emulator found")

    def _delete_selected_session(self) -> None:
        """選択されたセッションを削除する。"""
        selection = self.session_tree.selection()
        if not selection:
            return

        try:
            idx = int(selection[0])
            filtered = self._get_filtered_sessions()
            if idx >= len(filtered):
                return

            session = filtered[idx]
            file_path: Path = session["file_path"]
            first_msg = truncate_text(session["first_message"], 50)

            # セキュリティチェック
            if not is_safe_path(self.projects_dir, file_path):
                raise ValueError("Invalid file path")

            # 確認ダイアログ
            result = messagebox.askyesno(
                get_text("confirm_delete_title"),
                get_text(
                    "confirm_delete_message",
                    project=session["project_name"],
                    message=first_msg,
                ),
            )

            if not result:
                return

            # ファイルを削除
            if file_path.exists():
                file_path.unlink()

            # 関連するディレクトリも削除
            related_dir = file_path.with_suffix("")
            if related_dir.exists() and related_dir.is_dir():
                if is_safe_path(self.projects_dir, related_dir):
                    shutil.rmtree(related_dir)

            # セッションリストから削除
            self.sessions = [
                s for s in self.sessions if s["file_path"] != file_path
            ]

            # 現在表示中のセッションが削除された場合はクリア
            if self.current_session and self.current_session["file_path"] == file_path:
                self.current_session = None
                self.session_info_label.config(text=get_text("select_session"))
                self.conversation_text.config(state=tk.NORMAL)
                self.conversation_text.delete(1.0, tk.END)
                self.conversation_text.config(state=tk.DISABLED)

            self._filter_sessions()

            messagebox.showinfo(
                get_text("delete_success_title"), get_text("delete_success_message")
            )

        except Exception as e:
            messagebox.showerror(
                get_text("error_title"), get_text("error_delete", error=str(e))
            )


# ============================================================================
# エントリーポイント
# ============================================================================

def main() -> None:
    """アプリケーションのエントリーポイント。"""
    root = tk.Tk()
    ClaudeCodeRecall(root)
    root.mainloop()


if __name__ == "__main__":
    main()
