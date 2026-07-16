# generators/python_generator.py
import json
import random
import string
from typing import List, Dict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scanner.models.dataset import DatasetItem, Labels, Metadata


def random_string(length: int, charset: str = string.ascii_letters + string.digits) -> str:
    return ''.join(random.choice(charset) for _ in range(length))


def calc_entropy(s: str) -> float:
    if not s:
        return 0.0
    prob = [s.count(c) / len(s) for c in set(s)]
    return -sum(p * __import__('math').log2(p) for p in prob)


def make_item(
        item_id: str,
        snippet: str,
        context_before: str,
        context_after: str,
        is_secret: bool,
        is_insecure: bool,
        secret_type=None,
        insecure_type=None,
        variable_name: str = None,
        difficulty: str = "medium",
        note: str = None,
) -> Dict:
    return DatasetItem(
        id=item_id,
        source="synthetic",
        language="python",
        file_path=f"generated/sample_{item_id}.py",
        line_number=context_before.count('\n') + 1,
        context_before=context_before,
        target_snippet=snippet,
        context_after=context_after,
        labels=Labels(
            is_secret=is_secret,
            is_insecure=is_insecure,
            secret_type=secret_type,
            insecure_type=insecure_type,
        ),
        metadata=Metadata(
            entropy=calc_entropy(snippet),
            variable_name=variable_name,
            difficulty=difficulty,
            note=note,
        ),
    ).model_dump()


# ============ СЕКРЕТЫ ============

def gen_api_key_positive(i: int) -> Dict:
    key = random_string(40)
    var_names = ["API_KEY", "OPENAI_API_KEY", "STRIPE_KEY", "SERVICE_API_KEY"]
    var = random.choice(var_names)
    return make_item(
        f"py_secret_api_pos_{i:04d}",
        f'{var} = "{key}"',
        "import os\n\n# Configuration\n",
        "\nDEBUG = True\n",
        is_secret=True, is_insecure=False,
        secret_type="api_key",
        variable_name=var,
        difficulty="easy",
    )


def gen_api_key_negative(i: int) -> Dict:
    cases = [
        ('API_KEY = "test_key_for_local_dev"', "тестовый ключ"),
        ('API_KEY = "YOUR_API_KEY_HERE"', "плейсхолдер"),
        ('# API_KEY = "sk-real-looking-key"', "закомментировано"),
        ('API_KEY = os.getenv("API_KEY")', "из env"),
        ('API_KEY = ""', "пустой"),
    ]
    snippet, note = random.choice(cases)
    return make_item(
        f"py_secret_api_neg_{i:04d}",
        snippet,
        "import os\n\n",
        "\n",
        is_secret=False, is_insecure=False,
        variable_name="API_KEY",
        difficulty="hard",
        note=note,
    )


def gen_access_token_positive(i: int) -> Dict:
    prefixes = ["ghp_", "github_pat_", "glpat-", "xoxb-"]
    prefix = random.choice(prefixes)
    token = prefix + random_string(36)
    var = random.choice(["GITHUB_TOKEN", "TOKEN", "ACCESS_TOKEN"])
    return make_item(
        f"py_secret_token_pos_{i:04d}",
        f'{var} = "{token}"',
        "# Auth configuration\n",
        "\n",
        is_secret=True, is_insecure=False,
        secret_type="access_token",
        variable_name=var,
    )


def gen_password_positive(i: int) -> Dict:
    pwd = random_string(12) + random.choice(["!", "@", "#", "123"])
    var = random.choice(["DB_PASSWORD", "MYSQL_PASSWORD", "PASSWORD"])
    return make_item(
        f"py_secret_pwd_pos_{i:04d}",
        f'{var} = "{pwd}"',
        "# Database config\n",
        "\n",
        is_secret=True, is_insecure=False,
        secret_type="password",
        variable_name=var,
    )


def gen_private_key_positive(i: int) -> Dict:
    body = random_string(200, string.ascii_letters + string.digits + "+/=")
    key = f"-----BEGIN RSA PRIVATE KEY-----\n{body}\n-----END RSA PRIVATE KEY-----"
    return make_item(
        f"py_secret_pk_pos_{i:04d}",
        f'PRIVATE_KEY = """{key}"""',
        "",
        "\n",
        is_secret=True, is_insecure=False,
        secret_type="private_key",
        variable_name="PRIVATE_KEY",
    )


def gen_jwt_positive(i: int) -> Dict:
    parts = [random_string(40, string.ascii_letters + string.digits + "-_") for _ in range(3)]
    jwt = f"eyJ{''.join(parts[0][:10])}.{''.join(parts[1])}.{''.join(parts[2])}"
    return make_item(
        f"py_secret_jwt_pos_{i:04d}",
        f'JWT_TOKEN = "{jwt}"',
        "",
        "\n",
        is_secret=True, is_insecure=False,
        secret_type="jwt",
        variable_name="JWT_TOKEN",
    )


