"""Tests de détection des potential outliers (IQR / Z-score)."""

from __future__ import annotations

import pandas as pd

from condata.core.outliers import detect_outliers
from condata.models.config import AnalysisConfig


def test_iqr_flags_extreme_value() -> None:
    frame = pd.DataFrame({"x": [10, 12, 11, 13, 12, 10, 11, 100]})
    report = detect_outliers(frame)
    col = report.columns[0]
    assert report.method == "iqr"
    assert col.method == "iqr"
    assert col.n_potential_outliers == 1
    assert col.n_high == 1
    assert col.n_low == 0
    assert 100.0 in col.sample_values
    assert col.skipped_reason is None


def test_zscore_flags_extreme_value() -> None:
    values = [10.0] * 20 + [1000.0]
    frame = pd.DataFrame({"x": values})
    report = detect_outliers(frame, AnalysisConfig(outlier_method="zscore"))
    col = report.columns[0]
    assert col.method == "zscore"
    assert col.n_potential_outliers == 1
    assert 1000.0 in col.sample_values


def test_zscore_skips_zero_variance() -> None:
    frame = pd.DataFrame({"x": [5, 5, 5, 5, 5]})
    report = detect_outliers(frame, AnalysisConfig(outlier_method="zscore"))
    col = report.columns[0]
    assert col.skipped_reason == "zero_variance"
    assert col.n_potential_outliers == 0


def test_iqr_skips_short_series() -> None:
    frame = pd.DataFrame({"x": [1.0, 100.0]})
    report = detect_outliers(frame)
    col = report.columns[0]
    assert col.skipped_reason == "insufficient_values"
    assert report.n_columns_analyzed == 0


def test_ignores_categorical_columns() -> None:
    frame = pd.DataFrame({"x": [10, 12, 11, 13, 12, 10, 11, 100], "city": ["a"] * 8})
    report = detect_outliers(frame)
    assert [col.name for col in report.columns] == ["x"]


def test_does_not_treat_detection_as_error() -> None:
    frame = pd.DataFrame({"x": [10, 12, 11, 13, 12, 10, 11, 100]})
    report = detect_outliers(frame)
    dumped = report.model_dump_json()
    assert "potential" in dumped
    assert "error" not in dumped
