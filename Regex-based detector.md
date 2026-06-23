
**Что это:**  
**Regex-based detector** — детектор (инструмент поиска), который использует **регулярные выражения** (regular expressions, regex) для поиска паттернов в коде, например: секреты, уязвимости, unsafe-функции.

**Простыми словами:**  
Это «умный поиск» по тексту кода, который умеет находить сложные паттерны:

- `password\s*=\s*["\']` → найдёт `password = "123"`
- `api_key\s*=\s*["\']` → найдёт `api_key = "abc"`

**Пример regex:**

```python

import re pattern = r"password\s*=\s*['\"](.+)['\"]" 
match = re.search(pattern, code) if match:     
	print(f"Секрет найден: {match.group(1)}")`
```

**Плюсы:**

- быстрая работа
- простой синтаксис
- легко настроить

**Минусы:**

- не понимает контекст
- может находить ложные совпадения
- не работает со сложными структурами

**Ресурсы для изучения:**

- https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/RegExp/test
- https://openreplay.com/tools/regex-tester/

#стажировка 