# ============ НЕБЕЗОПАСНЫЙ КОД ============

def gen_eval_positive(i: int) -> Dict:
    return make_item(
        f"py_insecure_eval_pos_{i:04d}",
        "result = eval(user_input)",
        "user_input = input('Enter: ')\n",
        "print(result)\n",
        is_secret=False, is_insecure=True,
        insecure_type="eval_usage",
    )


def gen_exec_positive(i: int) -> Dict:
    return make_item(
        f"py_insecure_exec_pos_{i:04d}",
        "exec(code_from_user)",
        "code_from_user = request.data\n",
        "\n",
        is_secret=False, is_insecure=True,
        insecure_type="exec_usage",
    )


def gen_shell_true_positive(i: int) -> Dict:
    variants = [
        'subprocess.run(f"ls {user_dir}", shell=True)',
        'subprocess.call("rm -rf " + path, shell=True)',
        'os.system(f"cat {filename}")',
    ]
    return make_item(
        f"py_insecure_shell_pos_{i:04d}",
        random.choice(variants),
        "import subprocess\n",
        "\n",
        is_secret=False, is_insecure=True,
        insecure_type="shell_true",
    )


def gen_sql_concat_positive(i: int) -> Dict:
    variants = [
        'query = "SELECT * FROM users WHERE id = " + user_id',
        'query = f"SELECT * FROM users WHERE name = \'{name}\'"',
        'cursor.execute("SELECT * FROM users WHERE id = %s" % user_id)',
    ]
    return make_item(
        f"py_insecure_sql_pos_{i:04d}",
        random.choice(variants),
        "def get_user(user_id):\n",
        "    cursor.execute(query)\n",
        is_secret=False, is_insecure=True,
        insecure_type="sql_concat",
    )


def gen_weak_hash_positive(i: int) -> Dict:
    algo = random.choice(["md5", "sha1"])
    return make_item(
        f"py_insecure_hash_pos_{i:04d}",
        f'hashlib.{algo}(password.encode()).hexdigest()',
        "import hashlib\n",
        "\n",
        is_secret=False, is_insecure=True,
        insecure_type="weak_hash",
    )


def gen_hardcoded_creds_positive(i: int) -> Dict:
    variants = [
        'credentials = {"username": "admin", "password": "admin123"}',
        'login("root", "toor")',
        'USER, PASS = "admin", "secret"',
    ]
    return make_item(
        f"py_insecure_creds_pos_{i:04d}",
        random.choice(variants),
        "# Login\n",
        "\n",
        is_secret=False, is_insecure=True,
        insecure_type="hardcoded_creds",
    )


# ============ НЕГАТИВНЫЕ ПРИМЕРЫ ДЛЯ INSECURE ============

def gen_eval_negative(i: int) -> Dict:
    return make_item(
        f"py_insecure_eval_neg_{i:04d}",
        'result = eval("2 + 2")',
        "# Константное выражение\n",
        "\n",
        is_secret=False, is_insecure=False,
        note="константа в eval",
        difficulty="medium",
    )


def gen_sql_negative(i: int) -> Dict:
    return make_item(
        f"py_insecure_sql_neg_{i:04d}",
        'cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))',
        "def get_user(user_id):\n",
        "\n",
        is_secret=False, is_insecure=False,
        note="параметризованный запрос",
    )


def gen_shell_negative(i: int) -> Dict:
    return make_item(
        f"py_insecure_shell_neg_{i:04d}",
        'subprocess.run(["ls", user_dir])',
        "import subprocess\n",
        "\n",
        is_secret=False, is_insecure=False,
        note="без shell=True",
    )


# ============ СБОРКА ============

def generate_python_dataset(n_per_class: int = 30) -> List[Dict]:
    items = []
    generators = [
        (gen_api_key_positive, gen_api_key_negative),
        (gen_access_token_positive, None),
        (gen_password_positive, None),
        (gen_private_key_positive, None),
        (gen_jwt_positive, None),
        (gen_eval_positive, gen_eval_negative),
        (gen_exec_positive, None),
        (gen_shell_true_positive, gen_shell_negative),
        (gen_sql_concat_positive, gen_sql_negative),
        (gen_weak_hash_positive, None),
        (gen_hardcoded_creds_positive, None),
    ]

    for pos_gen, neg_gen in generators:
        for i in range(n_per_class):
            items.append(pos_gen(i))
            if neg_gen and i < n_per_class // 2:
                items.append(neg_gen(i))

    random.shuffle(items)
    return items


if __name__ == "__main__":
    dataset = generate_python_dataset(30)
    with open("data/python_dataset.jsonl", "w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Generated {len(dataset)} Python examples")