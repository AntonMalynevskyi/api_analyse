import typer

from api_analyse.collectors.download_traffic_data import download_traffic_data
from api_analyse.analysis import generate_heatmap
from api_analyse.parsers.parse_road_data import save_road_data
from api_analyse.parsers.parse_tmc import load_tmc_locations
from api_analyse.utils.config import config
from api_analyse.db import init_db
from api_analyse.analysis import app as analysis_app
from api_analyse.parsers import app as parser_app

app = typer.Typer(help="API Analysis CLI tool")
app.add_typer(analysis_app, name="generate", help="Generate different graphics using stored data")
app.add_typer(parser_app, help="Parse and load raw data into database")
app.command(name="download-data")(download_traffic_data)


@app.command()
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

    output_file = generate_heatmap()
    print(f"Pipeline finished successfully. Map saved to: {output_file}")


if __name__ == "__main__":
    main()
