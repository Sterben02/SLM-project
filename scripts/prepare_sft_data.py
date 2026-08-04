# scripts/prepare_sft_data.py
"""
Конвертация dataset.jsonl в SFT-формат для обучения Qwen2.5-Coder-1.5B.
Формат: instruction -> input -> output (JSON с объяснением).
"""
import json
import random
from pathlib import Path

random.seed(42)

INSTRUCTION = (
    "Ты — эксперт по безопасности кода. Проанализируй фрагмент кода и определи:\n"
    "1. Содержит ли он секрет (API-ключ, токен, пароль, приватный ключ, JWT).\n"
    "2. Содержит ли он небезопасный паттерн (eval, exec, shell=True, "
    "SQL-конкатенация, слабый хэш, захардкоженные учётные данные).\n\n"
    "Ответь строго в формате JSON:\n"
    '{"is_secret": bool, "secret_type": str|null, "is_insecure": bool, '
    '"insecure_type": str|null, "confidence": float, "explanation": str}'
)

# Шаблоны объяснений (rule-based, как в ТЗ пункт 6.5)
SECRET_EXPLANATIONS = {
    "api_key": "Строка похожа на hardcoded API key: имя переменной содержит KEY, "
               "значение имеет высокую энтропию и не является тестовым.",
    "access_token": "Обнаружен hardcoded access token: префикс соответствует "
                    "реальному формату провайдера (ghp_/glpat-/xoxb-).",
    "password": "Захардкоженный пароль в коде. Значение передаётся явно, "
                "а не через переменные окружения.",
    "private_key": "Обнаружен приватный ключ в PEM-формате (-----BEGIN ... KEY-----). "
                   "Это критический секрет.",
    "jwt": "Обнаружен hardcoded JWT token (три base64-части, разделённые точками).",
}

INSECURE_EXPLANATIONS = {
    "eval_usage": "Использование eval() с динамическим вводом может привести "
                  "к выполнению произвольного кода (RCE).",
    "exec_usage": "Использование exec() с динамическим вводом может привести "
                  "к выполнению произвольного кода (RCE).",
    "shell_true": "Вызов subprocess/shell с shell=True и динамическим вводом "
                  "подвержен инъекции команд.",
    "sql_concat": "SQL-запрос формируется конкатенацией строк — это подвержено "
                  "SQL-инъекции. Используйте параметризованные запросы.",
    "weak_hash": "MD5/SHA1 небезопасны для хэширования паролей. "
                 "Используйте bcrypt, scrypt или Argon2.",
    "hardcoded_creds": "Учётные данные захардкожены в коде. "
                       "Используйте переменные окружения или secret manager.",
    "insecure_code": "Фрагмент содержит небезопасный паттерн кода.",
}

NEGATIVE_EXPLANATION = (
    "Фрагмент не содержит секретов или небезопасных паттернов: "
    "значения берутся из окружения, являются тестовыми или код использует "
    "безопасные альтернативы."
)


def build_explanation(labels: dict) -> str:
    """Генерирует объяснение по меткам (template-based)."""
    if labels["is_secret"]:
        return SECRET_EXPLANATIONS.get(
            labels["secret_type"], "Обнаружен hardcoded секрет."
        )
    if labels["is_insecure"]:
        return INSECURE_EXPLANATIONS.get(
            labels["insecure_type"], "Обнаружен небезопасный паттерн."
        )
    return NEGATIVE_EXPLANATION


def convert_item(item: dict) -> dict:
    """Конвертирует DatasetItem в SFT-формат."""
    labels = item["labels"]

    input_text = (
        f"Язык: {item['language']}\n"
        f"Файл: {item['file_path']}\n\n"
        f"```{item['language']}\n"
        f"{item['context_before']}"
        f"{item['target_snippet']}\n"
        f"{item['context_after']}"
        f"```"
    )

    confidence = 0.92 if (labels["is_secret"] or labels["is_insecure"]) else 0.88

    output = {
        "is_secret": labels["is_secret"],
        "secret_type": labels["secret_type"],
        "is_insecure": labels["is_insecure"],
        "insecure_type": labels["insecure_type"],
        "confidence": confidence,
        "explanation": build_explanation(labels),
    }

    return {
        "instruction": INSTRUCTION,
        "input": input_text,
        "output": json.dumps(output, ensure_ascii=False),
    }


def main():
    splits = {
        "data/train.jsonl": "data/sft_train.jsonl",
        "data/valid.jsonl": "data/sft_valid.jsonl",
        "data/test.jsonl": "data/sft_test.jsonl",
    }

    for src, dst in splits.items():
        if not Path(src).exists():
            print(f"  Пропускаю {src} (не найден)")
            continue

        items = []
        with open(src, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    items.append(json.loads(line))

        sft_items = [convert_item(i) for i in items]

        with open(dst, "w", encoding="utf-8") as f:
            for sft in sft_items:
                f.write(json.dumps(sft, ensure_ascii=False) + "\n")

        print(f"{src} → {dst} ({len(sft_items)} примеров)")

    # Показываем пример результата
    print("\nПРИМЕР SFT-ЗАПИСИ:")
    with open("data/sft_train.jsonl", encoding="utf-8") as f:
        print(json.dumps(json.loads(f.readline()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
