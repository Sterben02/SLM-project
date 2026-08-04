# scanner/core/aggregator.py
"""
Агрегация результатов от разных детекторов.
Дедупликация и выбор лучших finding-ов.
"""
from typing import List, Dict, Tuple
from scanner.models import Finding


def dedupe_findings(findings: List[Finding]) -> List[Finding]:
    """
    Удаляет дубликаты: если несколько детекторов нашли одно и то же
    в одном файле/строке — оставляем finding с максимальной confidence.
    """
    # Группируем по (file, line, type)
    grouped: Dict[Tuple[str, int, str], List[Finding]] = {}
    for f in findings:
        key = (f.file, f.line, f.type)
        grouped.setdefault(key, []).append(f)

    result = []
    for key, group in grouped.items():
        # Выбираем finding с максимальной уверенностью
        best = max(group, key=lambda f: f.confidence)

        # Если несколько детекторов согласны — повышаем уверенность
        if len(group) > 1:
            detectors = list({f.detector.value for f in group})
            best.metadata = best.metadata or {}
            best.metadata["confirmed_by"] = detectors
            best.metadata["num_detectors"] = len(group)
            # Бонус за согласие детекторов
            best.confidence = min(0.99, best.confidence + 0.05 * (len(group) - 1))

        result.append(best)

    # Сортируем по серьёзности и уверенности
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    result.sort(key=lambda f: (severity_order.get(f.severity.value, 5), -f.confidence))

    return result