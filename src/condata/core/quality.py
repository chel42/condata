"""Analyse de qualité et Data Quality Score.

Le score n'est pas arbitraire. Il est la somme de quatre composantes
documentées, chacune bornée :

* Completeness (35 pts) — taux global de cellules manquantes.
  0 % manquant → 35 ; ≥ ``missing_zero_score_pct`` → 0 ; linéaire entre les deux.
* Uniqueness (25 pts) — taux de lignes dupliquées.
  0 % doublons → 25 ; ≥ ``duplicate_zero_score_pct`` → 0 ; linéaire entre les deux.
* Validity (20 pts) — colonnes au type mixte (nombres et texte mélangés).
  20 au départ, −5 par colonne mixte (plancher 0).
* Consistency (20 pts) — catégories quasi identiques (casse / espaces).
  20 au départ, −5 par colonne incohérente (plancher 0).

CONDATA signale les problèmes ; il ne modifie pas les données.
"""

from __future__ import annotations

import re

import pandas as pd

from condata.core.profiler import infer_semantic_type
from condata.models.config import AnalysisConfig
from condata.models.schema import (
    ColumnMissing,
    DuplicateReport,
    MissingValuesReport,
    QualityIssue,
    QualityReport,
    ScoreBreakdown,
    Status,
)

WEIGHT_COMPLETENESS = 35
WEIGHT_UNIQUENESS = 25
WEIGHT_VALIDITY = 20
WEIGHT_CONSISTENCY = 20
PENALTY_PER_COLUMN = 5

_NUMERIC_RE = re.compile(r"^-?\d+(?:[.,]\d+)?$")


def assess_quality(
    frame: pd.DataFrame,
    config: AnalysisConfig | None = None,
) -> QualityReport:
    """Évalue la qualité du dataset et calcule le score / 100."""
    cfg = config or AnalysisConfig()
    issues: list[QualityIssue] = []

    missing = _missing_report(frame, cfg, issues)
    duplicates = _duplicate_report(frame, cfg, issues)
    mixed_columns = _mixed_type_columns(frame, issues)
    inconsistent_columns = _inconsistent_categorical_columns(frame, issues)
    _flag_constant_columns(frame, issues)

    completeness = _linear_score(
        missing.overall_pct,
        zero_at=cfg.missing_zero_score_pct,
        weight=WEIGHT_COMPLETENESS,
    )
    uniqueness = _linear_score(
        duplicates.rate_pct,
        zero_at=cfg.duplicate_zero_score_pct,
        weight=WEIGHT_UNIQUENESS,
    )
    validity = max(0.0, WEIGHT_VALIDITY - PENALTY_PER_COLUMN * len(mixed_columns))
    consistency = max(
        0.0,
        WEIGHT_CONSISTENCY - PENALTY_PER_COLUMN * len(inconsistent_columns),
    )
    total = int(round(completeness + uniqueness + validity + consistency))
    total = min(100, max(0, total))

    return QualityReport(
        score=total,
        breakdown=ScoreBreakdown(
            completeness=round(completeness, 2),
            uniqueness=round(uniqueness, 2),
            validity=round(validity, 2),
            consistency=round(consistency, 2),
            total=total,
        ),
        missing=missing,
        duplicates=duplicates,
        issues=issues,
    )


def _missing_report(
    frame: pd.DataFrame,
    config: AnalysisConfig,
    issues: list[QualityIssue],
) -> MissingValuesReport:
    n_rows = int(len(frame))
    n_cols = int(frame.shape[1])
    total_cells = n_rows * n_cols
    total_missing = int(frame.isna().sum().sum())
    overall_pct = _pct(total_missing, total_cells)

    columns: list[ColumnMissing] = []
    for name in frame.columns:
        count = int(frame[name].isna().sum())
        pct = _pct(count, n_rows)
        status = _status(pct, config.missing_warning_pct, config.missing_critical_pct)
        columns.append(
            ColumnMissing(
                name=str(name),
                missing_count=count,
                missing_pct=pct,
                status=status,
            )
        )
        if status == "warning":
            issues.append(
                QualityIssue(
                    code="missing_values",
                    severity="warning",
                    column=str(name),
                    message=f"{pct:.1f} % de valeurs manquantes.",
                )
            )
        elif status == "critical":
            issues.append(
                QualityIssue(
                    code="missing_values",
                    severity="critical",
                    column=str(name),
                    message=f"{pct:.1f} % de valeurs manquantes.",
                )
            )

    columns.sort(key=lambda item: item.missing_pct, reverse=True)
    return MissingValuesReport(
        total_missing=total_missing,
        total_cells=total_cells,
        overall_pct=overall_pct,
        columns=columns,
    )


