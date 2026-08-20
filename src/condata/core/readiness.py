"""ML Readiness Score — indicateur heuristique.

Répond à : « le dataset présente-t-il les conditions *minimales*
pour commencer un projet de Machine Learning ? »

Ce n'est **pas** une garantie de performance. Le score / 100 est la
somme de huit checks documentés :

* Schema (15) — au moins 2 colonnes et ``MIN_ROWS_ML`` lignes.
* Missing values (15) — même barème que le Quality Score (taux global).
* Duplicates (10) — même barème que le Quality Score (taux de doublons).
* Data types (10) — -5 par colonne au type mixte (plancher 0).
* Outliers (15) — taux moyen de potential outliers ; 0 % → 15 ; ≥ 20 % → 0.
* Class balance (15) — équilibre de la cible si elle est catégorielle.
* Target variable (10) — colonne cible fournie, inférée, ou absente.
* Potential leakage (10) — identifiants uniques, ``*_id``, redondance,
  corrélation extrême avec la cible.

La cible se configure via ``AnalysisConfig.target_column``. Sinon, une
colonne nommée target / label / class / y / outcome est inférée.
"""

from __future__ import annotations

import re

import pandas as pd

from condata.core.correlations import compute_correlations
from condata.core.outliers import detect_outliers
from condata.core.profiler import infer_semantic_type, is_numeric_type
from condata.core.quality import assess_quality
from condata.models.config import AnalysisConfig
from condata.models.schema import (
    CorrelationReport,
    OutlierReport,
    QualityReport,
    ReadinessBreakdown,
    ReadinessCheck,
    ReadinessReport,
    Status,
)

WEIGHT_SCHEMA = 15
WEIGHT_MISSING = 15
WEIGHT_DUPLICATES = 10
WEIGHT_DTYPES = 10
WEIGHT_OUTLIERS = 15
WEIGHT_BALANCE = 15
WEIGHT_TARGET = 10
WEIGHT_LEAKAGE = 10
PENALTY_PER_SIGNAL = 5

MIN_ROWS_ML = 20
OUTLIER_ZERO_SCORE_PCT = 20.0
IMBALANCE_WARNING_PCT = 70.0
IMBALANCE_CRITICAL_PCT = 90.0

_TARGET_HINTS = {"target", "label", "class", "y", "outcome", "classe"}
_ID_EXACT = {"id", "uuid", "pk", "index"}
_ID_SUFFIX = re.compile(r"(?:^|_)id$", re.IGNORECASE)


def assess_readiness(
    frame: pd.DataFrame,
    config: AnalysisConfig | None = None,
    *,
    quality: QualityReport | None = None,
    outliers: OutlierReport | None = None,
    correlations: CorrelationReport | None = None,
) -> ReadinessReport:
    """Calcule le ML Readiness Score (heuristique)."""
    cfg = config or AnalysisConfig()
    quality = quality or assess_quality(frame, cfg)
    outliers = outliers or detect_outliers(frame, cfg)
    correlations = correlations or compute_correlations(frame, cfg)

    target, inferred = _resolve_target(frame, cfg)
    checks = [
        _check_schema(frame),
        _check_missing(quality, cfg),
        _check_duplicates(quality, cfg),
        _check_dtypes(quality),
        _check_outliers(outliers),
        _check_target(frame, target, inferred),
        _check_class_balance(frame, target),
        _check_leakage(frame, target, correlations),
    ]

    total = min(100, max(0, round(sum(item.score for item in checks))))
    by_code = {item.code: item.score for item in checks}

    return ReadinessReport(
        score=total,
        target_column=target,
        target_inferred=inferred,
        breakdown=ReadinessBreakdown(
            dataset_schema=round(by_code["schema"], 2),
            missing_values=round(by_code["missing_values"], 2),
            duplicates=round(by_code["duplicates"], 2),
            data_types=round(by_code["data_types"], 2),
            outliers=round(by_code["outliers"], 2),
            class_balance=round(by_code["class_balance"], 2),
            target_variable=round(by_code["target_variable"], 2),
            potential_leakage=round(by_code["potential_leakage"], 2),
            total=total,
        ),
        checks=checks,
    )


def _resolve_target(
    frame: pd.DataFrame,
    config: AnalysisConfig,
) -> tuple[str | None, bool]:
    if config.target_column:
        return config.target_column, False
    for name in frame.columns:
        if str(name).strip().casefold() in _TARGET_HINTS:
            return str(name), True
    return None, False


