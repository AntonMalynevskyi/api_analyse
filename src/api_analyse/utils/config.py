import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _bundle_root() -> Path:
    if _is_frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent.parent.parent.parent


def _writable_root() -> Path:
    if _is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent.parent.parent


def _seed_raw_data(destination: Path) -> None:
    """Copy bundled data/raw next to the binary when files are missing."""
    source = _bundle_root() / "data" / "raw"
    if not source.is_dir():
        return

    for path in source.rglob("*"):
        relative = path.relative_to(source)
        target = destination / relative
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


BUNDLE_ROOT = _bundle_root()
BASE_DIR = _writable_root()

def _seed_env_example() -> None:
    source = _bundle_root() / ".env.example"
    target = BASE_DIR / ".env.example"
    if source.is_file() and not target.exists():
        shutil.copy2(source, target)


_seed_raw_data(BASE_DIR / "data" / "raw")
_seed_env_example()
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class PathConfig:
    root: Path = BASE_DIR
    bundle_root: Path = BUNDLE_ROOT
    data_raw: Path = BASE_DIR / "data" / "raw"
    data_processed: Path = BASE_DIR / "data" / "processed"


@dataclass(frozen=True)
class DatabaseConfig:
    '''
    host: str = os.getenv("POSTGRES_HOST", "localhost")
    port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    name: str = os.getenv("POSTGRES_DB", "postgres")
    user: str = os.getenv("POSTGRES_USER", "postgres")
    password: str = os.getenv("POSTGRES_PASSWORD", "password")
    '''
    db_name: str = os.getenv("SQLITE_DB_NAME", "traffic_situations.db")

    @property
    def url(self) -> str:
        """SQLAlchemy / Psycopg v3 connection URL."""
        db_path = PathConfig().data_processed / self.db_name
        return f"sqlite:///{db_path}"


@dataclass(frozen=True)
class APIConfig:
    opentransport_key: str = os.getenv("OPENTRANSPORTDATA_API_KEY", None)
    traffic_api_url: str = os.getenv(
        "TRAFFIC_API_URL", "https://api.opentransportdata.swiss/TDP/Soap_Datex2/TrafficSituations/Pull")

    def validate(self) -> None:
        """Optionally check for critical keys on startup."""
        if not self.opentransport_key:
            raise ValueError("OPENTRANSPORTDATA_API_KEY is not set in environment or .env file.")
        if not self.traffic_api_url:
            raise ValueError("TRAFFIC_API_URL is not set in environment or .env file.")


@dataclass(frozen=True)
class Config:
    db: DatabaseConfig = DatabaseConfig()
    api: APIConfig = APIConfig()
    paths: PathConfig = PathConfig()


config = Config()
