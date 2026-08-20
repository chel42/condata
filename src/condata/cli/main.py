"""Point d'entrée CLI CONDATA."""

from __future__ import annotations

import typer

from condata import __version__

app = typer.Typer(
    name="condata",
    no_args_is_help=True,
    help="Audit local de qualité des datasets.",
    add_completion=False,
)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        help="Affiche la version de CONDATA.",
        is_eager=True,
    ),
) -> None:
    if version:
        typer.echo(__version__)
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
