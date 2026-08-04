# scripts/analyze_dataset.py
"""
Анализ датасета по классам.
Проверяет требования недели 6:
- Минимум 50 примеров на класс
- Всего 1500+ примеров
- Все 11 классов представлены
- Баланс позитивных/негативных примеров
"""
import json
import sys
from pathlib import Path
from collections import defaultdict

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

# Требуемые классы
REQUIRED_SECRET_CLASSES = [
    "api_key",
    "access_token",
    "password",
    "private_key",
    "jwt",
]

REQUIRED_INSECURE_CLASSES = [
    "eval_usage",
    "exec_usage",
    "shell_true",
    "sql_concat",
    "weak_hash",
    "hardcoded_creds",
]

MIN_PER_CLASS = 50
MIN_TOTAL = 1500


def load_dataset(path: str) -> list[dict]:
    """Загружает JSONL-датасет."""
    items = []
    file_path = Path(path)

    if not file_path.exists():
        console.print(f"[red]❌ Файл не найден: {path}[/red]")
        sys.exit(1)

    with open(file_path, encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError as e:
                console.print(f"[yellow]⚠️  Ошибка в строке {line_num}: {e}[/yellow]")

    return items


def get_class_key(item: dict) -> tuple[str, str]:
    """
    Возвращает (категория, класс) для примера.
    Категория: secret, insecure, negative
    """
    labels = item.get("labels", {})

    if labels.get("is_secret"):
        return "secret", labels.get("secret_type", "unknown")
    elif labels.get("is_insecure"):
        return "insecure", labels.get("insecure_type", "unknown")
    else:
        return "negative", "negative"


def analyze_by_classes(items: list[dict]) -> dict[str, dict]:
    """Группирует примеры по классам и считает статистику."""
    stats = defaultdict(lambda: {
        "count": 0,
        "languages": defaultdict(int),
        "sources": defaultdict(int),
        "difficulties": defaultdict(int),
    })

    for item in items:
        category, class_name = get_class_key(item)
        key = f"{category}_{class_name}" if category != "negative" else "negative"

        stats[key]["count"] += 1
        stats[key]["languages"][item.get("language", "unknown")] += 1
        stats[key]["sources"][item.get("source", "unknown")] += 1

        difficulty = item.get("metadata", {}).get("difficulty", "unknown")
        stats[key]["difficulties"][difficulty] += 1

    return dict(stats)


def print_class_table(stats: dict, total: int):
    """Выводит таблицу по классам."""
    table = Table(
        title="📊 Распределение по классам",
        box=box.ROUNDED,
        show_lines=True,
    )
    table.add_column("Класс", style="cyan", min_width=30)
    table.add_column("Кол-во", justify="right", style="magenta")
    table.add_column("% от общего", justify="right")
    table.add_column("Статус", justify="center")
    table.add_column("Топ языки", style="blue")

    # Сортировка: сначала секреты, потом insecure, потом negative
    def sort_key(k):
        if k.startswith("secret_"):
            return (0, k)
        elif k.startswith("insecure_"):
            return (1, k)
        else:
            return (2, k)

    for key in sorted(stats.keys(), key=sort_key):
        info = stats[key]
        count = info["count"]
        percent = count / total * 100 if total > 0 else 0

        # Статус
        if count == 0:
            status = "[red]❌ Отсутствует[/red]"
        elif count < MIN_PER_CLASS // 2:
            status = f"[red]🔴 Критич. мало (<{MIN_PER_CLASS // 2})[/red]"
        elif count < MIN_PER_CLASS:
            status = f"[yellow]🟡 Мало (<{MIN_PER_CLASS})[/yellow]"
        else:
            status = "[green]✅ OK[/green]"

        # Топ языки
        top_langs = sorted(info["languages"].items(), key=lambda x: -x[1])[:3]
        langs_str = ", ".join(f"{lang} ({cnt})" for lang, cnt in top_langs)

        # Цвет названия в зависимости от категории
        if key.startswith("secret_"):
            display_name = f"🔑 {key[7:]}"
        elif key.startswith("insecure_"):
            display_name = f"⚠️  {key[9:]}"
        else:
            display_name = "🚫 negative (безопасный код)"

        table.add_row(
            display_name,
            str(count),
            f"{percent:.1f}%",
            status,
            langs_str,
        )

    console.print(table)


def print_summary_table(items: list[dict]):
    """Выводит общую сводку."""
    total = len(items)

    secrets = sum(1 for i in items if i.get("labels", {}).get("is_secret"))
    insecure = sum(1 for i in items if i.get("labels", {}).get("is_insecure"))
    negative = total - secrets - insecure

    table = Table(title="📈 Общая сводка", box=box.ROUNDED)
    table.add_column("Метрика", style="bold cyan")
    table.add_column("Значение", justify="right")
    table.add_column("Требование", justify="right")
    table.add_column("Статус", justify="center")

    # Всего примеров
    status_total = "[green]✅[/green]" if total >= MIN_TOTAL else f"[red]❌ (<{MIN_TOTAL})[/red]"
    table.add_row("Всего примеров", str(total), f"≥{MIN_TOTAL}", status_total)

    # Секреты
    table.add_row("🔑 Секреты", str(secrets), "-", "")
    table.add_row("⚠️  Небезопасный код", str(insecure), "-", "")
    table.add_row("🚫 Негативные", str(negative), "30-50%", "")

    # Доля негативных
    neg_percent = negative / total * 100 if total > 0 else 0
    neg_status = "[green]✅[/green]" if 30 <= neg_percent <= 50 else "[yellow]⚠️[/yellow]"
    table.add_row("Доля негативных", f"{neg_percent:.1f}%", "30-50%", neg_status)

    console.print(table)


def print_languages_table(items: list[dict]):
    """Выводит распределение по языкам."""
    lang_counts = defaultdict(int)
    for item in items:
        lang_counts[item.get("language", "unknown")] += 1

    table = Table(title="🌍 Распределение по языкам", box=box.ROUNDED)
    table.add_column("Язык", style="cyan")
    table.add_column("Кол-во", justify="right", style="magenta")
    table.add_column("%", justify="right")

    total = len(items)
    for lang, count in sorted(lang_counts.items(), key=lambda x: -x[1]):
        percent = count / total * 100 if total > 0 else 0
        table.add_row(lang, str(count), f"{percent:.1f}%")

    console.print(table)


def print_sources_table(items: list[dict]):
    """Выводит распределение по источникам."""
    source_counts = defaultdict(int)
    for item in items:
        source_counts[item.get("source", "unknown")] += 1

    table = Table(title="📦 Распределение по источникам", box=box.ROUNDED)
    table.add_column("Источник", style="cyan")
    table.add_column("Кол-во", justify="right", style="magenta")
    table.add_column("%", justify="right")

    total = len(items)
    for source, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        percent = count / total * 100 if total > 0 else 0
        table.add_row(source, str(count), f"{percent:.1f}%")

    console.print(table)


def check_requirements(stats: dict, total: int) -> tuple[bool, list[str]]:
    """Проверяет все требования и возвращает рекомендации."""
    issues = []
    all_ok = True

    # 1. Всего примеров
    if total < MIN_TOTAL:
        issues.append(f"❌ Всего примеров {total}, требуется ≥{MIN_TOTAL}. Нужно ещё {MIN_TOTAL - total}.")
        all_ok = False

    # 2. Проверка классов секретов
    for cls in REQUIRED_SECRET_CLASSES:
        key = f"secret_{cls}"
        count = stats.get(key, {}).get("count", 0)
        if count == 0:
            issues.append(f"❌ Класс секретов '{cls}' отсутствует. Добавьте минимум {MIN_PER_CLASS} примеров.")
            all_ok = False
        elif count < MIN_PER_CLASS:
            issues.append(
                f"⚠️  Класс секретов '{cls}': {count} примеров, нужно ≥{MIN_PER_CLASS}. Добавьте ещё {MIN_PER_CLASS - count}.")
            all_ok = False

    # 3. Проверка классов insecure
    for cls in REQUIRED_INSECURE_CLASSES:
        key = f"insecure_{cls}"
        count = stats.get(key, {}).get("count", 0)
        if count == 0:
            issues.append(f"❌ Класс insecure '{cls}' отсутствует. Добавьте минимум {MIN_PER_CLASS} примеров.")
            all_ok = False
        elif count < MIN_PER_CLASS:
            issues.append(
                f"⚠️  Класс insecure '{cls}': {count} примеров, нужно ≥{MIN_PER_CLASS}. Добавьте ещё {MIN_PER_CLASS - count}.")
            all_ok = False

    # 4. Проверка негативных примеров
    neg_count = stats.get("negative", {}).get("count", 0)
    neg_percent = neg_count / total * 100 if total > 0 else 0
    if neg_percent < 20:
        issues.append(f"⚠️  Мало негативных примеров ({neg_percent:.1f}%). Рекомендуется 30-50% для снижения FPR.")

    return all_ok, issues


def print_recommendations(issues: list[str]):
    """Выводит рекомендации."""
    if not issues:
        console.print(Panel.fit(
            "[green]✅ ВСЕ ТРЕБОВАНИЯ ВЫПОЛНЕНЫ![/green]\n\n"
            "Датасет готов к использованию для обучения SLM.",
            title="🎉 Результат проверки",
            border_style="green",
        ))
        return

    panel_text = "\n".join(f"• {issue}" for issue in issues)
    console.print(Panel.fit(
        f"[yellow]Обнаружены проблемы:[/yellow]\n\n{panel_text}",
        title="⚠️  Результат проверки",
        border_style="yellow",
    ))

    console.print("\n[bold]💡 Рекомендации:[/bold]")
    console.print(
        "1. Запустите [cyan]python generators/boost_missing_classes.py[/cyan] для генерации недостающих примеров")
    console.print("2. Добавьте реальные кейсы из CWE, Gitleaks, HuggingFace")
    console.print("3. После добавления запустите [cyan]python scripts/merge_datasets.py[/cyan] заново")
    console.print("4. Переразбейте датасет: [cyan]python scripts/split_dataset.py[/cyan]")


def analyze_file(path: str):
    """Анализирует один файл датасета."""
    console.print(Panel.fit(
        f"[bold cyan]📊 Анализ датасета[/bold cyan]\n"
        f"Файл: [yellow]{path}[/yellow]",
        border_style="cyan",
    ))

    # Загрузка
    items = load_dataset(path)
    console.print(f"📥 Загружено примеров: [bold]{len(items)}[/bold]\n")

    if not items:
        console.print("[red]❌ Датасет пуст![/red]")
        return None

    # Анализ по классам
    stats = analyze_by_classes(items)

    # Вывод таблиц
    print_summary_table(items)
    console.print()
    print_class_table(stats, len(items))
    console.print()
    print_languages_table(items)
    console.print()
    print_sources_table(items)
    console.print()

    # Проверка требований
    all_ok, issues = check_requirements(stats, len(items))
    print_recommendations(issues)

    return stats


def analyze_splits():
    """Анализирует train/valid/test сплиты."""
    console.print("\n" + "=" * 80)
    console.print("[bold cyan]🔍 Проверка классов в train/valid/test сплитах[/bold cyan]")
    console.print("=" * 80 + "\n")

    splits = {
        "train": "data/train.jsonl",
        "valid": "data/valid.jsonl",
        "test": "data/test.jsonl",
    }

    table = Table(title="Классы в сплитах", box=box.ROUNDED)
    table.add_column("Класс", style="cyan")
    table.add_column("Train", justify="right")
    table.add_column("Valid", justify="right")
    table.add_column("Test", justify="right")
    table.add_column("Всего", justify="right", style="bold")

    # Собираем статистику по всем сплитам
    all_stats = {}
    for split_name, path in splits.items():
        if Path(path).exists():
            items = load_dataset(path)
            all_stats[split_name] = analyze_by_classes(items)

    if not all_stats:
        console.print("[yellow]⚠️  Сплиты не найдены. Сначала запустите split_dataset.py[/yellow]")
        return

    # Все уникальные классы
    all_classes = set()
    for stats in all_stats.values():
        all_classes.update(stats.keys())

    # Сортировка
    def sort_key(k):
        if k.startswith("secret_"):
            return (0, k)
        elif k.startswith("insecure_"):
            return (1, k)
        else:
            return (2, k)

    for cls in sorted(all_classes, key=sort_key):
        train_count = all_stats.get("train", {}).get(cls, {}).get("count", 0)
        valid_count = all_stats.get("valid", {}).get(cls, {}).get("count", 0)
        test_count = all_stats.get("test", {}).get(cls, {}).get("count", 0)
        total = train_count + valid_count + test_count

        # Подсветка, если в каком-то сплите нет примеров
        train_str = f"[red]{train_count}[/red]" if train_count == 0 else str(train_count)
        valid_str = f"[red]{valid_count}[/red]" if valid_count == 0 else str(valid_count)
        test_str = f"[red]{test_count}[/red]" if test_count == 0 else str(test_count)

        if cls.startswith("secret_"):
            display = f"🔑 {cls[7:]}"
        elif cls.startswith("insecure_"):
            display = f"⚠️  {cls[9:]}"
        else:
            display = "🚫 negative"

        table.add_row(display, train_str, valid_str, test_str, str(total))

    console.print(table)


def main():
    """Главная функция."""
    # Путь к датасету из аргументов или по умолчанию
    if len(sys.argv) > 1:
        dataset_path = sys.argv[1]
    else:
        dataset_path = "data/final_dataset.jsonl"

    # Анализ основного датасета
    stats = analyze_file(dataset_path)

    if stats is None:
        return

    # Анализ сплитов (если есть)
    if Path("data/train.jsonl").exists():
        analyze_splits()

    console.print("\n" + "=" * 80)
    console.print("[bold]Анализ завершён[/bold]")
    console.print("=" * 80)


if __name__ == "__main__":
    main()