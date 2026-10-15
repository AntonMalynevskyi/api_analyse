import subprocess
import sys

from api_analyse.analysis import generate_graphics
from api_analyse.utils.config import config


def steamlit_display():
    from api_analyse.main import ingest_data
    ingest_data()

    generate_graphics()

    app_path = config.paths.root / "src" / "api_analyse" / "display" / "show.py"
    subprocess.run(
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

if __name__ == "__main__":
    steamlit_display()