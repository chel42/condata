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


def test_custom_config_is_stored(valid_csv: Path) -> None:
    config = AnalysisConfig(missing_warning_pct=0.1)
    result = DatasetInspector(valid_csv, config=config).analyze()
    assert result.config.missing_warning_pct == 0.1


def test_inspector_rejects_missing_file(tmp_path: Path) -> None:
    inspector = DatasetInspector(tmp_path / "nope.csv")
    with pytest.raises(DatasetLoadError):
        inspector.analyze()
