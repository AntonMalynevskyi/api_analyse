import typer

from api_analyse.analysis import app as analysis_app
from api_analyse.collectors import download_traffic_data
from api_analyse.db import init_db
from api_analyse.display import run_showcase_pipeline
from api_analyse.parsers import app as parser_app
from api_analyse.parsers.parse_road_data import save_road_data
from api_analyse.parsers.parse_tmc import load_tmc_locations
from api_analyse.utils.config import config

app = typer.Typer(help="API Analysis CLI tool")
app.add_typer(analysis_app, name="generate")

data_app = typer.Typer(
    help="Download raw data and load it into the database. "
         "Run without a subcommand to download traffic data and load TMC plus traffic records.",
    no_args_is_help=False,
)
data_app.command(name="download")(download_traffic_data)
data_app.add_typer(parser_app, name="load")
app.add_typer(data_app, name="data")

app.command(name="showcase", help="Showcase graphics in a browser. "
                                  "Can be used as a main command, "
                                  "that will do the full pipeline")(run_showcase_pipeline)


def ingest_data() -> None:
    init_db()
    download_traffic_data(api_key=config.api.opentransport_key or None)
    load_tmc_locations()
    save_road_data()


@data_app.callback(invoke_without_command=True)
def run_data_pipeline(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is not None:
        return

    ingest_data()


'''
def main() -> None:
    init_db()

    print("Loading TMC location points...")
    load_tmc_locations()

    xml_path = config.paths.data_raw / "traffic" / "traffic_situations.xml"
    if xml_path.exists():
        print(f"Parsing and saving road data from {xml_path}...")
        save_road_data(xml_path)
    else:
        print(f"Warning: File not found at {xml_path}. Skipping road data ingestion.")

    output_file = generate_heatmap_road_work()
    print(f"Pipeline finished successfully. Map saved to: {output_file}")
'''

if __name__ == "__main__":
    app()
