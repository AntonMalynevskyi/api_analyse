import typer

from api_analyse.analysis.chart_road_works import generate_chart_road_work
from api_analyse.analysis.heatmap_road_works import generate_heatmap_road_work
from api_analyse.db import has_traffic_data

app = typer.Typer(
    help="Generate graphics from stored data. "
         "Run without a subcommand to generate heatmap and chart.",
    no_args_is_help=False,
)
app.command(name="heatmap")(generate_heatmap_road_work)
app.command(name="chart")(generate_chart_road_work)


def ensure_traffic_data() -> None:
    if has_traffic_data():
        return

    should_ingest = typer.confirm(
        "Database is missing or empty. Run `api-analyse data` (download and load) now?"
    )
    if not should_ingest:
        raise typer.Exit(code=1)

    from api_analyse.main import ingest_data
    ingest_data()


def generate_graphics() -> None:
    generate_heatmap_road_work()
    generate_chart_road_work()


@app.callback(invoke_without_command=True)
def run_analysis_pipeline(ctx: typer.Context) -> None:
    ensure_traffic_data()
    if ctx.invoked_subcommand is not None:
        return

    generate_graphics()


__all__ = [
    "generate_heatmap_road_work",
    "generate_chart_road_work",
    "generate_graphics",
    "ensure_traffic_data",
    "run_analysis_pipeline",
]
