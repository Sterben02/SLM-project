# scripts/test_slm_manual.py
"""Ручной тест обученной SLM на трёх примерах."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scanner.models import CodeChunk
from scanner.llm import SLMDetector

detector = SLMDetector()

tests = [
    ('API_KEY = "sk-live-a8f5f167f44f4964e6c9"', "python", "config.py"),
    ("result = eval(user_input)", "python", "app.py"),
    ("x = 2 + 2", "python", "safe.py"),
]

for snippet, lang, fname in tests:
    chunk = CodeChunk(
        file_path=fname, language=lang, start_line=1, end_line=1,
        target_snippet=snippet, context_before="", context_after="",
    )
    findings = detector.detect(chunk)
    print(f"\n📄 {snippet}")
    if not findings:
        print("   → SLM: безопасно")
    for f in findings:
        print(f"   → SLM: {f.category}/{f.type} (conf={f.confidence})")
        print(f"      💡 {f.explanation}")