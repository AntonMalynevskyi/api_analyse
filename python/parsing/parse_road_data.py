import os
import xml.etree.ElementTree as ET
from pathlib import Path
from dotenv import load_dotenv

from sqlalchemy import create_engine, Column, String, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.orm import declarative_base, sessionmaker

# Загружаем переменные окружения
load_dotenv()

# --- Настройка SQLAlchemy ---
Base = declarative_base()


class TrafficSituation(Base):
    __tablename__ = 'traffic_situations'

    record_id = Column(String(128), primary_key=True)
    situation_id = Column(String(128))
    situation_version = Column(String(16))
    record_version = Column(String(16))
    record_type = Column(String(64))
    subtype = Column(String(64))
    is_cancelled = Column(Boolean)
    validity_status = Column(String(64))
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    comments = Column(JSONB)
    location = Column(JSONB)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# --- Логика парсинга DATEX II ---
NAMESPACES = {
    "soap": "http://schemas.xmlsoap.org/soap/envelope/",
    "dx": "http://datex2.eu/schema/2/2_0",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}
XSI_TYPE = "{http://www.w3.org/2001/XMLSchema-instance}type"


def parse_locations(record_elem: ET.Element) -> dict:
    loc_elem = record_elem.find("dx:groupOfLocations", NAMESPACES)
    if loc_elem is None: return {}
    location_data = {"type": loc_elem.attrib.get(XSI_TYPE, "").split(":")[-1]}
    alertc_elem = loc_elem.find(".//dx:alertCLinear", NAMESPACES) or loc_elem.find(".//dx:alertCPoint", NAMESPACES)
    if alertc_elem is not None:
        dir_elem = alertc_elem.find(".//dx:alertCDirectionCoded", NAMESPACES)
        primary_code = alertc_elem.find(".//dx:alertCMethod4PrimaryPointLocation//dx:specificLocation", NAMESPACES)
        secondary_code = alertc_elem.find(".//dx:alertCMethod4SecondaryPointLocation//dx:specificLocation", NAMESPACES)
        location_data["alert_c"] = {
            "table_number": getattr(alertc_elem.find("dx:alertCLocationTableNumber", NAMESPACES), "text", None),
            "table_version": getattr(alertc_elem.find("dx:alertCLocationTableVersion", NAMESPACES), "text", None),
            "direction": getattr(dir_elem, "text", None),
            "primary_location_code": getattr(primary_code, "text", None),
            "secondary_location_code": getattr(secondary_code, "text", None),
        }
    return location_data


def parse_comments(record_elem: ET.Element) -> dict:
    comments = {}
    for comment_node in record_elem.findall("dx:generalPublicComment", NAMESPACES):
        comment_type_elem = comment_node.find("dx:commentType", NAMESPACES)
        comment_type = comment_type_elem.text if comment_type_elem is not None else "general"
        for val in comment_node.findall(".//dx:values/dx:value", NAMESPACES):
            lang = val.attrib.get("lang", "default")
            text = val.text.strip() if val.text else ""
            if text: comments.setdefault(comment_type, {})[lang] = text
    return comments


def parse_datex2_xml(xml_path: str | Path) -> list[dict]:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    situations_data = []

    for situation in root.findall(".//dx:situation", NAMESPACES):
        sit_id = situation.attrib.get("id")
        sit_version = situation.attrib.get("version")

        for record in situation.findall("dx:situationRecord", NAMESPACES):
            validity = record.find("dx:validity", NAMESPACES)

            # Собираем словарь данных (JSON-сериализация для comments и location больше не нужна,
            # SQLAlchemy и psycopg2 сами конвертируют dict в JSONB)
            record_payload = {
                "record_id": record.attrib.get("id"),
                "situation_id": sit_id,
                "situation_version": sit_version,
                "record_version": record.attrib.get("version"),
                "record_type": record.attrib.get(XSI_TYPE, "").split(":")[-1],
                "subtype": (
                        getattr(record.find("dx:abnormalTrafficType", NAMESPACES), "text", None) or
                        getattr(record.find("dx:roadMaintenanceType", NAMESPACES), "text", None) or
                        getattr(record.find("dx:roadOrCarriagewayOrLaneManagementType", NAMESPACES), "text", None) or
                        getattr(record.find("dx:carParkStatus", NAMESPACES), "text", None)
                ),
                "is_cancelled": getattr(record.find(".//dx:lifeCycleManagement/dx:cancel", NAMESPACES), "text",
                                        "false") == "true",
                "validity_status": getattr(validity.find("dx:validityStatus", NAMESPACES), "text",
                                           None) if validity else None,
                "start_time": getattr(validity.find(".//dx:overallStartTime", NAMESPACES), "text",
                                      None) if validity else None,
                "end_time": getattr(validity.find(".//dx:endOfPeriod", NAMESPACES), "text", None) if validity else None,
                "comments": parse_comments(record),  # Передаем как dict
                "location": parse_locations(record),  # Передаем как dict
            }
            situations_data.append(record_payload)
    return situations_data


def save_to_postgres_alchemy(records: list[dict], db_url: str):
    """Использует SQLAlchemy для создания таблиц и выполнения UPSERT."""

    # Инициализация подключения
    engine = create_engine(db_url)

    # Создаем таблицы, если их нет
    Base.metadata.create_all(engine)

    # Создаем сессию
    Session = sessionmaker(bind=engine)

    with Session() as session:
        try:
            # Формируем инструкцию INSERT
            stmt = insert(TrafficSituation).values(records)

            # Определяем, какие колонки обновлять при конфликте (ON CONFLICT DO UPDATE)
            update_dict = {
                c.name: c for c in stmt.excluded
                if c.name not in ('record_id', 'situation_id')  # Не обновляем первичные ключи
            }

            # Добавляем правило конфликта (по record_id)
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=['record_id'],
                set_=update_dict
            )

            # Выполняем и коммитим
            session.execute(upsert_stmt)
            session.commit()
            print(f"Successfully upserted {len(records)} records into PostgreSQL via SQLAlchemy.")

        except Exception as e:
            print(f"Database error: {e}")
            session.rollback()


if __name__ == "__main__":
    # 1. Парсинг XML
    parsed_records = parse_datex2_xml("../../traffic/traffic_situations.xml")

    # 2. Формирование строки подключения из .env
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    db = os.getenv("POSTGRES_DB")
    host = "localhost"
    port = "5432"

    db_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"

    # 3. Сохранение в БД
    if parsed_records:
        save_to_postgres_alchemy(parsed_records, db_url)