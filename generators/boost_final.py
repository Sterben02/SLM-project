# generators/boost_final.py
"""
Финальная генерация для закрытия недели 6:
1. Добавляет exec_usage (не хватает 10 примеров)
2. Добавляет 500+ негативных примеров (для снижения FPR)
"""
import json
import random
import string
from pathlib import Path

random.seed(42)


def random_string(length: int, charset: str = string.ascii_letters + string.digits) -> str:
    return ''.join(random.choice(charset) for _ in range(length))


# ==========================================
# 1. EXEC_USAGE (нужно ещё 10+)
# ==========================================

def generate_exec_usage(n: int = 20) -> list[dict]:
    """Генерирует примеры использования exec()."""
    items = []
    variants = [
        ("exec(user_code)", "code = request.data\n"),
        ("exec(code_from_api)", "code_from_api = fetch_remote_code()\n"),
        ("exec(script_content)", "script_content = read_script()\n"),
        ("exec(payload)", "payload = get_payload()\n"),
    ]

    for i in range(n):
        snippet, context = random.choice(variants)
        items.append({
            "id": f"boost_exec_{i:04d}",
            "source": "synthetic",
            "language": "python",
            "file_path": f"boost/exec_{i}.py",
            "line_number": random.randint(1, 30),
            "context_before": context,
            "target_snippet": snippet,
            "context_after": "\n",
            "labels": {
                "is_secret": False,
                "is_insecure": True,
                "secret_type": None,
                "insecure_type": "exec_usage",
            },
            "metadata": {"difficulty": "medium"},
        })

    return items


# ==========================================
# 2. НЕГАТИВНЫЕ ПРИМЕРЫ (главная часть)
# ==========================================

def generate_safe_sql(n: int = 100) -> list[dict]:
    """Параметризованные SQL-запросы (безопасная альтернатива)."""
    items = []
    variants = [
        'cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))',
        'cursor.execute("SELECT * FROM users WHERE name = ?", (name,))',
        'db.query("INSERT INTO logs (msg) VALUES (%s)", (message,))',
        'cursor.execute("UPDATE users SET email = %s WHERE id = %s", (email, uid))',
    ]

    for i in range(n):
        items.append({
            "id": f"neg_sql_{i:04d}",
            "source": "synthetic",
            "language": "python",
            "file_path": f"negative/db_{i}.py",
            "line_number": random.randint(1, 50),
            "context_before": "def get_user(user_id):\n    cursor = db.cursor()\n",
            "target_snippet": f"    {random.choice(variants)}",
            "context_after": "\n    return cursor.fetchone()\n",
            "labels": {
                "is_secret": False,
                "is_insecure": False,
                "secret_type": None,
                "insecure_type": None,
            },
            "metadata": {"difficulty": "hard", "note": "параметризованный запрос"},
        })

    return items


def generate_env_secrets(n: int = 100) -> list[dict]:
    """Секреты из переменных окружения (безопасно)."""
    items = []
    variants = [
        'API_KEY = os.getenv("API_KEY")',
        'DB_PASSWORD = os.environ["DB_PASSWORD"]',
        'SECRET = os.getenv("SECRET", "")',
        'TOKEN = os.environ.get("AUTH_TOKEN")',
        'API_KEY = get_secret_from_vault("api_key")',
    ]

    for i in range(n):
        items.append({
            "id": f"neg_env_{i:04d}",
            "source": "synthetic",
            "language": "python",
            "file_path": f"negative/config_{i}.py",
            "line_number": random.randint(1, 30),
            "context_before": "import os\n\n# Configuration\n",
            "target_snippet": random.choice(variants),
            "context_after": "\n",
            "labels": {
                "is_secret": False,
                "is_insecure": False,
                "secret_type": None,
                "insecure_type": None,
            },
            "metadata": {"difficulty": "medium", "note": "секрет из env"},
        })

    return items


def generate_test_values(n: int = 80) -> list[dict]:
    """Тестовые и плейсхолдер-значения (ложные срабатывания)."""
    items = []
    variants = [
        'API_KEY = "test_key_for_local_dev"',
        'API_KEY = "YOUR_API_KEY_HERE"',
        'API_KEY = "sk-test-000000000000000000000000"',
        'password = "changeme"',
        'TOKEN = "example_token_replace_me"',
        'SECRET = "xxxxxxxxxxxxxxxxxxxxxxxx"',
        'API_KEY = "<your-api-key>"',
        'TOKEN = "dummy_token_for_tests"',
    ]

    for i in range(n):
        items.append({
            "id": f"neg_test_{i:04d}",
            "source": "synthetic",
            "language": "python",
            "file_path": f"negative/test_{i}.py",
            "line_number": random.randint(1, 30),
            "context_before": "# Test configuration\n",
            "target_snippet": random.choice(variants),
            "context_after": "\n",
            "labels": {
                "is_secret": False,
                "is_insecure": False,
                "secret_type": None,
                "insecure_type": None,
            },
            "metadata": {"difficulty": "hard", "note": "тестовое значение"},
        })

    return items


