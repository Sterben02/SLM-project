# 🔍 Отчёт сканера секретов и небезопасного кода

**Версия:** 0.1.0

## 📊 Сводка

- **Всего срабатываний:** 2
- **Секретов:** 2
- **Небезопасного кода:** 0

## 📋 Таблица срабатываний

| Файл | Строка | Тип | Категория | Severity | Detector |
|---|---|---|---|---|---|
| `examples\example_repo_c\vulnerable.c` | 5 | generic_api_key | secret | high | regex |
| `examples\example_repo_c\vulnerable.c` | 5 | high_entropy_string | secret | medium | entropy |

## 💡 Объяснения

### `examples\example_repo_c\vulnerable.c:5` — generic_api_key
- **Категория:** secret
- **Severity:** high
- **Confidence:** 0.85
- **Объяснение:** [regex] Обнаружен паттерн 'Generic API Key': `api_key = "sk-proj-1234567890abcdef"`
- **Фрагмент:** `char* api_key = "sk-proj-1234567890abcdef";  // секрет`

### `examples\example_repo_c\vulnerable.c:5` — high_entropy_string
- **Категория:** secret
- **Severity:** medium
- **Confidence:** 0.99
- **Объяснение:** [entropy] Строка имеет высокую энтропию (4.50), тип: alphanumeric. Возможно, это случайный секрет.
- **Фрагмент:** `char* api_key = "sk-proj-1234567890abcdef";  // секрет`
