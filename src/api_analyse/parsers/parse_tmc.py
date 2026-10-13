from pathlib import Path
import pandas as pd

from api_analyse.utils.config import config
from api_analyse.db import get_db


def load_tmc_locations(
    data_dir: str | Path = config.paths.data_raw / "tmc" / "CH_104_E1_4_9_7.5_LTEF"
) -> None:
    data_dir = Path(data_dir)
    df_points = pd.read_csv(data_dir / "POINTS.DAT", sep=";", encoding="utf-8")
    df_names = pd.read_csv(data_dir / "NAMES.DAT", sep=";", encoding="utf-8")
    df_roads = pd.read_csv(data_dir / "ROADS.DAT", sep=";", encoding="utf-8")

    df_names = df_names.rename(columns=lambda x: x.strip())
    df_roads = df_roads.rename(columns=lambda x: x.strip())
    df_points = df_points.rename(columns=lambda x: x.strip())

    df_tmc = df_points[["LCD", "XCOORD", "YCOORD", "ROA_LCD", "N1ID", "CID", "TABCD"]].copy()
    df_tmc = df_tmc.merge(
        df_roads[["LCD", "ROADNUMBER"]],
        left_on="ROA_LCD",
        right_on="LCD",
        how="left",
        suffixes=("", "_road"),
    )
    df_tmc = df_tmc.merge(
        df_names[["NID", "NAME"]],
        left_on="N1ID",
        right_on="NID",
        how="left",
    )

    df_tmc["longitude"] = df_tmc["XCOORD"] / 100000.0
    df_tmc["latitude"] = df_tmc["YCOORD"] / 100000.0

    df_final = pd.DataFrame({
        "country_code": df_tmc["CID"],
        "table_number": df_tmc["TABCD"],
        "location_code": df_tmc["LCD"],
        "road_name": df_tmc["ROADNUMBER"],
        "description": df_tmc["NAME"],
        "latitude": df_tmc["latitude"],
        "longitude": df_tmc["longitude"],
    }).drop_duplicates(subset=["location_code"])

    with get_db() as session:
        df_final.to_sql("tmc_locations", session.connection(), if_exists="replace", index=False)
        print(f"Loaded {len(df_final)} TMC locations into database.")