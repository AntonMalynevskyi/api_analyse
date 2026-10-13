from pathlib import Path
import folium
import typer
from folium.plugins import HeatMap
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session
from api_analyse.utils.config import config
from api_analyse.db import get_db

HEATMAP_QUERY = text(
    """
    SELECT latitude,
           longitude
    FROM traffic_situations
    WHERE latitude IS NOT NULL
      AND longitude IS NOT NULL;
    """
)

def generate_heatmap(
        output_path: str = config.paths.data_processed / "switzerland_traffic_heatmap.html",
) -> Path:
    """Generates an HTML heatmap of traffic incidents across Switzerland."""

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    def _render(s: Session) -> Path:
        heat_data = []
        chunks = pd.read_sql(HEATMAP_QUERY, s.connection(), chunksize=50000)
        for chunk in chunks:
            heat_data.extend(chunk[["latitude", "longitude"]].values.tolist())
        m = folium.Map(location=[46.8, 8.2], zoom_start=8, tiles="OpenStreetMap")
        HeatMap(
            heat_data,
            radius=15,
            blur=10,
            min_opacity=0.3,
            gradient={0.2: "blue", 0.4: "lime", 0.6: "yellow", 0.8: "orange", 1.0: "red"},
        ).add_to(m)
        m.save(output_file)
        print(f"Heatmap saved to: {output_file}")
        return output_file

    with get_db() as db_session:
        return _render(db_session)
