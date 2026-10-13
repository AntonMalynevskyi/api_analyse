import typer

from api_analyse.analysis.heatmap import generate_heatmap

app = typer.Typer()

app.command(name="heatmap")(generate_heatmap)

__all__ = ["generate_heatmap"]
