import logging

from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET
import requests

from api_analyse.config import config

logger = logging.getLogger(__name__)


class DownloadError(Exception):
    """Raised when data retrieval or validation fails."""
    pass


def download_traffic_data(
        url: str = config.api.traffic_api_url,
        output_path: Path = config.paths.data_raw / "traffic" / "traffic_situations.xml",
        if_modified_since: datetime | str | None = None,
        timeout: int = 30,
) -> Path | None:
    """
    Downloads XML traffic data, validates HTTP status and SOAP payload,
    and writes the payload to disk.

    Returns Path if updated file is saved, or None if unchanged (304).
    """
    headers = {
        "User-Agent": "api-analyse/1.0",
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
        response = requests.get(url, headers=headers, timeout=timeout)

        # 304 Not Modified: Data hasn't changed since last run
        if response.status_code == 304:
            logger.info("Traffic data unchanged since last request (304 Not Modified).")
            return None

        # Raise exception for 4xx/5xx HTTP errors
        response.raise_for_status()

        # Validate that payload is valid XML and not a SOAP Fault
        if _is_soap_fault(response.content):
            raise DownloadError("Server returned a SOAP Fault response instead of valid traffic data.")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(response.content)

        logger.info(f"Successfully saved traffic data to {output_path}")
        return output_path

    except requests.RequestException as exc:
        logger.error(f"HTTP request to {url} failed: {exc}")
        raise DownloadError(f"Failed to fetch traffic data: {exc}") from exc


def _is_soap_fault(xml_bytes: bytes) -> bool:
    """Checks whether the XML response body contains a SOAP Fault element."""
    try:
        root = ET.fromstring(xml_bytes)
        # Search for any tag ending with 'Fault' across namespaces
        return any(elem.tag.endswith("Fault") for elem in root.iter())
    except ET.ParseError:
        # Payload is not valid XML (e.g., plain text or HTML error page)
        return True
