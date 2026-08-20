"""Point d'entrée CLI CONDATA."""

from __future__ import annotations

import typer

from condata import __version__
from condata.cli.commands.analyze import analyze
from condata.cli.commands.version import version

app = typer.Typer(
    name="condata",
    no_args_is_help=True,
    help="Audit local de qualité des datasets.",
    add_completion=False,
)
app.command("analyze")(analyze)
app.command("version")(version)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    show_version: bool = typer.Option(
        False,
        "--version",
        help="Affiche la version de CONDATA.",
        is_eager=True,
    ),
) -> None:
    if show_version:
        typer.echo(__version__)
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
