"""
Зона перетаскивания файлов (Drag & Drop).
Использует tkinterdnd2 для нативного DnD на Windows.
"""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from typing import Callable

import customtkinter as ctk

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False


class DropZone(ctk.CTkFrame):
    """
    Прямоугольная область для перетаскивания файлов.
    При drop вызывает on_files_dropped(list[Path]).
    """

    def __init__(
        self,
        master,
        on_files_dropped: Callable[[list[Path]], None],
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self._callback = on_files_dropped
        self._build()

    def _build(self):
        self.configure(
            corner_radius=12,
            border_width=2,
            border_color=("#4a9eff", "#2d7dd2"),
            fg_color=("#f0f7ff", "#1a2a3a"),
        )
        self._label = ctk.CTkLabel(
            self,
            text="Перетащите файлы сюда\nили нажмите для выбора",
            font=ctk.CTkFont(size=14),
            text_color=("#4a9eff", "#6bb8ff"),
            justify="center",
        )
        self._label.pack(expand=True, fill="both", padx=20, pady=30)

        # Клик для открытия диалога
        self._label.bind("<Button-1>", self._open_dialog)
        self.bind("<Button-1>", self._open_dialog)

        # Drag & Drop
        if DND_AVAILABLE:
            self.drop_target_register(DND_FILES)
            self.dnd_bind("<<Drop>>", self._on_dnd_drop)
            self.dnd_bind("<<DragEnter>>", self._on_drag_enter)
            self.dnd_bind("<<DragLeave>>", self._on_drag_leave)

    def _on_dnd_drop(self, event):
        self._reset_style()
        paths = self._parse_dnd_data(event.data)
        if paths:
            self._callback(paths)

    def _on_drag_enter(self, event):
        self.configure(border_color=("#ff9f2d", "#ff9f2d"))

    def _on_drag_leave(self, event):
        self._reset_style()

    def _reset_style(self):
        self.configure(border_color=("#4a9eff", "#2d7dd2"))

    def _open_dialog(self, event=None):
        from tkinter import filedialog
        files = filedialog.askopenfilenames(title="Выберите файлы")
        if files:
            self._callback([Path(f) for f in files])

    @staticmethod
    def _parse_dnd_data(data: str) -> list[Path]:
        """Парсит строку DnD: файлы могут быть в фигурных скобках или разделены пробелом."""
        import re
        paths = []
        # tkinterdnd2 оборачивает пути с пробелами в {}
        for token in re.findall(r'\{([^}]+)\}|(\S+)', data):
            p = token[0] or token[1]
            if p:
                paths.append(Path(p))
        return paths
