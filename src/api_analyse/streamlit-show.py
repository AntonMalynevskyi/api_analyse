import subprocess
import sys

from api_analyse.analysis import generate_graphics
from api_analyse.collectors import download_traffic_data
from api_analyse.db import init_db
from api_analyse.parsers import load_tmc_locations, save_road_data
from api_analyse.utils.config import config


def steamlit_display():
    init_db()
    download_traffic_data(api_key=config.api.opentransport_key or None)
    load_tmc_locations()
    save_road_data()

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