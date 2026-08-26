# 🔍 Отчёт сканера секретов и небезопасного кода

**Версия:** 0.1.0

## 📊 Сводка

- **Всего срабатываний:** 7
- **Секретов:** 5
- **Небезопасного кода:** 2

## 📋 Таблица срабатываний

| Файл | Строка | Тип | Категория | Severity | Detector |
|---|---|---|---|---|---|
| `examples\example_repo\config.py` | 5 | generic_api_key | secret | high | regex |
| `examples\example_repo\config.py` | 6 | password_in_code | secret | high | regex |
| `examples\example_repo\utils.py` | 6 | shell_true | insecure_code | high | regex |
| `examples\example_repo\utils.py` | 10 | eval_usage | insecure_code | high | regex |
| `examples\example_repo\config.py` | 5 | hardcoded_api_key | secret | high | keyword |
| `examples\example_repo\config.py` | 5 | high_entropy_string | secret | medium | entropy |
| `examples\example_repo\utils.py` | 6 | high_entropy_string | secret | medium | entropy |

## 💡 Объяснения

### `examples\example_repo\config.py:5` — generic_api_key
- **Категория:** secret
- **Severity:** high
- **Confidence:** 0.85
- **Объяснение:** [regex] Обнаружен паттерн 'Generic API Key': `API_KEY = "sk-live-abc123def456ghi789jkl012mno345"`
- **Фрагмент:** `API_KEY = "sk-live-abc123def456ghi789jkl012mno345"`

### `examples\example_repo\config.py:6` — password_in_code
- **Категория:** secret
- **Severity:** high
- **Confidence:** 0.85
- **Объяснение:** [regex] Обнаружен паттерн 'Hardcoded Password': `PASSWORD = "SuperSecret123!"`
- **Фрагмент:** `DB_PASSWORD = "SuperSecret123!"`

### `examples\example_repo\utils.py:6` — shell_true
- **Категория:** insecure_code
- **Severity:** high
- **Confidence:** 0.85
- **Объяснение:** [regex] Обнаружен паттерн 'subprocess с shell=True': `shell=True`
- **Фрагмент:** `subprocess.run(f"ls {user_input}", shell=True)`

### `examples\example_repo\utils.py:10` — eval_usage
- **Категория:** insecure_code
- **Severity:** high
- **Confidence:** 0.85
- **Объяснение:** [regex] Обнаружен паттерн 'Использование eval() с динамическим вводом': `eval(e`
- **Фрагмент:** `return eval(expression)`

### `examples\example_repo\config.py:5` — hardcoded_api_key
- **Категория:** secret
- **Severity:** high
- **Confidence:** 0.60
- **Объяснение:** [keyword] Имя переменной содержит 'api_key', присваивается строковое значение, файл 'config.py' часто содержит секреты, но код похож на тестовый.
- **Фрагмент:** `API_KEY = "sk-live-abc123def456ghi789jkl012mno345"`

### `examples\example_repo\config.py:5` — high_entropy_string
- **Категория:** secret
- **Severity:** medium
- **Confidence:** 0.99
- **Объяснение:** [entropy] Строка имеет высокую энтропию (4.72), тип: alphanumeric. Возможно, это случайный секрет.
- **Фрагмент:** `API_KEY = "sk-live-abc123def456ghi789jkl012mno345"`

### `examples\example_repo\utils.py:6` — high_entropy_string
- **Категория:** secret
- **Severity:** medium
- **Confidence:** 0.66
- **Объяснение:** [entropy] Строка имеет высокую энтропию (3.64), тип: alphanumeric. Возможно, это случайный секрет.
- **Фрагмент:** `subprocess.run(f"ls {user_input}", shell=True)`
