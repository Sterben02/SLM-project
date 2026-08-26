# scanner/core/cascade.py
"""Каскад: baseline находит кандидатов, SLM проверяет и отсекает ложные."""
from typing import List
from pathlib import Path 

from scanner.models import Finding
from scanner.core.scanner import parse_file
from scanner.utils.recommendations import get_recommendation


def verify_with_slm(findings: List[Finding]) -> List[Finding]:
    """Прогоняет каждое baseline-срабатывание через SLM."""
    if not findings:
        return findings

    from scanner.llm import SLMDetector
    slm = SLMDetector()

    confirmed: List[Finding] = []
    by_file = {}
    for f in findings:
        by_file.setdefault(f.file, []).append(f)

    total = len(findings)
    done = 0
    for file_path, file_findings in by_file.items():
        chunks = parse_file(Path(file_path))   # ← обернуть в Path
        for f in file_findings:
            done += 1
            f.recommendation = get_recommendation(f.type)
            print(f"🤖 SLM проверяет {done}/{total}: {f.file}:{f.line} ({f.type})")
            chunk = _chunk_for_finding(chunks, f)
            if chunk is None:
                confirmed.append(f)
                continue

            slm_hits = slm.detect(chunk)
            if slm_hits:
                f.explanation = f"{f.explanation} | 🤖 SLM: {slm_hits[0].explanation}"
                f.confidence = max(f.confidence, slm_hits[0].confidence)
                confirmed.append(f)
                print("   ✅ Подтверждено")
            else:
                print("   ❌ Отклонено (false positive)")

    return confirmed


def _chunk_for_finding(chunks, f):
    for c in chunks:
        if c.start_line <= f.line <= c.end_line:
            return c
    return None