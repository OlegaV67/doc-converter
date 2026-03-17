"""
Реестр форматов: объединяет возможности всех конвертеров в единую таблицу.
Приоритет движков: LibreOffice > Pandoc > Calibre (для пересекающихся пар).
"""
from __future__ import annotations

from converters.calibre import CalibreConverter
from converters.libreoffice import LibreOfficeConverter
from converters.pandoc import PandocConverter
from converters.base import BaseConverter

# Порядок определяет приоритет при конфликте
_CONVERTERS: list[BaseConverter] = [
    LibreOfficeConverter(),
    PandocConverter(),
    CalibreConverter(),
]

# Итоговая таблица: {in_ext: {out_ext: converter_instance}}
_registry: dict[str, dict[str, BaseConverter]] = {}

for _conv in _CONVERTERS:
    for _in_ext, _out_exts in _conv.supported_conversions().items():
        _in_ext = _in_ext.lower()
        if _in_ext not in _registry:
            _registry[_in_ext] = {}
        for _out_ext in _out_exts:
            _out_ext = _out_ext.lower()
            # Не перезаписываем — приоритет у первого добавленного (LibreOffice)
            if _out_ext not in _registry[_in_ext]:
                _registry[_in_ext][_out_ext] = _conv


def get_supported_outputs(in_ext: str) -> list[str]:
    """Возвращает список выходных форматов для данного входного расширения."""
    return sorted(_registry.get(in_ext.lower(), {}).keys())


def get_converter(in_ext: str, out_ext: str) -> BaseConverter | None:
    """Возвращает конвертер для пары форматов или None если не поддерживается."""
    return _registry.get(in_ext.lower(), {}).get(out_ext.lower())


def all_input_formats() -> list[str]:
    """Все поддерживаемые входные форматы."""
    return sorted(_registry.keys())
