"""Modèles de sortie de l'analyse (contrats Pydantic)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from condata.models.config import AnalysisConfig

SemanticType = Literal["numeric", "categorical", "datetime", "boolean", "unknown"]
Severity = Literal["info", "warning", "critical"]
Status = Literal["ok", "warning", "critical"]


class FileInfo(BaseModel):
    """Métadonnées du fichier ingéré, sans le contenu."""

    path: str
    name: str
    size_bytes: int
    encoding: str
    separator: str


class ColumnProfile(BaseModel):
    name: str
    pandas_dtype: str
    semantic_type: SemanticType
    non_null_count: int
    non_null_pct: float
    unique_count: int
    is_constant: bool
    missing_count: int
    missing_pct: float
    sample_values: list[str] = Field(default_factory=list)


class DatasetProfile(BaseModel):
    file_name: str
    file_path: str
    file_size_bytes: int
    n_rows: int
    n_columns: int
    n_numeric: int
    n_categorical: int
    n_datetime: int
    n_boolean: int
    n_constant: int
    memory_usage_bytes: int
    columns: list[ColumnProfile]


class ColumnMissing(BaseModel):
    name: str
    missing_count: int
    missing_pct: float
    status: Status


class MissingValuesReport(BaseModel):
    total_missing: int
    total_cells: int
    overall_pct: float
    columns: list[ColumnMissing]


class DuplicateReport(BaseModel):
    n_duplicates: int
    rate_pct: float
    status: Status


class QualityIssue(BaseModel):
    code: str
    severity: Severity
    column: str | None = None
    message: str


class ScoreBreakdown(BaseModel):
    """Décomposition documentée du Data Quality Score sur 100."""

    completeness: float
    uniqueness: float
    validity: float
    consistency: float
    total: int = Field(ge=0, le=100)


class QualityReport(BaseModel):
    score: int = Field(ge=0, le=100)
    breakdown: ScoreBreakdown
    missing: MissingValuesReport
    duplicates: DuplicateReport
    issues: list[QualityIssue] = Field(default_factory=list)


class NumericColumnStats(BaseModel):
    """Statistiques descriptives d'une colonne numérique."""

    name: str
    count: int
    mean: float | None = None
    median: float | None = None
    min: float | None = None
    max: float | None = None
    std: float | None = None
    q1: float | None = None
    q3: float | None = None
    p5: float | None = None
    p25: float | None = None
    p50: float | None = None
    p75: float | None = None
    p95: float | None = None


class CategoryFrequency(BaseModel):
    value: str
    count: int
    pct: float


class CategoricalColumnStats(BaseModel):
    """Distribution d'une colonne catégorielle (ou booléenne)."""

    name: str
    n_categories: int
    dominant: str | None = None
    dominant_count: int = 0
    dominant_pct: float = 0.0
    frequencies: list[CategoryFrequency] = Field(default_factory=list)
    truncated: bool = False


class StatisticsReport(BaseModel):
    numeric: list[NumericColumnStats] = Field(default_factory=list)
    categorical: list[CategoricalColumnStats] = Field(default_factory=list)


class ColumnOutliers(BaseModel):
    """Valeurs *potentiellement* aberrantes d'une colonne numérique.

    Une détection n'implique pas une erreur : ce sont des potential outliers.
    """

    name: str
    method: Literal["iqr", "zscore"]
    n_potential_outliers: int
    n_low: int = 0
    n_high: int = 0
    rate_pct: float = 0.0
    lower_bound: float | None = None
    upper_bound: float | None = None
    sample_values: list[float] = Field(default_factory=list)
    skipped_reason: str | None = None


class OutlierReport(BaseModel):
    method: Literal["iqr", "zscore"]
    n_columns_analyzed: int = 0
    n_columns_with_outliers: int = 0
    total_potential_outliers: int = 0
    columns: list[ColumnOutliers] = Field(default_factory=list)


class CorrelationPair(BaseModel):
    column_a: str
    column_b: str
    coefficient: float
    abs_coefficient: float


class CorrelationWarning(BaseModel):
    code: Literal["redundancy", "multicollinearity"]
    columns: list[str]
    message: str


class CorrelationReport(BaseModel):
    """Corrélations de Pearson entre variables numériques."""

    method: Literal["pearson"] = "pearson"
    n_numeric_columns: int = 0
    matrix: dict[str, dict[str, float | None]] = Field(default_factory=dict)
    strong_pairs: list[CorrelationPair] = Field(default_factory=list)
    redundant_pairs: list[CorrelationPair] = Field(default_factory=list)
    warnings: list[CorrelationWarning] = Field(default_factory=list)
    skipped_reason: str | None = None


class ReadinessCheck(BaseModel):
    """Un item du checklist ML Readiness (ok / warning / critical)."""

    code: str
    label: str
    status: Status
    score: float
    max_score: float
    message: str


class ReadinessBreakdown(BaseModel):
    """Décomposition documentée du ML Readiness Score sur 100."""

    dataset_schema: float
    missing_values: float
    duplicates: float
    data_types: float
    outliers: float
    class_balance: float
    target_variable: float
    potential_leakage: float
    total: int = Field(ge=0, le=100)


class ReadinessReport(BaseModel):
    """Indicateur heuristique de préparation au Machine Learning.

    Ce score ne garantit pas qu'un modèle s'entraînera correctement.
    """

    score: int = Field(ge=0, le=100)
    heuristic: bool = True
    disclaimer: str = (
        "Indicateur heuristique, pas une garantie de préparation ML."
    )
    target_column: str | None = None
    target_inferred: bool = False
    breakdown: ReadinessBreakdown
    checks: list[ReadinessCheck] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    """Résultat complet d'une analyse CONDATA (extensible)."""

    version: str
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    config: AnalysisConfig
    file: FileInfo
    profile: DatasetProfile
    quality: QualityReport
    statistics: StatisticsReport
    outliers: OutlierReport
    correlations: CorrelationReport
    readiness: ReadinessReport

    def export_json(self, path: str | Path) -> Path:
        from condata.reporting.json import export_json

        return export_json(self, path)

    def export_html(
        self,
        path: str | Path,
        *,
        frame: Any = None,
        open_browser: bool = False,
    ) -> Path:
        from condata.reporting.html import export_html

        return export_html(self, path, frame=frame, open_browser=open_browser)
