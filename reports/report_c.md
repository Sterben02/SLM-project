# 🔍 Отчёт сканера секретов и небезопасного кода

**Версия:** 0.1.0

## 📊 Сводка

- **Всего срабатываний:** 5
- **Секретов:** 2
- **Небезопасного кода:** 3

## 📋 Таблица срабатываний

| Файл | Строка | Тип | Категория | Severity | Detector |
|---|---|---|---|---|---|
| `examples\example_repo_c\vulnerable.c` | 5 | generic_api_key | secret | high | regex |
| `examples\example_repo_c\vulnerable.c` | 10 | unsafe_system | insecure_code | high | regex |
| `examples\example_repo_c\vulnerable.c` | 15 | unsafe_gets | insecure_code | high | regex |
| `examples\example_repo_c\vulnerable.c` | 5 | high_entropy_string | secret | medium | entropy |
| `examples\example_repo_c\vulnerable.c` | 9 | unsafe_sprintf | insecure_code | medium | regex |

## 💡 Объяснения

### `examples\example_repo_c\vulnerable.c:5` — generic_api_key
- **Категория:** secret
- **Severity:** high
- **Confidence:** 0.85
- **Объяснение:** [regex] Обнаружен паттерн 'Generic API Key': `api_key = "sk-proj-1234567890abcdef"`
- **Фрагмент:** `char* api_key = "sk-proj-1234567890abcdef";  // секрет`

### `examples\example_repo_c\vulnerable.c:10` — unsafe_system
- **Категория:** insecure_code
- **Severity:** high
- **Confidence:** 0.85
- **Объяснение:** [regex] Обнаружен паттерн 'system() с динамическим вводом — инъекция команд': `system(`
- **Фрагмент:** `system(cmd);  // небезопасно`

### `examples\example_repo_c\vulnerable.c:15` — unsafe_gets
- **Категория:** insecure_code
- **Severity:** high
- **Confidence:** 0.85
- **Объяснение:** [regex] Обнаружен паттерн 'gets() не проверяет границы буфера — переполнение': `gets(`
- **Фрагмент:** `gets(buffer);  // переполнение буфера`

### `examples\example_repo_c\vulnerable.c:5` — high_entropy_string
- **Категория:** secret
- **Severity:** medium
- **Confidence:** 0.99
- **Объяснение:** [entropy] Строка имеет высокую энтропию (4.50), тип: alphanumeric. Возможно, это случайный секрет.
- **Фрагмент:** `char* api_key = "sk-proj-1234567890abcdef";  // секрет`

### `examples\example_repo_c\vulnerable.c:9` — unsafe_sprintf
- **Категория:** insecure_code
- **Severity:** medium
- **Confidence:** 0.85
- **Объяснение:** [regex] Обнаружен паттерн 'sprintf() без проверки длины — используйте snprintf()': `sprintf(`
- **Фрагмент:** `sprintf(cmd, "echo %s", user_input);  // инъекция`
