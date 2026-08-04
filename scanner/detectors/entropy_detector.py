# scanner/detectors/entropy_detector.py
"""
Entropy-based детектор.
Ищет высокоэнтропийные строки — потенциальные секреты.
"""
import re
from typing import List

from scanner.models import CodeChunk, Finding, DetectorType, Severity
from scanner.detectors.base import BaseDetector
from scanner.utils.entropy import (
    extract_string_candidates,
    is_high_entropy,
    shannon_entropy,
)


# Ключевые слова, которые усиливают подозрение
SECRET_HINTS = re.compile(
    r'(?i)(key|token|secret|password|passwd|pwd|credential|auth|private)',
)

# Признаки тестовых/фейковых значений
FAKE_INDICATORS = re.compile(
    r'(?i)(test|example|dummy|fake|sample|placeholder|xxx+|your[_-]?\w+|change[_-]?me)',
)


class EntropyDetector(BaseDetector):
    name = "entropy"
    detector_type = DetectorType.ENTROPY

    def detect(self, chunk: CodeChunk) -> List[Finding]:
        findings = []
        snippet = chunk.target_snippet

        # Пропускаем комментарии
        if self.is_commented(snippet):
            return findings

        # Извлекаем кандидатов
        candidates = extract_string_candidates(snippet)

        for candidate in candidates:
            # Проверяем на фейковые значения
            if FAKE_INDICATORS.search(candidate):
                continue

            is_high, entropy, str_type = is_high_entropy(candidate)

            if not is_high:
                continue

            # Базовая уверенность от энтропии
            confidence = min(0.9, 0.5 + entropy / 10)

            # Усиливаем, если в строке есть ключевые слова
            if SECRET_HINTS.search(snippet):
                confidence = min(0.95, confidence + 0.15)
            else:
                # Без контекстного ключа — снижаем (меньше FP)
                confidence -= 0.2

            if confidence < 0.4:
                continue

            findings.append(Finding(
                file=chunk.file_path,
                line=chunk.start_line,
                type="high_entropy_string",
                category="secret",
                severity=Severity.MEDIUM,
                confidence=round(confidence, 2),
                detector=self.detector_type,
                snippet=snippet.strip(),
                explanation=(
                    f"[entropy] Строка имеет высокую энтропию ({entropy:.2f}), "
                    f"тип: {str_type}. Возможно, это случайный секрет."
                ),
                metadata={
                    "entropy": round(entropy, 3),
                    "string_type": str_type,
                    "candidate_length": len(candidate),
                },
            ))

        return findings