# scripts/collectors/collect_semgrep.py
"""
Сбор правил из репозитория Semgrep.
Требует: git, pyyaml
"""
import subprocess
import yaml
import json
from pathlib import Path

SEMGREP_REPO = "https://github.com/semgrep/semgrep-rules.git"
CLONE_DIR = Path("data/raw/semgrep-rules")

# Правила, которые нам интересны
TARGET_PATTERNS = {
    "eval": "eval_usage",
    "exec": "exec_usage",
    "shell": "shell_true",
    "sqli": "sql_concat",
    "sql-injection": "sql_concat",
    "md5": "weak_hash",
    "sha1": "weak_hash",
    "hardcoded": "hardcoded_creds",
}


def clone_repo():
    if CLONE_DIR.exists():
        print("Репозиторий уже клонирован")
        return

    print("Клонирую semgrep-rules (большой репозиторий)...")
    subprocess.run(
        ["git", "clone", "--depth", "1", SEMGREP_REPO, str(CLONE_DIR)],
        check=True,
    )


def parse_yaml_rule(yaml_path: Path) -> list[dict]:
    """Парсит одно YAML-правило Semgrep."""
    try:
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception:
        return []

    if not data or "rules" not in data:
        return []

    results = []
    for rule in data["rules"]:
        rule_id = rule.get("id", "").lower()

        # Проверяем, подходит ли правило
        insecure_type = None
        for pattern, itype in TARGET_PATTERNS.items():
            if pattern in rule_id:
                insecure_type = itype
                break

        if not insecure_type:
            continue

        # Извлекаем метаданные
        metadata = rule.get("metadata", {})
        cwe = metadata.get("cwe", [])

        results.append({
            "rule_id": rule_id,
            "insecure_type": insecure_type,
            "pattern": rule.get("pattern", ""),
            "message": rule.get("message", ""),
            "cwe": cwe,
            "language": rule.get("languages", ["python"])[0],
        })

    return results


def to_dataset_item(raw: dict, idx: int) -> dict:
    return {
        "id": f"real_semgrep_{idx:04d}",
        "source": "opensource",
        "language": raw["language"] if raw["language"] in ["python", "c", "javascript"] else "python",
        "file_path": f"semgrep/{raw['rule_id']}.py",
        "line_number": 1,
        "context_before": "",
        "target_snippet": raw["pattern"],
        "context_after": "",
        "labels": {
            "is_secret": False,
            "is_insecure": True,
            "secret_type": None,
            "insecure_type": raw["insecure_type"],
        },
        "metadata": {
            "source_rule": raw["rule_id"],
            "cwe": raw["cwe"],
            "difficulty": "medium",
            "note": raw["message"][:200],
        },
    }


def main():
    clone_repo()

    # Ищем все YAML-файлы
    yaml_files = list(CLONE_DIR.rglob("*.yaml")) + list(CLONE_DIR.rglob("*.yml"))
    print(f"Найдено YAML-файлов: {len(yaml_files)}")

    all_rules = []
    for yf in yaml_files:
        all_rules.extend(parse_yaml_rule(yf))

    print(f"Подходящих правил: {len(all_rules)}")

    items = [to_dataset_item(r, i) for i, r in enumerate(all_rules)]

    out = Path("data/collected/semgrep.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"✅ Собрано примеров: {len(items)} → {out}")


if __name__ == "__main__":
    main()