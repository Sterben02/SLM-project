
**Что это:**  
**argparse** — встроенный модуль Python для создания пользовательских интерфейсов командной строки. Он позволяет определять arguments (параметры), которые программа ожидает, парсить их из `sys.argv` и использовать в коде.

**Простыми словами:**  
Если ты хочешь, чтобы твой скрипт Python запускался так:

```bash
python script.py --name Анна --age 25
```

— то `argparse` помогает программам «понимать» эти параметры.

**Пример с argparse:**

```python

import argparse 
parser = argparse.ArgumentParser() 
parser.add_argument("--name", type=str, required=True) 
parser.add_argument("--age", type=int, default=18)

args = parser.parse_args() 
print(f"Привет, {args.name}! Возраст: {args.age}")`
```

**Что умеет argparse:**

- требуемые и опциональные arguments
- флаги (boolean flags)
- значения по умолчанию
- проверка типов
- автогенерация help-сообщений


**Ресурсы для изучения:**

- https://mimo.org/glossary/python/argparse
- https://pypi.org/project/argparse/

#стажировка 