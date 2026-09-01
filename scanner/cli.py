# scanner/cli.py
"""
CLI-РёРЅС‚РµСЂС„РµР№СЃ СЃРєР°РЅРµСЂР° РЅР° Р±Р°Р·Рµ Typer.
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
    help="рџ”Ќ SLM-СЃРєР°РЅРµСЂ СЃРµРєСЂРµС‚РѕРІ Рё РЅРµР±РµР·РѕРїР°СЃРЅРѕРіРѕ РєРѕРґР°",
    add_completion=False,
)

console = Console()


# ==========================================
# РљРѕРјР°РЅРґР°: scan
# ==========================================
@app.command()
def scan(
        path: str = typer.Argument(..., help="РџСѓС‚СЊ Рє С„Р°Р№Р»Сѓ РёР»Рё РїР°РїРєРµ"),
        format: str = typer.Option("text", "--format", "-f", help="Р¤РѕСЂРјР°С‚ РѕС‚С‡С‘С‚Р°: text, json, markdown"),
        out: Optional[str] = typer.Option(None, "--out", "-o", help="РџСѓС‚СЊ Рє С„Р°Р№Р»Сѓ РѕС‚С‡С‘С‚Р°"),
        with_slm: bool = typer.Option(
            False, "--with-slm",
            help="Р’РєР»СЋС‡РёС‚СЊ РєР°СЃРєР°Рґ: baseline в†’ РїСЂРѕРІРµСЂРєР° SLM (С‚РѕС‡РЅРµРµ, РЅРѕ РјРµРґР»РµРЅРЅРµРµ)"
        ),
        context_lines: int = typer.Option(3, "--context", help="РљРѕР»РёС‡РµСЃС‚РІРѕ СЃС‚СЂРѕРє РєРѕРЅС‚РµРєСЃС‚Р°"),
):
    """РЎРєР°РЅРёСЂСѓРµС‚ РїСѓС‚СЊ РЅР° СЃРµРєСЂРµС‚С‹ Рё РЅРµР±РµР·РѕРїР°СЃРЅС‹Р№ РєРѕРґ."""
    # Р‘Р°РЅРЅРµСЂ вЂ” Р”Рћ СЃРєР°РЅРёСЂРѕРІР°РЅРёСЏ
    console.print(Panel.fit(
        f"[bold cyan]рџ”Ќ SLM Secret & Insecure Code Scanner[/bold cyan]\n"
        f"Р’РµСЂСЃРёСЏ: {__version__}",
        border_style="cyan",
    ))

    target = Path(path)
    if not target.exists():
        console.print(f"[red]вќЊ РџСѓС‚СЊ РЅРµ РЅР°Р№РґРµРЅ: {path}[/red]")
        raise typer.Exit(code=1)

    files = list(iter_files(path))
    console.print(f"рџ“Ѓ РќР°Р№РґРµРЅРѕ С„Р°Р№Р»РѕРІ РґР»СЏ Р°РЅР°Р»РёР·Р°: [bold]{len(files)}[/bold]")

    if not files:
        console.print("[yellow]вљ пёЏ  РќРµС‚ С„Р°Р№Р»РѕРІ РґР»СЏ СЃРєР°РЅРёСЂРѕРІР°РЅРёСЏ[/yellow]")
        raise typer.Exit(code=0)

    # Р•Р”РРќРЎРўР’Р•РќРќРћР• СЃРєР°РЅРёСЂРѕРІР°РЅРёРµ: baseline РёР»Рё РєР°СЃРєР°Рґ
    if with_slm:
        console.print("[bold green]рџ¤– РљР°СЃРєР°Рґ: baseline в†’ РїСЂРѕРІРµСЂРєР° SLM[/bold green]")
        findings = scan_path(path, show_progress=True)
        from scanner.core.cascade import verify_with_slm
        findings = verify_with_slm(findings)
    else:
        findings = scan_path(path, show_progress=True)

    # РЎРІРѕРґРєР°
    secrets = [f for f in findings if f.category == "secret"]
    insecure = [f for f in findings if f.category == "insecure_code"]

    console.print()
    console.print(f"[green]вњ… РЎРєР°РЅРёСЂРѕРІР°РЅРёРµ Р·Р°РІРµСЂС€РµРЅРѕ[/green]")
    console.print(f"   РќР°Р№РґРµРЅРѕ СЃСЂР°Р±Р°С‚С‹РІР°РЅРёР№: [bold]{len(findings)}[/bold]")
    console.print(f"   вЂў РЎРµРєСЂРµС‚РѕРІ: [bold red]{len(secrets)}[/bold red]")
    console.print(f"   вЂў РќРµР±РµР·РѕРїР°СЃРЅРѕРіРѕ РєРѕРґР°: [bold yellow]{len(insecure)}[/bold yellow]")
    console.print()

    # Р’С‹РІРѕРґ СЂРµР·СѓР»СЊС‚Р°С‚РѕРІ
    if format == "text":
        _print_text_report(findings)
    elif format == "json":
        _save_json_report(findings, out or "reports/report.json")
    elif format == "markdown":
        _save_markdown_report(findings, out or "reports/report.md")
    else:
        console.print(f"[red]вќЊ РќРµРёР·РІРµСЃС‚РЅС‹Р№ С„РѕСЂРјР°С‚: {format}[/red]")
        raise typer.Exit(code=1)


def _print_text_report(findings):
    """Р’С‹РІРѕРґ РѕС‚С‡С‘С‚Р° РІ РєРѕРЅСЃРѕР»СЊ."""
    if not findings:
        console.print("[green]вњЁ РЎСЂР°Р±Р°С‚С‹РІР°РЅРёР№ РЅРµ РЅР°Р№РґРµРЅРѕ[/green]")
        return

    table = Table(title="рџ“‹ РќР°Р№РґРµРЅРЅС‹Рµ СЃСЂР°Р±Р°С‚С‹РІР°РЅРёСЏ", box=box.ROUNDED)
    table.add_column("Р¤Р°Р№Р»", style="cyan")
    table.add_column("РЎС‚СЂРѕРєР°", justify="right", style="magenta")
    table.add_column("РўРёРї", style="yellow")
    table.add_column("РљР°С‚РµРіРѕСЂРёСЏ", style="blue")
    table.add_column("Severity", style="red")
    table.add_column("Confidence", justify="right")
    table.add_column("Р”РµС‚РµРєС‚РѕСЂ", style="green")

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

    # РџРµСЂРІС‹Рµ 3 РѕР±СЉСЏСЃРЅРµРЅРёСЏ
    console.print()
    console.print("[bold]рџ’Ў РџСЂРёРјРµСЂС‹ РѕР±СЉСЏСЃРЅРµРЅРёР№:[/bold]")
    for f in findings[:3]:
        console.print(f"  вЂў [cyan]{f.file}:{f.line}[/cyan] вЂ” {f.explanation}")


def _save_json_report(findings, out_path: str):
    """РЎРѕС…СЂР°РЅРµРЅРёРµ JSON-РѕС‚С‡С‘С‚Р°."""
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

    console.print(f"рџ“ќ JSON-РѕС‚С‡С‘С‚ СЃРѕС…СЂР°РЅС‘РЅ: [bold]{out_path}[/bold]")


def _save_markdown_report(findings, out_path: str):
    """РЎРѕС…СЂР°РЅРµРЅРёРµ Markdown-РѕС‚С‡С‘С‚Р°."""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8-sig") as f:
        secrets = [f for f in findings if f.category == "secret"]
        insecure = [f for f in findings if f.category == "insecure_code"]
        lines = [
        "# рџ”Ќ РћС‚С‡С‘С‚ СЃРєР°РЅРµСЂР° СЃРµРєСЂРµС‚РѕРІ Рё РЅРµР±РµР·РѕРїР°СЃРЅРѕРіРѕ РєРѕРґР°",
        "",
        f"**Р’РµСЂСЃРёСЏ:** {__version__}",
        "",
        "## рџ“Љ РЎРІРѕРґРєР°",
        "",
        f"- **Р’СЃРµРіРѕ СЃСЂР°Р±Р°С‚С‹РІР°РЅРёР№:** {len(findings)}",
        f"- **РЎРµРєСЂРµС‚РѕРІ:** {len(secrets)}",
        f"- **РќРµР±РµР·РѕРїР°СЃРЅРѕРіРѕ РєРѕРґР°:** {len(insecure)}",
        "",
        "## рџ“‹ РўР°Р±Р»РёС†Р° СЃСЂР°Р±Р°С‚С‹РІР°РЅРёР№",
        "",
        "| Р¤Р°Р№Р» | РЎС‚СЂРѕРєР° | РўРёРї | РљР°С‚РµРіРѕСЂРёСЏ | Severity | Detector |",
        "|---|---|---|---|---|---|",
    ]

    for f in findings:
        lines.append(
            f"| `{f.file}` | {f.line} | {f.type} | {f.category} | "
            f"{f.severity.value} | {f.detector.value} |"
        )

    lines.extend(["", "## рџ’Ў РћР±СЉСЏСЃРЅРµРЅРёСЏ", ""])
    for f in findings:
        lines.append(f"### `{f.file}:{f.line}` вЂ” {f.type}")
        lines.append(f"- **РљР°С‚РµРіРѕСЂРёСЏ:** {f.category}")
        lines.append(f"- **Severity:** {f.severity.value}")
        lines.append(f"- **Confidence:** {f.confidence:.2f}")
        lines.append(f"- **РћР±СЉСЏСЃРЅРµРЅРёРµ:** {f.explanation}")
        lines.append(f"- **Р¤СЂР°РіРјРµРЅС‚:** `{f.snippet.strip()}`")
        lines.append("")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    console.print(f"рџ“ќ Markdown-РѕС‚С‡С‘С‚ СЃРѕС…СЂР°РЅС‘РЅ: [bold]{out_path}[/bold]")


# ==========================================
# РљРѕРјР°РЅРґР°: info
# ==========================================
@app.command()
def info():
    """
    РџРѕРєР°Р·Р°С‚СЊ РёРЅС„РѕСЂРјР°С†РёСЋ Рѕ СЃРєР°РЅРµСЂРµ Рё РјРѕРґРµР»Рё.
    """
    console.print(Panel.fit(
        "[bold cyan]рџ”Ќ SLM Secret & Insecure Code Scanner[/bold cyan]\n"
        f"Р’РµСЂСЃРёСЏ: {__version__}",
        border_style="cyan",
    ))

    table = Table(box=box.ROUNDED, show_header=False)
    table.add_column("РџР°СЂР°РјРµС‚СЂ", style="bold")
    table.add_column("Р—РЅР°С‡РµРЅРёРµ")

    table.add_row("РЇР·С‹Рє", "Python 3.11+")
    table.add_row("CLI", "Typer")
    table.add_row("SLM", "Qwen2.5-Coder-1.5B-Instruct")
    table.add_row("Baseline-РґРµС‚РµРєС‚РѕСЂС‹", "regex, entropy, keyword")
    table.add_row("РљР»Р°СЃСЃС‹ СЃРµРєСЂРµС‚РѕРІ", "5 (api_key, token, password, private_key, jwt)")
    table.add_row("РљР»Р°СЃСЃС‹ insecure", "6 (eval, exec, shell, sql, hash, creds)")

    console.print(table)


# ==========================================
# РљРѕРјР°РЅРґР°: version
# ==========================================
@app.command()
def version():
    """РџРѕРєР°Р·Р°С‚СЊ РІРµСЂСЃРёСЋ СЃРєР°РЅРµСЂР°."""
    console.print(f"[cyan]SLM Scanner[/cyan] version [bold]{__version__}[/bold]")


# ==========================================
# РљРѕРјР°РЅРґР°: demo
# ==========================================
@app.command()
def demo():
    """
    Р—Р°РїСѓСЃС‚РёС‚СЊ РґРµРјРѕРЅСЃС‚СЂР°С†РёСЋ РЅР° СѓС‡РµР±РЅРѕРј СЂРµРїРѕР·РёС‚РѕСЂРёРё.
    """
    console.print(Panel.fit(
        "[bold cyan]рџЋ¬ Р”РµРјРѕРЅСЃС‚СЂР°С†РёСЏ СЃРєР°РЅРµСЂР°[/bold cyan]",
        border_style="cyan",
    ))

    demo_path = Path("examples/example_repo")
    if not demo_path.exists():
        console.print("[yellow]вљ пёЏ  РЈС‡РµР±РЅС‹Р№ СЂРµРїРѕР·РёС‚РѕСЂРёР№ РЅРµ РЅР°Р№РґРµРЅ.[/yellow]")
        console.print("РЎРѕР·РґР°Р№С‚Рµ [bold]examples/example_repo/[/bold] СЃ С‚РµСЃС‚РѕРІС‹РјРё С„Р°Р№Р»Р°РјРё.")
        console.print()
        console.print("Р—Р°РїСѓСЃС‚РёС‚Рµ СЃРєР°РЅРёСЂРѕРІР°РЅРёРµ РІСЂСѓС‡РЅСѓСЋ:")
        console.print("  [cyan]python -m scanner scan <РїСѓС‚СЊ>[/cyan]")
        raise typer.Exit(code=1)

    # Р’С‹Р·С‹РІР°РµРј scan
    scan(str(demo_path), format="text", baseline_only=True)


# ==========================================
# Callback РґР»СЏ РіР»Р°РІРЅРѕРіРѕ РјРµРЅСЋ
# ==========================================
@app.callback()
def main():
    """
    рџ”Ќ SLM-СЃРєР°РЅРµСЂ СЃРµРєСЂРµС‚РѕРІ Рё РЅРµР±РµР·РѕРїР°СЃРЅРѕРіРѕ РєРѕРґР°.
    РСЃРїРѕР»СЊР·СѓР№С‚Рµ --help РґР»СЏ СЃРїРёСЃРєР° РєРѕРјР°РЅРґ.
    """
    pass


if __name__ == "__main__":
    app()
