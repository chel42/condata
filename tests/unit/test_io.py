"""Tests d'ingestion CSV."""

from __future__ import annotations

from pathlib import Path

import pytest

from condata.models.config import AnalysisConfig
from condata.utils.io import DatasetLoadError, load_csv


def test_load_csv_reads_rows_and_metadata(valid_csv: Path) -> None:
    frame, info = load_csv(valid_csv)
    assert len(frame) == 6
    assert list(frame.columns) == ["age", "region", "speed", "observed_at"]
    assert info.name == "valid.csv"
    assert info.size_bytes > 0
    assert info.encoding
    assert info.separator == ","


def test_load_csv_missing_file(tmp_path: Path) -> None:
    with pytest.raises(DatasetLoadError, match="introuvable"):
        load_csv(tmp_path / "absent.csv")


def test_load_csv_rejects_non_csv(tmp_path: Path) -> None:
    path = tmp_path / "notes.txt"
    path.write_text("a,b\n1,2\n", encoding="utf-8")
    with pytest.raises(DatasetLoadError, match="Format non supporté"):
        load_csv(path)


def test_load_csv_rejects_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "empty.csv"
    path.write_text("", encoding="utf-8")
    with pytest.raises(DatasetLoadError, match="vide"):
        load_csv(path)


def test_load_csv_rejects_oversized_file(tmp_path: Path) -> None:
    path = tmp_path / "big.csv"
    path.write_text("a,b\n1,2\n", encoding="utf-8")
    config = AnalysisConfig(max_file_size_mb=0.0000001)
    with pytest.raises(DatasetLoadError, match="trop volumineux"):
        load_csv(path, config)


def test_load_csv_detects_semicolon(tmp_path: Path) -> None:
    path = tmp_path / "semi.csv"
    path.write_text("a;b\n1;2\n3;4\n", encoding="utf-8")
    frame, info = load_csv(path)
    assert info.separator == ";"
    assert list(frame.columns) == ["a", "b"]
    assert len(frame) == 2
