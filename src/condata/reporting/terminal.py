"""Rendu CLI enrichi (tableaux Rich)."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from condata.models.schema import AnalysisResult
from condata.reporting.recommendations import build_recommendations
from condata.utils.formatters import format_bytes, format_pct


def render_terminal(result: AnalysisResult, *, console: Console | None = None) -> None:
    """Affiche le résumé d'analyse dans le terminal."""
    out = console or Console()
    profile = result.profile
    quality = result.quality
    readiness = result.readiness

    header = Text.assemble(
        ("CONDATA", "bold cyan"),
        "  ",
        (profile.file_name, "bold"),
        f"  ·  {profile.n_rows} lignes  ·  {profile.n_columns} colonnes  ·  "
        f"{format_bytes(profile.file_size_bytes)}",
    )
    out.print(header)
    out.print()

    scores = Table.grid(padding=(0, 3))
    scores.add_column()
    scores.add_column()
    scores.add_row(
        Panel(
            _score_text("DATA QUALITY", quality.score),
            border_style=_score_style(quality.score),
        ),
        Panel(
            _score_text("ML READINESS", readiness.score),
            border_style=_score_style(readiness.score),
        ),
    )
    out.print(scores)
    out.print(f"[dim]{readiness.disclaimer}[/dim]")
    out.print()

    schema = Table(title="Schema", show_header=True, header_style="bold")
    schema.add_column("Colonne")
    schema.add_column("Type")
    schema.add_column("Non-null", justify="right")
    schema.add_column("Unique", justify="right")
    schema.add_column("Manquant", justify="right")
    for column in profile.columns:
        schema.add_row(
            column.name,
            column.semantic_type,
            format_pct(column.non_null_pct),
            str(column.unique_count),
            format_pct(column.missing_pct),
        )
    out.print(schema)
    out.print()

    issues = Table(title="Warnings", show_header=True, header_style="bold")
    issues.add_column("Sévérité")
    issues.add_column("Colonne")
    issues.add_column("Message")
    if quality.issues:
        for issue in quality.issues:
            issues.add_row(
                issue.severity.upper(),
                issue.column or "—",
                issue.message,
            )
        out.print(issues)
        out.print()

    recs = build_recommendations(result)
    out.print("[bold]Recommendations[/bold]")
    for item in recs:
        out.print(f"  • {item}")
    out.print()
    out.print("[dim]Les données n'ont pas quitté cette machine.[/dim]")


def _score_text(title: str, score: int) -> Text:
    text = Text()
    text.append(f"{title}\n", style="dim")
    text.append(f"{score}", style=f"bold {_score_style(score)}")
    text.append(" / 100")
    return text


def _score_style(score: int) -> str:
    if score >= 80:
        return "green"
    if score >= 50:
        return "yellow"
    return "red"
