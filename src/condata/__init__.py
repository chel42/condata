"""CONDATA — bibliothèque Python d'audit local de qualité des datasets."""

from __future__ import annotations

__version__ = "0.1.0"

from condata.core.inspector import DatasetInspector
from condata.models.config import AnalysisConfig
from condata.models.schema import AnalysisResult

__all__ = [
    "AnalysisConfig",
    "AnalysisResult",
    "DatasetInspector",
    "__version__",
]
