# generators/build_dataset.py
import json
from python_generation import generate_python_dataset
from c_generation import generate_c_dataset


def main():
    py_data = generate_python_dataset(n_per_class=40)  # ~600 примеров
    c_data = generate_c_dataset(n_per_class=35)  # ~350 примеров

    all_data = py_data + c_data

    # Пронумеруем заново
    for i, item in enumerate(all_data):
        item["id"] = f"example_{i + 1:05d}"

    with open("data/dataset.jsonl", "w", encoding="utf-8") as f:
        for item in all_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Total examples: {len(all_data)}")
    print(f"  Python: {len(py_data)}")
    print(f"  C: {len(c_data)}")


if __name__ == "__main__":
    main()