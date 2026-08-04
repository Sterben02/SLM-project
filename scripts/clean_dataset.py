# scripts/clean_dataset.py
"""
Очистка и фильтрация собранного датасета.
- Удаление markdown-обёртки (```python, ```c++ и т.д.)
- Фильтрация по нужным языкам
- Балансировка классов
"""
import json
import re
from pathlib import Path
from collections import defaultdict


def extract_code_from_markdown(text: str) -> str:
    """Извлекает чистый код из markdown-блока."""
    if not text:
        return ""

    # Паттерн: ```язык\nкод\n```
    pattern = r'```(?:\w+)?\n(.*?)```'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Если нет markdown-обёртки, возвращаем как есть
    return text.strip()


def normalize_language(lang: str) -> str | None:
    """Нормализует язык и фильтрует ненужные."""
    if not lang:
        return None

    lang = lang.lower()

    # Маппинг на наши поддерживаемые языки
    if any(x in lang for x in ["python", "py"]):
        return "python"
    elif lang in ["c", "c++", "cpp", "c#"]:
        return "c"
    elif any(x in lang for x in ["javascript", "js", "typescript", "ts"]):
        return "javascript"
    elif "java" in lang and "javascript" not in lang:
        return "java"

    # Игнорируем другие языки
    return None


def map_vulnerability_to_our_types(vuln: str) -> str:
    """Маппит тип уязвимости на наши классы."""
    if not vuln:
        return "insecure_code"

    vuln_lower = vuln.lower()

    # SQL Injection
    if any(x in vuln_lower for x in ["sql injection", "sqli", "sql"]):
        return "sql_concat"

    # Command/Shell Injection
    if any(x in vuln_lower for x in ["command injection", "shell injection", "os command"]):
        return "shell_true"

    # Code Injection (eval/exec)
    if any(x in vuln_lower for x in ["code injection", "eval", "exec"]):
        return "eval_usage"

    # Weak Hash
    if any(x in vuln_lower for x in ["weak hash", "md5", "sha1", "weak cryptography"]):
        return "weak_hash"

    # Hardcoded Credentials
    if any(x in vuln_lower for x in ["hardcoded credential", "hardcoded password", "hardcoded secret"]):
        return "hardcoded_creds"

    # Всё остальное
    return "insecure_code"


def clean_dataset():
    """Основная функция очистки."""
    input_path = Path("data/real_cases.jsonl")
    output_path = Path("data/real_cases_clean.jsonl")

    print(f"Читаю {input_path}...")

    items = []
    with open(input_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))

    print(f"  Загружено: {len(items)}")

    # Очистка и фильтрация
    cleaned = []
    stats = {
        "total": 0,
        "filtered_language": 0,
        "filtered_empty": 0,
        "kept": 0,
    }

    for item in items:
        stats["total"] += 1

        # Извлекаем чистый код
        code = extract_code_from_markdown(item.get("target_snippet", ""))

        # Фильтруем пустой код
        if not code or len(code) < 10:
            stats["filtered_empty"] += 1
            continue

        # Фильтруем по языку
        lang = normalize_language(item.get("language", ""))
        if not lang:
            stats["filtered_language"] += 1
            continue

        # Обновляем item
        item["target_snippet"] = code
        item["language"] = lang

        # Маппим тип уязвимости
        if item["labels"].get("is_insecure") and item["labels"].get("insecure_type"):
            original_type = item["labels"]["insecure_type"]
            if original_type == "insecure_code":
                # Пытаемся уточнить из метаданных
                note = item.get("metadata", {}).get("original_vulnerability", "")
                if not note:
                    note = item.get("metadata", {}).get("original_label", "")
                if note:
                    item["labels"]["insecure_type"] = map_vulnerability_to_our_types(note)

        cleaned.append(item)
        stats["kept"] += 1

    print(f"\nСТАТИСТИКА ОЧИСТКИ:")
    print(f"  Всего обработано: {stats['total']}")
    print(f"  Отфильтровано (пустой код): {stats['filtered_empty']}")
    print(f"  Отфильтровано (не наш язык): {stats['filtered_language']}")
    print(f"  Оставлено: {stats['kept']}")

    # Статистика по языкам
    lang_counts = defaultdict(int)
    for item in cleaned:
        lang_counts[item["language"]] += 1

    print(f"\nПО ЯЗЫКАМ:")
    for lang, count in sorted(lang_counts.items(), key=lambda x: -x[1]):
        print(f"  {lang}: {count}")

    # Статистика по типам
    type_counts = defaultdict(int)
    for item in cleaned:
        if item["labels"]["is_secret"]:
            type_counts[f"secret_{item['labels']['secret_type']}"] += 1
        elif item["labels"]["is_insecure"]:
            type_counts[f"insecure_{item['labels']['insecure_type']}"] += 1
        else:
            type_counts["negative"] += 1

    print(f"\nПО ТИПАМ:")
    for type_, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {type_}: {count}")

    # Сохраняем
    with open(output_path, "w", encoding="utf-8") as f:
        for item in cleaned:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"\nСохранено: {output_path}")

    return cleaned


if __name__ == "__main__":
    clean_dataset()