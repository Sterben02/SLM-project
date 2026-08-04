# scanner/core/scanner.py
"""
Основной сканер: обход файлов, применение детекторов.
"""
import os
from pathlib import Path
from typing import List, Iterable

from rich.progress import Progress

from scanner.models import CodeChunk, Finding
from scanner.detectors import get_baseline_detectors, BaseDetector


# Расширения файлов, которые мы анализируем
SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".js": "javascript",
    ".ts": "typescript",
    ".java": "java",
    ".go": "go",
    ".rb": "ruby",
    ".php": "php",
}

# Директории, которые пропускаем
SKIP_DIRS = {
    "venv", ".venv", "env", ".env",
    "node_modules", "__pycache__", ".git", ".idea", ".vscode",
    "dist", "build", ".pytest_cache", "models_cache",
}


def iter_files(path: str) -> Iterable[Path]:
    """Рекурсивно обходит каталог и возвращает пути к файлам."""
    root = Path(path)
    if root.is_file():
        yield root
        return

    for dirpath, dirnames, filenames in os.walk(root):
        # Фильтруем директории
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for fname in filenames:
            fpath = Path(dirpath) / fname
            if fpath.suffix.lower() in SUPPORTED_EXTENSIONS:
                yield fpath


def parse_file(file_path: Path, context_lines: int = 3) -> List[CodeChunk]:
    """
    Разбирает файл на CodeChunk-и.
    Каждая строка — один CodeChunk с контекстом.
    """
    language = SUPPORTED_EXTENSIONS.get(file_path.suffix.lower(), "unknown")
    chunks = []

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Не удалось прочитать {file_path}: {e}")
        return []

    for i, line in enumerate(lines):
        if not line.strip():
            continue

        start = max(0, i - context_lines)
        end = min(len(lines), i + context_lines + 1)

        chunks.append(CodeChunk(
            file_path=str(file_path),
            language=language,
            start_line=i + 1,
            end_line=i + 1,
            target_snippet=line,
            context_before="".join(lines[start:i]),
            context_after="".join(lines[i + 1:end]),
        ))

    return chunks


def scan_path(
    path: str,
    detectors: List[BaseDetector] = None,
    show_progress: bool = True,
) -> List[Finding]:
    """
    Сканирует путь (файл или каталог) и возвращает все finding-и.
    """
    if detectors is None:
        detectors = get_baseline_detectors()

    all_findings: List[Finding] = []
    files = list(iter_files(path))

    if not files:
        return []

    if show_progress:
        from rich.progress import track
        iterator = track(files, description="Сканирование...")
    else:
        iterator = files

    for file_path in iterator:
        chunks = parse_file(file_path)
        for chunk in chunks:
            for detector in detectors:
                findings = detector.detect(chunk)
                all_findings.extend(findings)

    from scanner.core.aggregator import dedupe_findings
    return dedupe_findings(all_findings)