def _check_schema(frame: pd.DataFrame) -> ReadinessCheck:
    n_rows = len(frame)
    n_cols = int(frame.shape[1])
    if n_rows == 0 or n_cols == 0:
        return _check(
            "schema",
            "Schema",
            "critical",
            0,
            WEIGHT_SCHEMA,
            "Dataset vide.",
        )
    if n_cols < 2:
        return _check(
            "schema",
            "Schema",
            "warning",
            7,
            WEIGHT_SCHEMA,
            "Une seule colonne : trop peu de variables pour un modèle.",
        )
    if n_rows < MIN_ROWS_ML:
        return _check(
            "schema",
            "Schema",
            "warning",
            8,
            WEIGHT_SCHEMA,
            f"{n_rows} lignes seulement (minimum conseillé : {MIN_ROWS_ML}).",
        )
    return _check(
        "schema",
        "Schema",
        "ok",
        WEIGHT_SCHEMA,
        WEIGHT_SCHEMA,
        f"{n_rows} lignes, {n_cols} colonnes.",
    )


def _check_missing(quality: QualityReport, config: AnalysisConfig) -> ReadinessCheck:
    score = _linear_score(
        quality.missing.overall_pct,
        config.missing_zero_score_pct,
        WEIGHT_MISSING,
    )
    worst = _worst_status(col.status for col in quality.missing.columns)
    if quality.missing.overall_pct <= 0:
        worst = "ok"
    elif worst == "ok" and quality.missing.overall_pct > 0:
        worst = "warning"
    return _check(
        "missing_values",
        "Missing values",
        worst,
        score,
        WEIGHT_MISSING,
        f"{quality.missing.overall_pct:.1f} % de cellules manquantes.",
    )


def _check_duplicates(quality: QualityReport, config: AnalysisConfig) -> ReadinessCheck:
    score = _linear_score(
        quality.duplicates.rate_pct,
        config.duplicate_zero_score_pct,
        WEIGHT_DUPLICATES,
    )
    return _check(
        "duplicates",
        "Duplicates",
        quality.duplicates.status,
        score,
        WEIGHT_DUPLICATES,
        (
            f"{quality.duplicates.n_duplicates} doublons "
            f"({quality.duplicates.rate_pct:.2f} %)."
        ),
    )


def _check_dtypes(quality: QualityReport) -> ReadinessCheck:
    mixed = [issue for issue in quality.issues if issue.code == "mixed_types"]
    score = max(0.0, WEIGHT_DTYPES - PENALTY_PER_SIGNAL * len(mixed))
    if mixed:
        names = ", ".join(issue.column or "?" for issue in mixed)
        return _check(
            "data_types",
            "Data types",
            "warning",
            score,
            WEIGHT_DTYPES,
            f"Colonnes au type mixte : {names}.",
        )
    return _check(
        "data_types",
        "Data types",
        "ok",
        WEIGHT_DTYPES,
        WEIGHT_DTYPES,
        "Pas de type mixte détecté.",
    )


def _check_outliers(outliers: OutlierReport) -> ReadinessCheck:
    analyzed = [col for col in outliers.columns if col.skipped_reason is None]
    if not analyzed:
        return _check(
            "outliers",
            "Outliers",
            "ok",
            WEIGHT_OUTLIERS,
            WEIGHT_OUTLIERS,
            "Pas de colonne numérique analysable.",
        )
    avg_rate = sum(col.rate_pct for col in analyzed) / len(analyzed)
    score = _linear_score(avg_rate, OUTLIER_ZERO_SCORE_PCT, WEIGHT_OUTLIERS)
    if avg_rate <= 0:
        status: Status = "ok"
    elif avg_rate >= OUTLIER_ZERO_SCORE_PCT:
        status = "critical"
    else:
        status = "warning"
    return _check(
        "outliers",
        "Outliers",
        status,
        score,
        WEIGHT_OUTLIERS,
        f"{outliers.total_potential_outliers} potential outliers "
        f"(taux moyen {avg_rate:.1f} %).",
    )


def _check_target(
    frame: pd.DataFrame,
    target: str | None,
    inferred: bool,
) -> ReadinessCheck:
    if target is None:
        return _check(
            "target_variable",
            "Target variable",
            "warning",
            5,
            WEIGHT_TARGET,
            "Aucune colonne cible fournie (option target_column).",
        )
    if target not in set(map(str, frame.columns)):
        return _check(
            "target_variable",
            "Target variable",
            "critical",
            0,
            WEIGHT_TARGET,
            f"Colonne cible introuvable : '{target}'.",
        )
    series = frame[target]
    n_valid = int(series.notna().sum())
    if n_valid == 0:
        return _check(
            "target_variable",
            "Target variable",
            "critical",
            0,
            WEIGHT_TARGET,
            f"La cible '{target}' est entièrement vide.",
        )
    origin = "inférée" if inferred else "configurée"
    return _check(
        "target_variable",
        "Target variable",
        "ok",
        WEIGHT_TARGET,
        WEIGHT_TARGET,
        f"Cible {origin} : '{target}' ({n_valid} valeurs non nulles).",
    )


