# scripts/collectors/load_hf_direct.py
"""
Прямая загрузка датасетов с HuggingFace с адаптацией под наш формат.
"""
from datasets import load_dataset
import json
from pathlib import Path


def load_cybernative() -> list[dict]:
    """
    CyberNative/Code_Vulnerability_Security_DPO
    1371 загрузок, 165 лайков — самый популярный.
    Обычно содержит пары: уязвимый код → безопасный код.
    """
    print("📥 Загружаю CyberNative/Code_Vulnerability_Security_DPO...")
    try:
        ds = load_dataset("CyberNative/Code_Vulnerability_Security_DPO", split="train")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return []

    print(f"  Колонки: {ds.column_names}")
    print(f"  Примеров: {len(ds)}")
    print(f"  Первый пример: {ds[0]}")

    items = []
    for i, row in enumerate(ds):
        # Пытаемся найти код в разных возможных колонках
        code = None
        for col in ["chosen", "rejected", "prompt", "text", "code", "input"]:
            if col in row and row[col]:
                val = str(row[col])
                if len(val) > 20 and ("<code" in val or "def " in val or "class " in val or "function" in val):
                    code = val
                    break

        if not code:
            # Берём любую строковую колонку
            for col in row:
                if isinstance(row[col], str) and len(row[col]) > 20:
                    code = row[col]
                    break

        if not code:
            continue

        # Определяем язык
        language = "python"
        if "<?php" in code or "$" in code[:500]:
            language = "php"
        elif "public class" in code or "import java" in code:
            language = "java"
        elif "#include" in code or "printf" in code:
            language = "c"
        elif "function " in code and "=>" in code:
            language = "javascript"

        # DPO-датасеты обычно содержат пары: chosen (хорошо) и rejected (плохо)
        # Мы берём rejected как уязвимый пример
        is_insecure = True
        if "chosen" in ds.column_names and "rejected" in ds.column_names:
            if row.get("chosen") == code:
                is_insecure = False  # безопасный пример

        items.append({
            "id": f"hf_cybernative_{i:05d}",
            "source": "opensource",
            "language": language,
            "file_path": f"huggingface/cybernative_{i}.py",
            "line_number": 1,
            "context_before": "",
            "target_snippet": code[:1500],
            "context_after": "",
            "labels": {
                "is_secret": False,
                "is_insecure": is_insecure,
                "secret_type": None,
                "insecure_type": "insecure_code" if is_insecure else None,
            },
            "metadata": {
                "source_dataset": "CyberNative/Code_Vulnerability_Security_DPO",
                "note": "⚠️ Требует ручной проверки",
                "difficulty": "medium",
            },
        })

    print(f"  ✅ Собрано: {len(items)}")
    return items


def load_lemon42() -> list[dict]:
    """
    lemon42-ai/Code_Vulnerability_Labeled_Dataset
    Размеченный датасет с конкретными CWE.
    """
    print("\n📥 Загружаю lemon42-ai/Code_Vulnerability_Labeled_Dataset...")
    try:
        ds = load_dataset("lemon42-ai/Code_Vulnerability_Labeled_Dataset", split="train")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return []

    print(f"  Колонки: {ds.column_names}")
    print(f"  Примеров: {len(ds)}")
    if len(ds) > 0:
        print(f"  Первый пример: {ds[0]}")

    items = []
    for i, row in enumerate(ds):
        code = None
        for col in ["code", "text", "input", "vulnerable_code"]:
            if col in row and row[col]:
                code = str(row[col])
                break

        if not code or len(code) < 20:
            continue

        # Ищем CWE/метку
        label = None
        for col in ["label", "cwe", "vulnerability", "type", "category"]:
            if col in row and row[col]:
                label = str(row[col]).lower()
                break

        # Маппим метку на наш insecure_type
        insecure_type = "insecure_code"
        if label:
            if "sql" in label or "sqli" in label or "cwe-89" in label:
                insecure_type = "sql_concat"
            elif "xss" in label or "cwe-79" in label:
                insecure_type = "insecure_code"
            elif "command" in label or "cwe-78" in label:
                insecure_type = "shell_true"
            elif "eval" in label or "cwe-95" in label:
                insecure_type = "eval_usage"
            elif "md5" in label or "sha1" in label or "cwe-328" in label:
                insecure_type = "weak_hash"

        items.append({
            "id": f"hf_lemon42_{i:05d}",
            "source": "opensource",
            "language": "python",
            "file_path": f"huggingface/lemon42_{i}.py",
            "line_number": 1,
            "context_before": "",
            "target_snippet": code[:1500],
            "context_after": "",
            "labels": {
                "is_secret": False,
                "is_insecure": True,
                "secret_type": None,
                "insecure_type": insecure_type,
            },
            "metadata": {
                "source_dataset": "lemon42-ai/Code_Vulnerability_Labeled_Dataset",
                "original_label": label,
                "note": "⚠️ Автоматический маппинг меток",
                "difficulty": "medium",
            },
        })

    print(f"  ✅ Собрано: {len(items)}")
    return items


def main():
    all_items = []
    all_items.extend(load_cybernative())
    all_items.extend(load_lemon42())

    out = Path("data/collected/huggingface.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for item in all_items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"\n🎉 ИТОГО С HUGGINGFACE: {len(all_items)} примеров → {out}")
    print("\n⚠️  ВАЖНО: просмотрите первые 10 примеров вручную!")
    print("   Убедитесь, что код и разметка корректны.")


if __name__ == "__main__":
    main()