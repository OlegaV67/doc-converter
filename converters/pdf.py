"""
PDF converter using pdf2docx and pdfminer.six.
- PDF -> DOCX: pdf2docx
- PDF -> TXT:  pdfminer.six
- PDF -> HTML: pdfminer.six
- PDF -> ODT:  pdf2docx (DOCX) -> LibreOffice (ODT) via chain
"""
from __future__ import annotations

import io
from pathlib import Path

from .base import BaseConverter, ConversionError

_SUPPORTED: dict[str, list[str]] = {
    "pdf": ["docx", "txt", "html", "odt"],
}


class PDFConverter(BaseConverter):

    def supported_conversions(self) -> dict[str, list[str]]:
        return _SUPPORTED

    def convert(self, input_path: Path, output_path: Path) -> None:
        out_ext = output_path.suffix.lstrip(".").lower()
        if out_ext == "docx":
            self._to_docx(input_path, output_path)
        elif out_ext == "txt":
            self._to_txt(input_path, output_path)
        elif out_ext == "html":
            self._to_html(input_path, output_path)
        elif out_ext == "odt":
            self._to_odt(input_path, output_path)
        else:
            raise ConversionError(f"Неподдерживаемый выходной формат: {out_ext}")

    def _to_docx(self, input_path: Path, output_path: Path) -> None:
        try:
            from pdf2docx import Converter as PDF2Docx
        except ImportError:
            raise ConversionError("pdf2docx не установлен. Выполните: pip install pdf2docx")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv = PDF2Docx(str(input_path))
        try:
            cv.convert(str(output_path), start=0, end=None)
        finally:
            cv.close()

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise ConversionError("pdf2docx не создал выходной файл.")

    def _to_txt(self, input_path: Path, output_path: Path) -> None:
        try:
            from pdfminer.high_level import extract_text
        except ImportError:
            raise ConversionError("pdfminer.six не установлен. Выполните: pip install pdfminer.six")

        text = extract_text(str(input_path))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")

    def _to_html(self, input_path: Path, output_path: Path) -> None:
        try:
            from pdfminer.high_level import extract_text_to_fp
            from pdfminer.layout import LAParams
        except ImportError:
            raise ConversionError("pdfminer.six не установлен. Выполните: pip install pdfminer.six")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        buf = io.BytesIO()
        with open(input_path, "rb") as f:
            extract_text_to_fp(f, buf, laparams=LAParams(), output_type="html", codec=None)
        output_path.write_bytes(buf.getvalue())

    def _to_odt(self, input_path: Path, output_path: Path) -> None:
        import tempfile
        from pathlib import Path as _Path

        # Сначала конвертируем PDF -> DOCX, затем DOCX -> ODT через LibreOffice
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_docx = _Path(tmp_dir) / (input_path.stem + ".docx")
            self._to_docx(input_path, tmp_docx)

            # Используем LibreOfficeConverter для DOCX -> ODT
            from converters.libreoffice import LibreOfficeConverter
            LibreOfficeConverter().convert(tmp_docx, output_path)
