import xml.etree.ElementTree as ET
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from sqlalchemy import select, inspect
from api_analyse.db import TrafficSituation, TmcLocation, get_db, init_db
from api_analyse.parsers import load_tmc_locations
from api_analyse.utils.config import config

NAMESPACES = {
    "soap": "http://schemas.xmlsoap.org/soap/envelope/",
    "dx": "http://datex2.eu/schema/2/2_0",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}

XSI_TYPE = "{http://www.w3.org/2001/XMLSchema-instance}type"


def parse_locations(record_elem: ET.Element) -> dict:
    loc_elem = record_elem.find("dx:groupOfLocations", NAMESPACES)
    if loc_elem is None:
        return {}
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
            if text:
                comments.setdefault(comment_type, {})[lang] = text
    return comments


def parse_datex2_xml(
        xml_path: str | Path,
        tmc_lookup: dict[int, tuple[float, float]] | None = None,
) -> pd.DataFrame:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    situations_data = []

    for situation in root.findall(".//dx:situation", NAMESPACES):
        sit_id = situation.attrib.get("id")
        sit_version = situation.attrib.get("version")
        for record in situation.findall("dx:situationRecord", NAMESPACES):
            validity = record.find("dx:validity", NAMESPACES)
            location_dict = parse_locations(record)

            start_str = getattr(validity.find(".//dx:overallStartTime", NAMESPACES), "text", None) if validity else None
            end_str = getattr(validity.find(".//dx:endOfPeriod", NAMESPACES), "text", None) if validity else None

            latitude, longitude = None, None
            if tmc_lookup and "alert_c" in location_dict:
                primary_code_str = location_dict["alert_c"].get("primary_location_code")
                if primary_code_str is not None:
                    try:
                        code = int(primary_code_str)
                        if code in tmc_lookup:
                            latitude, longitude = tmc_lookup[code]
                    except (ValueError, TypeError):
                        pass

            record_payload = {
                "record_id": record.attrib.get("id"),
                "situation_id": sit_id,
                "situation_version": sit_version,
                "record_version": record.attrib.get("version"),
                "record_type": record.attrib.get(XSI_TYPE, "").split(":")[-1],
                "subtype": (
                        getattr(record.find("dx:abnormalTrafficType", NAMESPACES), "text", None)
                        or getattr(record.find("dx:roadMaintenanceType", NAMESPACES), "text", None)
                        or getattr(record.find("dx:roadOrCarriagewayOrLaneManagementType", NAMESPACES), "text", None)
                        or getattr(record.find("dx:carParkStatus", NAMESPACES), "text", None)
                ),
                "is_cancelled": getattr(record.find(".//dx:lifeCycleManagement/dx:cancel", NAMESPACES), "text",
                                        "false") == "true",
                "validity_status": getattr(validity.find("dx:validityStatus", NAMESPACES), "text",
                                           None) if validity else None,
                "start_time": datetime.fromisoformat(start_str) if start_str else None,
                "end_time": datetime.fromisoformat(end_str) if end_str else None,

                "comments": json.dumps(parse_comments(record)),
                "location": json.dumps(location_dict),

                "latitude": latitude,
                "longitude": longitude,
            }
            situations_data.append(record_payload)

    return pd.DataFrame(situations_data)


def save_road_data(xml_path: Path = config.paths.data_raw / "traffic" / "traffic_situations.xml") -> None:
    with get_db() as session:
        inspector = inspect(session.connection())

        if not inspector.has_table(TmcLocation.__tablename__):
            load_tmc_locations()
            print("Warning: 'tmc_locations' table not found. Creating new one and filling.")

        tmc_stmt = select(TmcLocation.location_code, TmcLocation.latitude, TmcLocation.longitude).where(
            TmcLocation.latitude.is_not(None),
            TmcLocation.longitude.is_not(None),
        )
        tmc_rows = session.execute(tmc_stmt).all()
        tmc_lookup = {row.location_code: (row.latitude, row.longitude) for row in tmc_rows}

        df = parse_datex2_xml(xml_path, tmc_lookup=tmc_lookup)

        if not df.empty:
            if inspector.has_table("traffic_situations"):
                existing_ids_stmt = select(TrafficSituation.record_id)
                existing_ids = set(session.execute(existing_ids_stmt).scalars().all())
                new_df = df[~df["record_id"].isin(existing_ids)]
            else:
                new_df = df

            if not new_df.empty:
                new_df.to_sql(
                    name="traffic_situations",
                    con=session.connection(),
                    if_exists="append",
                    index=False,
                    chunksize=1000
                )
                session.commit()
                print(f"Successfully appended {len(new_df)} new records (skipped {len(df) - len(new_df)} existing).")
            else:
                print(f"No new records to append. All {len(df)} records are already in the database.")
