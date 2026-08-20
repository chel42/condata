"""Générateur du rapport HTML interactif (Jinja2 + Plotly)."""

from __future__ import annotations

import base64
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
from jinja2 import Environment, FileSystemLoader, select_autoescape

from condata.core.profiler import is_numeric_type
from condata.models.schema import AnalysisResult
from condata.reporting.recommendations import build_recommendation_items
from condata.utils.formatters import (
    format_bytes,
    format_int,
    format_number,
    format_pct,
    quality_label,
    readiness_label,
    score_level,
)

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
_MONTHS = (
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
)
_TYPE_FR = {
    "integer": "Entier",
    "float": "Réel",
    "datetime": "Date/heure",
    "text": "Texte",
    "boolean": "Booléen",
    "unknown": "Inconnu",
}
_STATUS_FR = {
    "ok": "OK",
    "warning": "Attention",
    "critical": "Critique",
    "info": "Info",
}
_SKIP_FR = {
    "insufficient_values": "Pas assez de valeurs",
    "zero_variance": "Variance nulle",
}
_AXIS = dict(
    gridcolor="rgba(0, 180, 200, 0.12)",
    zerolinecolor="rgba(0, 229, 255, 0.18)",
    linecolor="rgba(0, 229, 255, 0.18)",
    tickfont=dict(color="#7ea8a2"),
    title=dict(font=dict(color="#9ecdc4")),
)
_PLOTLY_LAYOUT = dict(
    margin=dict(l=36, r=16, t=12, b=48),
    height=260,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(5, 25, 55, 0.35)",
    font=dict(
        color="#b7dcd4",
        size=12,
        family="Segoe UI, Bahnschrift, system-ui, sans-serif",
    ),
    showlegend=True,
    legend=dict(orientation="h", y=-0.18, font=dict(color="#b7dcd4")),
    xaxis=_AXIS,
    yaxis=_AXIS,
    colorway=["#00b4a8", "#39ff14", "#00e5ff", "#ffb800", "#0a4a8a"],
)


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
    env.filters["intspace"] = format_int
    env.filters["typefr"] = lambda value: _TYPE_FR.get(str(value), str(value))
    env.filters["statusfr"] = lambda value: _STATUS_FR.get(str(value), str(value))
    env.filters["statuslevel"] = _status_level
    env.filters["skipfr"] = _skip_reason_fr
    template = env.get_template("report.html.j2")
    css = (_TEMPLATE_DIR / "assets" / "style.css").read_text(encoding="utf-8")
    charts, dist_name = _build_charts(result, frame)
    html = template.render(
        result=result,
        css=css,
        logo_src=_logo_data_uri(),
        charts=charts,
        distribution_column=dist_name,
        recommendations=build_recommendation_items(result),
        warnings=_html_warnings(result),
        stats_truncated=any(col.truncated for col in result.statistics.categorical),
        quality_level=score_level(result.quality.score),
        readiness_level=score_level(result.readiness.score),
        quality_badge=quality_label(result.quality.score),
        readiness_badge=readiness_label(result.readiness.score),
        check_counts=_check_counts(result),
        generated_label=_format_datetime_fr(result.generated_at),
        json_payload=result.model_dump_json(),
    )
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    resolved = output.resolve()
    if open_browser:
        webbrowser.open(resolved.as_uri())
    return resolved


def _check_counts(result: AnalysisResult) -> dict[str, int]:
    counts = {"ok": 0, "warning": 0, "critical": 0, "info": 0}
    for check in result.readiness.checks:
        counts[check.status] = counts.get(check.status, 0) + 1
    counts["total"] = len(result.readiness.checks)
    return counts


def _status_level(status: str) -> str:
    if status in {"ok", "info"}:
        return "good"
    if status == "warning":
        return "mid"
    return "bad"


def _skip_reason_fr(value: str | None) -> str:
    if not value:
        return ""
    return _SKIP_FR.get(str(value), str(value))


def _html_warnings(result: AnalysisResult) -> list[dict[str, str]]:
    """Problèmes affichés dans le bloc Warnings (qualité + corrélations)."""
    items: list[dict[str, str]] = []
    for issue in result.quality.issues:
        items.append(
            {
                "severity": issue.severity,
                "column": issue.column or "—",
                "message": issue.message,
            }
        )
    for warning in result.correlations.warnings:
        items.append(
            {
                "severity": "warning",
                "column": ", ".join(warning.columns) or "—",
                "message": warning.message,
            }
        )
    return items


def _format_datetime_fr(moment: datetime) -> str:
    local = moment.astimezone() if moment.tzinfo else moment
    return (
        f"{local.day} {_MONTHS[local.month - 1]} {local.year} "
        f"à {local.hour:02d}:{local.minute:02d}"
    )


