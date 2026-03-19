import shutil
import subprocess
import tempfile
from pathlib import Path

from .base import BaseConverter, ConversionError

# LibreOffice export filter names по целевому расширению
_EXPORT_FILTERS = {
    "pdf":  "writer_pdf_Export",
    "docx": "MS Word 2007 XML",
    "odt":  "writer8",
    "html": "HTML (StarWriter)",
    "txt":  "Text",
    "xlsx": "Calc MS Excel 2007 XML",
    "ods":  "calc8",
    "csv":  "Text - txt - csv (StarCalc)",
    "pptx": "Impress MS PowerPoint 2007 XML",
    "odp":  "impress8",
}

# Какие входные форматы обрабатывает LibreOffice
_SUPPORTED: dict[str, list[str]] = {
    "docx": ["pdf", "odt", "html", "txt"],
    "doc":  ["pdf", "odt", "docx", "html", "txt"],
    "odt":  ["pdf", "docx", "html", "txt"],
    "rtf":  ["pdf", "docx", "odt", "html", "txt"],
    "xlsx": ["pdf", "ods", "csv"],
    "xls":  ["pdf", "ods", "xlsx", "csv"],
    "ods":  ["pdf", "xlsx", "csv"],
    "pptx": ["pdf", "odp"],
    "ppt":  ["pdf", "odp", "pptx"],
    "odp":  ["pdf", "pptx"],
    # PDF как входной формат не поддерживается: LibreOffice открывает PDF
    # в режиме Draw и не может экспортировать в форматы Writer/Calc.
}


def _find_soffice() -> str:
    """Ищет исполняемый файл LibreOffice."""
    candidate = shutil.which("soffice")
    if candidate:
        return candidate
    common_paths = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        "/usr/bin/soffice",
        "/usr/lib/libreoffice/program/soffice",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    ]
    for path in common_paths:
        if Path(path).exists():
            return path
    raise FileNotFoundError("LibreOffice (soffice) не найден в системе.")


class LibreOfficeConverter(BaseConverter):

    def supported_conversions(self) -> dict[str, list[str]]:
        return _SUPPORTED

    def convert(self, input_path: Path, output_path: Path) -> None:
        soffice = _find_soffice()
        out_ext = output_path.suffix.lstrip(".").lower()

        if out_ext not in _EXPORT_FILTERS:
            raise ConversionError(f"Неподдерживаемый выходной формат: {out_ext}")

        # LibreOffice не позволяет задать имя выходного файла напрямую —
        # конвертируем во временную папку, затем переименовываем.
        with tempfile.TemporaryDirectory() as tmp_dir:
            cmd = [
                soffice,
                "--headless",
                "--norestore",
                "--convert-to", out_ext,
                "--outdir", tmp_dir,
                str(input_path),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode != 0:
                raise ConversionError(
                    f"LibreOffice завершился с ошибкой:\n{result.stderr or result.stdout}"
                )

            # LibreOffice сохраняет файл с тем же именем, но новым расширением
            expected = Path(tmp_dir) / (input_path.stem + "." + out_ext)
            if not expected.exists():
                # На некоторых платформах расширение uppercase
                candidates = list(Path(tmp_dir).glob(f"{input_path.stem}.*"))
                if not candidates:
                    raise ConversionError("LibreOffice не создал выходной файл.")
                expected = candidates[0]

            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(expected), str(output_path))
