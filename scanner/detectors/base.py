# scanner/detectors/base.py
"""
Базовый класс для всех детекторов.
"""
from abc import ABC, abstractmethod
from typing import List

from scanner.models import CodeChunk, Finding


class BaseDetector(ABC):
    """Абстрактный базовый класс детектора."""

    name: str = "base"

    @abstractmethod
    def detect(self, chunk: CodeChunk) -> List[Finding]:
        """Анализирует фрагмент кода и возвращает список Finding."""
        ...

    def is_commented(self, line: str) -> bool:
        """
        Проверяет, является ли строка комментарием.
        Поддерживает Python (#), C/JS (//, /*, *).
        """
        stripped = line.strip()
        return (
            stripped.startswith("#")
            or stripped.startswith("//")
            or stripped.startswith("/*")
            or stripped.startswith("*")
        )