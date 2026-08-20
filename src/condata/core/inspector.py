"""Orchestrateur principal : DatasetInspector."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import pandas as pd

from condata.core.correlations import compute_correlations
from condata.core.outliers import detect_outliers
from condata.core.profiler import profile_dataset
from condata.core.quality import assess_quality
from condata.core.readiness import assess_readiness
from condata.core.statistics import compute_statistics
from condata.models.config import AnalysisConfig
from condata.models.schema import AnalysisResult, FileInfo
from condata.utils.io import load_csv


def _package_version() -> str:
    try:
        return version("condata")
    except PackageNotFoundError:
        return "0.1.0"


class DatasetInspector:
    """Point d'entrée de la bibliothèque Python.

    Example
    -------
    >>> inspector = DatasetInspector("dataset.csv")
    >>> result = inspector.analyze()
    >>> result.quality.score
    """

    def __init__(
        self,
        source: str | Path,
        config: AnalysisConfig | None = None,
    ) -> None:
        self.source = Path(source)
        self.config = config or AnalysisConfig()
        self._frame: pd.DataFrame | None = None
        self._file_info: FileInfo | None = None

    def load(self) -> pd.DataFrame:
        """Charge le CSV une seule fois et le met en cache."""
        self._frame, self._file_info = load_csv(self.source, self.config)
        return self._frame

    @property
    def dataframe(self) -> pd.DataFrame:
        if self._frame is None:
            self.load()
        assert self._frame is not None
        return self._frame

    def analyze(self) -> AnalysisResult:
        """Exécute le pipeline d'analyse jusqu'au ML Readiness Score."""
        frame = self.dataframe
        assert self._file_info is not None
        profile = profile_dataset(frame, self._file_info)
        quality = assess_quality(frame, self.config)
        statistics = compute_statistics(frame, self.config)
        outliers = detect_outliers(frame, self.config)
        correlations = compute_correlations(frame, self.config)
        readiness = assess_readiness(
            frame,
            self.config,
            quality=quality,
            outliers=outliers,
            correlations=correlations,
        )
        return AnalysisResult(
            version=_package_version(),
            config=self.config,
            file=self._file_info,
            profile=profile,
            quality=quality,
            statistics=statistics,
            outliers=outliers,
            correlations=correlations,
            readiness=readiness,
        )
