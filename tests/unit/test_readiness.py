"""Tests du ML Readiness Score."""

from __future__ import annotations

import pandas as pd

from condata.core.readiness import assess_readiness
from condata.models.config import AnalysisConfig


def _ml_frame(*, imbalanced: bool = False, with_id: bool = False) -> pd.DataFrame:
    n = 20
    target = (["a"] * 18 + ["b"] * 2) if imbalanced else (["a", "b"] * 10)
    data: dict[str, object] = {
        "feat_a": list(range(10)) * 2,
        "feat_b": [0, 3, 1, 8, 2, 7, 4, 6, 5, 9] * 2,
        "target": target,
    }
    if with_id:
        data["id"] = list(range(n))
    return pd.DataFrame(data)


def test_balanced_dataset_with_target_scores_high() -> None:
    report = assess_readiness(_ml_frame())
    assert report.heuristic is True
    assert report.target_column == "target"
    assert report.target_inferred is True
    assert report.score >= 80
    by_code = {item.code: item for item in report.checks}
    assert by_code["schema"].status == "ok"
    assert by_code["target_variable"].status == "ok"
    assert by_code["class_balance"].status == "ok"


def test_explicit_target_column() -> None:
    frame = _ml_frame().rename(columns={"target": "y_true"})
    report = assess_readiness(frame, AnalysisConfig(target_column="y_true"))
    assert report.target_column == "y_true"
    assert report.target_inferred is False
    assert report.score >= 80


def test_missing_target_warns() -> None:
    frame = pd.DataFrame(
        {"feat_a": list(range(20)), "feat_b": list(range(20, 40))}
    )
    report = assess_readiness(frame)
    by_code = {item.code: item for item in report.checks}
    assert by_code["target_variable"].status == "warning"
    assert by_code["class_balance"].status == "warning"
    assert 0 <= report.score <= 100


def test_imbalanced_target_is_flagged() -> None:
    report = assess_readiness(_ml_frame(imbalanced=True))
    by_code = {item.code: item for item in report.checks}
    assert by_code["class_balance"].status in {"warning", "critical"}
    assert by_code["class_balance"].score < 15


def test_id_column_flags_potential_leakage() -> None:
    report = assess_readiness(_ml_frame(with_id=True))
    by_code = {item.code: item for item in report.checks}
    assert by_code["potential_leakage"].status == "warning"
    assert "id" in by_code["potential_leakage"].message


def test_unknown_target_is_critical() -> None:
    report = assess_readiness(
        _ml_frame(), AnalysisConfig(target_column="absent")
    )
    by_code = {item.code: item for item in report.checks}
    assert by_code["target_variable"].status == "critical"
    assert by_code["target_variable"].score == 0


def test_score_is_bounded() -> None:
    frame = pd.DataFrame({"a": [None, None]})
    report = assess_readiness(frame)
    assert 0 <= report.score <= 100
    assert report.disclaimer
