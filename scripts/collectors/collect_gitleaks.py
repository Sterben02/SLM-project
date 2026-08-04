# scripts/collectors/collect_gitleaks.py (ИСПРАВЛЕННАЯ ВЕРСИЯ)
"""
Сбор правил из конфига Gitleaks и генерация примеров из regex-паттернов.
"""
import tomllib
import urllib.request
import json
import re
import random
import string
from pathlib import Path

GITLEAKS_URL = "https://raw.githubusercontent.com/gitleaks/gitleaks/master/config/gitleaks.toml"

# Маппинг правил gitleaks на ваши классы
TYPE_MAPPING = {
    # Ключи облачных провайдеров
    "aws-access-token": ("api_key", "AWS Access Key"),
    "aws-secret-access-key": ("api_key", "AWS Secret Key"),
    "gcp-api-key": ("api_key", "GCP API Key"),
    "azure-ad-client-secret": ("api_key", "Azure Client Secret"),
    "heroku-api-key": ("api_key", "Heroku API Key"),

    # Токены GitHub/GitLab
    "github-pat": ("access_token", "GitHub Personal Access Token"),
    "github-fine-grained-pat": ("access_token", "GitHub Fine-Grained PAT"),
    "github-oauth": ("access_token", "GitHub OAuth"),
    "gitlab-pat": ("access_token", "GitLab Personal Access Token"),
    "gitlab-rrt": ("access_token", "GitLab Runner Token"),

    # Коммуникационные сервисы
    "slack-access-token": ("access_token", "Slack Token"),
    "slack-webhook": ("access_token", "Slack Webhook"),
    "discord-webhook": ("access_token", "Discord Webhook"),
    "telegram-bot-api-token": ("access_token", "Telegram Bot Token"),
    "twilio-api-key": ("api_key", "Twilio API Key"),
    "sendgrid-api-key": ("api_key", "SendGrid API Key"),

    # Платёжные системы
    "stripe-access-token": ("api_key", "Stripe API Key"),
    "paypal-braintree-access-token": ("api_key", "PayPal Braintree Token"),
    "square-access-token": ("api_key", "Square Access Token"),

    # Базы данных
    "mongodb-connection-string": ("password", "MongoDB Connection String"),
    "postgres-connection-string": ("password", "PostgreSQL Connection String"),
    "mysql-connection-string": ("password", "MySQL Connection String"),
    "redis-connection-string": ("password", "Redis Connection String"),

    # Криптография
    "private-key": ("private_key", "Private Key (PEM)"),
    "jwt": ("jwt", "JWT Token"),

    # Общие
    "generic-api-key": ("api_key", "Generic API Key"),
    "hardcoded-password": ("password", "Hardcoded Password"),
    "mailchimp-api-key": ("api_key", "Mailchimp API Key"),
    "mailgun-private-api-key": ("api_key", "Mailgun API Key"),
    "new-relic-user-api-key": ("api_key", "New Relic API Key"),
    "npm-access-token": ("access_token", "NPM Access Token"),
    "pypi-upload-token": ("access_token", "PyPI Upload Token"),
    "hashicorp-vault-batch-token": ("access_token", "Vault Batch Token"),
}


def download_config() -> str:
    print("Скачиваю gitleaks.toml...")
    with urllib.request.urlopen(GITLEAKS_URL) as resp:
        return resp.read().decode("utf-8")


def parse_rules(toml_content: str) -> list[dict]:
    data = tomllib.loads(toml_content)
    rules = data.get("rules", [])
    print(f"Найдено правил: {len(rules)}")
    return rules


def generate_connection_string(rule_id: str) -> str | None:
    """Генерирует строки подключения для баз данных."""
    fake_host = "example.com"
    fake_user = "admin"
    fake_pwd = "SuperSecretPassword123!"

    if "mongodb" in rule_id:
        return f"mongodb+srv://{fake_user}:{fake_pwd}@cluster0.{fake_host}/mydb"
    if "postgres" in rule_id:
        return f"postgresql://{fake_user}:{fake_pwd}@{fake_host}:5432/mydb"
    if "mysql" in rule_id:
        return f"mysql://{fake_user}:{fake_pwd}@{fake_host}:3306/mydb"
    if "redis" in rule_id:
        return f"redis://:{fake_pwd}@{fake_host}:6379/0"
    return None


