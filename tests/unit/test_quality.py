"""Tests du Data Quality Score et des détections associées."""

from __future__ import annotations

import pandas as pd

from condata.core.quality import assess_quality


def test_clean_dataset_scores_high(clean_df: pd.DataFrame) -> None:
    report = assess_quality(clean_df)
    assert report.score == 100
    assert report.breakdown.completeness == 35
    assert report.breakdown.uniqueness == 25
    assert report.duplicates.n_duplicates == 0
    assert report.missing.total_missing == 0


def test_messy_dataset_detects_issues(messy_df: pd.DataFrame) -> None:
    report = assess_quality(messy_df)
    codes = {issue.code for issue in report.issues}
    assert "missing_values" in codes
    assert "duplicates" in codes
    assert "categorical_inconsistency" in codes
    assert "mixed_types" in codes
    assert "constant_column" in codes
    assert 0 <= report.score < 100
    assert report.duplicates.n_duplicates == 1


def test_score_is_bounded() -> None:
    frame = pd.DataFrame({"a": [None, None], "b": [None, None]})
    report = assess_quality(frame)
    assert 0 <= report.score <= 100
