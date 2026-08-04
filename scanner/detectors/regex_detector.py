# scanner/detectors/regex_detector.py
"""
Regex-based детектор.
Ищет секреты и небезопасные паттерны по регулярным выражениям.
"""
import re
from typing import List

from scanner.models import CodeChunk, Finding, DetectorType
from scanner.detectors.base import BaseDetector
from scanner.detectors.regex_rules import REGEX_RULES


class RegexDetector(BaseDetector):
    name = "regex"
    detector_type = DetectorType.REGEX

    def __init__(self):
        # Компилируем правила один раз для производительности
        self.compiled_rules = [
            (type_, category, re.compile(pattern), severity, description)
            for type_, category, pattern, severity, description in REGEX_RULES
        ]

    def detect(self, chunk: CodeChunk) -> List[Finding]:
        findings = []
        snippet = chunk.target_snippet

        # Пропускаем комментарии (но не закомментированные секреты — они тоже могут быть опасны)
        # Для insecure-паттернов комментарии пропускаем
        is_comment = self.is_commented(snippet)

        for type_, category, pattern, severity, description in self.compiled_rules:
            # Для insecure-кода пропускаем комментарии
            if is_comment and category == "insecure_code":
                continue

            match = pattern.search(snippet)
            if match:
                # Снижаем confidence для комментариев
                confidence = 0.5 if is_comment else 0.85

                findings.append(Finding(
                    file=chunk.file_path,
                    line=chunk.start_line,
                    type=type_,
                    category=category,
                    severity=severity,
                    confidence=confidence,
                    detector=self.detector_type,
                    snippet=snippet.strip(),
                    explanation=f"[regex] Обнаружен паттерн '{description}': `{match.group(0)[:60]}`",
                    metadata={
                        "matched_text": match.group(0),
                        "rule": type_,
                        "is_comment": is_comment,
                    },
                ))

        return findings