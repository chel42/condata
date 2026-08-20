"""Tests des corrélations numériques."""

from __future__ import annotations

import pandas as pd

from condata.core.correlations import compute_correlations
from condata.models.config import AnalysisConfig


def test_perfect_correlation_is_redundant() -> None:
    frame = pd.DataFrame(
        {
            "a": [1.0, 2.0, 3.0, 4.0, 5.0],
            "b": [2.0, 4.0, 6.0, 8.0, 10.0],
        }
    )
    report = compute_correlations(frame)
    assert report.skipped_reason is None
    assert report.matrix["a"]["b"] == 1.0
    assert report.matrix["a"]["a"] == 1.0
    assert len(report.strong_pairs) == 1
    assert len(report.redundant_pairs) == 1
    codes = {item.code for item in report.warnings}
    assert "redundancy" in codes
    assert "multicollinearity" in codes


def test_uncorrelated_columns_have_no_strong_pairs() -> None:
    frame = pd.DataFrame(
        {
            "a": [1.0, 2.0, 3.0, 4.0, 5.0],
            "b": [5.0, 1.0, 4.0, 2.0, 3.0],
        }
    )
    report = compute_correlations(frame)
    assert report.strong_pairs == []
    assert report.redundant_pairs == []
    assert report.warnings == []


def test_negative_correlation_counts_as_strong() -> None:
    frame = pd.DataFrame(
        {
            "a": [1.0, 2.0, 3.0, 4.0, 5.0],
            "b": [10.0, 8.0, 6.0, 4.0, 2.0],
        }
    )
    report = compute_correlations(frame)
    assert len(report.strong_pairs) == 1
    assert report.strong_pairs[0].coefficient == -1.0
    assert report.strong_pairs[0].abs_coefficient == 1.0


def test_single_numeric_column_is_skipped() -> None:
    frame = pd.DataFrame({"a": [1, 2, 3, 4], "city": ["x", "y", "z", "w"]})
    report = compute_correlations(frame)
    assert report.skipped_reason == "insufficient_numeric_columns"
    assert report.matrix == {}


def test_custom_strong_threshold() -> None:
    frame = pd.DataFrame(
        {
            "a": [1.0, 2.0, 3.0, 4.0, 5.0],
            "b": [1.1, 1.9, 3.2, 3.8, 5.1],
        }
    )
    loose = compute_correlations(
        frame, AnalysisConfig(correlation_strong_threshold=0.5)
    )
    strict = compute_correlations(
        frame, AnalysisConfig(correlation_strong_threshold=0.999)
    )
    assert len(loose.strong_pairs) == 1
    assert strict.strong_pairs == []
