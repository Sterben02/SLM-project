# scanner/detectors/keyword_detector.py
"""
Keyword/context детектор.
Анализирует имена переменных, типы файлов и контекст.
"""
import re
from typing import List
from pathlib import Path

from scanner.models import CodeChunk, Finding, DetectorType, Severity
from scanner.detectors.base import BaseDetector


# Имена переменных, указывающие на секреты
SECRET_VAR_PATTERNS = [
    (r'(?i)\b(api[_-]?key|apikey)\b', "api_key", "Имя переменной содержит 'api_key'"),
    (r'(?i)\b(access[_-]?token|auth[_-]?token)\b', "access_token", "Имя переменной содержит 'token'"),
    (r'(?i)\b(password|passwd|pwd)\b', "password", "Имя переменной содержит 'password'"),
    (r'(?i)\b(private[_-]?key|secret[_-]?key)\b', "private_key", "Имя переменной содержит 'private_key'"),
    (r'(?i)\b(jwt|json[_-]?web[_-]?token)\b', "jwt", "Имя переменной содержит 'jwt'"),
    (r'(?i)\b(secret|credential)\b', "generic_secret", "Имя переменной содержит 'secret'"),
]

# Типы файлов, где секреты более вероятны
SENSITIVE_FILES = {
    ".env": 0.3,
    "config.py": 0.2,
    "settings.py": 0.2,
    "config.js": 0.2,
    "settings.js": 0.2,
    "config.yaml": 0.2,
    "config.yml": 0.2,
    "config.json": 0.2,
    ".env.local": 0.3,
    ".env.production": 0.3,
}

# Индикаторы тестового кода
TEST_INDICATORS = re.compile(
    r'(?i)(test|mock|fake|example|sample|fixture|stub)',
)

# Признаки, что значение берётся извне (не hardcoded)
EXTERNAL_VALUE = re.compile(
    r'(os\.getenv|os\.environ|getenv\(|process\.env|System\.getenv|getenv\()',
)


class KeywordDetector(BaseDetector):
    name = "keyword"
    detector_type = DetectorType.KEYWORD

    def detect(self, chunk: CodeChunk) -> List[Finding]:
        findings = []
        snippet = chunk.target_snippet

        # Пропускаем комментарии
        if self.is_commented(snippet):
            return findings

        # Пропускаем строки, где значение берётся из env
        if EXTERNAL_VALUE.search(snippet):
            return findings

        # Проверяем имена переменных
        for pattern, secret_type, reason in SECRET_VAR_PATTERNS:
            match = re.search(pattern, snippet)
            if not match:
                continue

            # Базовая уверенность
            confidence = 0.5

            # Повышаем, если есть присваивание строкового значения
            if re.search(r'[=:]\s*["\'][^"\']{4,}["\']', snippet):
                confidence += 0.2
                reason += ", присваивается строковое значение"

            # Повышаем для чувствительных файлов
            file_bonus = self._file_bonus(chunk.file_path)
            if file_bonus > 0:
                confidence += file_bonus
                reason += f", файл '{Path(chunk.file_path).name}' часто содержит секреты"

            # Снижаем для тестового кода
            if TEST_INDICATORS.search(chunk.file_path) or TEST_INDICATORS.search(chunk.context_before):
                confidence -= 0.3
                reason += ", но код похож на тестовый"

            # Пропускаем низкую уверенность
            if confidence < 0.4:
                continue

            findings.append(Finding(
                file=chunk.file_path,
                line=chunk.start_line,
                type=f"hardcoded_{secret_type}",
                category="secret",
                severity=Severity.HIGH,
                confidence=round(min(confidence, 0.95), 2),
                detector=self.detector_type,
                snippet=snippet.strip(),
                explanation=f"[keyword] {reason}.",
                metadata={
                    "variable_pattern": pattern,
                    "secret_type": secret_type,
                    "file_bonus": file_bonus,
                },
            ))
            break  # Одно срабатывание на строку

        return findings

    def _file_bonus(self, file_path: str) -> float:
        """Бонус уверенности на основе типа файла."""
        filename = Path(file_path).name.lower()
        for sensitive, bonus in SENSITIVE_FILES.items():
            if sensitive in filename:
                return bonus
        return 0.0