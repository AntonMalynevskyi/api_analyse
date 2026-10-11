import argparse
from api_analyse.analysis import generate_heatmap
from api_analyse.collectors.download_data import download_traffic_data
from api_analyse.parsers.parse_road_data import save_road_data
from api_analyse.parsers.parse_tmc import load_tmc_locations
from api_analyse.config import config
from api_analyse.db import init_db


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load bundled traffic data and generate a heatmap."
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Fetch a fresh traffic_situations.xml from the API before loading.",
    )
    return parser.parse_args()


def main() -> None:
    init_db()

    args = parse_args()

    if args.download:
        print("Downloading fresh DATEX II XML road data...")
        download_traffic_data()

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