def _duplicate_report(
    frame: pd.DataFrame,
    config: AnalysisConfig,
    issues: list[QualityIssue],
) -> DuplicateReport:
    n_rows = int(len(frame))
    n_duplicates = int(frame.duplicated().sum())
    rate_pct = _pct(n_duplicates, n_rows)
    status = _status(
        rate_pct,
        config.duplicate_warning_pct,
        config.duplicate_critical_pct,
    )
    if status != "ok":
        label = "ligne dupliquée" if n_duplicates == 1 else "lignes dupliquées"
        issues.append(
            QualityIssue(
                code="duplicates",
                severity=status,
                message=f"{n_duplicates} {label} ({rate_pct:.2f} %).",
            )
        )
    return DuplicateReport(
        n_duplicates=n_duplicates,
        rate_pct=rate_pct,
        status=status,
    )


def _mixed_type_columns(frame: pd.DataFrame, issues: list[QualityIssue]) -> list[str]:
    mixed: list[str] = []
    for name in frame.columns:
        series = frame[name]
        if infer_semantic_type(series) != "categorical":
            continue
        sample = series.dropna().astype(str).str.strip()
        if sample.empty:
            continue
        looks_numeric = sample.str.match(_NUMERIC_RE)
        if bool(looks_numeric.any()) and not bool(looks_numeric.all()):
            mixed.append(str(name))
            issues.append(
                QualityIssue(
                    code="mixed_types",
                    severity="warning",
                    column=str(name),
                    message="Colonne au type mixte (valeurs numériques et textuelles).",
                )
            )
    return mixed


def _inconsistent_categorical_columns(
    frame: pd.DataFrame,
    issues: list[QualityIssue],
) -> list[str]:
    inconsistent: list[str] = []
    for name in frame.columns:
        series = frame[name]
        if infer_semantic_type(series) != "categorical":
            continue
        text = series.dropna().astype(str)
        if text.empty:
            continue
        raw_nunique = int(text.nunique())
        normalized_nunique = int(text.str.strip().str.casefold().nunique())
        if normalized_nunique < raw_nunique:
            inconsistent.append(str(name))
            issues.append(
                QualityIssue(
                    code="categorical_inconsistency",
                    severity="warning",
                    column=str(name),
                    message=(
                        "Incohérence catégorielle possible "
                        f"({raw_nunique} formes brutes, {normalized_nunique} après normalisation)."
                    ),
                )
            )
    return inconsistent


def _flag_constant_columns(frame: pd.DataFrame, issues: list[QualityIssue]) -> None:
    for name in frame.columns:
        if int(frame[name].nunique(dropna=True)) <= 1:
            issues.append(
                QualityIssue(
                    code="constant_column",
                    severity="info",
                    column=str(name),
                    message="Colonne constante (une seule valeur distincte).",
                )
            )


def _status(pct: float, warning_at: float, critical_at: float) -> Status:
    if pct >= critical_at:
        return "critical"
    if pct >= warning_at:
        return "warning"
    return "ok"


def _linear_score(pct: float, zero_at: float, weight: int) -> float:
    if pct <= 0:
        return float(weight)
    if pct >= zero_at:
        return 0.0
    return weight * (1.0 - pct / zero_at)


def _pct(part: int, whole: int) -> float:
    if whole == 0:
        return 0.0
    return round(100.0 * part / whole, 4)
