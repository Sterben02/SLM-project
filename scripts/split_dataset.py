# scripts/split_dataset.py
"""
Разбиение финального датасета на train/valid/test.
Использует стратификацию для сохранения баланса классов.
"""
import json
import random
from pathlib import Path
from collections import defaultdict

random.seed(42)


def get_class_key(item: dict) -> str:
    """Ключ для стратификации."""
    labels = item["labels"]
    if labels["is_secret"]:
        return f"secret_{labels['secret_type']}"
    elif labels["is_insecure"]:
        return f"insecure_{labels['insecure_type']}"
    else:
        return "negative"


def split_dataset():
    """Разбивает датасет."""
    input_path = Path("data/final_dataset.jsonl")

    print(f"Читаю {input_path}...")

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

    train, valid, test = [], [], []

    # Для каждого класса делим 70/15/15
    for key, group in groups.items():
        random.shuffle(group)
        n = len(group)
        train_end = int(n * 0.70)
        valid_end = int(n * 0.85)

        train.extend(group[:train_end])
        valid.extend(group[train_end:valid_end])
        test.extend(group[valid_end:])

    # Перемешиваем
    for part in (train, valid, test):
        random.shuffle(part)

    # Перенумеруем
    for i, item in enumerate(train + valid + test):
        item["id"] = f"example_{i + 1:05d}"

    # Сохраняем
    outputs = {
        "data/train.jsonl": train,
        "data/valid.jsonl": valid,
        "data/test.jsonl": test,
    }

    for path, part in outputs.items():
        with open(path, "w", encoding="utf-8") as f:
            for item in part:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"  {path}: {len(part)} примеров")

    print(f"\nРАЗБИЕНИЕ:")
    print(f"  Train: {len(train)} ({len(train) / len(items) * 100:.1f}%)")
    print(f"  Valid: {len(valid)} ({len(valid) / len(items) * 100:.1f}%)")
    print(f"  Test:  {len(test)} ({len(test) / len(items) * 100:.1f}%)")


if __name__ == "__main__":
    split_dataset()