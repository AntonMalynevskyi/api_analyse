import typer

from api_analyse.analysis.chart_road_works import generate_chart_road_work
from api_analyse.analysis.heatmap_road_works import generate_heatmap_road_work

app = typer.Typer(
    help="Generate graphics from stored data. "
         "Run without a subcommand to generate heatmap and chart.",
    no_args_is_help=False,
)
app.command(name="heatmap")(generate_heatmap_road_work)
app.command(name="chart")(generate_chart_road_work)


def generate_graphics() -> None:
    generate_heatmap_road_work()
    generate_chart_road_work()


@app.callback(invoke_without_command=True)
def run_analysis_pipeline(ctx: typer.Context) -> None:
    from api_analyse.main import ingest_data
    ingest_data()

    if ctx.invoked_subcommand is not None:
        return
    generate_graphics()


__all__ = [
    "generate_heatmap_road_work",
    "generate_chart_road_work",
    "generate_graphics",
    "run_analysis_pipeline",
]
