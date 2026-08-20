"""Commande ``condata analyze``."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

import typer

from condata import DatasetInspector
from condata.models.config import AnalysisConfig
from condata.reporting.html import export_html
from condata.reporting.json import export_json
from condata.reporting.terminal import render_terminal
from condata.utils.io import DatasetLoadError


class OutputFormat(str, Enum):
    html = "html"
    json = "json"
    all = "all"


def analyze(
    dataset: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="Fichier CSV à analyser (local).",
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.html,
        "--format",
        "-f",
        help="Format d'export : html, json, ou all.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Chemin du fichier généré (html ou json selon --format).",
    ),
    browser: bool = typer.Option(
        True,
        "--browser/--no-browser",
        help="Ouvre le rapport HTML dans le navigateur.",
    ),
    target: str | None = typer.Option(
        None,
        "--target",
        help="Nom de la colonne cible (ML Readiness).",
    ),
) -> None:
    """Analyse un dataset CSV et génère un rapport local."""
    config = AnalysisConfig(target_column=target) if target else AnalysisConfig()
    try:
        inspector = DatasetInspector(dataset, config=config)
        result = inspector.analyze()
    except DatasetLoadError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    render_terminal(result)
    html_path, json_path = _resolve_outputs(output_format, output)

    if html_path is not None:
        written = export_html(
            result,
            html_path,
            frame=inspector.dataframe,
            open_browser=browser,
        )
        typer.echo(f"Rapport HTML : {written}")

    if json_path is not None:
        written = export_json(result, json_path)
        typer.echo(f"Rapport JSON : {written}")


def _resolve_outputs(
    output_format: OutputFormat,
    output: Path | None,
) -> tuple[Path | None, Path | None]:
    if output_format is OutputFormat.html:
        return output or Path("condata-report.html"), None
    if output_format is OutputFormat.json:
        return None, output or Path("condata-report.json")
    if output is None:
        return Path("condata-report.html"), Path("condata-report.json")
    if output.suffix.lower() == ".json":
        return output.with_suffix(".html"), output
    return output, output.with_suffix(".json")