def generate_uuids_and_hashes(n: int = 80) -> list[dict]:
    """UUID, хэши, base64 — похожи на секреты, но не секреты."""
    items = []

    for i in range(n):
        variant_type = random.choice(["uuid", "hash", "base64", "commit"])

        if variant_type == "uuid":
            value = f"{random_string(8, '0123456789abcdef')}-{random_string(4, '0123456789abcdef')}-{random_string(4, '0123456789abcdef')}-{random_string(4, '0123456789abcdef')}-{random_string(12, '0123456789abcdef')}"
            var = random.choice(["user_id", "session_id", "request_id", "object_id"])
            note = "UUID"
        elif variant_type == "hash":
            value = random_string(64, "0123456789abcdef")
            var = random.choice(["file_hash", "checksum", "sha256_sum", "content_hash"])
            note = "SHA-256 хэш файла"
        elif variant_type == "base64":
            value = random_string(44, string.ascii_letters + string.digits + "+/=")
            var = random.choice(["encoded_data", "base64_content", "serialized"])
            note = "base64-кодированные данные"
        else:
            value = random_string(40, "0123456789abcdef")
            var = random.choice(["commit_hash", "git_sha", "revision"])
            note = "git commit hash"

        items.append({
            "id": f"neg_hash_{i:04d}",
            "source": "synthetic",
            "language": "python",
            "file_path": f"negative/data_{i}.py",
            "line_number": random.randint(1, 40),
            "context_before": "# Data processing\n",
            "target_snippet": f'{var} = "{value}"',
            "context_after": "\n",
            "labels": {
                "is_secret": False,
                "is_insecure": False,
                "secret_type": None,
                "insecure_type": None,
            },
            "metadata": {"difficulty": "hard", "note": note},
        })

    return items


def generate_safe_subprocess(n: int = 60) -> list[dict]:
    """Безопасный subprocess (без shell=True)."""
    items = []
    variants = [
        'subprocess.run(["ls", user_dir])',
        'subprocess.run(["git", "status"], capture_output=True)',
        'subprocess.call(["python", script_path])',
        'subprocess.Popen(["cat", filename], stdout=subprocess.PIPE)',
    ]

    for i in range(n):
        items.append({
            "id": f"neg_subprocess_{i:04d}",
            "source": "synthetic",
            "language": "python",
            "file_path": f"negative/utils_{i}.py",
            "line_number": random.randint(1, 40),
            "context_before": "import subprocess\n\ndef run_command(user_dir):\n",
            "target_snippet": f"    {random.choice(variants)}",
            "context_after": "\n",
            "labels": {
                "is_secret": False,
                "is_insecure": False,
                "secret_type": None,
                "insecure_type": None,
            },
            "metadata": {"difficulty": "medium", "note": "безопасный subprocess"},
        })

    return items


def generate_safe_hash(n: int = 60) -> list[dict]:
    """Безопасные хэши (SHA-256, bcrypt)."""
    items = []
    variants = [
        "hashlib.sha256(password.encode()).hexdigest()",
        "hashlib.sha512(data).digest()",
        "bcrypt.hashpw(password.encode(), bcrypt.gensalt())",
        "hashlib.blake2b(content).hexdigest()",
    ]

    for i in range(n):
        items.append({
            "id": f"neg_hash_safe_{i:04d}",
            "source": "synthetic",
            "language": "python",
            "file_path": f"negative/crypto_{i}.py",
            "line_number": random.randint(1, 30),
            "context_before": "import hashlib\n",
            "target_snippet": random.choice(variants),
            "context_after": "\n",
            "labels": {
                "is_secret": False,
                "is_insecure": False,
                "secret_type": None,
                "insecure_type": None,
            },
            "metadata": {"difficulty": "medium", "note": "безопасный хэш"},
        })

    return items


def generate_safe_eval(n: int = 60) -> list[dict]:
    """Безопасные альтернативы eval."""
    items = []
    variants = [
        "result = ast.literal_eval(user_input)",
        "result = eval(\"2 + 2\")",  # константа
        "value = json.loads(json_string)",
        "result = safe_eval(expression)",
    ]

    for i in range(n):
        items.append({
            "id": f"neg_eval_{i:04d}",
            "source": "synthetic",
            "language": "python",
            "file_path": f"negative/calc_{i}.py",
            "line_number": random.randint(1, 30),
            "context_before": "import ast\nimport json\n",
            "target_snippet": random.choice(variants),
            "context_after": "\n",
            "labels": {
                "is_secret": False,
                "is_insecure": False,
                "secret_type": None,
                "insecure_type": None,
            },
            "metadata": {"difficulty": "medium", "note": "безопасная альтернатива eval"},
        })

    return items


