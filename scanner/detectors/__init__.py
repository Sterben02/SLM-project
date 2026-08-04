# scanner/detectors/__init__.py
from .base import BaseDetector
from .regex_detector import RegexDetector
from .entropy_detector import EntropyDetector
from .keyword_detector import KeywordDetector


def get_baseline_detectors():
    """Возвращает список всех baseline-детекторов."""
    return [
        RegexDetector(),
        EntropyDetector(),
        KeywordDetector(),
    ]


__all__ = [
    "BaseDetector",
    "RegexDetector",
    "EntropyDetector",
    "KeywordDetector",
    "get_baseline_detectors",
]