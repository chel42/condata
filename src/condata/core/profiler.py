"""Profiling de structure d'un dataset (indépendant de la CLI)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from condata.models.schema import ColumnProfile, DatasetProfile, FileInfo, SemanticType

_DATETIME_SAMPLE = 80
_DATETIME_HIT_RATIO = 0.8
_SAMPLE_VALUES = 5


def profile_dataset(frame: pd.DataFrame, file_info: FileInfo) -> DatasetProfile:
    """Construit le profil structurel du dataset."""
    columns = [_profile_column(name, frame[name]) for name in frame.columns]
    type_counts = _count_semantic_types(columns)
    n_rows = len(frame)
    n_columns = int(frame.shape[1])

    return DatasetProfile(
        file_name=file_info.name,
        file_path=file_info.path,
        file_size_bytes=file_info.size_bytes,
        n_rows=n_rows,
        n_columns=n_columns,
        n_numeric=type_counts["numeric"],
        n_categorical=type_counts["categorical"],
        n_datetime=type_counts["datetime"],
        n_boolean=type_counts["boolean"],
        n_constant=sum(1 for col in columns if col.is_constant),
        memory_usage_bytes=int(frame.memory_usage(deep=True).sum()),
        columns=columns,
    )


def _profile_column(name: str, series: pd.Series) -> ColumnProfile:
    n_rows = len(series)
    missing_count = int(series.isna().sum())
    non_null_count = n_rows - missing_count
    unique_count = int(series.nunique(dropna=True))
    semantic_type = infer_semantic_type(series)

    return ColumnProfile(
        name=str(name),
        pandas_dtype=str(series.dtype),
        semantic_type=semantic_type,
        non_null_count=non_null_count,
        non_null_pct=_pct(non_null_count, n_rows),
        unique_count=unique_count,
        is_constant=unique_count <= 1,
        missing_count=missing_count,
        missing_pct=_pct(missing_count, n_rows),
        sample_values=_sample_values(series),
    )


def infer_semantic_type(series: pd.Series) -> SemanticType:
    """Infère un type sémantique sans muter la série."""
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    if _looks_like_datetime(series):
        return "datetime"
    if pd.api.types.is_string_dtype(series) or series.dtype == object:
        return "categorical"
    return "unknown"


def _looks_like_datetime(series: pd.Series) -> bool:
    sample = series.dropna().astype(str).head(_DATETIME_SAMPLE)
    if sample.empty:
        return False
    # pd.to_datetime accepte les entiers (epoch) : on les écarte.
    if sample.str.fullmatch(r"-?\d+(\.\d+)?").fillna(False).all():
        return False
    parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
    return float(parsed.notna().mean()) >= _DATETIME_HIT_RATIO


def _sample_values(series: pd.Series) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for raw in series.dropna().head(50):
        text = _stringify(raw)
        if text in seen:
            continue
        seen.add(text)
        values.append(text)
        if len(values) >= _SAMPLE_VALUES:
            break
    return values


def _stringify(value: Any) -> str:
    text = str(value)
    return text if len(text) <= 80 else text[:77] + "..."


def _pct(part: int, whole: int) -> float:
    if whole == 0:
        return 0.0
    return round(100.0 * part / whole, 4)


def _count_semantic_types(columns: list[ColumnProfile]) -> dict[str, int]:
    counts = {
        "numeric": 0,
        "categorical": 0,
        "datetime": 0,
        "boolean": 0,
        "unknown": 0,
    }
    for column in columns:
        counts[column.semantic_type] += 1
    return counts
