# generators/boost_missing_classes.py
"""
Генерация дополнительных примеров для классов с недостаточным количеством.
"""
import json
import random
import string
from pathlib import Path

random.seed(42)


def random_string(length: int, charset: str = string.ascii_letters + string.digits) -> str:
    return ''.join(random.choice(charset) for _ in range(length))


def generate_api_keys(n: int = 50) -> list[dict]:
    """Генерирует примеры API ключей."""
    items = []
    prefixes = ["sk-", "pk-", "key-", "api_", "secret_"]
    var_names = ["API_KEY", "SECRET_KEY", "SERVICE_KEY", "APP_KEY", "MASTER_KEY"]

    for i in range(n):
        prefix = random.choice(prefixes)
        var = random.choice(var_names)
        key = prefix + random_string(32 + random.randint(0, 16))

        items.append({
            "id": f"boost_api_key_{i:04d}",
            "source": "synthetic",
            "language": "python",
            "file_path": f"boost/config_{i}.py",
            "line_number": random.randint(1, 50),
            "context_before": "import os\n\n# Configuration\n",
            "target_snippet": f'{var} = "{key}"',
            "context_after": "\nDEBUG = True\n",
            "labels": {
                "is_secret": True,
                "is_insecure": False,
                "secret_type": "api_key",
                "insecure_type": None,
            },
            "metadata": {"difficulty": "easy"},
        })

    return items


def generate_access_tokens(n: int = 50) -> list[dict]:
    """Генерирует примеры access токенов."""
    items = []
    token_formats = [
        ("ghp_", 36),  # GitHub
        ("glpat-", 20),  # GitLab
        ("xoxb-", 48),  # Slack
        ("github_pat_", 82),  # GitHub fine-grained
    ]

    for i in range(n):
        prefix, length = random.choice(token_formats)
        token = prefix + random_string(length, string.ascii_letters + string.digits + "-_")
        var = random.choice(["TOKEN", "ACCESS_TOKEN", "AUTH_TOKEN", "GITHUB_TOKEN"])

        items.append({
            "id": f"boost_token_{i:04d}",
            "source": "synthetic",
            "language": "python",
            "file_path": f"boost/auth_{i}.py",
            "line_number": random.randint(1, 30),
            "context_before": "# Authentication\n",
            "target_snippet": f'{var} = "{token}"',
            "context_after": "\n",
            "labels": {
                "is_secret": True,
                "is_insecure": False,
                "secret_type": "access_token",
                "insecure_type": None,
            },
            "metadata": {"difficulty": "easy"},
        })

    return items


def generate_passwords(n: int = 50) -> list[dict]:
    """Генерирует примеры паролей."""
    items = []
    var_names = ["PASSWORD", "DB_PASSWORD", "MYSQL_PASSWORD", "ADMIN_PASSWORD", "USER_PASSWORD"]

    for i in range(n):
        var = random.choice(var_names)
        pwd = random_string(8 + random.randint(0, 8)) + random.choice(["!", "@", "#", "123"])

        items.append({
            "id": f"boost_password_{i:04d}",
            "source": "synthetic",
            "language": "python",
            "file_path": f"boost/db_{i}.py",
            "line_number": random.randint(1, 40),
            "context_before": "# Database configuration\n",
            "target_snippet": f'{var} = "{pwd}"',
            "context_after": "\n",
            "labels": {
                "is_secret": True,
                "is_insecure": False,
                "secret_type": "password",
                "insecure_type": None,
            },
            "metadata": {"difficulty": "easy"},
        })

    return items


def generate_private_keys(n: int = 50) -> list[dict]:
    """Генерирует примеры приватных ключей."""
    items = []

    for i in range(n):
        key_type = random.choice(["RSA", "EC", "DSA"])
        body = random_string(200, string.ascii_letters + string.digits + "+/=")
        key = f"-----BEGIN {key_type} PRIVATE KEY-----\n{body}\n-----END {key_type} PRIVATE KEY-----"

        items.append({
            "id": f"boost_pkey_{i:04d}",
            "source": "synthetic",
            "language": "python",
            "file_path": f"boost/crypto_{i}.py",
            "line_number": 1,
            "context_before": "",
            "target_snippet": f'PRIVATE_KEY = """{key}"""',
            "context_after": "\n",
            "labels": {
                "is_secret": True,
                "is_insecure": False,
                "secret_type": "private_key",
                "insecure_type": None,
            },
            "metadata": {"difficulty": "easy"},
        })

    return items


