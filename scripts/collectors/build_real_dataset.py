# scripts/collectors/build_real_dataset.py
"""
Объединяет все собранные данные в единый датасет.
"""
import json
from pathlib import Path


def merge_collected():
    collected_dir = Path("data/collected")
    all_items = []

    for jsonl_file in collected_dir.glob("*.jsonl"):
        print(f"Читаю {jsonl_file}...")
        with open(jsonl_file, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    all_items.append(json.loads(line))

    print(f"Всего собрано: {len(all_items)}")

    # Переименовываем id
    for i, item in enumerate(all_items):
        item["id"] = f"real_{i + 1:05d}"

    out = Path("data/real_cases.jsonl")
    with open(out, "w", encoding="utf-8") as f:
        for item in all_items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"✅ Объединённый датасет: {out}")


if __name__ == "__main__":
    merge_collected()