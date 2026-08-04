# scanner/cli.py
"""
CLI-интерфейс сканера на базе Typer.
"""
import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from scanner import __version__
from scanner.core.scanner import scan_path, iter_files

app = typer.Typer(
    name="scanner",
    help="🔍 SLM-сканер секретов и небезопасного кода",
    add_completion=False,
)

console = Console()


# ==========================================
# Команда: scan
# ==========================================
@app.command()
def scan(
    path: str = typer.Argument(..., help="Путь к файлу или каталогу для сканирования"),
    format: str = typer.Option("text", "--format", "-f", help="Формат отчёта: text, json, markdown"),
    out: Optional[str] = typer.Option(None, "--out", "-o", help="Путь к файлу отчёта"),
    baseline_only: bool = typer.Option(True, "--baseline-only", help="Использовать только baseline-детекторы"),
    context_lines: int = typer.Option(3, "--context", help="Количество строк контекста"),
):
    """
    Сканировать каталог на наличие секретов и небезопасного кода.
    """
    console.print(Panel.fit(
        f"[bold cyan]🔍 SLM Secret & Insecure Code Scanner[/bold cyan]\n"
        f"Версия: {__version__}",
        border_style="cyan",
    ))

    target = Path(path)
    if not target.exists():
        console.print(f"[red]❌ Путь не найден: {path}[/red]")
        raise typer.Exit(code=1)

    files = list(iter_files(path))
    console.print(f"📁 Найдено файлов для анализа: [bold]{len(files)}[/bold]")

    if not files:
        console.print("[yellow]⚠️  Нет файлов для сканирования[/yellow]")
        raise typer.Exit(code=0)

    # Сканирование
    findings = scan_path(path, show_progress=True)

    # Сводка
    secrets = [f for f in findings if f.category == "secret"]
    insecure = [f for f in findings if f.category == "insecure_code"]

    console.print()
    console.print(f"[green]✅ Сканирование завершено[/green]")
    console.print(f"   Найдено срабатываний: [bold]{len(findings)}[/bold]")
    console.print(f"   • Секретов: [bold red]{len(secrets)}[/bold red]")
    console.print(f"   • Небезопасного кода: [bold yellow]{len(insecure)}[/bold yellow]")
    console.print()

    # Вывод результатов
    if format == "text":
        _print_text_report(findings)
    elif format == "json":
        _save_json_report(findings, out or "reports/report.json")
    elif format == "markdown":
        _save_markdown_report(findings, out or "reports/report.md")
    else:
        console.print(f"[red]❌ Неизвестный формат: {format}[/red]")
        raise typer.Exit(code=1)


def _print_text_report(findings):
    """Вывод отчёта в консоль."""
    if not findings:
        console.print("[green]✨ Срабатываний не найдено[/green]")
        return

    table = Table(title="📋 Найденные срабатывания", box=box.ROUNDED)
    table.add_column("Файл", style="cyan")
    table.add_column("Строка", justify="right", style="magenta")
    table.add_column("Тип", style="yellow")
    table.add_column("Категория", style="blue")
    table.add_column("Severity", style="red")
    table.add_column("Confidence", justify="right")
    table.add_column("Детектор", style="green")

    for f in findings:
        table.add_row(
            f.file,
            str(f.line),
            f.type,
            f.category,
            f.severity.value,
            f"{f.confidence:.2f}",
            f.detector.value,
        )

    console.print(table)

    # Первые 3 объяснения
    console.print()
    console.print("[bold]💡 Примеры объяснений:[/bold]")
    for f in findings[:3]:
        console.print(f"  • [cyan]{f.file}:{f.line}[/cyan] — {f.explanation}")


