# scripts/balance_dataset.py
"""
Балансировка датасета и ограничение размера.
Берём максимум N примеров на каждый класс для равномерного распределения.
"""
import json
import random
from pathlib import Path
from collections import defaultdict

random.seed(42)

# Максимум примеров на каждый класс
MAX_PER_CLASS = 400


def get_class_key(item: dict) -> str:
    """Возвращает ключ класса для балансировки."""
    labels = item["labels"]
    if labels["is_secret"]:
        return f"secret_{labels['secret_type']}"
    elif labels["is_insecure"]:
        return f"insecure_{labels['insecure_type']}"
    else:
        return "negative"


def balance_dataset():
    """Балансирует датасет."""
    input_path = Path("data/real_cases_clean.jsonl")
    output_path = Path("data/real_cases_balanced.jsonl")

    print(f"📥 Читаю {input_path}...")

    items = []
    with open(input_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))

    print(f"  Загружено: {len(items)}")

    # Группируем по классам
    groups = defaultdict(list)
    for item in items:
        key = get_class_key(item)
        groups[key].append(item)

    print(f"\nКЛАССОВ: {len(groups)}")

    # Берём максимум MAX_PER_CLASS из каждого
    balanced = []
    for key, group in groups.items():
        random.shuffle(group)
        taken = group[:MAX_PER_CLASS]
        balanced.extend(taken)
        print(f"  {key}: {len(group)} → {len(taken)}")

    # Перемешиваем итоговый датасет
    random.shuffle(balanced)

    # Перенумеруем ID
    for i, item in enumerate(balanced):
        item["id"] = f"real_balanced_{i + 1:05d}"

    print(f"\nИТОГО: {len(balanced)} примеров")

    # Сохраняем
    with open(output_path, "w", encoding="utf-8") as f:
        for item in balanced:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Сохранено: {output_path}")

    return balanced


if __name__ == "__main__":
    balance_dataset()