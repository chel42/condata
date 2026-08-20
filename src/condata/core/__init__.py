"""Moteur métier CONDATA."""

from condata.core.correlations import compute_correlations
from condata.core.inspector import DatasetInspector
from condata.core.outliers import detect_outliers
from condata.core.profiler import profile_dataset
from condata.core.quality import assess_quality
from condata.core.readiness import assess_readiness
from condata.core.statistics import compute_statistics

__all__ = [
    "DatasetInspector",
    "assess_quality",
    "assess_readiness",
    "compute_correlations",
    "compute_statistics",
    "detect_outliers",
    "profile_dataset",
]