def _save_json_report(findings, out_path: str):
    """Сохранение JSON-отчёта."""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    report = {
        "scan_info": {
            "version": __version__,
            "total_findings": len(findings),
            "secrets": len([f for f in findings if f.category == "secret"]),
            "insecure_code": len([f for f in findings if f.category == "insecure_code"]),
        },
        "findings": [f.model_dump() for f in findings],
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    console.print(f"📝 JSON-отчёт сохранён: [bold]{out_path}[/bold]")


def _save_markdown_report(findings, out_path: str):
    """Сохранение Markdown-отчёта."""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    secrets = [f for f in findings if f.category == "secret"]
    insecure = [f for f in findings if f.category == "insecure_code"]

    lines = [
        "# 🔍 Отчёт сканера секретов и небезопасного кода",
        "",
        f"**Версия:** {__version__}",
        "",
        "## 📊 Сводка",
        "",
        f"- **Всего срабатываний:** {len(findings)}",
        f"- **Секретов:** {len(secrets)}",
        f"- **Небезопасного кода:** {len(insecure)}",
        "",
        "## 📋 Таблица срабатываний",
        "",
        "| Файл | Строка | Тип | Категория | Severity | Detector |",
        "|---|---|---|---|---|---|",
    ]

    for f in findings:
        lines.append(
            f"| `{f.file}` | {f.line} | {f.type} | {f.category} | "
            f"{f.severity.value} | {f.detector.value} |"
        )

    lines.extend(["", "## 💡 Объяснения", ""])
    for f in findings:
        lines.append(f"### `{f.file}:{f.line}` — {f.type}")
        lines.append(f"- **Категория:** {f.category}")
        lines.append(f"- **Severity:** {f.severity.value}")
        lines.append(f"- **Confidence:** {f.confidence:.2f}")
        lines.append(f"- **Объяснение:** {f.explanation}")
        lines.append(f"- **Фрагмент:** `{f.snippet.strip()}`")
        lines.append("")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    console.print(f"📝 Markdown-отчёт сохранён: [bold]{out_path}[/bold]")


# ==========================================
# Команда: info
# ==========================================
@app.command()
def info():
    """
    Показать информацию о сканере и модели.
    """
    console.print(Panel.fit(
        "[bold cyan]🔍 SLM Secret & Insecure Code Scanner[/bold cyan]\n"
        f"Версия: {__version__}",
        border_style="cyan",
    ))

    table = Table(box=box.ROUNDED, show_header=False)
    table.add_column("Параметр", style="bold")
    table.add_column("Значение")

    table.add_row("Язык", "Python 3.11+")
    table.add_row("CLI", "Typer")
    table.add_row("SLM", "Qwen2.5-Coder-1.5B-Instruct")
    table.add_row("Baseline-детекторы", "regex, entropy, keyword")
    table.add_row("Классы секретов", "5 (api_key, token, password, private_key, jwt)")
    table.add_row("Классы insecure", "6 (eval, exec, shell, sql, hash, creds)")

    console.print(table)


# ==========================================
# Команда: version
# ==========================================
@app.command()
def version():
    """Показать версию сканера."""
    console.print(f"[cyan]SLM Scanner[/cyan] version [bold]{__version__}[/bold]")


# ==========================================
# Команда: demo
# ==========================================
@app.command()
def demo():
    """
    Запустить демонстрацию на учебном репозитории.
    """
    console.print(Panel.fit(
        "[bold cyan]🎬 Демонстрация сканера[/bold cyan]",
        border_style="cyan",
    ))

    demo_path = Path("examples/example_repo")
    if not demo_path.exists():
        console.print("[yellow]⚠️  Учебный репозиторий не найден.[/yellow]")
        console.print("Создайте [bold]examples/example_repo/[/bold] с тестовыми файлами.")
        console.print()
        console.print("Запустите сканирование вручную:")
        console.print("  [cyan]python -m scanner scan <путь>[/cyan]")
        raise typer.Exit(code=1)

    # Вызываем scan
    scan(str(demo_path), format="text", baseline_only=True)


# ==========================================
# Callback для главного меню
# ==========================================
@app.callback()
def main():
    """
    🔍 SLM-сканер секретов и небезопасного кода.
    Используйте --help для списка команд.
    """
    pass


if __name__ == "__main__":
    app()