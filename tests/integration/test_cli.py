"""Tests CLI — le point d'entrée Typer existe."""

from __future__ import annotations

from typer.testing import CliRunner

from condata.cli.main import app

runner = CliRunner()


def test_cli_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "condata" in result.output.lower() or "usage" in result.output.lower()
