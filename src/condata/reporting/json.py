"""Sérialiseur JSON des résultats Pydantic."""

from __future__ import annotations

from pathlib import Path

from condata.models.schema import AnalysisResult


def export_json(result: AnalysisResult, path: str | Path) -> Path:
    """Écrit le résultat d'analyse en JSON UTF-8 (local, sans appel réseau)."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    return output.resolve()
