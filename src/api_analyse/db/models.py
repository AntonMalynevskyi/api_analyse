from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, Float, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from api_analyse.db.base import Base


class TrafficSituation(Base):
    __tablename__ = "traffic_situations"

    record_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    situation_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    situation_version: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    record_version: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    record_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    subtype: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_cancelled: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    validity_status: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    comments: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    location: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class TmcLocation(Base):
    __tablename__ = "tmc_locations"

    location_code: Mapped[int] = mapped_column(primary_key=True)
    country_code: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    table_number: Mapped[Optional[int]] = mapped_column(nullable=True)
    road_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
