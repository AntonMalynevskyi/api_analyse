from collections.abc import Generator
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

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