# scripts/collectors/collect_cwe.py (ИСПРАВЛЕННАЯ ВЕРСИЯ)
"""
Сбор примеров кода из официального CWE XML.
"""
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
import json
from pathlib import Path

CWE_URL = "https://cwe.mitre.org/data/xml/cwec_latest.xml.zip"

# Интересующие нас CWE
TARGET_CWES = {
    "95": ("eval_usage", "Eval Injection"),
    "78": ("shell_true", "OS Command Injection"),
    "89": ("sql_concat", "SQL Injection"),
    "328": ("weak_hash", "Weak Hash"),
    "798": ("hardcoded_creds", "Hard-coded Credentials"),
    "502": ("insecure_code", "Deserialization of Untrusted Data"),
}


def download_and_extract() -> Path:
    zip_path = Path("data/raw/cwec.zip")
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    if not zip_path.exists():
        print("Скачиваю CWE XML (может занять время)...")
        urllib.request.urlretrieve(CWE_URL, zip_path)

    extract_dir = Path("data/raw/cwec")
    if not extract_dir.exists():
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extract_dir)

    xml_files = list(extract_dir.glob("*.xml"))
    return xml_files[0]


def get_text(element, tag, ns):
    """Безопасно извлекает текст из элемента."""
    el = element.find(f"{ns}{tag}")
    return el.text.strip() if el is not None and el.text else ""


def parse_cwe_xml(xml_path: Path) -> list[dict]:
    """Парсит CWE XML и извлекает примеры кода."""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Определяем namespace
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    items = []

    # Ищем все Weakness элементы
    for weakness in root.iter(f"{ns}Weakness"):
        cwe_id = weakness.get("ID")

        if cwe_id not in TARGET_CWES:
            continue

        insecure_type, description = TARGET_CWES[cwe_id]

        # Ищем примеры в Demonstrative_Examples
        demo_examples = weakness.find(f"{ns}Demonstrative_Examples")
        if demo_examples is None:
            continue

        for example in demo_examples.findall(f"{ns}Demonstrative_Example"):
            # Ищем код в Example_Code
            example_code = example.find(f"{ns}Example_Code")
            if example_code is None:
                continue

            code_text = example_code.text
            if not code_text or len(code_text.strip()) < 10:
                continue

            # Извлекаем описание
            intro_text = get_text(example, "Intro_Text", ns)

            items.append({
                "cwe_id": f"CWE-{cwe_id}",
                "insecure_type": insecure_type,
                "description": description,
                "code": code_text.strip(),
                "explanation": intro_text,
            })

    return items


def to_dataset_item(raw: dict, idx: int) -> dict:
    """Конвертирует CWE-пример в формат DatasetItem."""
    # Определяем язык по содержимому
    code = raw["code"]
    language = "python"
    if "#include" in code or "printf" in code:
        language = "c"
    elif "<?php" in code:
        language = "php"
    elif "import java" in code or "public class" in code:
        language = "java"

    return {
        "id": f"real_cwe_{raw['cwe_id']}_{idx:03d}",
        "source": "opensource",
        "language": language,
        "file_path": f"cwe/{raw['cwe_id']}.{language}",
        "line_number": 1,
        "context_before": "",
        "target_snippet": raw["code"][:1000],
        "context_after": "",
        "labels": {
            "is_secret": False,
            "is_insecure": True,
            "secret_type": None,
            "insecure_type": raw["insecure_type"],
        },
        "metadata": {
            "cwe_id": raw["cwe_id"],
            "difficulty": "medium",
            "note": raw.get("explanation", raw["description"])[:200],
        },
    }


def main():
    xml_path = download_and_extract()
    print(f"Парсю {xml_path}...")

    raw_items = parse_cwe_xml(xml_path)
    print(f"Найдено примеров CWE: {len(raw_items)}")

    items = [to_dataset_item(r, i) for i, r in enumerate(raw_items)]

    out = Path("data/collected/cwe.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"✅ Собрано примеров: {len(items)} → {out}")


if __name__ == "__main__":
    main()