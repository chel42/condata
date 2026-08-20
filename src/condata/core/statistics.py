"""Statistiques descriptives (entiers, réels, texte, booléens).

Pour les colonnes entières et réelles : moyenne, médiane, min/max, écart-type,
quartiles (Q1/Q3) et percentiles (5, 25, 50, 75, 95).

Pour les colonnes texte et booléennes : nombre de valeurs distinctes,
fréquences, valeur dominante et distribution. Les fréquences sont
tronquées à ``AnalysisConfig.max_category_frequencies`` pour éviter
d'exploser le rapport sur une colonne à haute cardinalité.
"""

from __future__ import annotations

import pandas as pd

from condata.core.profiler import infer_semantic_type, is_numeric_type
from condata.models.config import AnalysisConfig
from condata.models.schema import (
    CategoricalColumnStats,
    CategoryFrequency,
    NumericColumnStats,
    StatisticsReport,
)

_PERCENTILES = (0.05, 0.25, 0.50, 0.75, 0.95)


def compute_statistics(
    frame: pd.DataFrame,
    config: AnalysisConfig | None = None,
) -> StatisticsReport:
    """Calcule les statistiques descriptives sans muter le DataFrame."""
    cfg = config or AnalysisConfig()
    numeric: list[NumericColumnStats] = []
    categorical: list[CategoricalColumnStats] = []

    for name in frame.columns:
        series = frame[name]
        kind = infer_semantic_type(series)
        column_name = str(name)
        if is_numeric_type(kind):
            numeric.append(_numeric_stats(column_name, series))
        elif kind in {"text", "boolean"}:
            categorical.append(
                _categorical_stats(
                    column_name,
                    series,
                    max_frequencies=cfg.max_category_frequencies,
                )
            )

    return StatisticsReport(numeric=numeric, categorical=categorical)


def _numeric_stats(name: str, series: pd.Series) -> NumericColumnStats:
    values = pd.to_numeric(series, errors="coerce").dropna()
    count = len(values)
    if count == 0:
        return NumericColumnStats(name=name, count=0)

    quantiles = values.quantile(list(_PERCENTILES))
    q1 = _finite(quantiles.loc[0.25])
    q3 = _finite(quantiles.loc[0.75])
    median = _finite(values.median())

    return NumericColumnStats(
        name=name,
        count=count,
        mean=_finite(values.mean()),
        median=median,
        min=_finite(values.min()),
        max=_finite(values.max()),
        std=_finite(values.std(ddof=1)) if count > 1 else None,
        q1=q1,
        q3=q3,
        p5=_finite(quantiles.loc[0.05]),
        p25=q1,
        p50=median,
        p75=q3,
        p95=_finite(quantiles.loc[0.95]),
    )


def _categorical_stats(
    name: str,
    series: pd.Series,
    max_frequencies: int,
) -> CategoricalColumnStats:
    text = series.dropna().astype(str)
    n_obs = len(text)
    n_categories = int(text.nunique())
    if n_obs == 0:
        return CategoricalColumnStats(name=name, n_categories=0)

    counts = text.value_counts()
    ranked = sorted(counts.items(), key=lambda item: (-int(item[1]), str(item[0])))
    truncated = len(ranked) > max_frequencies
    visible = ranked[:max_frequencies]

    frequencies = [
        CategoryFrequency(
            value=str(value),
            count=int(count),
            pct=_pct(int(count), n_obs),
        )
        for value, count in visible
    ]
    dominant_value, dominant_count = ranked[0]
    dominant_count_int = int(dominant_count)

    return CategoricalColumnStats(
        name=name,
        n_categories=n_categories,
        dominant=str(dominant_value),
        dominant_count=dominant_count_int,
        dominant_pct=_pct(dominant_count_int, n_obs),
        frequencies=frequencies,
        truncated=truncated,
    )


def _finite(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), 6)


def _pct(part: int, whole: int) -> float:
    if whole == 0:
        return 0.0
    return round(100.0 * part / whole, 4)
