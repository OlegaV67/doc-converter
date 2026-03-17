from abc import ABC, abstractmethod
from pathlib import Path


class ConversionError(Exception):
    pass


class BaseConverter(ABC):
    """Абстрактный базовый класс для всех конвертеров."""

    @abstractmethod
    def convert(self, input_path: Path, output_path: Path) -> None:
        """
        Конвертирует файл.

        :param input_path: Путь к исходному файлу.
        :param output_path: Путь к выходному файлу (с нужным расширением).
        :raises ConversionError: При ошибке конвертации.
        """

    @abstractmethod
    def supported_conversions(self) -> dict[str, list[str]]:
        """
        Возвращает словарь поддерживаемых конвертаций.
        Ключ — входное расширение, значение — список выходных расширений.
        Расширения без точки, в нижнем регистре. Пример: {'docx': ['pdf', 'odt']}
        """
