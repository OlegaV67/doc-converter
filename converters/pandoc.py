import shutil
import subprocess
from pathlib import Path

from .base import BaseConverter, ConversionError

_SUPPORTED: dict[str, list[str]] = {
    "docx": ["pdf", "odt", "html", "txt", "md", "epub", "rst"],
    "odt":  ["pdf", "docx", "html", "txt", "md", "epub"],
    "md":   ["pdf", "docx", "odt", "html", "epub", "txt", "rst"],
    "rst":  ["pdf", "docx", "html", "txt", "md", "epub"],
    "html": ["pdf", "docx", "odt", "txt", "md", "epub"],
    "txt":  ["pdf", "docx", "html", "md", "epub"],
    "epub": ["docx", "odt", "html", "txt", "md", "pdf"],
}


def _find_pandoc() -> str:
    candidate = shutil.which("pandoc")
    if candidate:
        return candidate
    common_paths = [
        r"C:\Program Files\Pandoc\pandoc.exe",
        r"C:\Users\%USERNAME%\AppData\Local\Pandoc\pandoc.exe",
        "/usr/bin/pandoc",
        "/usr/local/bin/pandoc",
    ]
    for path in common_paths:
        expanded = str(Path(path).expanduser())
        if Path(expanded).exists():
            return expanded
    raise FileNotFoundError("Pandoc не найден в системе.")


class PandocConverter(BaseConverter):

    def supported_conversions(self) -> dict[str, list[str]]:
        return _SUPPORTED

    def convert(self, input_path: Path, output_path: Path) -> None:
        pandoc = _find_pandoc()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [pandoc, str(input_path), "-o", str(output_path)]

        # PDF требует движок — используем встроенный wkhtmltopdf или xelatex если доступен
        out_ext = output_path.suffix.lstrip(".").lower()
        if out_ext == "pdf":
            cmd += ["--pdf-engine=xelatex"]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode != 0:
            raise ConversionError(
                f"Pandoc завершился с ошибкой:\n{result.stderr or result.stdout}"
            )
