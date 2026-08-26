# scanner/utils/recommendations.py
RECOMMENDATIONS = {
    "generic_api_key": "Вынесите API-ключ в переменные окружения (os.environ['API_KEY']) или .env файл",
    "password_in_code": "Используйте secrets-менеджер (HashiCorp Vault, AWS Secrets Manager)",
    "high_entropy_string": "Проверьте, не является ли это секретом. Если да — вынесите в env",
    "shell_true": "Замените shell=True на список аргументов: subprocess.run(['cmd', 'arg'])",
    "eval_usage": "Замените eval() на безопасный парсер (ast.literal_eval для простых структур)",
    "hardcoded_api_key": "Используйте переменные окружения или secrets-менеджер",
}

def get_recommendation(finding_type: str) -> str:
    return RECOMMENDATIONS.get(finding_type, "Проверьте код вручную")