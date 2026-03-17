"""
Главный движок: принимает файл и целевой формат, запускает нужный конвертер.
"""
from __future__ import annotations

from pathlib import Path

from converters.base import ConversionError
from core.format_registry import get_converter, get_supported_outputs


class ConverterEngine:

    @staticmethod
    def get_output_formats(file_path: Path) -> list[str]:
        """Возвращает список форматов, в которые можно конвертировать файл."""
        ext = file_path.suffix.lstrip(".").lower()
        return get_supported_outputs(ext)

    @staticmethod
    def convert(
        input_path: Path,
        out_ext: str,
        output_dir: Path | None = None,
    ) -> Path:
        """
        Конвертирует файл в нужный формат.

        :param input_path: Исходный файл.
        :param out_ext:    Целевое расширение без точки (например 'pdf').
        :param output_dir: Папка для сохранения. Если None — та же папка, что у входного файла.
        :returns:          Путь к созданному файлу.
        :raises ConversionError: При ошибке конвертации или неподдерживаемой паре форматов.
        """
        in_ext = input_path.suffix.lstrip(".").lower()
        out_ext = out_ext.lower()

        converter = get_converter(in_ext, out_ext)
        if converter is None:
            raise ConversionError(
                f"Конвертация {in_ext.upper()} → {out_ext.upper()} не поддерживается."
            )

        save_dir = output_dir if output_dir else input_path.parent
        output_path = save_dir / (input_path.stem + "." + out_ext)

        # Если файл уже существует — добавляем суффикс
        counter = 1
        while output_path.exists():
            output_path = save_dir / f"{input_path.stem}_{counter}.{out_ext}"
            counter += 1

        converter.convert(input_path, output_path)
        return output_path
