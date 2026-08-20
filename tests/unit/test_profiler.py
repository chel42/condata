"""Tests du profiler."""

from __future__ import annotations

import pandas as pd

from condata.core.profiler import infer_semantic_type, profile_dataset
from condata.models.schema import FileInfo


def _file_info() -> FileInfo:
    return FileInfo(
        path="memory://clean.csv",
        name="clean.csv",
        size_bytes=128,
        encoding="utf-8",
        separator=",",
    )


def test_profile_counts(clean_df: pd.DataFrame) -> None:
    profile = profile_dataset(clean_df, _file_info())
    assert profile.n_rows == 4
    assert profile.n_columns == 3
    assert profile.n_integer == 1
    assert profile.n_float == 1
    assert profile.n_text == 1
    assert profile.file_size_bytes == 128
    assert profile.columns[0].name == "age"
    assert profile.columns[0].semantic_type == "integer"
    assert profile.columns[0].missing_count == 0


def test_profile_detects_missing_and_constant(messy_df: pd.DataFrame) -> None:
    profile = profile_dataset(messy_df, _file_info())
    age = next(col for col in profile.columns if col.name == "age")
    flag = next(col for col in profile.columns if col.name == "flag")
    assert age.missing_count == 1
    assert flag.is_constant is True
    assert profile.n_constant >= 1


def test_infer_known_types() -> None:
    dates = pd.Series(["2024-01-01", "2024-02-01", "2024-03-01"])
    integers = pd.Series([1, 2, 3])
    reals = pd.Series([1.5, 2.0, 3.25])
    labels = pd.Series(["a", "b", "c"])
    flags = pd.Series([True, False, True])
    assert infer_semantic_type(dates) == "datetime"
    assert infer_semantic_type(integers) == "integer"
    assert infer_semantic_type(reals) == "float"
    assert infer_semantic_type(labels) == "text"
    assert infer_semantic_type(flags) == "boolean"
