"""Modèles de sortie de l'analyse (contrats Pydantic)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

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
