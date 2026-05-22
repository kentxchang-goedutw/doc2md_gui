"""
微軟文件轉 Markdown 工具
Made by 阿剛老師 (https://kentxchang.blogspot.tw)
CC BY-NC-SA 4.0
"""

import threading
import webbrowser
import os
import re
import sys
import subprocess
import importlib.util
from pathlib import Path
from urllib.parse import urlparse

try:
    import customtkinter as ctk
except ImportError:
    raise SystemExit("請先安裝 customtkinter：pip install customtkinter")

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    from markitdown import MarkItDown
    MARKITDOWN_AVAILABLE = True
except ImportError:
    MARKITDOWN_AVAILABLE = False

# ── 常數 ─────────────────────────────────────────────────────────────────────

BLOG_URL = "https://kentxchang.blogspot.tw"

FORMAT_INFO = (
    "PDF　　Word　　Excel　　PowerPoint　　HTML\n"
    "圖片　　音訊／影片　　CSV　　JSON　　XML\n"
    "EPUB　　ZIP　　Outlook 郵件　　YouTube URL"
)

SUPPORTED_EXTS = {
    ".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls",
    ".html", ".htm", ".csv", ".json", ".xml", ".epub",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
    ".mp3", ".mp4", ".wav", ".m4a", ".flac", ".ogg", ".aac",
    ".zip", ".msg",
}

AUDIO_EXTS = {".mp3", ".mp4", ".wav", ".m4a", ".flac", ".ogg", ".aac", ".webm"}

FILETYPES = [
    ("所有支援格式",
     "*.pdf *.docx *.doc *.pptx *.ppt *.xlsx *.xls "
     "*.html *.htm *.csv *.json *.xml *.epub "
     "*.jpg *.jpeg *.png *.gif *.bmp *.webp "
     "*.mp3 *.mp4 *.wav *.m4a *.zip *.msg"),
    ("PDF 文件",        "*.pdf"),
    ("Word 文件",       "*.docx *.doc"),
    ("PowerPoint 簡報", "*.pptx *.ppt"),
    ("Excel 試算表",    "*.xlsx *.xls"),
    ("網頁 / HTML",     "*.html *.htm"),
    ("資料格式",        "*.csv *.json *.xml"),
    ("電子書",          "*.epub"),
    ("圖片",            "*.jpg *.jpeg *.png *.gif *.bmp *.webp"),
    ("音訊 / 影片",     "*.mp3 *.mp4 *.wav *.m4a"),
    ("壓縮檔",          "*.zip"),
    ("Outlook 郵件",    "*.msg"),
    ("所有檔案",        "*.*"),
]

# 批次清單欄位
BATCH_COLS = ("#", "檔案名稱", "路徑", "狀態")
COL_WIDTHS  = (40,  220,       380,   80)

# 狀態標籤顏色 (tag → foreground)
STATUS_COLORS = {
    "等待中": "#888888",
    "轉換中": "#E8A838",
    "完成":   "#3BAA6E",
    "失敗":   "#D94F4F",
}


# ── 設定對話框 ────────────────────────────────────────────────────────────────

# ── 套件安裝輔助對話框 ────────────────────────────────────────────────────────

