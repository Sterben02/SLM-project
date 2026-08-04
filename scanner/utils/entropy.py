# scanner/utils/entropy.py
"""
Расчёт энтропии Шеннона и вспомогательные функции.
"""
import math
import re
from typing import List


def shannon_entropy(s: str) -> float:
    """
    Энтропия Шеннона строки.
    Высокое значение → строка более «случайная».

    Примеры:
        "aaaa"        → 0.0
        "password"    → ~2.75
        "sk-abc123..." → ~4.5+
    """
    if not s:
        return 0.0
    length = len(s)
    freq = {}
    for c in s:
        freq[c] = freq.get(c, 0) + 1
    entropy = -sum((count / length) * math.log2(count / length) for count in freq.values())
    return entropy


def extract_string_candidates(line: str) -> List[str]:
    """
    Извлекает строки-кандидаты из строки кода.
    Ищем строки в кавычках и значения после `=` или `:`.
    """
    candidates = []

    # Строки в кавычках (одинарных и двойных)
    quoted = re.findall(r'["\']([^"\']{8,})["\']', line)
    candidates.extend(quoted)

    # Значения после = или :
    assigned = re.findall(r'[=:]\s*["\']?([A-Za-z0-9+/=_\-]{16,})["\']?', line)
    candidates.extend(assigned)

    return candidates


def classify_string_type(s: str) -> str:
    """
    Определяет тип строки для выбора порога энтропии.
    """
    if re.fullmatch(r'[0-9a-fA-F]+', s):
        return "hex"
    if re.fullmatch(r'[A-Za-z0-9+/=]+', s) and len(s) % 4 == 0:
        return "base64"
    if re.fullmatch(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', s):
        return "uuid"
    return "alphanumeric"


# Пороги энтропии для разных типов строк
ENTROPY_THRESHOLDS = {
    "hex": 3.0,  # hex-строки обычно менее энтропийны
    "base64": 4.5,  # base64 более случайный
    "alphanumeric": 3.5,  # общий случай
    "uuid": 999.0,  # UUID исключаем (порог недостижим)
}


def is_high_entropy(s: str) -> tuple[bool, float, str]:
    """
    Проверяет, является ли строка высокоэнтропийной.
    Возвращает: (является, значение энтропии, тип строки).
    """
    str_type = classify_string_type(s)
    entropy = shannon_entropy(s)
    threshold = ENTROPY_THRESHOLDS.get(str_type, 3.5)
    return entropy >= threshold, entropy, str_type