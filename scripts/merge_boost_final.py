# scripts/merge_boost_final.py
import json
from pathlib import Path

final_path = Path("data/final_dataset.jsonl")
boost_path = Path("data/boost_final.jsonl")

# Читаем финальный датасет
final_items = []
with open(final_path, encoding="utf-8") as f:
    for line in f:
        if line.strip():
            final_items.append(json.loads(line))

# Читаем boost
boost_items = []
with open(boost_path, encoding="utf-8") as f:
    for line in f:
        if line.strip():
            boost_items.append(json.loads(line))

# Объединяем
all_items = final_items + boost_items

# Перенумеруем
for i, item in enumerate(all_items):
    item["id"] = f"final_{i+1:05d}"

print(f"Финальный датасет: {len(final_items)}")
print(f"Boost примеры: {len(boost_items)}")
print(f"ИТОГО: {len(all_items)}")

# Сохраняем
with open(final_path, "w", encoding="utf-8") as f:
    for item in all_items:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print(f"Сохранено: {final_path}")