def _build_charts(
    result: AnalysisResult,
    frame: pd.DataFrame | None,
) -> tuple[dict[str, str], str | None]:
    charts: dict[str, str] = {}
    include_js: Any = "inline"
    counts = _check_counts(result)
    pie_labels = []
    pie_values = []
    pie_colors = []
    mapping = (
        ("Bon", "ok", "#39FF14"),
        ("Attention", "warning", "#FFB800"),
        ("Critique", "critical", "#FF4D6D"),
    )
    for label, key, color in mapping:
        if counts.get(key, 0):
            pie_labels.append(label)
            pie_values.append(counts[key])
            pie_colors.append(color)
    if pie_values:
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=pie_labels,
                    values=pie_values,
                    hole=0.62,
                    marker=dict(colors=pie_colors),
                    textinfo="percent",
                    hovertemplate="%{label}: %{value}<extra></extra>",
                )
            ]
        )
        pie_layout = dict(_PLOTLY_LAYOUT)
        pie_layout.update(
            annotations=[
                dict(
                    text=f"<b>{counts['total']}</b><br>Vérifications",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                    font=dict(size=13, color="#eaf6f2"),
                )
            ],
            margin=dict(l=10, r=10, t=10, b=40),
            height=280,
        )
        fig.update_layout(**pie_layout)
        charts["overview"] = _fig_html(fig, include_js)
        include_js = False

    missing = result.quality.missing.columns
    if missing:
        colors = [
            (
                "#FF4D6D"
                if col.missing_pct >= 20
                else "#FFB800"
                if col.missing_pct >= 5
                else "#39FF14"
            )
            for col in missing
        ]
        fig = go.Figure(
            data=[
                go.Bar(
                    x=[col.name for col in missing],
                    y=[col.missing_pct for col in missing],
                    marker_color=colors,
                    hovertemplate="%{x}: %{y:.1f} %<extra></extra>",
                )
            ]
        )
        layout = dict(_PLOTLY_LAYOUT)
        layout["showlegend"] = False
        layout["yaxis"] = {**_AXIS, "ticksuffix": " %", "range": [0, 100]}
        fig.update_layout(**layout)
        charts["missing"] = _fig_html(fig, include_js)
        include_js = False

    dist = _distribution_figure(result, frame)
    dist_name = None
    if dist is not None:
        charts["distribution"] = _fig_html(dist[0], include_js)
        dist_name = dist[1]
        include_js = False

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
                    colorscale=[
                        [0, "#FF4D6D"],
                        [0.5, "#051937"],
                        [1, "#39FF14"],
                    ],
                    colorbar=dict(
                        title=dict(text="r", font=dict(color="#b7dcd4")),
                        thickness=12,
                        tickfont=dict(color="#b7dcd4"),
                    ),
                    text=[[_cell(v) for v in row] for row in z],
                    texttemplate="%{text}",
                    hovertemplate="%{y} x %{x}: %{z:.2f}<extra></extra>",
                )
            ]
        )
        heat_layout = dict(_PLOTLY_LAYOUT)
        heat_layout.update(
            showlegend=False,
            height=300,
            margin=dict(l=80, r=20, t=12, b=80),
        )
        fig.update_layout(**heat_layout)
        charts["heatmap"] = _fig_html(fig, include_js)

    return charts, dist_name


def _distribution_figure(
    result: AnalysisResult,
    frame: pd.DataFrame | None,
) -> tuple[go.Figure, str] | None:
    if frame is None or frame.empty:
        return None
    numeric = [
        col for col in result.profile.columns if is_numeric_type(col.semantic_type)
    ]
    if not numeric:
        return None
    numeric.sort(key=lambda col: col.unique_count)
    column = numeric[0]
    if column.name not in frame.columns:
        return None
    series = pd.to_numeric(frame[column.name], errors="coerce").dropna()
    if series.empty:
        return None
    layout = dict(_PLOTLY_LAYOUT)
    layout["showlegend"] = False
    if column.unique_count <= 12:
        if _is_int_like(series):
            counts = series.astype(int).value_counts().sort_index()
        else:
            counts = series.value_counts().sort_index()
        palette = _score_palette(list(counts.index))
        fig = go.Figure(
            data=[
                go.Bar(
                    x=[str(idx) for idx in counts.index],
                    y=counts.values,
                    marker_color=palette,
                    hovertemplate="%{x}: %{y}<extra></extra>",
                )
            ]
        )
        layout["xaxis"] = {**_AXIS, "title": column.name}
        fig.update_layout(**layout)
        return fig, column.name
    fig = go.Figure(
        data=[go.Histogram(x=series, marker_color="#00b4a8", nbinsx=24)]
    )
    layout["xaxis"] = {**_AXIS, "title": column.name}
    fig.update_layout(**layout)
    return fig, column.name


def _is_int_like(series: pd.Series) -> bool:
    return bool(((series - series.round()).abs() < 1e-9).all())


def _score_palette(values: list[Any]) -> list[str]:
    scale = {1: "#FF4D6D", 2: "#ff7a00", 3: "#FFB800", 4: "#00b4a8", 5: "#39FF14"}
    colors = []
    for value in values:
        try:
            key = int(value)
        except (TypeError, ValueError):
            colors.append("#00b4a8")
            continue
        colors.append(scale.get(key, "#00b4a8"))
    return colors


def _logo_data_uri() -> str:
    path = _TEMPLATE_DIR / "assets" / "logo.png"
    if not path.exists():
        return ""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _cell(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.2f}"


def _fig_html(fig: go.Figure, include_js: Any) -> str:
    return fig.to_html(
        full_html=False,
        include_plotlyjs=include_js,
        config={"displayModeBar": False, "responsive": True},
    )
