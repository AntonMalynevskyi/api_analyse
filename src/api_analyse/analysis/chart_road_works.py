from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from pandas.errors import DatabaseError
from sqlalchemy import text

from api_analyse.db import get_db
from api_analyse.utils.config import config

CHART_QUERY = text(
    """
    SELECT record_type, subtype, COUNT(*) AS count
    FROM traffic_situations
    WHERE record_type IN ("ConstructionWorks",
                          "GeneralNetworkManagement",
                          "MaintenanceWorks",
                          "ReroutingManagement",
                          "RoadOrCarriagewayOrLaneManagement")
    group by record_type, subtype;
    """
)


def generate_chart_road_work(
        output_path: str = config.paths.data_processed / "switzerland_road_works_chart.webp",
) -> Path | None:
    """Generates an HTML grouped bar chart of road works across Switzerland."""

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    data = pd.DataFrame()
    try:
        with get_db() as session:
            data = pd.read_sql(CHART_QUERY, session.connection())
            data["subtype"] = data["subtype"].fillna("Not Specified")
            data_pivot = data.pivot(index="record_type", columns="subtype", values="count").fillna(0)
            subtype_totals = data_pivot.sum(axis=0)
            sorted_columns = subtype_totals.sort_values(ascending=False).index
            data_pivot = data_pivot[sorted_columns]
            data_pivot["Total"] = data_pivot.sum(axis=1)
            data_pivot = data_pivot.sort_values(by="Total", ascending=False).drop(columns=["Total"])
    except DatabaseError:
        print(
            "Database error. Probably, database file wasn't created or it is empty. Please run \'api-analyse load-traffic\'")
    fig, ax = plt.subplots(figsize=(12, 8), layout="constrained")

    data_pivot.plot(kind="bar", stacked=True, ax=ax, width=0.75)

    for container in ax.containers:
        ax.bar_label(container, label_type='center', fmt=lambda x: f"{int(x)}" if x > 15 else "", fontsize=10)

    # Formatting
    ax.set_ylabel("Frequency")
    ax.set_xlabel("Record Type")
    ax.set_title("Frequency of Road Works Across Switzerland")
    plt.xticks(rotation=45, ha="right")
    plt.legend(title="Subtypes", bbox_to_anchor=(1.05, 1), loc="upper left")

    plt.savefig(output_path, bbox_inches="tight")


if __name__ == "__main__":
    generate_chart_road_work()
