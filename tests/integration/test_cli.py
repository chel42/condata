"""Tests d'export HTML / JSON et de la CLI analyze."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from condata import DatasetInspector
from condata.cli.main import app

runner = CliRunner()


def test_cli_help_lists_analyze() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "analyze" in result.output.lower()


def test_cli_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_analyze_writes_html(valid_csv: Path, tmp_path: Path) -> None:
    out = tmp_path / "report.html"
    result = runner.invoke(
        app,
        ["analyze", str(valid_csv), "-o", str(out), "--no-browser"],
    )
    assert result.exit_code == 0, result.output
    assert out.exists()
    html = out.read_text(encoding="utf-8")
    assert "CONDATA" in html
    assert "DATA QUALITY SCORE" in html
    assert "Doublons" in html
    assert "Warnings" in html
    assert "Outliers" in html
    assert "Statistiques" in html
    assert "valid.csv" in html


def test_analyze_writes_json(valid_csv: Path, tmp_path: Path) -> None:
    out = tmp_path / "report.json"
    result = runner.invoke(
        app,
        ["analyze", str(valid_csv), "-f", "json", "-o", str(out), "--no-browser"],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert "quality" in payload
    assert "readiness" in payload
    assert payload["profile"]["n_rows"] == 6


def test_python_export_api(valid_csv: Path, tmp_path: Path) -> None:
    inspector = DatasetInspector(valid_csv)
    result = inspector.analyze()
    html = result.export_html(tmp_path / "api.html", frame=inspector.dataframe)
    json_path = result.export_json(tmp_path / "api.json")
    assert html.exists()
    assert "potential outliers" in html.read_text(encoding="utf-8").lower()
    assert json.loads(json_path.read_text(encoding="utf-8"))["file"]["name"] == "valid.csv"
