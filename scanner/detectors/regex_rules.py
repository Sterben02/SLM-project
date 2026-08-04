# scanner/detectors/regex_rules.py
"""
Правила для regex-детектора.
Каждое правило: (имя, категория, паттерн, severity, описание).
"""
from scanner.models import Severity

# Формат: (type, category, regex_pattern, severity, description)
REGEX_RULES = [
    # ============ СЕКРЕТЫ ============
    ("aws_access_key", "secret",
     r'\bAKIA[0-9A-Z]{16}\b',
     Severity.CRITICAL, "AWS Access Key ID"),

    ("aws_secret_key", "secret",
     r'(?i)aws(.{0,20})?(secret|private)[\'"].{0,20}?[\'"][0-9a-zA-Z/+]{40}',
     Severity.CRITICAL, "AWS Secret Access Key"),

    ("github_token", "secret",
     r'\bghp_[A-Za-z0-9]{36}\b|\bgithub_pat_[A-Za-z0-9_]{82}\b',
     Severity.CRITICAL, "GitHub Personal Access Token"),

    ("gitlab_token", "secret",
     r'\bglpat-[A-Za-z0-9\-_]{20}\b',
     Severity.CRITICAL, "GitLab Personal Access Token"),

    ("slack_token", "secret",
     r'\bxox[baprs]-[A-Za-z0-9\-]{10,48}\b',
     Severity.HIGH, "Slack Token"),

    ("openai_key", "secret",
     r'\bsk-[A-Za-z0-9]{32,}\b',
     Severity.CRITICAL, "OpenAI API Key"),

    ("stripe_key", "secret",
     r'\b[ps]k_live_[A-Za-z0-9]{20,}\b',
     Severity.CRITICAL, "Stripe API Key"),

    ("google_api_key", "secret",
     r'\bAIza[0-9A-Za-z\-_]{35}\b',
     Severity.HIGH, "Google API Key"),

    ("jwt_token", "secret",
     r'\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b',
     Severity.HIGH, "JWT Token"),

    ("private_key", "secret",
     r'-----BEGIN\s+(RSA|EC|DSA|OPENSSH|PGP)?\s*PRIVATE KEY( BLOCK)?-----',
     Severity.CRITICAL, "Private Key (PEM)"),

    ("generic_api_key", "secret",
     r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\'][A-Za-z0-9\-_]{16,}["\']',
     Severity.HIGH, "Generic API Key"),

    ("generic_secret", "secret",
     r'(?i)(secret|token)\s*[=:]\s*["\'][A-Za-z0-9\-_]{16,}["\']',
     Severity.HIGH, "Generic Secret/Token"),

    ("password_in_code", "secret",
     r'(?i)(password|passwd|pwd)\s*[=:]\s*["\'][^"\']{4,}["\']',
     Severity.HIGH, "Hardcoded Password"),

    # ============ НЕБЕЗОПАСНЫЙ КОД ============
    ("eval_usage", "insecure_code",
     r'\beval\s*\(\s*[a-zA-Z_]',
     Severity.HIGH, "Использование eval() с динамическим вводом"),

    ("exec_usage", "insecure_code",
     r'\bexec\s*\(\s*[a-zA-Z_]',
     Severity.HIGH, "Использование exec() с динамическим вводом"),

    ("shell_true", "insecure_code",
     r'shell\s*=\s*True',
     Severity.HIGH, "subprocess с shell=True"),

    ("os_system", "insecure_code",
     r'\bos\.system\s*\(',
     Severity.MEDIUM, "Использование os.system()"),

    ("sql_concat", "insecure_code",
     r'(?i)(select|insert|update|delete)\s+.{0,50}?["\']\s*\+\s*\w',
     Severity.HIGH, "SQL через конкатенацию строк"),

    ("sql_fstring", "insecure_code",
     r'(?i)f["\'](select|insert|update|delete)\s+.{0,80}?\{\w+\}',
     Severity.HIGH, "SQL через f-string"),

    ("sql_percent", "insecure_code",
     r'(?i)["\'](select|insert|update|delete)\s+.{0,80}?%s?.{0,20}["\']\s*%\s*\w',
     Severity.HIGH, "SQL через % форматирование"),

    ("weak_hash_md5", "insecure_code",
     r'\bhashlib\.md5\s*\(|\bMD5\s*\(',
     Severity.MEDIUM, "Слабый хэш MD5"),

    ("weak_hash_sha1", "insecure_code",
     r'\bhashlib\.sha1\s*\(|\bSHA1\s*\(',
     Severity.MEDIUM, "Слабый хэш SHA1"),

    ("hardcoded_creds_dict", "insecure_code",
     r'(?i)["\'](username|user|login)["\']\s*:\s*["\'][^"\']+["\'].{0,50}?["\'](password|pass)["\']\s*:\s*["\'][^"\']+["\']',
     Severity.HIGH, "Захардкоженные учётные данные"),

    ("tls_verify_disabled", "insecure_code",
     r'verify\s*=\s*False',
     Severity.MEDIUM, "Отключена TLS-проверка"),

    ("pickle_loads", "insecure_code",
     r'\bpickle\.loads?\s*\(',
     Severity.HIGH, "Небезопасная десериализация pickle"),
]