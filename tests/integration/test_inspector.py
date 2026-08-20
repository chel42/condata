"""Tests d'intégration de DatasetInspector."""

from __future__ import annotations

from pathlib import Path

import pytest

from condata import DatasetInspector
from condata.models.config import AnalysisConfig
from condata.utils.io import DatasetLoadError


def test_analyze_valid_csv(valid_csv: Path) -> None:
    result = DatasetInspector(valid_csv).analyze()
    assert result.profile.n_rows == 6
    assert result.profile.n_columns == 4
    assert result.profile.file_name == "valid.csv"
    assert 0 <= result.quality.score <= 100
    assert result.quality.duplicates.n_duplicates == 1
    codes = {issue.code for issue in result.quality.issues}
    assert "categorical_inconsistency" in codes
    assert result.file.separator == ","
    numeric_names = {col.name for col in result.statistics.numeric}
    categorical_names = {col.name for col in result.statistics.categorical}
    assert "age" in numeric_names
    assert "speed" in numeric_names
    assert "region" in categorical_names
    age = next(col for col in result.statistics.numeric if col.name == "age")
    assert age.count == 5
    assert age.min == 25.0
    assert age.max == 40.0
    assert result.outliers.method == "iqr"
    speed = next(col for col in result.outliers.columns if col.name == "speed")
    assert speed.n_potential_outliers >= 1
    assert 1200.0 in speed.sample_values
    assert result.correlations.method == "pearson"
    assert "age" in result.correlations.matrix
    assert "speed" in result.correlations.matrix["age"]
    assert 0 <= result.readiness.score <= 100
    assert result.readiness.heuristic is True
    check_codes = {item.code for item in result.readiness.checks}
    assert check_codes == {
        "schema",
        "missing_values",
        "duplicates",
        "data_types",
        "outliers",
        "target_variable",
        "class_balance",
        "potential_leakage",
    }


def test_custom_config_is_stored(valid_csv: Path) -> None:
    config = AnalysisConfig(missing_warning_pct=0.1)
    result = DatasetInspector(valid_csv, config=config).analyze()
    assert result.config.missing_warning_pct == 0.1


def test_inspector_rejects_missing_file(tmp_path: Path) -> None:
    inspector = DatasetInspector(tmp_path / "nope.csv")
    with pytest.raises(DatasetLoadError):
        inspector.analyze()