def _check_class_balance(frame: pd.DataFrame, target: str | None) -> ReadinessCheck:
    if target is None:
        return _check(
            "class_balance",
            "Class balance",
            "warning",
            8,
            WEIGHT_BALANCE,
            "Cible absente : équilibre des classes non évalué.",
        )
    if target not in set(map(str, frame.columns)):
        return _check(
            "class_balance",
            "Class balance",
            "critical",
            0,
            WEIGHT_BALANCE,
            "Cible introuvable : équilibre des classes non évalué.",
        )
    series = frame[target]
    if is_numeric_type(infer_semantic_type(series)):
        return _check(
            "class_balance",
            "Class balance",
            "ok",
            WEIGHT_BALANCE,
            WEIGHT_BALANCE,
            f"Cible numérique '{target}' (régression) : pas de balance de classes.",
        )
    values = series.dropna().astype(str)
    n_classes = int(values.nunique())
    if n_classes < 2:
        return _check(
            "class_balance",
            "Class balance",
            "critical",
            0,
            WEIGHT_BALANCE,
            f"Une seule classe dans '{target}'.",
        )
    max_pct = float(values.value_counts(normalize=True).iloc[0] * 100)
    fair_pct = 100.0 / n_classes
    excess = max(0.0, max_pct - fair_pct)
    denom = 100.0 - fair_pct
    score = WEIGHT_BALANCE * (1.0 - excess / denom) if denom else 0.0
    if max_pct >= IMBALANCE_CRITICAL_PCT:
        status: Status = "critical"
    elif max_pct >= IMBALANCE_WARNING_PCT:
        status = "warning"
    else:
        status = "ok"
    return _check(
        "class_balance",
        "Class balance",
        status,
        score,
        WEIGHT_BALANCE,
        f"Classe majoritaire à {max_pct:.1f} % ({n_classes} classes).",
    )


def _check_leakage(
    frame: pd.DataFrame,
    target: str | None,
    correlations: CorrelationReport,
) -> ReadinessCheck:
    signals: list[str] = []
    n_rows = len(frame)
    for name in frame.columns:
        column = str(name)
        if target is not None and column == target:
            continue
        unique = int(frame[name].nunique(dropna=True))
        if n_rows >= 8 and unique == n_rows and unique > 1:
            signals.append(f"'{column}' unique par ligne (identifiant probable)")
            continue
        folded = column.strip().casefold()
        if folded in _ID_EXACT or _ID_SUFFIX.search(column):
            signals.append(f"'{column}' ressemble à un identifiant")

    if target and target in correlations.matrix:
        for other, coeff in correlations.matrix[target].items():
            if other == target or coeff is None:
                continue
            if abs(coeff) >= 0.95:
                signals.append(
                    f"corrélation extrême cible/'{other}' (r={coeff:.3f})"
                )

    for pair in correlations.redundant_pairs:
        if target and target in {pair.column_a, pair.column_b}:
            continue
        signals.append(
            f"features redondantes '{pair.column_a}' / '{pair.column_b}'"
        )

    unique_signals = list(dict.fromkeys(signals))
    score = max(0.0, WEIGHT_LEAKAGE - PENALTY_PER_SIGNAL * len(unique_signals))
    if not unique_signals:
        return _check(
            "potential_leakage",
            "Potential leakage",
            "ok",
            WEIGHT_LEAKAGE,
            WEIGHT_LEAKAGE,
            "Pas de fuite évidente détectée.",
        )
    status: Status = "critical" if len(unique_signals) >= 3 else "warning"
    preview = "; ".join(unique_signals[:3])
    return _check(
        "potential_leakage",
        "Potential leakage",
        status,
        score,
        WEIGHT_LEAKAGE,
        preview + ("…" if len(unique_signals) > 3 else ""),
    )


def _check(
    code: str,
    label: str,
    status: Status,
    score: float,
    max_score: float,
    message: str,
) -> ReadinessCheck:
    return ReadinessCheck(
        code=code,
        label=label,
        status=status,
        score=round(float(score), 2),
        max_score=float(max_score),
        message=message,
    )


def _linear_score(pct: float, zero_at: float, weight: int) -> float:
    if pct <= 0:
        return float(weight)
    if pct >= zero_at:
        return 0.0
    return weight * (1.0 - pct / zero_at)


def _worst_status(statuses: object) -> Status:
    order = {"ok": 0, "warning": 1, "critical": 2}
    worst: Status = "ok"
    for status in statuses:  # type: ignore[assignment]
        if order.get(status, 0) > order[worst]:
            worst = status
    return worst
