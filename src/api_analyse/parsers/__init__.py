import typer

from .parse_tmc import load_tmc_locations
from .parse_road_data import save_road_data

app = typer.Typer(name="load")

app.command(name="tmc")(load_tmc_locations)
app.command(name="traffic")(save_road_data)