# scripts/merge_datasets.py
"""
Объединение реальных и синтетических примеров в финальный датасет.
"""
import json
import random
from pathlib import Path

random.seed(42)


def merge_datasets():
    """Объединяет датасеты."""
    real_path = Path("data/real_cases_balanced.jsonl")
    synthetic_path = Path("data/dataset.jsonl")
    output_path = Path("data/final_dataset.jsonl")

    # Читаем реальные
    real_items = []
    if real_path.exists():
        with open(real_path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    real_items.append(json.loads(line))
        print(f"Реальных примеров: {len(real_items)}")

    # Читаем синтетические
    synthetic_items = []
    if synthetic_path.exists():
        with open(synthetic_path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    synthetic_items.append(json.loads(line))
        print(f"Синтетических примеров: {len(synthetic_items)}")

    # Объединяем
    all_items = real_items + synthetic_items

    # Перемешиваем
    random.shuffle(all_items)

    # Перенумеруем ID
    for i, item in enumerate(all_items):
        item["id"] = f"final_{i + 1:05d}"

    print(f"\n🎉 ИТОГО: {len(all_items)} примеров")

    # Сохраняем
    with open(output_path, "w", encoding="utf-8") as f:
        for item in all_items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Сохранено: {output_path}")

    return all_items


if __name__ == "__main__":
    merge_datasets()