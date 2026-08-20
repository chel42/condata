"""Corrélations entre variables numériques (Pearson).

Le module fournit :

* la matrice de corrélation (pour une heatmap HTML ultérieure) ;
* les paires fortement corrélées (|r| ≥ ``correlation_strong_threshold``) ;
* les paires redondantes (|r| ≥ ``correlation_redundant_threshold``) ;
* des avertissements de multicolinéarité potentielle.

Ce n'est pas un VIF complet : c'est un signal heuristique pour le rapport.
"""

from __future__ import annotations

import pandas as pd

from condata.core.profiler import infer_semantic_type, is_numeric_type
from condata.models.config import AnalysisConfig
from condata.models.schema import (
    CorrelationPair,
    CorrelationReport,
    CorrelationWarning,
)

_MIN_NUMERIC_COLUMNS = 2
_MIN_NON_NULL = 3


def compute_correlations(
    frame: pd.DataFrame,
    config: AnalysisConfig | None = None,
) -> CorrelationReport:
    """Calcule la matrice de corrélation Pearson sans muter le DataFrame."""
    cfg = config or AnalysisConfig()
    numeric = _numeric_frame(frame)

    if numeric.shape[1] < _MIN_NUMERIC_COLUMNS:
        return CorrelationReport(
            n_numeric_columns=int(numeric.shape[1]),
            skipped_reason="insufficient_numeric_columns",
        )

    usable = numeric.loc[:, numeric.notna().sum() >= _MIN_NON_NULL]
    usable = usable.copy()
    usable.columns = [str(col) for col in usable.columns]
    if usable.shape[1] < _MIN_NUMERIC_COLUMNS:
        return CorrelationReport(
            n_numeric_columns=int(numeric.shape[1]),
            skipped_reason="insufficient_observations",
        )

    corr = usable.corr(method="pearson")
    names = [str(col) for col in corr.columns]
    matrix = {
        row: {col: _finite(corr.loc[row, col]) for col in names} for row in names
    }
    strong_pairs, redundant_pairs = _pair_lists(corr, names, cfg)
    warnings = _build_warnings(strong_pairs, redundant_pairs)

    return CorrelationReport(
        n_numeric_columns=len(names),
        matrix=matrix,
        strong_pairs=strong_pairs,
        redundant_pairs=redundant_pairs,
        warnings=warnings,
    )


def _numeric_frame(frame: pd.DataFrame) -> pd.DataFrame:
    columns = [
        name
        for name in frame.columns
        if is_numeric_type(infer_semantic_type(frame[name]))
    ]
    if not columns:
        return pd.DataFrame(index=frame.index)
    return frame[columns].apply(pd.to_numeric, errors="coerce")


def _pair_lists(
    corr: pd.DataFrame,
    names: list[str],
    config: AnalysisConfig,
) -> tuple[list[CorrelationPair], list[CorrelationPair]]:
    strong: list[CorrelationPair] = []
    redundant: list[CorrelationPair] = []
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            coefficient = _finite(corr.loc[left, right])
            if coefficient is None:
                continue
            pair = CorrelationPair(
                column_a=left,
                column_b=right,
                coefficient=coefficient,
                abs_coefficient=round(abs(coefficient), 6),
            )
            if pair.abs_coefficient >= config.correlation_strong_threshold:
                strong.append(pair)
            if pair.abs_coefficient >= config.correlation_redundant_threshold:
                redundant.append(pair)
    strong.sort(key=lambda item: item.abs_coefficient, reverse=True)
    redundant.sort(key=lambda item: item.abs_coefficient, reverse=True)
    return strong, redundant


def _build_warnings(
    strong_pairs: list[CorrelationPair],
    redundant_pairs: list[CorrelationPair],
) -> list[CorrelationWarning]:
    warnings: list[CorrelationWarning] = []
    for pair in redundant_pairs:
        warnings.append(
            CorrelationWarning(
                code="redundancy",
                columns=[pair.column_a, pair.column_b],
                message=(
                    "Variables potentiellement redondantes : "
                    f"'{pair.column_a}' et '{pair.column_b}' "
                    f"(r={pair.coefficient:.3f})."
                ),
            )
        )
    if strong_pairs:
        involved: list[str] = []
        seen: set[str] = set()
        for pair in strong_pairs:
            for name in (pair.column_a, pair.column_b):
                if name not in seen:
                    seen.add(name)
                    involved.append(name)
        warnings.append(
            CorrelationWarning(
                code="multicollinearity",
                columns=involved,
                message=(
                    "Risque de multicolinéarité entre : "
                    + ", ".join(involved)
                    + "."
                ),
            )
        )
    return warnings


def _finite(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), 6)
