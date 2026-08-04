# scripts/collectors/collect_vuln_repos.py (ИСПРАВЛЕННАЯ ВЕРСИЯ)
"""
Сбор реальных кейсов из учебных уязвимых приложений.
"""
import subprocess
import re
import json
from pathlib import Path

# Учебные уязвимые приложения (актуальные репозитории)
VULN_REPOS = {
    "wrongsecrets": "https://github.com/OWASP/wrongsecrets.git",
    "juice-shop": "https://github.com/juice-shop/juice-shop.git",
    "dvwa": "https://github.com/digininja/DVWA.git",
}

CLONE_DIR = Path("data/raw/vuln_repos")

# Паттерны для поиска
PATTERNS = {
    "eval_usage": [r'\beval\s*\('],
    "exec_usage": [r'\bexec\s*\('],
    "shell_true": [r'shell\s*=\s*True', r'\bos\.system\s*\('],
    "sql_concat": [r'(?i)(select|insert|update|delete)\s.{0,60}?\+\s*\w', r'(?i)f["\'](select|insert|update|delete)'],
    "weak_hash": [r'\bmd5\s*\(', r'\bsha1\s*\('],
    "api_key": [r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']'],
    "password": [r'(?i)(password|passwd)\s*[=:]\s*["\'][^"\']+["\']'],
}


def clone_repos():
    CLONE_DIR.mkdir(parents=True, exist_ok=True)
    for name, url in VULN_REPOS.items():
        target = CLONE_DIR / name
        if target.exists():
            print(f"{name} уже клонирован")
            continue
        print(f"Клонирую {name}...")
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", url, str(target)],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка клонирования {name}: {e}")


def scan_file(file_path: Path, language: str) -> list[dict]:
    findings = []
    try:
        lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return findings

    for i, line in enumerate(lines):
        for insecure_type, patterns in PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, line):
                    start = max(0, i - 3)
                    end = min(len(lines), i + 4)
                    findings.append({
                        "file_path": str(file_path),
                        "line_number": i + 1,
                        "language": language,
                        "context_before": "\n".join(lines[start:i]),
                        "target_snippet": line,
                        "context_after": "\n".join(lines[i + 1:end]),
                        "insecure_type": insecure_type,
                    })
                    break
    return findings


def to_dataset_item(raw: dict, source_repo: str, idx: int) -> dict:
    is_secret = raw["insecure_type"] in ("api_key", "password")

    return {
        "id": f"real_vuln_{source_repo}_{idx:04d}",
        "source": "opensource",
        "language": raw["language"],
        "file_path": raw["file_path"],
        "line_number": raw["line_number"],
        "context_before": raw["context_before"],
        "target_snippet": raw["target_snippet"],
        "context_after": raw["context_after"],
        "labels": {
            "is_secret": is_secret,
            "is_insecure": not is_secret,
            "secret_type": raw["insecure_type"] if is_secret else None,
            "insecure_type": None if is_secret else raw["insecure_type"],
        },
        "metadata": {
            "source_repo": source_repo,
            "difficulty": "medium",
            "note": "⚠️ Требует ручной проверки разметки",
        },
    }


def main():
    clone_repos()

    all_findings = []
    for repo_name in VULN_REPOS:
        repo_dir = CLONE_DIR / repo_name
        if not repo_dir.exists():
            continue

        print(f"\n📂 Сканирую {repo_name}...")

        # Python-файлы
        py_files = list(repo_dir.rglob("*.py"))
        py_files = [f for f in py_files if ".git" not in str(f) and "node_modules" not in str(f)]
        for py_file in py_files:
            all_findings.extend(
                (f, repo_name) for f in scan_file(py_file, "python")
            )

        # C-файлы
        c_files = list(repo_dir.rglob("*.c"))
        c_files = [f for f in c_files if ".git" not in str(f)]
        for c_file in c_files:
            all_findings.extend(
                (f, repo_name) for f in scan_file(c_file, "c")
            )

        # PHP-файлы (для DVWA)
        php_files = list(repo_dir.rglob("*.php"))
        php_files = [f for f in php_files if ".git" not in str(f)]
        for php_file in php_files:
            all_findings.extend(
                (f, repo_name) for f in scan_file(php_file, "php")
            )

    print(f"\nНайдено кандидатов: {len(all_findings)}")

    items = [
        to_dataset_item(raw, repo, i)
        for i, (raw, repo) in enumerate(all_findings)
    ]

    out = Path("data/collected/vuln_repos.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"✅ Собрано кандидатов: {len(items)} → {out}")
    print("⚠️  ВАЖНО: проверьте разметку вручную перед добавлением в датасет!")


if __name__ == "__main__":
    main()