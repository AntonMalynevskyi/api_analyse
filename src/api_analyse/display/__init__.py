import subprocess
import sys

import typer

from api_analyse.analysis import run_analysis_pipeline
from api_analyse.utils.config import config


def run_showcase_pipeline(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is not None:
        return

    run_analysis_pipeline(ctx)
    app_path = config.paths.root / "src" / "api_analyse" / "display" / "show.py"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(app_path),
            "--global.developmentMode=false",
            "--server.fileWatcherType=none",
        ]
    )
    raise typer.Exit(completed.returncode)
