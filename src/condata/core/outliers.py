"""Détection de valeurs potentiellement aberrantes (IQR / Z-score).

Une valeur hors-norme n'est pas forcément une erreur. CONDATA parle
donc de *potential outliers* : le module signale, il ne corrige pas.

* IQR (défaut) : hors ``[Q1 - k·IQR, Q3 + k·IQR]`` (Tukey, k=1.5).
* Z-score : ``|x - mean| / std > seuil`` (défaut 3). Moins robuste
  si un outlier extrême gonfle l'écart-type.
"""

from __future__ import annotations

import pandas as pd

from condata.core.profiler import infer_semantic_type
from condata.models.config import AnalysisConfig
from condata.models.schema import ColumnOutliers, OutlierReport

_MIN_VALUES_IQR = 4
_MIN_VALUES_ZSCORE = 3
_SAMPLE_SIZE = 8


def detect_outliers(
    frame: pd.DataFrame,
    config: AnalysisConfig | None = None,
) -> OutlierReport:
    """Repère les potential outliers sur les colonnes numériques."""
    cfg = config or AnalysisConfig()
    method = cfg.outlier_method
    columns: list[ColumnOutliers] = []

    for name in frame.columns:
        series = frame[name]
        if infer_semantic_type(series) != "numeric":
            continue
        columns.append(_analyze_column(str(name), series, cfg))

    analyzed = [col for col in columns if col.skipped_reason is None]
    with_outliers = [col for col in analyzed if col.n_potential_outliers > 0]
    return OutlierReport(
        method=method,
        n_columns_analyzed=len(analyzed),
        n_columns_with_outliers=len(with_outliers),
        total_potential_outliers=sum(col.n_potential_outliers for col in analyzed),
        columns=columns,
    )


def _analyze_column(
    name: str,
    series: pd.Series,
    config: AnalysisConfig,
) -> ColumnOutliers:
    values = pd.to_numeric(series, errors="coerce").dropna()
    method = config.outlier_method
    count = len(values)
    min_required = _MIN_VALUES_IQR if method == "iqr" else _MIN_VALUES_ZSCORE

    if count < min_required:
        return ColumnOutliers(
            name=name,
            method=method,
            n_potential_outliers=0,
            skipped_reason="insufficient_values",
        )

    if method == "iqr":
        mask, lower, upper = _iqr_mask(values, config.iqr_multiplier)
    else:
        mask, lower, upper = _zscore_mask(values, config.zscore_threshold)
        if mask is None:
            return ColumnOutliers(
                name=name,
                method=method,
                n_potential_outliers=0,
                skipped_reason="zero_variance",
            )

    n_low = int((values < lower).sum())
    n_high = int((values > upper).sum())
    n_out = int(mask.sum())
    samples = _sample_values(values[mask], values.median())

    return ColumnOutliers(
        name=name,
        method=method,
        n_potential_outliers=n_out,
        n_low=n_low,
        n_high=n_high,
        rate_pct=_pct(n_out, count),
        lower_bound=_finite(lower),
        upper_bound=_finite(upper),
        sample_values=samples,
    )


def _iqr_mask(
    values: pd.Series,
    multiplier: float,
) -> tuple[pd.Series, float, float]:
    q1 = float(values.quantile(0.25))
    q3 = float(values.quantile(0.75))
    iqr = q3 - q1
    lower = q1 - multiplier * iqr
    upper = q3 + multiplier * iqr
    mask = (values < lower) | (values > upper)
    return mask, lower, upper


def _zscore_mask(
    values: pd.Series,
    threshold: float,
) -> tuple[pd.Series | None, float, float]:
    std = float(values.std(ddof=0))
    if std == 0 or pd.isna(std):
        return None, 0.0, 0.0
    mean = float(values.mean())
    lower = mean - threshold * std
    upper = mean + threshold * std
    zscores = (values - mean).abs() / std
    mask = zscores > threshold
    return mask, lower, upper


def _sample_values(outliers: pd.Series, center: float) -> list[float]:
    if outliers.empty:
        return []
    ranked = outliers.reindex(
        outliers.sub(center).abs().sort_values(ascending=False).index
    )
    samples: list[float] = []
    seen: set[float] = set()
    for raw in ranked:
        value = _finite(raw)
        if value is None or value in seen:
            continue
        seen.add(value)
        samples.append(value)
        if len(samples) >= _SAMPLE_SIZE:
            break
    return samples


def _finite(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), 6)


def _pct(part: int, whole: int) -> float:
    if whole == 0:
        return 0.0
    return round(100.0 * part / whole, 4)
