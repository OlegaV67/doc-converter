"""
Проверка наличия внешних зависимостей при старте приложения.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DependencyStatus:
    name: str
    found: bool
    path: str
    install_url: str


_COMMON_PATHS: dict[str, list[str]] = {
    "soffice": [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        "/usr/bin/soffice",
        "/usr/lib/libreoffice/program/soffice",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    ],
    "ebook-convert": [
        r"C:\Program Files\Calibre2\ebook-convert.exe",
        r"C:\Program Files (x86)\Calibre2\ebook-convert.exe",
        "/usr/bin/ebook-convert",
        "/Applications/calibre.app/Contents/MacOS/ebook-convert",
    ],
    "pandoc": [
        r"C:\Program Files\Pandoc\pandoc.exe",
        "/usr/bin/pandoc",
        "/usr/local/bin/pandoc",
    ],
}

_INSTALL_URLS = {
    "soffice":        "https://www.libreoffice.org/download/download/",
    "ebook-convert":  "https://calibre-ebook.com/download",
    "pandoc":         "https://pandoc.org/installing.html",
}


def _find(executable: str) -> str | None:
    found = shutil.which(executable)
    if found:
        return found
    for path in _COMMON_PATHS.get(executable, []):
        if Path(path).exists():
            return path
    return None


def check_all() -> list[DependencyStatus]:
    """Проверяет все внешние зависимости и возвращает их статус."""
    results = []
    for exe, url in _INSTALL_URLS.items():
        path = _find(exe)
        results.append(DependencyStatus(
            name=exe,
            found=path is not None,
            path=path or "",
            install_url=url,
        ))
    return results


def missing() -> list[DependencyStatus]:
    """Возвращает только отсутствующие зависимости."""
    return [d for d in check_all() if not d.found]
