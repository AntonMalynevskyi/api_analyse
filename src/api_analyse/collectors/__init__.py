import typer

from .download_data import download_traffic_data

app = typer.Typer()
app.command(name="download-data")(download_traffic_data)

__all__ = ["download_data"]
