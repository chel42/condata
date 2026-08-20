"""Générateur du rapport HTML interactif (Jinja2 + Plotly)."""

from __future__ import annotations

import webbrowser
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
from jinja2 import Environment, FileSystemLoader, select_autoescape

from condata.models.schema import AnalysisResult
from condata.reporting.recommendations import build_recommendations
from condata.utils.formatters import (
    format_bytes,
    format_number,
    format_pct,
    score_level,
)

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
_MAX_CHARTS = 8


def export_html(
    result: AnalysisResult,
    path: str | Path,
    *,
    frame: pd.DataFrame | None = None,
    open_browser: bool = False,
) -> Path:
    """Génère un rapport HTML local et l'ouvre éventuellement dans le navigateur."""
    env = Environment(
        loader=FileSystemLoader(_TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "j2"]),
    )
    env.filters["bytes"] = format_bytes
    env.filters["pct"] = format_pct
    env.filters["num"] = format_number
    template = env.get_template("report.html.j2")
    css = (_TEMPLATE_DIR / "assets" / "style.css").read_text(encoding="utf-8")
    html = template.render(
        result=result,
        css=css,
        charts=_build_charts(result, frame),
        recommendations=build_recommendations(result),
        quality_level=score_level(result.quality.score),
        readiness_level=score_level(result.readiness.score),
    )
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    resolved = output.resolve()
    if open_browser:
        webbrowser.open(resolved.as_uri())
    return resolved


def _build_charts(
    result: AnalysisResult,
    frame: pd.DataFrame | None,
) -> dict[str, str]:
    charts: dict[str, str] = {}
    include_js = "inline"
    if frame is not None and not frame.empty:
        numeric_done = 0
        for column in result.profile.columns:
            if numeric_done >= _MAX_CHARTS:
                break
            if column.semantic_type != "numeric" or column.name not in frame.columns:
                continue
            series = pd.to_numeric(frame[column.name], errors="coerce").dropna()
            if series.empty:
                continue
            fig = go.Figure(
                data=[go.Histogram(x=series, marker_color="#0f766e", nbinsx=20)]
            )
            fig.update_layout(
                title=f"Distribution — {column.name}",
                margin=dict(l=40, r=20, t=50, b=40),
                height=320,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="#f8fafb",
                font=dict(color="#134e4a"),
            )
            charts[f"hist_{column.name}"] = _fig_html(fig, include_js)
            include_js = False
            numeric_done += 1

        cat_done = 0
        for stats in result.statistics.categorical:
            if cat_done >= 4 or not stats.frequencies:
                continue
            fig = go.Figure(
                data=[
                    go.Bar(
                        x=[item.value for item in stats.frequencies[:15]],
                        y=[item.count for item in stats.frequencies[:15]],
                        marker_color="#115e59",
                    )
                ]
            )
            fig.update_layout(
                title=f"Fréquences — {stats.name}",
                margin=dict(l=40, r=20, t=50, b=80),
                height=320,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="#f8fafb",
                font=dict(color="#134e4a"),
            )
            charts[f"bar_{stats.name}"] = _fig_html(fig, include_js)
            include_js = False
            cat_done += 1

    matrix = result.correlations.matrix
    names = list(matrix.keys())
    if len(names) >= 2:
        z: list[list[float | None]] = [
            [matrix[row].get(col) for col in names] for row in names
        ]
        fig = go.Figure(
            data=[
                go.Heatmap(
                    z=z,
                    x=names,
                    y=names,
                    zmin=-1,
                    zmax=1,
                    colorscale="Teal",
                    colorbar=dict(title="r"),
                )
            ]
        )
        fig.update_layout(
            title="Matrice de corrélation",
            margin=dict(l=80, r=20, t=50, b=80),
            height=420,
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#134e4a"),
        )
        charts["heatmap"] = _fig_html(fig, include_js)

    missing = result.quality.missing.columns
    if missing:
        fig = go.Figure(
            data=[
                go.Bar(
                    x=[col.name for col in missing],
                    y=[col.missing_pct for col in missing],
                    marker_color="#b45309",
                )
            ]
        )
        fig.update_layout(
            title="Valeurs manquantes (%)",
            margin=dict(l=40, r=20, t=50, b=80),
            height=320,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#f8fafb",
            font=dict(color="#134e4a"),
            yaxis=dict(ticksuffix=" %"),
        )
        charts["missing"] = _fig_html(fig, include_js)

    return charts


def _fig_html(fig: go.Figure, include_js: Any) -> str:
    return fig.to_html(
        full_html=False,
        include_plotlyjs=include_js,
        config={"displayModeBar": False, "responsive": True},
    )
