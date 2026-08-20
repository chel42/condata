"""Ingestion locale et sécurisée des datasets CSV.

CONDATA ne lit que des fichiers présents sur la machine. Aucune donnée
n'est envoyée vers un service externe.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

from condata.models.config import AnalysisConfig
from condata.models.schema import FileInfo

_ALLOWED_SUFFIXES = {".csv"}
_ENCODING_CANDIDATES = ("utf-8-sig", "utf-8", "cp1252", "latin-1")
_SEPARATOR_CANDIDATES = ",;\t|"
_SNIFF_BYTES = 65_536


class CondataError(Exception):
    """Erreur de base CONDATA."""


class DatasetLoadError(CondataError):
    """Le dataset n'a pas pu être chargé de façon sûre."""


def load_csv(
    path: str | Path,
    config: AnalysisConfig | None = None,
) -> tuple[pd.DataFrame, FileInfo]:
    """Charge un CSV local après validations de chemin, taille et format.

    Returns
    -------
    tuple[pandas.DataFrame, FileInfo]
        Le tableau et les métadonnées d'ingestion (encodage, séparateur, taille).
    """
    cfg = config or AnalysisConfig()
    file_path = _resolve_csv_path(path)
    _assert_file_size(file_path, cfg.max_file_size_mb)

    encoding = cfg.csv_encoding or _detect_encoding(file_path)
    separator = cfg.csv_separator or _detect_separator(file_path, encoding)

    try:
        frame = pd.read_csv(
            file_path,
            encoding=encoding,
            sep=separator,
            low_memory=False,
        )
    except Exception as exc:
        raise DatasetLoadError(
            f"Impossible de parser le CSV '{file_path}': {exc}"
        ) from exc

    if frame.columns.size == 0:
        raise DatasetLoadError(
            f"Le fichier '{file_path}' ne contient aucune colonne."
        )

    info = FileInfo(
        path=str(file_path),
        name=file_path.name,
        size_bytes=file_path.stat().st_size,
        encoding=encoding,
        separator=separator,
    )
    return frame, info


def _resolve_csv_path(path: str | Path) -> Path:
    file_path = Path(path).expanduser()
    try:
        file_path = file_path.resolve(strict=False)
    except OSError as exc:
        raise DatasetLoadError(f"Chemin invalide: {path}") from exc

    if not file_path.exists():
        raise DatasetLoadError(f"Fichier introuvable: {file_path}")
    if not file_path.is_file():
        raise DatasetLoadError(f"Le chemin n'est pas un fichier: {file_path}")
    if file_path.suffix.lower() not in _ALLOWED_SUFFIXES:
        raise DatasetLoadError(
            f"Format non supporté '{file_path.suffix}'. "
            "Le MVP CONDATA n'accepte que les fichiers .csv."
        )
    if file_path.stat().st_size == 0:
        raise DatasetLoadError(f"Le fichier est vide: {file_path}")
    return file_path


def _assert_file_size(file_path: Path, max_file_size_mb: float) -> None:
    size_bytes = file_path.stat().st_size
    max_bytes = max_file_size_mb * 1024 * 1024
    if size_bytes > max_bytes:
        raise DatasetLoadError(
            f"Fichier trop volumineux ({size_bytes} octets). "
            f"Limite configurée: {max_file_size_mb} Mo."
        )


def _detect_encoding(file_path: Path) -> str:
    sample = file_path.read_bytes()[:_SNIFF_BYTES]
    for encoding in _ENCODING_CANDIDATES:
        try:
            sample.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue
    return "latin-1"


def _detect_separator(file_path: Path, encoding: str) -> str:
    with file_path.open(encoding=encoding, newline="") as handle:
        sample = handle.read(_SNIFF_BYTES)
    if not sample.strip():
        raise DatasetLoadError(f"Le fichier ne contient pas de données: {file_path}")
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=_SEPARATOR_CANDIDATES)
        return dialect.delimiter
    except csv.Error:
        return ","
