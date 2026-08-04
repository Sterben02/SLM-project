# 🔍 Отчёт сканера секретов и небезопасного кода

**Версия:** 0.1.0

## 📊 Сводка

- **Всего срабатываний:** 5
- **Секретов:** 2
- **Небезопасного кода:** 3

## 📋 Таблица срабатываний

| Файл | Строка | Тип | Категория | Severity | Detector |
|---|---|---|---|---|---|
| `examples\example_repo\config.py` | 5 | api_key | secret | high | regex |
| `examples\example_repo\config.py` | 6 | password | secret | high | regex |
| `examples\example_repo\utils.py` | 5 | shell_true | insecure_code | medium | regex |
| `examples\example_repo\utils.py` | 6 | shell_true | insecure_code | medium | regex |
| `examples\example_repo\utils.py` | 10 | eval_usage | insecure_code | medium | regex |

## 💡 Объяснения

### `examples\example_repo\config.py:5` — api_key
- **Категория:** secret
- **Severity:** high
- **Confidence:** 0.70
- **Объяснение:** [regex] Обнаружен паттерн: API_KEY\s*=\s*["\'][^"\']+["\']
- **Фрагмент:** `API_KEY = "sk-live-abc123def456ghi789jkl012mno345"`

### `examples\example_repo\config.py:6` — password
- **Категория:** secret
- **Severity:** high
- **Confidence:** 0.70
- **Объяснение:** [regex] Обнаружен паттерн: PASSWORD\s*=\s*["\'][^"\']+["\']
- **Фрагмент:** `DB_PASSWORD = "SuperSecret123!"`

### `examples\example_repo\utils.py:5` — shell_true
- **Категория:** insecure_code
- **Severity:** medium
- **Confidence:** 0.70
- **Объяснение:** [regex] Обнаружен паттерн: shell\s*=\s*True
- **Фрагмент:** `# ОПАСНО: shell=True с пользовательским вводом`

### `examples\example_repo\utils.py:6` — shell_true
- **Категория:** insecure_code
- **Severity:** medium
- **Confidence:** 0.70
- **Объяснение:** [regex] Обнаружен паттерн: shell\s*=\s*True
- **Фрагмент:** `subprocess.run(f"ls {user_input}", shell=True)`

### `examples\example_repo\utils.py:10` — eval_usage
- **Категория:** insecure_code
- **Severity:** medium
- **Confidence:** 0.70
- **Объяснение:** [regex] Обнаружен паттерн: \beval\s*\(
- **Фрагмент:** `return eval(expression)`