def generate_regular_code(n: int = 100) -> list[dict]:
    """Обычный код без секретов и уязвимостей."""
    items = []
    variants = [
        ("def calculate_sum(a, b):\n    return a + b", "math_utils"),
        ("class User:\n    def __init__(self, name):\n        self.name = name", "models"),
        ("for item in items:\n    process(item)", "main"),
        ("import logging\nlogger = logging.getLogger(__name__)", "app"),
        ("def validate_email(email):\n    return '@' in email", "validators"),
        ("data = [x ** 2 for x in range(10)]", "processing"),
        ("with open('file.txt', 'r') as f:\n    content = f.read()", "io_utils"),
        ("result = sorted(items, key=lambda x: x.date)", "sorting"),
    ]

    for i in range(n):
        code, filename = random.choice(variants)
        items.append({
            "id": f"neg_regular_{i:04d}",
            "source": "synthetic",
            "language": "python",
            "file_path": f"negative/{filename}_{i}.py",
            "line_number": random.randint(1, 20),
            "context_before": "",
            "target_snippet": code,
            "context_after": "\n",
            "labels": {
                "is_secret": False,
                "is_insecure": False,
                "secret_type": None,
                "insecure_type": None,
            },
            "metadata": {"difficulty": "easy", "note": "обычный код"},
        })

    return items


def generate_commented_secrets(n: int = 50) -> list[dict]:
    """Закомментированные секреты (не должны срабатывать)."""
    items = []
    variants = [
        '# API_KEY = "old_key_do_not_use"',
        '# password = "admin123"  # deprecated',
        '# TOKEN = "expired_token_xyz"',
        '# SECRET = "legacy_secret_value"',
    ]

    for i in range(n):
        items.append({
            "id": f"neg_commented_{i:04d}",
            "source": "synthetic",
            "language": "python",
            "file_path": f"negative/legacy_{i}.py",
            "line_number": random.randint(1, 30),
            "context_before": "# Legacy code - do not use\n",
            "target_snippet": random.choice(variants),
            "context_after": "\n",
            "labels": {
                "is_secret": False,
                "is_insecure": False,
                "secret_type": None,
                "insecure_type": None,
            },
            "metadata": {"difficulty": "hard", "note": "закомментированный секрет"},
        })

    return items


# ==========================================
# ГЛАВНАЯ ФУНКЦИЯ
# ==========================================

def main():
    print("🔧 Финальная генерация для закрытия недели 6...")
    print()

    all_items = []

    # 1. Добавляем exec_usage
    print("Генерация exec_usage...")
    exec_items = generate_exec_usage(20)
    all_items.extend(exec_items)
    print(f"   ✅ {len(exec_items)} примеров")

    # 2. Генерируем негативные примеры
    print("\nГенерация негативных примеров:")

    generators = [
        ("Параметризованные SQL", generate_safe_sql(100)),
        ("Секреты из env", generate_env_secrets(100)),
        ("Тестовые значения", generate_test_values(80)),
        ("UUID/хэши/base64", generate_uuids_and_hashes(80)),
        ("Безопасный subprocess", generate_safe_subprocess(60)),
        ("Безопасные хэши", generate_safe_hash(60)),
        ("Безопасный eval", generate_safe_eval(60)),
        ("Обычный код", generate_regular_code(100)),
        ("Закомментированные секреты", generate_commented_secrets(50)),
    ]

    total_negative = 0
    for name, items in generators:
        all_items.extend(items)
        total_negative += len(items)
        print(f"   • {name}: {len(items)}")

    print(f"\n   Всего негативных: {total_negative}")
    print(f"\nИТОГО СГЕНЕРИРОВАНО: {len(all_items)} примеров")

    # Сохраняем
    out = Path("data/boost_final.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for item in all_items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"💾 Сохранено: {out}")

    # Прогноз
    print("\nПРОГНОЗ ПОСЛЕ ОБЪЕДИНЕНИЯ:")
    print(f"   Было: 2771 пример (19.2% негативных)")
    print(f"   Добавляем: {len(all_items)} ({total_negative} негативных)")
    new_total = 2771 + len(all_items)
    new_negative = 531 + total_negative
    new_percent = new_negative / new_total * 100
    print(f"   Станет: {new_total} примеров ({new_percent:.1f}% негативных)")


if __name__ == "__main__":
    main()