"""Commande ``condata version``."""

from __future__ import annotations

import typer

from condata import __version__


def version() -> None:
    """Affiche la version de CONDATA."""
    typer.echo(__version__)