def generate_example_from_regex(pattern: str, rule_id: str) -> str | None:
    """
    Генерирует пример строки на основе regex-паттерна.
    Это упрощённая версия — для сложных паттернов нужны более умные генераторы.
    """
    # Специальные случаи для известных форматов
    if "AKIA" in pattern:  # AWS Access Key
        return "AKIA" + "".join(random.choices("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=16))

    if "ghp_" in pattern:  # GitHub PAT
        return "ghp_" + "".join(random.choices(string.ascii_letters + string.digits, k=36))

    if "glpat-" in pattern:  # GitLab PAT
        return "glpat-" + "".join(random.choices(string.ascii_letters + string.digits + "-_", k=20))

    if "xox" in pattern:  # Slack
        return "xoxb-" + "".join(random.choices(string.ascii_letters + string.digits + "-", k=48))

    if "sk_live" in pattern or "pk_live" in pattern:  # Stripe
        return "sk_live_" + "".join(random.choices(string.ascii_letters + string.digits, k=24))

    if "AIza" in pattern:  # Google API Key
        return "AIza" + "".join(random.choices(string.ascii_letters + string.digits + "-_", k=35))

    if "BEGIN" in pattern and "PRIVATE KEY" in pattern:
        return "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA" + "".join(
            random.choices(string.ascii_letters + string.digits + "+/=", k=100)) + "\n-----END RSA PRIVATE KEY-----"

    if "eyJ" in pattern:  # JWT
        parts = [
            "".join(random.choices(string.ascii_letters + string.digits + "-_", k=20)),
            "".join(random.choices(string.ascii_letters + string.digits + "-_", k=30)),
            "".join(random.choices(string.ascii_letters + string.digits + "-_", k=40)),
        ]
        return f"eyJ{parts[0]}.eyJ{parts[1]}.{parts[2]}"

    # Общий случай — генерируем случайную строку
    return "".join(random.choices(string.ascii_letters + string.digits + "-_", k=40))


def generate_from_rule(rule: dict) -> dict | None:
    """Генерирует пример на основе regex-правила."""
    rule_id = rule.get("id", "")
    mapping = TYPE_MAPPING.get(rule_id)

    if not mapping:
        return None

    secret_type, description = mapping

    # Пытаемся взять пример из правила
    example = rule.get("example", "")

    # Если примера нет — генерируем из паттерна
    if not example:
        pattern = rule.get("regex", "")
        if pattern:
            example = generate_example_from_regex(pattern, rule_id)

    if not example:
        return None

    # Для строк подключения
    if "connection-string" in rule_id:
        example = generate_connection_string(rule_id)
        if example:
            return {
                "id": f"real_gitleaks_{rule_id}",
                "source": "opensource",
                "language": "python",
                "file_path": f"gitleaks/{rule_id}.py",
                "line_number": 1,
                "context_before": f"# {description}\n",
                "target_snippet": f'DATABASE_URL = "{example}"',
                "context_after": "",
                "labels": {
                    "is_secret": True,
                    "is_insecure": False,
                    "secret_type": secret_type,
                    "insecure_type": None,
                },
                "metadata": {
                    "source_rule": rule_id,
                    "difficulty": "easy",
                    "note": f"Сгенерировано из правила gitleaks: {description}",
                },
            }

    var_name = rule_id.replace("-", "_").upper()

    return {
        "id": f"real_gitleaks_{rule_id}",
        "source": "opensource",
        "language": "python",
        "file_path": f"gitleaks/{rule_id}.py",
        "line_number": 1,
        "context_before": f"# {description}\n",
        "target_snippet": f'{var_name} = "{example}"',
        "context_after": "",
        "labels": {
            "is_secret": True,
            "is_insecure": False,
            "secret_type": secret_type,
            "insecure_type": None,
        },
        "metadata": {
            "source_rule": rule_id,
            "difficulty": "easy",
            "note": f"Сгенерировано из правила gitleaks: {description}",
        },
    }


def main():
    content = download_config()
    rules = parse_rules(content)

    items = []
    for rule in rules:
        item = generate_from_rule(rule)
        if item:
            items.append(item)

    out = Path("data/collected/gitleaks.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"✅ Собрано примеров: {len(items)} → {out}")


if __name__ == "__main__":
    main()