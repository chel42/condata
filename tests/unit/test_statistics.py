"""Tests des statistiques descriptives."""

from __future__ import annotations

import pandas as pd
import pytest

from condata.core.statistics import compute_statistics
from condata.models.config import AnalysisConfig


def test_numeric_stats_match_pandas(clean_df: pd.DataFrame) -> None:
    report = compute_statistics(clean_df)
    names = {col.name for col in report.numeric}
    assert names == {"age", "score"}

    age = next(col for col in report.numeric if col.name == "age")
    series = clean_df["age"]
    assert age.count == 4
    assert age.mean == pytest.approx(float(series.mean()), rel=1e-6)
    assert age.median == pytest.approx(float(series.median()), rel=1e-6)
    assert age.min == pytest.approx(float(series.min()), rel=1e-6)
    assert age.max == pytest.approx(float(series.max()), rel=1e-6)
    assert age.std == pytest.approx(float(series.std(ddof=1)), rel=1e-6)
    assert age.q1 == pytest.approx(float(series.quantile(0.25)), rel=1e-6)
    assert age.q3 == pytest.approx(float(series.quantile(0.75)), rel=1e-6)
    assert age.p25 == age.q1
    assert age.p50 == age.median
    assert age.p75 == age.q3


def test_categorical_frequencies_and_dominant(clean_df: pd.DataFrame) -> None:
    report = compute_statistics(clean_df)
    region = next(col for col in report.categorical if col.name == "region")
    assert region.n_categories == 4
    assert region.dominant_count == 1
    assert len(region.frequencies) == 4
    assert region.truncated is False
    assert sum(item.count for item in region.frequencies) == 4


def test_messy_df_ignores_na_in_numeric(messy_df: pd.DataFrame) -> None:
    report = compute_statistics(messy_df)
    age = next(col for col in report.numeric if col.name == "age")
    assert age.count == 3
    assert age.mean == pytest.approx((21 + 34 + 21) / 3, rel=1e-6)

    region = next(col for col in report.categorical if col.name == "region")
    assert region.dominant == "Brazzaville"
    assert region.dominant_count == 2


def test_all_nan_numeric_returns_empty_metrics() -> None:
    frame = pd.DataFrame({"x": pd.Series([float("nan"), float("nan")])})
    report = compute_statistics(frame)
    assert len(report.numeric) == 1
    stats = report.numeric[0]
    assert stats.count == 0
    assert stats.mean is None
    assert stats.min is None


def test_frequency_truncation() -> None:
    frame = pd.DataFrame({"label": [f"c{i}" for i in range(10)]})
    config = AnalysisConfig(max_category_frequencies=3)
    report = compute_statistics(frame, config)
    stats = report.categorical[0]
    assert stats.n_categories == 10
    assert len(stats.frequencies) == 3
    assert stats.truncated is True
