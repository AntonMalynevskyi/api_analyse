import subprocess
import sys
from pathlib import Path

import typer

from api_analyse.analysis import run_analysis_pipeline


def _streamlit_app_path() -> Path:
    candidates: list[Path] = []
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        candidates.append(Path(sys._MEIPASS) / "api_analyse" / "display" / "show.py")

    import api_analyse.display as display_pkg

    for entry in getattr(display_pkg, "__path__", []):
        candidates.append(Path(entry) / "show.py")
    if display_pkg.__file__:
        candidates.append(Path(display_pkg.__file__).resolve().parent / "show.py")
    candidates.append(Path(__file__).resolve().parent / "show.py")

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    raise FileNotFoundError(
        "Streamlit app show.py is missing from the bundle. Rebuild the binary."
    )


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
