from pathlib import Path
import folium
from folium.plugins import HeatMap
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from api_analyse.config import config
from api_analyse.db import get_db

HEATMAP_QUERY = text(
    """
    SELECT start_loc.latitude,
           start_loc.longitude
    FROM traffic_situations ts
             JOIN tmc_locations start_loc
                  ON (ts.location -> 'alert_c' ->> 'primary_location_code')::INT = start_loc.location_code
    WHERE start_loc.latitude IS NOT NULL
      AND start_loc.longitude IS NOT NULL;
    """
)


def generate_heatmap(
        output_file: str | Path | None = None,
) -> Path:
    """Generates an HTML heatmap of traffic incidents across Switzerland."""
    output_path = (
        Path(output_file)
        if output_file
        else config.paths.data_processed / "switzerland_traffic_heatmap.html"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    def _render(s: Session) -> Path:
        df = pd.read_sql(HEATMAP_QUERY, s.connection())
        print(f"Found {len(df)} traffic incidents with valid coordinates.")

        m = folium.Map(location=[46.8, 8.2], zoom_start=8, tiles="OpenStreetMap")

        # Fast vectorization instead of slow df.iterrows()
        heat_data = df[["latitude", "longitude"]].values.tolist()

        HeatMap(
            heat_data,
            radius=15,
            blur=10,
            min_opacity=0.3,
            gradient={0.2: "blue", 0.4: "lime", 0.6: "yellow", 0.8: "orange", 1.0: "red"},
        ).add_to(m)

        m.save(output_path)
        print(f"Heatmap saved to: {output_path}")
        return output_path

    with get_db() as db_session:
        return _render(db_session)
