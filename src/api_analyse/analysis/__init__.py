import typer

from api_analyse.analysis.heatmap_road_works import generate_heatmap_road_work

app = typer.Typer()

app.command(name="heatmap")(generate_heatmap_road_work)

__all__ = ["generate_heatmap_road_work"]