class PackageInstallDialog(ctk.CTkToplevel):
    """顯示缺少套件的安裝指令，並可一鍵自動安裝。"""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("需要安裝套件")
        self.geometry("600x480")
        self.resizable(False, False)
        self.grab_set()
        self.lift()
        self.focus_force()

        self._installed = False   # True after pip succeeds
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # ── Title ─────────────────────────────────────────────────────────────
        ctk.CTkLabel(self, text="需要安裝 openai-whisper 套件",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     ).grid(row=0, column=0, padx=24, pady=(20, 4), sticky="w")

        ctk.CTkLabel(self,
                     text="本機 Whisper 音訊轉文字功能需要以下套件與工具。",
                     font=ctk.CTkFont(size=12),
                     text_color=("gray45", "gray60"),
                     ).grid(row=1, column=0, padx=24, pady=(0, 12), sticky="w")

        # ── Commands ──────────────────────────────────────────────────────────
        cmds_frame = ctk.CTkFrame(self, corner_radius=8)
        cmds_frame.grid(row=2, column=0, padx=24, sticky="ew")
        cmds_frame.grid_columnconfigure(1, weight=1)

        # pip install
        ctk.CTkLabel(cmds_frame, text="① Python 套件",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     ).grid(row=0, column=0, columnspan=3, padx=14, pady=(12, 4), sticky="w")

        pip_cmd = "pip install openai-whisper"
        ctk.CTkEntry(cmds_frame, fg_color=("gray85", "gray20"),
                     border_width=0, state="readonly",
                     font=ctk.CTkFont(family="Consolas", size=12),
                     textvariable=ctk.StringVar(value=pip_cmd),
                     height=32,
                     ).grid(row=1, column=0, columnspan=1, padx=(14, 4), pady=(0, 8), sticky="ew")

        ctk.CTkButton(cmds_frame, text="複製", width=62, height=32,
                      fg_color=("gray75", "gray30"),
                      hover_color=("gray60", "gray40"),
                      text_color=("gray10", "gray90"),
                      command=lambda: self._copy(pip_cmd),
                      ).grid(row=1, column=1, padx=4, pady=(0, 8))

        self._install_btn = ctk.CTkButton(
            cmds_frame, text="立即安裝", width=90, height=32,
            command=self._run_install,
        )
        self._install_btn.grid(row=1, column=2, padx=(4, 14), pady=(0, 8))

        # ffmpeg
        ctk.CTkLabel(cmds_frame, text="② ffmpeg（Windows）",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     ).grid(row=2, column=0, columnspan=3, padx=14, pady=(4, 4), sticky="w")

        winget_cmd = "winget install ffmpeg"
        ctk.CTkEntry(cmds_frame, fg_color=("gray85", "gray20"),
                     border_width=0, state="readonly",
                     font=ctk.CTkFont(family="Consolas", size=12),
                     textvariable=ctk.StringVar(value=winget_cmd),
                     height=32,
                     ).grid(row=3, column=0, padx=(14, 4), pady=(0, 4), sticky="ew")

        ctk.CTkButton(cmds_frame, text="複製", width=62, height=32,
                      fg_color=("gray75", "gray30"),
                      hover_color=("gray60", "gray40"),
                      text_color=("gray10", "gray90"),
                      command=lambda: self._copy(winget_cmd),
                      ).grid(row=3, column=1, padx=4, pady=(0, 4))

        ctk.CTkLabel(cmds_frame,
                     text="（亦可至 https://ffmpeg.org/download.html 手動安裝）",
                     font=ctk.CTkFont(size=10),
                     text_color=("gray45", "gray60"),
                     ).grid(row=4, column=0, columnspan=3,
                            padx=14, pady=(0, 12), sticky="w")

        # ── Log area ──────────────────────────────────────────────────────────
        ctk.CTkLabel(self, text="安裝輸出",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     ).grid(row=3, column=0, padx=24, pady=(10, 2), sticky="w")

        self._log = ctk.CTkTextbox(self,
                                   font=ctk.CTkFont(family="Consolas", size=11),
                                   state="disabled",
                                   wrap="word",
                                   height=110)
        self._log.grid(row=4, column=0, padx=24, sticky="nsew", pady=(0, 8))

        # ── Bottom bar ────────────────────────────────────────────────────────
        bot = ctk.CTkFrame(self, fg_color="transparent")
        bot.grid(row=5, column=0, padx=24, pady=(4, 16), sticky="ew")
        bot.grid_columnconfigure(0, weight=1)

        self._hint_lbl = ctk.CTkLabel(bot, text="",
                                      font=ctk.CTkFont(size=11),
                                      text_color=("gray45", "gray60"),
                                      anchor="w")
        self._hint_lbl.grid(row=0, column=0, sticky="w")

        ctk.CTkButton(bot, text="關閉", width=90,
                      command=self.destroy,
                      ).grid(row=0, column=1)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _copy(self, text: str):
        self.clipboard_clear()
        self.clipboard_append(text)
        self._hint_lbl.configure(text="✔  已複製到剪貼簿")

    def _append_log(self, text: str):
        self._log.configure(state="normal")
        self._log.insert("end", text)
        self._log.see("end")
        self._log.configure(state="disabled")

    def _run_install(self):
        self._install_btn.configure(state="disabled", text="安裝中…")
        self._hint_lbl.configure(text="正在執行 pip install openai-whisper…")
        self._append_log("$ pip install openai-whisper\n")

        def worker():
            try:
                proc = subprocess.Popen(
                    [sys.executable, "-m", "pip", "install", "openai-whisper"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                for line in proc.stdout:
                    self.after(0, lambda l=line: self._append_log(l))
                proc.wait()
                if proc.returncode == 0:
                    self.after(0, self._on_install_ok)
                else:
                    self.after(0, lambda: self._on_install_fail(proc.returncode))
            except Exception as exc:
                self.after(0, lambda: self._on_install_fail(str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_install_ok(self):
        self._installed = True
        self._install_btn.configure(state="disabled", text="已安裝 ✔")
        self._hint_lbl.configure(
            text="✔  安裝完成！記得也要安裝 ffmpeg，然後關閉此視窗重新轉換。",
            text_color="#3BAA6E",
        )
        self._append_log("\n✔  安裝完成！\n")

    def _on_install_fail(self, reason):
        self._install_btn.configure(state="normal", text="重試安裝")
        self._hint_lbl.configure(
            text=f"✘  安裝失敗（{reason}），請手動在終端機執行安裝指令。",
            text_color="#D94F4F",
        )


LOCAL_MODELS = {
    "tiny":   "~75 MB，速度最快，適合短音訊",
    "base":   "~145 MB，推薦，速度與精準度平衡",
    "small":  "~480 MB，精準度佳",
    "medium": "~1.5 GB，高精準度",
    "large":  "~3 GB，最高精準度，需較多記憶體",
}


class SettingsDialog(ctk.CTkToplevel):
    """音訊轉錄設定：本機 Whisper（免費）或 OpenAI API（需 Key）。"""

    def __init__(self, parent, mode: str = "local",
                 model_size: str = "base", api_key: str = ""):
        super().__init__(parent)
        self.title("音訊轉錄設定")
        self.geometry("580x420")
        self.resizable(False, False)
        self.grab_set()
        self.lift()
        self.focus_force()

        self._cancelled = True
        self.grid_columnconfigure(0, weight=1)

        # ── Title ─────────────────────────────────────────────────────────────
        ctk.CTkLabel(self, text="音訊轉錄設定",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     ).grid(row=0, column=0, padx=24, pady=(20, 2), sticky="w")

        ctk.CTkLabel(self,
                     text="選擇音訊（MP3、WAV、MP4…）轉文字的方式。其他格式不受影響。",
                     font=ctk.CTkFont(size=12),
                     text_color=("gray45", "gray60"),
                     ).grid(row=1, column=0, padx=24, pady=(0, 14), sticky="w")

        # ── Mode selector ─────────────────────────────────────────────────────
        self._mode_var = ctk.StringVar(value=mode)
        seg = ctk.CTkSegmentedButton(
            self,
            values=["本機 Whisper（免費）", "OpenAI API（需 Key）"],
            variable=self._mode_var,
            command=self._on_mode_change,
            font=ctk.CTkFont(size=13),
        )
        seg.grid(row=2, column=0, padx=24, pady=(0, 16), sticky="ew")

        # ── Local panel ───────────────────────────────────────────────────────
        self._local_frame = ctk.CTkFrame(self, corner_radius=8)
        self._local_frame.grid(row=3, column=0, padx=24, sticky="ew")
        self._local_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self._local_frame, text="模型大小：",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     ).grid(row=0, column=0, padx=(14, 8), pady=12)

        self._model_var = ctk.StringVar(value=model_size)
        ctk.CTkComboBox(self._local_frame,
                        values=list(LOCAL_MODELS.keys()),
                        variable=self._model_var,
                        command=self._on_model_change,
                        width=130,
                        ).grid(row=0, column=1, padx=4, pady=12, sticky="w")

        self._model_info = ctk.CTkLabel(
            self._local_frame,
            text=LOCAL_MODELS.get(model_size, ""),
            font=ctk.CTkFont(size=11),
            text_color=("gray45", "gray60"),
        )
        self._model_info.grid(row=0, column=2, padx=(4, 14), pady=12, sticky="w")

        ctk.CTkLabel(self._local_frame,
                     text="首次使用時會自動下載模型（需網路）。之後可離線使用。\n"
                          "另需安裝 ffmpeg：https://ffmpeg.org/download.html",
                     font=ctk.CTkFont(size=11),
                     text_color=("gray45", "gray60"),
                     justify="left",
                     ).grid(row=1, column=0, columnspan=3, padx=14, pady=(0, 12), sticky="w")

        # ── API panel ─────────────────────────────────────────────────────────
        self._api_frame = ctk.CTkFrame(self, corner_radius=8)
        self._api_frame.grid(row=3, column=0, padx=24, sticky="ew")
        self._api_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self._api_frame, text="OpenAI API Key",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     ).grid(row=0, column=0, padx=14, pady=(12, 4), sticky="w")

        self._key_var = ctk.StringVar(value=api_key)
        self._key_entry = ctk.CTkEntry(
            self._api_frame,
            textvariable=self._key_var,
            placeholder_text="sk-…",
            show="•",
            height=36,
            font=ctk.CTkFont(size=13),
        )
        self._key_entry.grid(row=1, column=0, padx=14, pady=(0, 6), sticky="ew")

        hint_row = ctk.CTkFrame(self._api_frame, fg_color="transparent")
        hint_row.grid(row=2, column=0, padx=14, pady=(0, 12), sticky="w")

        self._show_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(hint_row, text="顯示金鑰",
                        variable=self._show_var,
                        command=lambda: self._key_entry.configure(
                            show="" if self._show_var.get() else "•"),
                        font=ctk.CTkFont(size=11),
                        ).pack(side="left")

        ctk.CTkLabel(hint_row,
                     text="金鑰僅存於記憶體，關閉程式後不留存。",
                     font=ctk.CTkFont(size=10),
                     text_color=("gray50", "gray60"),
                     ).pack(side="left", padx=(14, 0))

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=4, column=0, padx=24, pady=(18, 20), sticky="e")

        ctk.CTkButton(btn_row, text="取消", width=90,
                      fg_color=("gray75", "gray30"),
                      hover_color=("gray60", "gray40"),
                      text_color=("gray10", "gray90"),
                      command=self.destroy,
                      ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(btn_row, text="儲存", width=90,
                      command=self._save,
                      ).pack(side="left")

        # init panel visibility
        self._on_mode_change(mode)

    def _on_mode_change(self, value: str):
        is_local = value.startswith("本機")
        if is_local:
            self._api_frame.grid_remove()
            self._local_frame.grid()
        else:
            self._local_frame.grid_remove()
            self._api_frame.grid()

    def _on_model_change(self, value: str):
        self._model_info.configure(text=LOCAL_MODELS.get(value, ""))

    def _save(self):
        self._cancelled = False
        self.destroy()

    @property
    def mode(self) -> str:
        return "local" if self._mode_var.get().startswith("本機") else "api"

    @property
    def model_size(self) -> str:
        return self._model_var.get()

    @property
    def api_key(self) -> str:
        return self._key_var.get().strip()


# ── 主視窗 ────────────────────────────────────────────────────────────────────

class MarkItDownApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("微軟文件轉 Markdown 工具")
        self.geometry("1020x760")
        self.minsize(820, 620)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._whisper_mode: str = "local"   # "local" or "api"
        self._whisper_model: str = "base"   # tiny/base/small/medium/large
        self._openai_key: str = ""          # used only when mode == "api"

        self._build_header()
        self._build_tabs()
        self._build_footer()

        if not MARKITDOWN_AVAILABLE:
            self._show_install_warning()

    # ── Header ───────────────────────────────────────────────────────────────

    def _build_header(self):
        hf = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray88", "gray14"))
        hf.grid(row=0, column=0, sticky="ew")
        hf.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(hf, text="微軟文件轉 Markdown 工具",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     ).grid(row=0, column=0, pady=(16, 4))

        ctk.CTkLabel(hf, text=FORMAT_INFO,
                     font=ctk.CTkFont(size=12),
                     text_color=("gray45", "gray65"),
                     justify="center",
                     ).grid(row=1, column=0, pady=(0, 14))

        # Settings button — top-right corner (spans both rows)
        self._settings_btn = ctk.CTkButton(
            hf, text="⚙  轉錄設定", width=110, height=32,
            font=ctk.CTkFont(size=12),
            fg_color=("gray75", "gray28"),
            hover_color=("gray60", "gray38"),
            text_color=("gray10", "gray90"),
            command=self._open_settings,
        )
        self._settings_btn.grid(row=0, column=1, rowspan=2, padx=(0, 16), pady=0)

    # ── Tab view ─────────────────────────────────────────────────────────────

    def _build_tabs(self):
        self._tabs = ctk.CTkTabview(self, anchor="nw")
        self._tabs.grid(row=1, column=0, sticky="nsew", padx=16, pady=(10, 6))
        self._tabs.grid_columnconfigure(0, weight=1)

        self._tabs.add("單檔轉換")
        self._tabs.add("批次轉換")

        self._tabs.tab("單檔轉換").grid_columnconfigure(0, weight=1)
        self._tabs.tab("單檔轉換").grid_rowconfigure(1, weight=1)

        self._tabs.tab("批次轉換").grid_columnconfigure(0, weight=1)
        self._tabs.tab("批次轉換").grid_rowconfigure(2, weight=1)

        self._build_single_tab(self._tabs.tab("單檔轉換"))
        self._build_batch_tab(self._tabs.tab("批次轉換"))

    # ════════════════════════════════════════════════════════════════════════
    #  單檔轉換 tab
    # ════════════════════════════════════════════════════════════════════════

    def _build_single_tab(self, parent):
        # ── Input row ────────────────────────────────────────────────────────
        row = ctk.CTkFrame(parent, corner_radius=10)
        row.grid(row=0, column=0, sticky="ew", pady=(4, 10))
        row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(row, text="來源：",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     ).grid(row=0, column=0, padx=(14, 8), pady=12)

        self._s_input = ctk.StringVar()
        ctk.CTkEntry(row, textvariable=self._s_input,
                     placeholder_text="輸入檔案路徑、YouTube URL 或其他支援來源…",
                     height=38, font=ctk.CTkFont(size=13),
                     ).grid(row=0, column=1, padx=4, pady=12, sticky="ew")

        ctk.CTkButton(row, text="瀏覽", width=80, height=38,
                      fg_color=("gray75", "gray30"),
                      hover_color=("gray60", "gray40"),
                      text_color=("gray10", "gray90"),
                      command=self._s_browse,
                      ).grid(row=0, column=2, padx=4, pady=12)

        self._s_btn = ctk.CTkButton(row, text="▶  轉換", width=100, height=38,
                                    font=ctk.CTkFont(size=13, weight="bold"),
                                    command=self._s_convert,
                                    )
        self._s_btn.grid(row=0, column=3, padx=(4, 14), pady=12)

        # ── Output area ──────────────────────────────────────────────────────
        out = ctk.CTkFrame(parent, corner_radius=10)
        out.grid(row=1, column=0, sticky="nsew")
        out.grid_columnconfigure(0, weight=1)
        out.grid_rowconfigure(1, weight=1)

        tb = ctk.CTkFrame(out, fg_color="transparent")
        tb.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 0))
        tb.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tb, text="Markdown 輸出",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     ).grid(row=0, column=0, sticky="w")

        for col, (label, cmd) in enumerate([
            ("清除",    self._s_clear),
            ("複製",    self._s_copy),
            ("儲存 .md", self._s_save),
        ], start=1):
            ctk.CTkButton(tb, text=label,
                          width=80 if label != "儲存 .md" else 90,
                          height=28,
                          fg_color=("gray75", "gray30") if label == "清除" else None,
                          hover_color=("gray60", "gray40") if label == "清除" else None,
                          text_color=("gray10", "gray90") if label == "清除" else None,
                          command=cmd,
                          ).grid(row=0, column=col, padx=4)

        self._s_textbox = ctk.CTkTextbox(out,
                                         font=ctk.CTkFont(family="Consolas", size=12),
                                         wrap="word")
        self._s_textbox.grid(row=1, column=0, sticky="nsew", padx=14, pady=(6, 14))

        # ── Status ───────────────────────────────────────────────────────────
        self._s_status_var = ctk.StringVar(value="就緒")
        self._s_status_lbl = ctk.CTkLabel(parent,
                                          textvariable=self._s_status_var,
                                          font=ctk.CTkFont(size=11),
                                          text_color=("gray45", "gray60"),
                                          anchor="w")
        self._s_status_lbl.grid(row=2, column=0, sticky="w", pady=(2, 2))

    # ════════════════════════════════════════════════════════════════════════
    #  批次轉換 tab
    # ════════════════════════════════════════════════════════════════════════

    def _build_batch_tab(self, parent):
        # ── Output folder ────────────────────────────────────────────────────
        dest_row = ctk.CTkFrame(parent, corner_radius=10)
        dest_row.grid(row=0, column=0, sticky="ew", pady=(4, 8))
        dest_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(dest_row, text="輸出資料夾：",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     ).grid(row=0, column=0, padx=(14, 8), pady=10)

        self._b_dest_var = ctk.StringVar(value="（與原檔同資料夾）")
        ctk.CTkEntry(dest_row, textvariable=self._b_dest_var,
                     height=34, font=ctk.CTkFont(size=12),
                     ).grid(row=0, column=1, padx=4, pady=10, sticky="ew")

        ctk.CTkButton(dest_row, text="選擇", width=70, height=34,
                      fg_color=("gray75", "gray30"),
                      hover_color=("gray60", "gray40"),
                      text_color=("gray10", "gray90"),
                      command=self._b_pick_dest,
                      ).grid(row=0, column=2, padx=4, pady=10)

        ctk.CTkButton(dest_row, text="重設", width=60, height=34,
                      fg_color=("gray75", "gray30"),
                      hover_color=("gray60", "gray40"),
                      text_color=("gray10", "gray90"),
                      command=lambda: self._b_dest_var.set("（與原檔同資料夾）"),
                      ).grid(row=0, column=3, padx=(4, 14), pady=10)

        # ── URL input row ─────────────────────────────────────────────────────
        url_row = ctk.CTkFrame(parent, corner_radius=10)
        url_row.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        url_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(url_row, text="新增網址：",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     ).grid(row=0, column=0, padx=(14, 8), pady=10)

        self._b_url_var = ctk.StringVar()
        url_entry = ctk.CTkEntry(url_row, textvariable=self._b_url_var,
                                 placeholder_text="貼上 YouTube、網頁或其他支援的 URL…",
                                 height=34, font=ctk.CTkFont(size=12))
        url_entry.grid(row=0, column=1, padx=4, pady=10, sticky="ew")
        url_entry.bind("<Return>", lambda _e: self._b_add_url())

        ctk.CTkButton(url_row, text="新增網址", width=90, height=34,
                      command=self._b_add_url,
                      ).grid(row=0, column=2, padx=(4, 14), pady=10)

        # ── File list + buttons ───────────────────────────────────────────────
        mid = ctk.CTkFrame(parent, corner_radius=10)
        mid.grid(row=2, column=0, sticky="nsew", pady=(0, 8))
        mid.grid_columnconfigure(0, weight=1)
        mid.grid_rowconfigure(1, weight=1)

        # Toolbar buttons
        btns = ctk.CTkFrame(mid, fg_color="transparent")
        btns.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 0))

        for label, cmd in [
            ("新增檔案",   self._b_add_files),
            ("新增資料夾", self._b_add_folder),
            ("移除選取",   self._b_remove_selected),
            ("清除全部",   self._b_clear_all),
        ]:
            ctk.CTkButton(btns, text=label, width=96, height=30,
                          fg_color=("gray75", "gray30") if "移除" in label or "清除" in label else None,
                          hover_color=("gray60", "gray40") if "移除" in label or "清除" in label else None,
                          text_color=("gray10", "gray90") if "移除" in label or "清除" in label else None,
                          command=cmd,
                          ).pack(side="left", padx=(0, 6))

        self._b_count_lbl = ctk.CTkLabel(btns, text="共 0 個項目",
                                         font=ctk.CTkFont(size=11),
                                         text_color=("gray45", "gray60"))
        self._b_count_lbl.pack(side="right")

        # Treeview (file list)
        tree_frame = ctk.CTkFrame(mid, fg_color="transparent")
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=14, pady=(6, 0))
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Batch.Treeview",
                        background="#2b2b2b",
                        foreground="white",
                        fieldbackground="#2b2b2b",
                        rowheight=24,
                        font=("Segoe UI", 11))
        style.configure("Batch.Treeview.Heading",
                        background="#3a3a3a",
                        foreground="white",
                        font=("Segoe UI", 11, "bold"),
                        relief="flat")
        style.map("Batch.Treeview",
                  background=[("selected", "#1f6aa5")],
                  foreground=[("selected", "white")])

        self._b_tree = ttk.Treeview(
            tree_frame,
            columns=BATCH_COLS,
            show="headings",
            selectmode="extended",
            style="Batch.Treeview",
        )
        for col, w in zip(BATCH_COLS, COL_WIDTHS):
            self._b_tree.heading(col, text=col)
            anchor = "center" if col in ("#", "狀態") else "w"
            self._b_tree.column(col, width=w, anchor=anchor,
                                 minwidth=30 if col == "#" else 80,
                                 stretch=(col == "路徑"))

        for tag, color in STATUS_COLORS.items():
            self._b_tree.tag_configure(tag, foreground=color)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                             command=self._b_tree.yview)
        self._b_tree.configure(yscrollcommand=vsb.set)
        self._b_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        # ── Progress + start ──────────────────────────────────────────────────
        bottom = ctk.CTkFrame(parent, corner_radius=10)
        bottom.grid(row=3, column=0, sticky="ew", pady=(0, 4))
        bottom.grid_columnconfigure(0, weight=1)

        prog_row = ctk.CTkFrame(bottom, fg_color="transparent")
        prog_row.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 4))
        prog_row.grid_columnconfigure(0, weight=1)

        self._b_progress = ctk.CTkProgressBar(prog_row, height=14)
        self._b_progress.set(0)
        self._b_progress.grid(row=0, column=0, sticky="ew", padx=(0, 12))

        self._b_pct_lbl = ctk.CTkLabel(prog_row, text="0%",
                                        font=ctk.CTkFont(size=11), width=40)
        self._b_pct_lbl.grid(row=0, column=1)

        action_row = ctk.CTkFrame(bottom, fg_color="transparent")
        action_row.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 10))
        action_row.grid_columnconfigure(1, weight=1)

        self._b_start_btn = ctk.CTkButton(
            action_row,
            text="▶  開始批次轉換",
            width=150, height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._b_start,
        )
        self._b_start_btn.grid(row=0, column=0, padx=(0, 12))

        self._b_status_var = ctk.StringVar(value="就緒，請新增要轉換的檔案")
        ctk.CTkLabel(action_row,
                     textvariable=self._b_status_var,
                     font=ctk.CTkFont(size=11),
                     text_color=("gray45", "gray60"),
                     anchor="w",
                     ).grid(row=0, column=1, sticky="w")

        # internal state — stores file path strings and URLs mixed
        self._b_sources: list[str] = []
        self._b_running = False

    # ── Footer ───────────────────────────────────────────────────────────────

    def _build_footer(self):
        ff = ctk.CTkFrame(self, corner_radius=0,
                          fg_color=("gray88", "gray14"), height=48)
        ff.grid(row=2, column=0, sticky="ew")
        ff.grid_propagate(False)
        ff.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(ff, text="Made by ",
                     font=ctk.CTkFont(size=12),
                     ).grid(row=0, column=0, padx=(18, 0))

        link = ctk.CTkLabel(ff, text="阿剛老師",
                            font=ctk.CTkFont(size=12, underline=True),
                            text_color=("#1565C0", "#64B5F6"),
                            cursor="hand2")
        link.grid(row=0, column=1, padx=(0, 18))
        link.bind("<Button-1>", lambda _e: webbrowser.open(BLOG_URL, new=2))

        ctk.CTkLabel(ff,
                     text=("本程式以 CC BY-NC-SA 4.0 授權釋出｜"
                           "允許非商業使用、分享與改作｜須署名並以相同條件分享"),
                     font=ctk.CTkFont(size=10),
                     text_color=("gray45", "gray60"),
                     anchor="e",
                     ).grid(row=0, column=2, padx=18, sticky="e")

    # ════════════════════════════════════════════════════════════════════════
    #  單檔 actions
    # ════════════════════════════════════════════════════════════════════════

    def _s_browse(self):
        path = filedialog.askopenfilename(title="選擇要轉換的檔案",
                                          filetypes=FILETYPES)
        if path:
            self._s_input.set(path)

    def _s_convert(self):
        source = self._s_input.get().strip()
        if not source:
            messagebox.showwarning("請輸入來源", "請先輸入檔案路徑或網址。")
            return
        if not MARKITDOWN_AVAILABLE:
            self._no_markitdown()
            return
        if self._is_audio(source) and self._needs_whisper_install():
            self._show_whisper_install_dialog()
            return

        self._s_btn.configure(state="disabled", text="轉換中…")
        self._s_set_status("轉換中，請稍候…", color="orange")
        self._s_textbox.delete("1.0", "end")

        def worker():
            try:
                text = self._convert_source(source)
                self.after(0, lambda: self._s_on_ok(text, source))
            except Exception as exc:
                msg = str(exc)
                self.after(0, lambda: self._s_on_err(msg))

        threading.Thread(target=worker, daemon=True).start()

    def _s_on_ok(self, text: str, source: str):
        self._s_textbox.delete("1.0", "end")
        self._s_textbox.insert("1.0", text)
        lines = text.count("\n") + 1
        name = Path(source).name if os.path.exists(source) else source[:60]
        self._s_set_status(f"✔  {name}　│　{lines} 行 / {len(text):,} 字元")
        self._s_btn.configure(state="normal", text="▶  轉換")

    def _s_on_err(self, msg: str):
        self._s_textbox.insert("1.0", f"【轉換失敗】\n\n{msg}")
        self._s_set_status(f"✘  {msg[:120]}", color="red")
        self._s_btn.configure(state="normal", text="▶  轉換")

    def _s_clear(self):
        self._s_textbox.delete("1.0", "end")
        self._s_set_status("已清除")

    def _s_copy(self):
        text = self._s_textbox.get("1.0", "end-1c")
        if not text:
            messagebox.showinfo("提示", "目前沒有可複製的內容。")
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        self._s_set_status("✔  已複製到剪貼簿")

    def _s_save(self):
        text = self._s_textbox.get("1.0", "end-1c")
        if not text:
            messagebox.showinfo("提示", "目前沒有可儲存的內容。")
            return
        path = filedialog.asksaveasfilename(
            title="儲存 Markdown 檔案",
            defaultextension=".md",
            filetypes=[("Markdown 文件", "*.md"),
                       ("純文字", "*.txt"),
                       ("所有檔案", "*.*")])
        if path:
            Path(path).write_text(text, encoding="utf-8")
            self._s_set_status(f"✔  已儲存：{path}")

    def _s_set_status(self, msg: str, color=None):
        self._s_status_var.set(msg)
        self._s_status_lbl.configure(
            text_color=color if color else ("gray45", "gray60"))

    # ════════════════════════════════════════════════════════════════════════
    #  批次 actions
    # ════════════════════════════════════════════════════════════════════════

    # ── URL helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _is_url(s: str) -> bool:
        return s.startswith("http://") or s.startswith("https://")

    @staticmethod
    def _url_to_stem(url: str) -> str:
        """Derive a safe filename stem from a URL."""
        # YouTube
        yt = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", url)
        if yt:
            return f"youtube_{yt.group(1)}"
        parsed = urlparse(url)
        # Last non-empty path segment
        parts = [p for p in parsed.path.split("/") if p]
        if parts:
            stem = parts[-1]
            # strip common extensions
            stem = re.sub(r"\.[a-zA-Z0-9]{1,5}$", "", stem)
            stem = re.sub(r"[^\w\-]", "_", stem)
            if stem:
                return stem[:60]
        # Fallback: domain
        domain = parsed.netloc.replace("www.", "").replace(".", "_")
        return domain[:60] or "url_output"

    # ── Batch actions ─────────────────────────────────────────────────────────

    def _b_add_url(self):
        url = self._b_url_var.get().strip()
        if not url:
            return
        if not self._is_url(url):
            messagebox.showwarning("格式不符",
                                   "請輸入以 http:// 或 https:// 開頭的網址。")
            return
        added = self._b_enqueue([url])
        if added:
            self._b_url_var.set("")

    def _b_add_files(self):
        paths = filedialog.askopenfilenames(title="選擇要轉換的檔案",
                                            filetypes=FILETYPES)
        self._b_enqueue([str(p) for p in paths])

    def _b_add_folder(self):
        folder = filedialog.askdirectory(title="選擇要批次轉換的資料夾")
        if not folder:
            return
        files = [p for p in Path(folder).rglob("*")
                 if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS]
        if not files:
            messagebox.showinfo("找不到支援的檔案",
                                "在所選資料夾內找不到任何支援的檔案格式。\n\n"
                                f"支援的副檔名：{', '.join(sorted(SUPPORTED_EXTS))}")
            return
        self._b_enqueue([str(p) for p in sorted(files)])

    def _b_enqueue(self, sources: list[str]) -> int:
        existing = set(self._b_sources)
        added = 0
        for src in sources:
            if src in existing:
                continue
            self._b_sources.append(src)
            existing.add(src)
            idx = len(self._b_sources)
            if self._is_url(src):
                display_name = self._url_to_stem(src)
                display_path = src
            else:
                p = Path(src)
                display_name = p.name
                display_path = str(p.parent)
            self._b_tree.insert("", "end",
                                 values=(idx, display_name, display_path, "等待中"),
                                 tags=("等待中",))
            added += 1
        self._b_refresh_count()
        if added:
            self._b_status_var.set(
                f"已新增 {added} 個項目，共 {len(self._b_sources)} 個")
        return added

    def _b_remove_selected(self):
        selected = self._b_tree.selection()
        if not selected:
            return
        indices = sorted(
            [self._b_tree.index(iid) for iid in selected],
            reverse=True,
        )
        for idx in indices:
            self._b_sources.pop(idx)
            self._b_tree.delete(self._b_tree.get_children()[idx])
        for i, iid in enumerate(self._b_tree.get_children(), start=1):
            vals = list(self._b_tree.item(iid, "values"))
            vals[0] = i
            self._b_tree.item(iid, values=vals)
        self._b_refresh_count()

    def _b_clear_all(self):
        if not self._b_sources:
            return
        if not messagebox.askyesno("確認清除", "確定要清除所有項目嗎？"):
            return
        self._b_sources.clear()
        for iid in self._b_tree.get_children():
            self._b_tree.delete(iid)
        self._b_refresh_count()
        self._b_progress.set(0)
        self._b_pct_lbl.configure(text="0%")
        self._b_status_var.set("就緒，請新增要轉換的檔案或網址")

    def _b_refresh_count(self):
        n = len(self._b_sources)
        self._b_count_lbl.configure(text=f"共 {n} 個項目")

    def _b_pick_dest(self):
        folder = filedialog.askdirectory(title="選擇輸出資料夾")
        if folder:
            self._b_dest_var.set(folder)

    def _b_start(self):
        if self._b_running:
            return
        if not self._b_sources:
            messagebox.showwarning("清單為空", "請先新增要轉換的檔案或網址。")
            return
        if not MARKITDOWN_AVAILABLE:
            self._no_markitdown()
            return
        has_audio = any(self._is_audio(s) for s in self._b_sources)
        if has_audio and self._needs_whisper_install():
            self._show_whisper_install_dialog()
            return

        dest_text = self._b_dest_var.get().strip()
        dest_fixed = None if dest_text.startswith("（") else Path(dest_text)

        # URLs need an explicit output folder
        has_urls = any(self._is_url(s) for s in self._b_sources)
        if has_urls and dest_fixed is None:
            messagebox.showwarning(
                "請指定輸出資料夾",
                "清單中包含網址，無法使用「與原檔同資料夾」。\n"
                "請在上方選擇一個輸出資料夾後再開始轉換。",
            )
            return

        if dest_fixed and not dest_fixed.exists():
            try:
                dest_fixed.mkdir(parents=True)
            except Exception as exc:
                messagebox.showerror("無法建立資料夾", str(exc))
                return

        # reset all rows
        for iid in self._b_tree.get_children():
            vals = list(self._b_tree.item(iid, "values"))
            vals[3] = "等待中"
            self._b_tree.item(iid, values=vals, tags=("等待中",))

        self._b_running = True
        self._b_start_btn.configure(state="disabled", text="轉換中…")
        self._b_progress.set(0)
        self._b_pct_lbl.configure(text="0%")

        total = len(self._b_sources)
        sources_snapshot = list(self._b_sources)
        iids = list(self._b_tree.get_children())

        def worker():
            ok = fail = 0
            for i, (src, iid) in enumerate(zip(sources_snapshot, iids)):
                display = (self._url_to_stem(src) if self._is_url(src)
                           else Path(src).name)
                self.after(0, lambda iid=iid: self._b_set_row_status(iid, "轉換中"))
                self.after(0, lambda d=display, i=i: self._b_status_var.set(
                    f"轉換中 {i+1}/{total}：{d}"))
                try:
                    text = self._convert_source(src)
                    stem = (self._url_to_stem(src) if self._is_url(src)
                            else Path(src).stem)
                    out_dir = dest_fixed if dest_fixed else Path(src).parent
                    out_path = out_dir / f"{stem}.md"
                    counter = 1
                    while out_path.exists():
                        out_path = out_dir / f"{stem}_{counter}.md"
                        counter += 1
                    out_path.write_text(text, encoding="utf-8")
                    ok += 1
                    self.after(0, lambda iid=iid: self._b_set_row_status(iid, "完成"))
                except Exception:
                    fail += 1
                    self.after(0, lambda iid=iid: self._b_set_row_status(iid, "失敗"))

                pct = (i + 1) / total
                self.after(0, lambda p=pct: self._b_update_progress(p))

            self.after(0, lambda: self._b_on_done(ok, fail, total))

        threading.Thread(target=worker, daemon=True).start()

    def _b_set_row_status(self, iid: str, status: str):
        vals = list(self._b_tree.item(iid, "values"))
        vals[3] = status
        self._b_tree.item(iid, values=vals, tags=(status,))
        self._b_tree.see(iid)

    def _b_update_progress(self, pct: float):
        self._b_progress.set(pct)
        self._b_pct_lbl.configure(text=f"{int(pct * 100)}%")

    def _b_on_done(self, ok: int, fail: int, total: int):
        self._b_running = False
        self._b_start_btn.configure(state="normal", text="▶  開始批次轉換")
        summary = f"✔  完成：{ok} 成功"
        if fail:
            summary += f"　✘  {fail} 失敗"
        summary += f"　（共 {total} 個）"
        self._b_status_var.set(summary)
        messagebox.showinfo("批次轉換完成", summary.replace("　", "\n"))

    # ── Shared helpers ────────────────────────────────────────────────────────

    def _open_settings(self):
        dlg = SettingsDialog(self,
                             mode=self._whisper_mode,
                             model_size=self._whisper_model,
                             api_key=self._openai_key)
        self.wait_window(dlg)
        if dlg._cancelled:
            return
        self._whisper_mode = dlg.mode
        self._whisper_model = dlg.model_size
        self._openai_key = dlg.api_key
        self._settings_btn.configure(text="⚙  轉錄設定 ✔")

    def _is_audio(self, source: str) -> bool:
        return Path(source).suffix.lower() in AUDIO_EXTS

    def _convert_source(self, source: str) -> str:
        """Route to Whisper (audio) or MarkItDown (everything else)."""
        if self._is_audio(source):
            return self._whisper_transcribe(source)
        md = MarkItDown(enable_plugins=False)
        result = md.convert(source)
        return result.text_content or "(無輸出內容)"

    def _whisper_transcribe(self, audio_path: str) -> str:
        if self._whisper_mode == "local":
            return self._whisper_local(audio_path)
        return self._whisper_api(audio_path)

    def _whisper_local(self, audio_path: str) -> str:
        """Transcribe using local openai-whisper model (no API key needed)."""
        try:
            import whisper
        except ImportError:
            raise RuntimeError("找不到 openai-whisper 套件，請先透過安裝對話框安裝。")
        p = Path(audio_path)
        model = whisper.load_model(self._whisper_model)
        result = model.transcribe(str(audio_path))
        text = result.get("text", "").strip()
        detected_lang = result.get("language", "")
        lang_note = f"**偵測語言：** {detected_lang}  \n" if detected_lang else ""
        return (
            f"# 音訊轉文字\n\n"
            f"**檔案：** {p.name}  \n"
            f"**大小：** {p.stat().st_size / 1024:.1f} KB  \n"
            f"{lang_note}"
            f"**模型：** whisper-{self._whisper_model}\n\n"
            f"---\n\n"
            f"## 逐字稿\n\n"
            f"{text}\n"
        )

    def _whisper_api(self, audio_path: str) -> str:
        """Transcribe via OpenAI Whisper cloud API."""
        if not self._openai_key:
            raise RuntimeError(
                "尚未設定 OpenAI API Key。\n\n"
                "請點擊右上角「⚙ 轉錄設定」，輸入 API Key，\n"
                "或切換為「本機 Whisper」模式（不需 Key）。"
            )
        try:
            from openai import OpenAI
        except ImportError:
            raise RuntimeError(
                "找不到 openai 套件。\n\n請執行：pip install openai"
            )
        client = OpenAI(api_key=self._openai_key)
        p = Path(audio_path)
        with open(audio_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="text",
            )
        text = transcript if isinstance(transcript, str) else transcript.text
        return (
            f"# 音訊轉文字\n\n"
            f"**檔案：** {p.name}  \n"
            f"**大小：** {p.stat().st_size / 1024:.1f} KB  \n"
            f"**模型：** whisper-1 (OpenAI API)\n\n"
            f"---\n\n"
            f"## 逐字稿\n\n"
            f"{text}\n"
        )

    def _needs_whisper_install(self) -> bool:
        """True when mode is local and openai-whisper is not installed."""
        return (self._whisper_mode == "local"
                and importlib.util.find_spec("whisper") is None)

    def _show_whisper_install_dialog(self):
        dlg = PackageInstallDialog(self)
        self.wait_window(dlg)

    def _no_markitdown(self):
        messagebox.showerror(
            "套件未安裝",
            "找不到 markitdown 套件。\n\n"
            "請在終端機執行：\n"
            "  pip install \"markitdown[all]\"",
        )

    def _show_install_warning(self):
        self.after(200, lambda: messagebox.showwarning(
            "套件未安裝",
            "找不到 markitdown 套件，轉換功能將無法使用。\n\n"
            "請在終端機執行：\n"
            "  pip install \"markitdown[all]\"\n\n"
            "安裝完成後重新啟動程式即可。",
        ))


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")
    app = MarkItDownApp()
    app.mainloop()


if __name__ == "__main__":
    main()
