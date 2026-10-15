import subprocess
import sys
from pathlib import Path

import typer

from api_analyse.analysis import run_analysis_pipeline


def _streamlit_app_path() -> Path:
    import api_analyse.display.show as show_mod

    return Path(show_mod.__file__).resolve()


def run_showcase_pipeline(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is not None:
        return

    run_analysis_pipeline(ctx)
    app_path = str(_streamlit_app_path())
    streamlit_args = [
        "run",
        app_path,
        "--global.developmentMode=false",
        "--server.fileWatcherType=none",
    ]

    if getattr(sys, "frozen", False):
        from streamlit.web import cli as stcli

        sys.argv = ["streamlit", *streamlit_args]
        raise typer.Exit(stcli.main())

    completed = subprocess.run([sys.executable, "-m", "streamlit", *streamlit_args])
    raise typer.Exit(completed.returncode)
