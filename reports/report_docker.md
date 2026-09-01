# рџ”Ќ РћС‚С‡С‘С‚ СЃРєР°РЅРµСЂР° СЃРµРєСЂРµС‚РѕРІ Рё РЅРµР±РµР·РѕРїР°СЃРЅРѕРіРѕ РєРѕРґР°

**Р’РµСЂСЃРёСЏ:** 0.1.0

## рџ“Љ РЎРІРѕРґРєР°

- **Р’СЃРµРіРѕ СЃСЂР°Р±Р°С‚С‹РІР°РЅРёР№:** 7
- **РЎРµРєСЂРµС‚РѕРІ:** 5
- **РќРµР±РµР·РѕРїР°СЃРЅРѕРіРѕ РєРѕРґР°:** 2

## рџ“‹ РўР°Р±Р»РёС†Р° СЃСЂР°Р±Р°С‚С‹РІР°РЅРёР№

| Р¤Р°Р№Р» | РЎС‚СЂРѕРєР° | РўРёРї | РљР°С‚РµРіРѕСЂРёСЏ | Severity | Detector |
|---|---|---|---|---|---|
| `examples/example_repo/config.py` | 5 | generic_api_key | secret | high | regex |
| `examples/example_repo/config.py` | 6 | password_in_code | secret | high | regex |
| `examples/example_repo/config.py` | 5 | hardcoded_api_key | secret | high | keyword |
| `examples/example_repo/config.py` | 5 | high_entropy_string | secret | medium | entropy |
| `examples/example_repo/utils.py` | 6 | shell_true | insecure_code | high | regex |
| `examples/example_repo/utils.py` | 10 | eval_usage | insecure_code | high | regex |
| `examples/example_repo/utils.py` | 6 | high_entropy_string | secret | medium | entropy |

## рџ’Ў РћР±СЉСЏСЃРЅРµРЅРёСЏ

### `examples/example_repo/config.py:5` вЂ” generic_api_key
- **РљР°С‚РµРіРѕСЂРёСЏ:** secret
- **Severity:** high
- **Confidence:** 0.92
- **РћР±СЉСЏСЃРЅРµРЅРёРµ:** [regex] Обнаружен паттерн 'Generic API Key': `API_KEY = "sk-live-abc123def456ghi789jkl012mno345"` | 🤖 SLM: [slm] Строка похожа на hardcoded API key: имя переменной содержит KEY, значение имеет высокую энтропию и не является тестовым.
- **Р¤СЂР°РіРјРµРЅС‚:** `API_KEY = "sk-live-abc123def456ghi789jkl012mno345"`

### `examples/example_repo/config.py:6` вЂ” password_in_code
- **РљР°С‚РµРіРѕСЂРёСЏ:** secret
- **Severity:** high
- **Confidence:** 0.92
- **РћР±СЉСЏСЃРЅРµРЅРёРµ:** [regex] Обнаружен паттерн 'Hardcoded Password': `PASSWORD = "SuperSecret123!"` | 🤖 SLM: [slm] Строка содержит секрет API-key: имя переменной содержит KEY, значение имеет высокую энтропию или является тестовым.
- **Р¤СЂР°РіРјРµРЅС‚:** `DB_PASSWORD = "SuperSecret123!"`

### `examples/example_repo/config.py:5` вЂ” hardcoded_api_key
- **РљР°С‚РµРіРѕСЂРёСЏ:** secret
- **Severity:** high
- **Confidence:** 0.92
- **РћР±СЉСЏСЃРЅРµРЅРёРµ:** [keyword] Имя переменной содержит 'api_key', присваивается строковое значение, файл 'config.py' часто содержит секреты, но код похож на тестовый. | 🤖 SLM: [slm] Строка похожа на hardcoded API key: имя переменной содержит KEY, значение имеет высокую энтропию и не является тестовым.
- **Р¤СЂР°РіРјРµРЅС‚:** `API_KEY = "sk-live-abc123def456ghi789jkl012mno345"`

### `examples/example_repo/config.py:5` вЂ” high_entropy_string
- **РљР°С‚РµРіРѕСЂРёСЏ:** secret
- **Severity:** medium
- **Confidence:** 0.99
- **РћР±СЉСЏСЃРЅРµРЅРёРµ:** [entropy] Строка имеет высокую энтропию (4.72), тип: alphanumeric. Возможно, это случайный секрет. | 🤖 SLM: [slm] Строка похожа на hardcoded API key: имя переменной содержит KEY, значение имеет высокую энтропию и не является тестовым.
- **Р¤СЂР°РіРјРµРЅС‚:** `API_KEY = "sk-live-abc123def456ghi789jkl012mno345"`

### `examples/example_repo/utils.py:6` вЂ” shell_true
- **РљР°С‚РµРіРѕСЂРёСЏ:** insecure_code
- **Severity:** high
- **Confidence:** 0.92
- **РћР±СЉСЏСЃРЅРµРЅРёРµ:** [regex] Обнаружен паттерн 'subprocess с shell=True': `shell=True` | 🤖 SLM: [slm] Вызов subprocess/shell с shell=True и динамическим вводом подвержен инъекции команд.
- **Р¤СЂР°РіРјРµРЅС‚:** `subprocess.run(f"ls {user_input}", shell=True)`

### `examples/example_repo/utils.py:10` вЂ” eval_usage
- **РљР°С‚РµРіРѕСЂРёСЏ:** insecure_code
- **Severity:** high
- **Confidence:** 0.92
- **РћР±СЉСЏСЃРЅРµРЅРёРµ:** [regex] Обнаружен паттерн 'Использование eval() с динамическим вводом': `eval(e` | 🤖 SLM: [slm] Использование eval() с динамическим вводом может привести к выполнению произвольного кода (RCE).
- **Р¤СЂР°РіРјРµРЅС‚:** `return eval(expression)`

### `examples/example_repo/utils.py:6` вЂ” high_entropy_string
- **РљР°С‚РµРіРѕСЂРёСЏ:** secret
- **Severity:** medium
- **Confidence:** 0.92
- **РћР±СЉСЏСЃРЅРµРЅРёРµ:** [entropy] Строка имеет высокую энтропию (3.64), тип: alphanumeric. Возможно, это случайный секрет. | 🤖 SLM: [slm] Вызов subprocess/shell с shell=True и динамическим вводом подвержен инъекции команд.
- **Р¤СЂР°РіРјРµРЅС‚:** `subprocess.run(f"ls {user_input}", shell=True)`
