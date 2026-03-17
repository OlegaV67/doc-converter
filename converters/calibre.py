import shutil
import subprocess
from pathlib import Path

from .base import BaseConverter, ConversionError

_SUPPORTED: dict[str, list[str]] = {
    "epub": ["mobi", "fb2", "pdf", "docx", "html", "txt", "azw3", "lit"],
    "mobi": ["epub", "fb2", "pdf", "html", "txt", "azw3"],
    "fb2":  ["epub", "mobi", "pdf", "html", "txt", "azw3"],
    "azw3": ["epub", "mobi", "fb2", "pdf", "html", "txt"],
    "lit":  ["epub", "mobi", "fb2", "pdf", "html", "txt"],
    "lrf":  ["epub", "mobi", "pdf", "txt"],
    "html": ["epub", "mobi", "fb2", "pdf", "txt"],
    "txt":  ["epub", "mobi", "fb2", "pdf", "html"],
}


def _find_ebook_convert() -> str:
    candidate = shutil.which("ebook-convert")
    if candidate:
        return candidate
    common_paths = [
        r"C:\Program Files\Calibre2\ebook-convert.exe",
        r"C:\Program Files (x86)\Calibre2\ebook-convert.exe",
        "/usr/bin/ebook-convert",
        "/Applications/calibre.app/Contents/MacOS/ebook-convert",
    ]
    for path in common_paths:
        if Path(path).exists():
            return path
    raise FileNotFoundError("Calibre (ebook-convert) не найден в системе.")


class CalibreConverter(BaseConverter):

    def supported_conversions(self) -> dict[str, list[str]]:
        return _SUPPORTED

    def convert(self, input_path: Path, output_path: Path) -> None:
        ebook_convert = _find_ebook_convert()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [ebook_convert, str(input_path), str(output_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)

        if result.returncode != 0:
            raise ConversionError(
                f"Calibre завершился с ошибкой:\n{result.stderr or result.stdout}"
            )
