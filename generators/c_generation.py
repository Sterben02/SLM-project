# generators/c_generator.py
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


def make_c_item(
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
        language="c",
        file_path=f"generated/sample_{item_id}.c",
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


# ============ СЕКРЕТЫ В C ============

def gen_c_api_key_positive(i: int) -> Dict:
    key = random_string(32)
    return make_c_item(
        f"c_secret_api_pos_{i:04d}",
        f'const char *API_KEY = "{key}";',
        '#include <stdio.h>\n\n',
        '\nint main() { return 0; }\n',
        is_secret=True, is_insecure=False,
        secret_type="api_key",
        variable_name="API_KEY",
    )


def gen_c_password_positive(i: int) -> Dict:
    pwd = random_string(10)
    variants = [
        f'char password[] = "{pwd}";',
        f'const char *DB_PASSWORD = "{pwd}";',
        f'char pwd[32] = "{pwd}";',
    ]
    return make_c_item(
        f"c_secret_pwd_pos_{i:04d}",
        random.choice(variants),
        "#include <string.h>\n\n",
        "\n",
        is_secret=True, is_insecure=False,
        secret_type="password",
    )


def gen_c_private_key_positive(i: int) -> Dict:
    body = random_string(120, string.ascii_letters + string.digits + "+/=")
    return make_c_item(
        f"c_secret_pk_pos_{i:04d}",
        f'const char *PRIVATE_KEY = "-----BEGIN RSA PRIVATE KEY-----\\n{body}\\n-----END RSA PRIVATE KEY-----";',
        "",
        "\n",
        is_secret=True, is_insecure=False,
        secret_type="private_key",
    )


def gen_c_api_key_negative(i: int) -> Dict:
    cases = [
        ('const char *API_KEY = "test_key";', "тестовый"),
        ('const char *API_KEY = getenv("API_KEY");', "из env"),
        ('// const char *API_KEY = "real-looking";', "закомментировано"),
        ('#define API_KEY ""', "пустой"),
    ]
    snippet, note = random.choice(cases)
    return make_c_item(
        f"c_secret_api_neg_{i:04d}",
        snippet,
        "#include <stdlib.h>\n",
        "\n",
        is_secret=False, is_insecure=False,
        note=note,
        difficulty="hard",
    )


# ============ НЕБЕЗОПАСНЫЙ КОД В C ============

def gen_c_gets_positive(i: int) -> Dict:
    return make_c_item(
        f"c_insecure_gets_pos_{i:04d}",
        "gets(buffer);",
        "char buffer[256];\n",
        "\n",
        is_secret=False, is_insecure=True,
        insecure_type="shell_true",  # buffer overflow → инъекции
        note="gets() не проверяет длину буфера",
    )


def gen_c_strcpy_positive(i: int) -> Dict:
    return make_c_item(
        f"c_insecure_strcpy_pos_{i:04d}",
        "strcpy(dest, user_input);",
        "char dest[64];\n",
        "\n",
        is_secret=False, is_insecure=True,
        insecure_type="shell_true",
        note="strcpy без проверки длины",
    )


def gen_c_system_positive(i: int) -> Dict:
    variants = [
        'system(cmd);',
        'system(user_input);',
        'sprintf(buf, "ls %s", path); system(buf);',
    ]
    return make_c_item(
        f"c_insecure_system_pos_{i:04d}",
        random.choice(variants),
        '#include <stdlib.h>\n',
        "\n",
        is_secret=False, is_insecure=True,
        insecure_type="shell_true",
    )


def gen_c_sprintf_positive(i: int) -> Dict:
    return make_c_item(
        f"c_insecure_sprintf_pos_{i:04d}",
        'sprintf(query, "SELECT * FROM users WHERE id = %s", user_id);',
        "char query[256];\n",
        "\n",
        is_secret=False, is_insecure=True,
        insecure_type="sql_concat",
    )


def gen_c_md5_positive(i: int) -> Dict:
    return make_c_item(
        f"c_insecure_md5_pos_{i:04d}",
        "MD5(password, strlen(password), result);",
        "#include <openssl/md5.h>\n",
        "\n",
        is_secret=False, is_insecure=True,
        insecure_type="weak_hash",
    )


def gen_c_hardcoded_creds_positive(i: int) -> Dict:
    return make_c_item(
        f"c_insecure_creds_pos_{i:04d}",
        'char *user = "admin"; char *pass = "admin123";',
        "",
        "\n",
        is_secret=False, is_insecure=True,
        insecure_type="hardcoded_creds",
    )


# ============ НЕГАТИВНЫЕ ============

def gen_c_strcpy_negative(i: int) -> Dict:
    return make_c_item(
        f"c_insecure_strcpy_neg_{i:04d}",
        "strncpy(dest, src, sizeof(dest) - 1);",
        "char dest[64];\n",
        "\n",
        is_secret=False, is_insecure=False,
        note="безопасная версия strncpy",
    )


def gen_c_system_negative(i: int) -> Dict:
    return make_c_item(
        f"c_insecure_system_neg_{i:04d}",
        'system("ls");',
        "#include <stdlib.h>\n",
        "\n",
        is_secret=False, is_insecure=False,
        note="константная команда",
    )


# ============ СБОРКА ============

def generate_c_dataset(n_per_class: int = 25) -> List[Dict]:
    items = []
    generators = [
        (gen_c_api_key_positive, gen_c_api_key_negative),
        (gen_c_password_positive, None),
        (gen_c_private_key_positive, None),
        (gen_c_gets_positive, None),
        (gen_c_strcpy_positive, gen_c_strcpy_negative),
        (gen_c_system_positive, gen_c_system_negative),
        (gen_c_sprintf_positive, None),
        (gen_c_md5_positive, None),
        (gen_c_hardcoded_creds_positive, None),
    ]

    for pos_gen, neg_gen in generators:
        for i in range(n_per_class):
            items.append(pos_gen(i))
            if neg_gen and i < n_per_class // 2:
                items.append(neg_gen(i))

    random.shuffle(items)
    return items


if __name__ == "__main__":
    dataset = generate_c_dataset(25)
    with open("data/c_dataset.jsonl", "w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Generated {len(dataset)} C examples")