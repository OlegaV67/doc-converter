from __future__ import annotations

import os
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from core.converter_engine import ConverterEngine
from converters.base import ConversionError
from ui.drop_zone import DropZone
from ui.format_selector import FormatSelector
from utils.dependency_checker import missing as missing_deps

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# Совмещаем CustomTkinter с TkinterDnD для нативного Drag & Drop
try:
    from tkinterdnd2 import TkinterDnD

    class _AppBase(ctk.CTk, TkinterDnD.DnDWrapper):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.TkdndVersion = TkinterDnD._require(self)

except ImportError:
    _AppBase = ctk.CTk

_STATUS_COLORS = {
    "pending": ("#555555", "#aaaaaa"),
    "ok":      ("#1a7a3e", "#4caf7d"),
    "error":   ("#c0392b", "#e74c3c"),
    "running": ("#1a5a9a", "#4a9eff"),
}


class FileRow(ctk.CTkFrame):

    def __init__(self, master, file_path: Path, on_remove, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.file_path = file_path
        self._on_remove = on_remove
        self._build()

    def _build(self):
        ext = self.file_path.suffix.lstrip(".").upper() or "?"
        ctk.CTkLabel(
            self, text=ext, width=42,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=("#dce8ff", "#1e3a5f"),
            corner_radius=4,
            text_color=("#1a5aaa", "#6bb8ff"),
        ).pack(side="left", padx=(0, 8))

        name = self.file_path.name
        if len(name) > 42:
            name = name[:20] + "..." + name[-18:]
        ctk.CTkLabel(
            self, text=name, anchor="w",
            font=ctk.CTkFont(size=12),
        ).pack(side="left", fill="x", expand=True)

        self._status_label = ctk.CTkLabel(
            self, text="ожидание", width=80, anchor="e",
            font=ctk.CTkFont(size=11),
            text_color=_STATUS_COLORS["pending"],
        )
        self._status_label.pack(side="right", padx=(8, 4))

        ctk.CTkButton(
            self, text="x", width=24, height=24,
            fg_color="transparent",
            hover_color=("#ffdddd", "#5a1a1a"),
            text_color=("#888888", "#aaaaaa"),
            command=lambda: self._on_remove(self),
        ).pack(side="right")

    def set_status(self, status: str, text=None):
        color = _STATUS_COLORS.get(status, _STATUS_COLORS["pending"])
        labels = {
            "pending": "ожидание",
            "ok": "готово",
            "error": "ошибка",
            "running": "конвертирую...",
        }
        self._status_label.configure(
            text=text or labels.get(status, status),
            text_color=color,
        )


class App(_AppBase):

    def __init__(self):
        super().__init__()
        self.title("Doc Converter")
        self.geometry("620x640")
        self.minsize(500, 520)

        self._files: list[Path] = []
        self._rows: list[FileRow] = []
        self._output_dir: Path = None
        self._converting = False

        self._check_deps()
        self._build_ui()

    def _check_deps(self):
        import json, platform as _platform
        from pathlib import Path
        _sys = _platform.system()
        if _sys == "Windows":
            _base = Path(os.environ.get("APPDATA", Path.home()))
        elif _sys == "Darwin":
            _base = Path.home() / "Library" / "Application Support"
        else:
            _base = Path.home() / ".config"
        flag_file = _base / "DocConverter" / "deps_warned.json"

        absent = missing_deps()
        if not absent:
            return

        # Remember which engines were missing last time
        warned = set()
        if flag_file.exists():
            try:
                warned = set(json.loads(flag_file.read_text()))
            except Exception:
                pass

        absent_names = {d.name for d in absent}
        new_absent = absent_names - warned
        if not new_absent:
            return  # already warned about all of these

        names = "\n".join(
            f"  - {d.name}  ({d.install_url})" for d in absent if d.name in new_absent
        )
        messagebox.showwarning(
            "Не найдены зависимости",
            f"Следующие программы не установлены:\n\n{names}\n\nЧасть форматов будет недоступна.",
        )

        # Save updated warned set
        flag_file.parent.mkdir(parents=True, exist_ok=True)
        flag_file.write_text(json.dumps(list(absent_names)))

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(
            self, text="Doc Converter",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=0, pady=(20, 4), padx=24, sticky="w")

        ctk.CTkLabel(
            self,
            text="Конвертируйте офисные документы и электронные книги",
            font=ctk.CTkFont(size=12),
            text_color=("#666666", "#999999"),
        ).grid(row=1, column=0, padx=24, sticky="w")

        self._drop_zone = DropZone(
            self,
            on_files_dropped=self._on_files_added,
            height=100,
        )
        self._drop_zone.grid(row=2, column=0, padx=24, pady=(14, 0), sticky="ew")

        self._list_frame = ctk.CTkScrollableFrame(self, label_text="")
        self._list_frame.grid(row=3, column=0, padx=24, pady=(10, 0), sticky="nsew")
        self._list_frame.grid_columnconfigure(0, weight=1)

        self._empty_label = ctk.CTkLabel(
            self._list_frame,
            text="Добавьте файлы выше",
            text_color=("#aaaaaa", "#555555"),
            font=ctk.CTkFont(size=12),
        )
        self._empty_label.pack(pady=20)

        ctrl = ctk.CTkFrame(self, fg_color="transparent")
        ctrl.grid(row=4, column=0, padx=24, pady=(10, 0), sticky="ew")
        ctrl.grid_columnconfigure(1, weight=1)

        self._format_selector = FormatSelector(ctrl)
        self._format_selector.grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            ctrl, text="Папка сохранения", width=160,
            fg_color=("#e8e8e8", "#2a2a2a"),
            hover_color=("#d0d0d0", "#383838"),
            text_color=("#333333", "#cccccc"),
            command=self._choose_output_dir,
        ).grid(row=0, column=1, sticky="e")

        self._dir_label = ctk.CTkLabel(
            ctrl, text="Та же папка, что у файла",
            font=ctk.CTkFont(size=11),
            text_color=("#888888", "#777777"),
            anchor="e",
        )
        self._dir_label.grid(row=1, column=0, columnspan=2, sticky="e", pady=(2, 0))

        progress_row = ctk.CTkFrame(self, fg_color="transparent")
        progress_row.grid(row=5, column=0, padx=24, pady=(10, 0), sticky="ew")
        progress_row.grid_columnconfigure(0, weight=1)

        self._progress = ctk.CTkProgressBar(progress_row)
        self._progress.grid(row=0, column=0, sticky="ew")
        self._progress.set(0)

        self._progress_label = ctk.CTkLabel(
            progress_row, text="", width=60, anchor="e",
            font=ctk.CTkFont(size=11),
            text_color=("#888888", "#777777"),
        )
        self._progress_label.grid(row=0, column=1, padx=(8, 0))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=6, column=0, padx=24, pady=(10, 20), sticky="ew")
        btn_row.grid_columnconfigure(0, weight=1)

        self._clear_btn = ctk.CTkButton(
            btn_row, text="Очистить",
            fg_color=("#e8e8e8", "#2a2a2a"),
            hover_color=("#d0d0d0", "#383838"),
            text_color=("#333333", "#cccccc"),
            width=120,
            command=self._clear,
        )
        self._clear_btn.grid(row=0, column=0, sticky="w")

        self._open_folder_btn = ctk.CTkButton(
            btn_row, text="Открыть папку",
            fg_color=("#e8e8e8", "#2a2a2a"),
            hover_color=("#d0d0d0", "#383838"),
            text_color=("#333333", "#cccccc"),
            width=130,
            command=self._open_output_folder,
        )
        self._open_folder_btn.grid(row=0, column=1, padx=(8, 0))
        self._open_folder_btn.grid_remove()  # скрыта до завершения конвертации

        self._convert_btn = ctk.CTkButton(
            btn_row, text="Конвертировать",
            width=160, height=38,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._start_conversion,
        )
        self._convert_btn.grid(row=0, column=2, sticky="e")

    def _on_files_added(self, paths: list):
        added = 0
        for p in paths:
            if p not in self._files and p.is_file():
                self._files.append(p)
                self._add_row(p)
                added += 1
        if added:
            self._empty_label.pack_forget()
            self._format_selector.update_formats(self._files)

    def _add_row(self, path: Path):
        row = FileRow(self._list_frame, file_path=path, on_remove=self._remove_row)
        row.pack(fill="x", padx=4, pady=2)
        self._rows.append(row)

    def _remove_row(self, row: FileRow):
        if self._converting:
            return
        self._files.remove(row.file_path)
        self._rows.remove(row)
        row.destroy()
        if not self._files:
            self._empty_label.pack(pady=20)
        self._format_selector.update_formats(self._files)

    def _clear(self):
        if self._converting:
            return
        for row in list(self._rows):
            row.destroy()
        self._rows.clear()
        self._files.clear()
        self._progress.set(0)
        self._progress_label.configure(text="")
        self._open_folder_btn.grid_remove()
        self._last_output_dir = None
        self._empty_label.pack(pady=20)
        self._format_selector.update_formats([])

    def _choose_output_dir(self):
        d = filedialog.askdirectory(title="Выберите папку для сохранения")
        if d:
            self._output_dir = Path(d)
            short = str(self._output_dir)
            if len(short) > 45:
                short = "..." + short[-43:]
            self._dir_label.configure(text=short)

    def _start_conversion(self):
        if self._converting:
            return
        if not self._files:
            messagebox.showinfo("Нет файлов", "Добавьте файлы для конвертации.")
            return
        out_fmt = self._format_selector.get_format()
        if not out_fmt:
            messagebox.showinfo("Формат не выбран", "Выберите целевой формат.")
            return

        self._converting = True
        self._last_output_dir = None
        self._convert_btn.configure(state="disabled", text="Конвертирую...")
        self._clear_btn.configure(state="disabled")
        self._open_folder_btn.grid_remove()
        self._progress.set(0)
        self._progress_label.configure(text="")
        for row in self._rows:
            row.set_status("pending")

        threading.Thread(
            target=self._run_conversion,
            args=(list(self._rows), out_fmt, self._output_dir),
            daemon=True,
        ).start()

    def _run_conversion(self, rows, out_fmt, output_dir):
        total = len(rows)
        ok_count = 0
        errors: list[tuple[str, str]] = []
        last_output: Path = None

        for i, row in enumerate(rows):
            self.after(0, row.set_status, "running")
            self.after(0, self._progress_label.configure, {"text": f"{i + 1}/{total}"})
            try:
                result = ConverterEngine.convert(row.file_path, out_fmt, output_dir)
                self.after(0, row.set_status, "ok", "готово: " + result.name)
                ok_count += 1
                last_output = result.parent
            except (ConversionError, Exception) as e:
                self.after(0, row.set_status, "error", "ошибка")
                errors.append((row.file_path.name, str(e)))
            self.after(0, self._progress.set, (i + 1) / total)

        self.after(0, self._on_done, ok_count, errors, last_output)

    def _on_done(self, ok_count: int, errors: list, last_output: Path):
        self._converting = False
        self._last_output_dir = last_output
        self._convert_btn.configure(state="normal", text="Конвертировать")
        self._clear_btn.configure(state="normal")

        if last_output:
            self._open_folder_btn.grid()

        total = ok_count + len(errors)
        if not errors:
            if total > 1:
                messagebox.showinfo("Готово", f"Все {total} файлов успешно конвертированы.")
        else:
            err_lines = "\n".join(f"  - {name}: {msg[:80]}" for name, msg in errors[:10])
            if len(errors) > 10:
                err_lines += f"\n  ... и ещё {len(errors) - 10}"
            messagebox.showwarning(
                "Завершено с ошибками",
                f"Успешно: {ok_count} из {total}\n\nОшибки:\n{err_lines}",
            )

    def _open_output_folder(self):
        if self._last_output_dir and self._last_output_dir.exists():
            import subprocess, platform
            p = platform.system()
            if p == "Windows":
                subprocess.Popen(["explorer", str(self._last_output_dir)])
            elif p == "Darwin":
                subprocess.Popen(["open", str(self._last_output_dir)])
            else:
                subprocess.Popen(["xdg-open", str(self._last_output_dir)])

    def _show_error(self, filename, message):
        messagebox.showerror(f"Ошибка: {filename}", message[:500])
