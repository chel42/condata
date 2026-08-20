"""Seuils d'analyse documentés.

Ces valeurs sont des paramètres métier, pas des constantes magiques
disséminées dans le moteur. L'utilisateur peut les surcharger à
l'instanciation de ``DatasetInspector``.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AnalysisConfig(BaseModel):
    """Configuration des seuils d'ingestion et d'analyse."""

    model_config = ConfigDict(extra="forbid")

    # --- Ingestion ---
    max_file_size_mb: float = Field(default=512.0, gt=0)
    csv_encoding: str | None = None
    csv_separator: str | None = None

    # --- Valeurs manquantes (% de la colonne) ---
    missing_warning_pct: float = Field(default=5.0, ge=0, le=100)
    missing_critical_pct: float = Field(default=20.0, ge=0, le=100)

    # --- Doublons (% des lignes) ---
    duplicate_warning_pct: float = Field(default=1.0, ge=0, le=100)
    duplicate_critical_pct: float = Field(default=5.0, ge=0, le=100)

    # --- Outliers (utilisés plus tard par core.outliers) ---
    outlier_method: Literal["iqr", "zscore"] = "iqr"
    iqr_multiplier: float = Field(default=1.5, gt=0)
    zscore_threshold: float = Field(default=3.0, gt=0)

    # --- Corrélations ---
    correlation_strong_threshold: float = Field(default=0.8, gt=0, le=1)

    # --- Barèmes du Quality Score (taux à partir duquel la composante = 0) ---
    missing_zero_score_pct: float = Field(default=25.0, gt=0, le=100)
    duplicate_zero_score_pct: float = Field(default=10.0, gt=0, le=100)
