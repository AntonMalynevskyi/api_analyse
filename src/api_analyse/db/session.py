from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, func, inspect, select
from sqlalchemy.orm import Session, sessionmaker

from api_analyse.db.models import TrafficSituation
from api_analyse.utils.config import config

engine = create_engine(
    config.db.url,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False},
    echo=False,  # Set to True to log raw SQL queries during debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Provides a transactional database session scope."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Creates tables if they do not exist (useful for quick prototyping/testing)."""
    from api_analyse.db.base import Base

    Base.metadata.create_all(bind=engine)


def sqlite_db_path() -> Path:
    return config.paths.data_processed / config.db.db_name


def has_traffic_data() -> bool:
    """True when the SQLite file exists and traffic_situations has at least one row."""
    db_path = sqlite_db_path()
    if not db_path.exists() or db_path.stat().st_size == 0:
        return False

    with get_db() as session:
        inspector = inspect(session.connection())
        if not inspector.has_table(TrafficSituation.__tablename__):
            return False
        count = session.scalar(select(func.count()).select_from(TrafficSituation))
        return (count or 0) > 0