def generate_jwt(n: int = 50) -> list[dict]:
    """Генерирует примеры JWT токенов."""
    items = []

    for i in range(n):
        parts = [
            random_string(20 + random.randint(0, 10), string.ascii_letters + string.digits + "-_"),
            random_string(30 + random.randint(0, 20), string.ascii_letters + string.digits + "-_"),
            random_string(40 + random.randint(0, 20), string.ascii_letters + string.digits + "-_"),
        ]
        jwt = f"eyJhbGciOiJIUzI1NiJ9.{parts[0]}.{parts[1]}.{parts[2]}"

        items.append({
            "id": f"boost_jwt_{i:04d}",
            "source": "synthetic",
            "language": "python",
            "file_path": f"boost/auth_{i}.py",
            "line_number": random.randint(1, 30),
            "context_before": "# JWT token\n",
            "target_snippet": f'token = "{jwt}"',
            "context_after": "\n",
            "labels": {
                "is_secret": True,
                "is_insecure": False,
                "secret_type": "jwt",
                "insecure_type": None,
            },
            "metadata": {"difficulty": "easy"},
        })

    return items


def generate_shell_true(n: int = 50) -> list[dict]:
    """Генерирует примеры shell=True."""
    items = []
    variants = [
        'subprocess.run(f"ls {user_dir}", shell=True)',
        'subprocess.call("rm -rf " + path, shell=True)',
        'os.system(f"cat {filename}")',
        'subprocess.Popen(cmd, shell=True)',
    ]

    for i in range(n):
        items.append({
            "id": f"boost_shell_{i:04d}",
            "source": "synthetic",
            "language": "python",
            "file_path": f"boost/utils_{i}.py",
            "line_number": random.randint(1, 50),
            "context_before": "import subprocess\n\ndef run_command(user_input):\n",
            "target_snippet": f"    {random.choice(variants)}",
            "context_after": "\n",
            "labels": {
                "is_secret": False,
                "is_insecure": True,
                "secret_type": None,
                "insecure_type": "shell_true",
            },
            "metadata": {"difficulty": "medium"},
        })

    return items


def generate_hardcoded_creds(n: int = 50) -> list[dict]:
    """Генерирует примеры захардкоженных учётных данных."""
    items = []
    variants = [
        'credentials = {"username": "admin", "password": "admin123"}',
        'login("root", "toor")',
        'USER, PASS = "admin", "secret"',
        'auth = {"user": "test", "pwd": "test123"}',
    ]

    for i in range(n):
        items.append({
            "id": f"boost_creds_{i:04d}",
            "source": "synthetic",
            "language": "python",
            "file_path": f"boost/auth_{i}.py",
            "line_number": random.randint(1, 30),
            "context_before": "# Login\n",
            "target_snippet": random.choice(variants),
            "context_after": "\n",
            "labels": {
                "is_secret": False,
                "is_insecure": True,
                "secret_type": None,
                "insecure_type": "hardcoded_creds",
            },
            "metadata": {"difficulty": "easy"},
        })

    return items


def generate_weak_hash(n: int = 50) -> list[dict]:
    """Генерирует примеры слабых хэшей."""
    items = []

    for i in range(n):
        algo = random.choice(["md5", "sha1"])
        items.append({
            "id": f"boost_hash_{i:04d}",
            "source": "synthetic",
            "language": "python",
            "file_path": f"boost/crypto_{i}.py",
            "line_number": random.randint(1, 40),
            "context_before": "import hashlib\n",
            "target_snippet": f"hashlib.{algo}(password.encode()).hexdigest()",
            "context_after": "\n",
            "labels": {
                "is_secret": False,
                "is_insecure": True,
                "secret_type": None,
                "insecure_type": "weak_hash",
            },
            "metadata": {"difficulty": "medium"},
        })

    return items


def main():
    """Генерирует дополнительные примеры для недостающих классов."""
    print("🔧 Генерация дополнительных примеров для недостающих классов...")

    all_items = []

    # Секреты
    all_items.extend(generate_api_keys(50))
    all_items.extend(generate_access_tokens(50))
    all_items.extend(generate_passwords(50))
    all_items.extend(generate_private_keys(50))
    all_items.extend(generate_jwt(50))

    # Небезопасный код
    all_items.extend(generate_shell_true(50))
    all_items.extend(generate_hardcoded_creds(50))
    all_items.extend(generate_weak_hash(50))

    print(f"✅ Сгенерировано: {len(all_items)} примеров")

    # Сохраняем
    out = Path("data/boost_examples.jsonl")
    with open(out, "w", encoding="utf-8") as f:
        for item in all_items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"💾 Сохранено: {out}")

    return all_items


if __name__ == "__main__":
    main()