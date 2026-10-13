import logging
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET
import requests
import typer

from api_analyse.utils.config import config

logger = logging.getLogger(__name__)

app = typer.Typer()


class DownloadError(Exception):
    """Custom exception raised when road data retrieval or validation fails."""
    pass


def download_traffic_data(
        if_modified_since: datetime = None,
        timeout: int = 30,
        api_key: str = config.api.opentransport_key
) -> Path | None:
    """
    Requires OpenTransport API key in .env
    Downloads DATEX II traffic XML from OpenTransportData Swiss using SOAP POST request.
    Returns the destination Path if new data is saved, or None if unchanged (HTTP 304).
    """
    if not api_key:
        raise DownloadError("Missing OpenTransport API key in .env to download traffic data.")

    traffic_dir = config.paths.data_raw / "traffic"
    request_body_path = traffic_dir / "VM_request_body.xml"
    output_path = traffic_dir / "traffic_situations.xml"

    if not request_body_path.exists():
        raise DownloadError(f"SOAP request body template missing at {request_body_path}")

    # Standardize Authorization header format
    auth_header = api_key if api_key.startswith("Bearer ") else f"Bearer {api_key}"

    headers = {
        "Authorization": auth_header,
        "SOAPAction": "http://opentransportdata.swiss/TDP/Soap_Datex2/Pull/v1/pullTrafficMessages",
        "Content-Type": "text/xml; charset=utf-8",
        "Accept": "application/xml, text/xml",
    }

    # Format timestamp to standard HTTP-date (RFC 1123) if a datetime object is passed
    if isinstance(if_modified_since, datetime):
        headers["If-Modified-Since"] = if_modified_since.astimezone(timezone.utc).strftime(
            "%a, %d %b %Y %H:%M:%S GMT"
        )
    elif isinstance(if_modified_since, str):
        headers["If-Modified-Since"] = if_modified_since

    try:
        data = request_body_path.read_bytes()
    except OSError as exc:
        raise DownloadError(f"Failed to read SOAP request payload: {exc}") from exc

    url = "https://api.opentransportdata.swiss/TDP/Soap_Datex2/TrafficSituations/Pull"

    try:
        response = requests.post(url, headers=headers, data=data, timeout=timeout)

        if response.status_code == 304:
            logger.info("Traffic data unchanged since last request (304 Not Modified).")
            return None

        response.raise_for_status()

        if _is_soap_fault(response.content):
            raise DownloadError("Server returned a SOAP Fault or invalid XML response body.")

        traffic_dir.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(response.content)

        logger.info(f"Successfully saved traffic data to {output_path}")
        return output_path

    except requests.RequestException as exc:
        logger.error(f"HTTP POST request to {url} failed: {exc}")
        raise DownloadError(f"Failed to fetch road data: {exc}") from exc


def _is_soap_fault(xml_bytes: bytes) -> bool:
    """Checks whether the XML response body contains a SOAP Fault element or invalid XML."""
    try:
        root = ET.fromstring(xml_bytes)
        return any(elem.tag.endswith("Fault") for elem in root.iter())
    except ET.ParseError:
        return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        download_traffic_data()
    except DownloadError as err:
        logger.error(err)
