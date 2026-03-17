"""
Виджет выбора целевого формата.
Обновляет список доступных форматов в зависимости от загруженных файлов.
"""
from __future__ import annotations

from pathlib import Path

import customtkinter as ctk

from core.format_registry import get_supported_outputs


class FormatSelector(ctk.CTkFrame):
    """Выпадающий список форматов с подписью."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Конвертировать в:", font=ctk.CTkFont(size=13)).pack(
            side="left", padx=(0, 10)
        )
        self._var = ctk.StringVar(value="—")
        self._menu = ctk.CTkOptionMenu(
            self,
            variable=self._var,
            values=["—"],
            width=140,
            dynamic_resizing=False,
        )
        self._menu.pack(side="left")

    def update_formats(self, files: list[Path]) -> None:
        """Пересчитывает доступные форматы по набору файлов."""
        if not files:
            self._set_formats([])
            return

        # Пересечение доступных форматов для всех файлов
        sets = []
        for f in files:
            ext = f.suffix.lstrip(".").lower()
            outs = get_supported_outputs(ext)
            sets.append(set(outs))

        common = sorted(set.intersection(*sets)) if sets else []
        self._set_formats(common)

    def _set_formats(self, formats: list[str]) -> None:
        if formats:
            upper = [f.upper() for f in formats]
            self._menu.configure(values=upper)
            self._var.set(upper[0])
        else:
            self._menu.configure(values=["—"])
            self._var.set("—")

    def get_format(self) -> str | None:
        """Возвращает выбранный формат (lowercase) или None."""
        val = self._var.get()
        return val.lower() if val != "—" else None
