# scripts/collectors/load_huggingface_datasets.py
"""
Загрузка выбранных датасетов с HuggingFace.
"""
from datasets import load_dataset
import json
from pathlib import Path

# Рекомендуемые датасеты (на основе вашего поиска)
RECOMMENDED_DATASETS = [
    {
        "id": "CyberNative/Code_Vulnerability_Security_DPO",
        "description": "Большой датасет с уязвимостями (1371 загрузок, 165 лайков)",
        "priority": "high",
    },
    {
        "id": "lemon42-ai/Code_Vulnerability_Labeled_Dataset",
        "description": "Размеченный датасет уязвимостей (562 загрузок)",
        "priority": "high",
    },
    {
        "id": "ayshajavd/code-security-vulnerability-dataset",
        "description": "Датасет безопасности кода (420 загрузок)",
        "priority": "medium",
    },
]


def load_and_convert(dataset_id: str, idx: int) -> list[dict]:
    """Загружает датасет и конвертирует в наш формат."""
    print(f"\n📥 Загружаю {dataset_id}...")

    try:
        ds = load_dataset(dataset_id)
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        return []

    items = []

    # Обрабатываем train split (или первый доступный)
    split_name = "train" if "train" in ds else list(ds.keys())[0]
    data = ds[split_name]

    print(f"  Записей: {len(data)}")
    print(f"  Колонки: {data.column_names}")

    # Пытаемся адаптировать под наш формат
    for i, row in enumerate(data):
        # Это заглушка — нужно адаптировать под конкретную структуру датасета
        # В реальности нужно смотреть на column_names и маппить поля

        item = {
            "id": f"hf_{dataset_id.replace('/', '_')}_{i:05d}",
            "source": "opensource",
            "language": "python",  # Угадываем или берём из данных
            "file_path": f"huggingface/{dataset_id.replace('/', '_')}.py",
            "line_number": 1,
            "context_before": "",
            "target_snippet": str(row.get("code", row.get("text", str(row))))[:1000],
            "context_after": "",
            "labels": {
                "is_secret": False,
                "is_insecure": True,  # Предполагаем
                "secret_type": None,
                "insecure_type": "insecure_code",  # Нужно маппить
            },
            "metadata": {
                "source_dataset": dataset_id,
                "original_data": str(row)[:200],
                "note": "⚠️ Автоматическая конвертация — требуется ручная проверка",
            },
        }
        items.append(item)

        if i >= 100:  # Ограничиваем для теста
            break

    return items


def main():
    all_items = []

    for ds_info in RECOMMENDED_DATASETS:
        if ds_info["priority"] == "high":
            items = load_and_convert(ds_info["id"], len(all_items))
            all_items.extend(items)

    out = Path("data/collected/huggingface.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for item in all_items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"\n✅ Загружено примеров: {len(all_items)} → {out}")
    print("⚠️  ВАЖНО: проверьте структуру и разметку каждого датасета вручную!")


if __name__ == "__main__":
    main()