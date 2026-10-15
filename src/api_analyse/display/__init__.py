import subprocess
import sys

import typer

from api_analyse.analysis import ensure_traffic_data, generate_graphics
from api_analyse.utils.config import config


def ensure_graphics() -> None:
    heatmap = config.paths.data_processed / "switzerland_road_works_heatmap.html"
    chart = config.paths.data_processed / "switzerland_road_works_chart.webp"
    if heatmap.is_file() and chart.is_file():
        return

    should_generate = typer.confirm(
        "No heatmap or chart found. Run `api-analyse generate` now?"
    )
    if not should_generate:
        raise typer.Exit(code=1)

    ensure_traffic_data()
    generate_graphics()


def run_showcase_pipeline() -> None:
    ensure_graphics()
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
