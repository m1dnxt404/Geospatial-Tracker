import httpx
import logging
from typing import Optional

from models.schemas import AircraftPosition
from config import settings

logger = logging.getLogger(__name__)

OPENSKY_URL = "https://opensky-network.org/api/states/all"

# OpenSky state vector field indices (documented at opensky-network.org/apidoc)
_IDX_ICAO24 = 0
_IDX_CALLSIGN = 1
_IDX_ORIGIN_COUNTRY = 2
_IDX_LAST_CONTACT = 4
_IDX_LONGITUDE = 5
_IDX_LATITUDE = 6
_IDX_BARO_ALTITUDE = 7
_IDX_ON_GROUND = 8
_IDX_VELOCITY = 9
_IDX_HEADING = 10
_IDX_VERTICAL_RATE = 11


def _parse_state_vector(state: list) -> Optional[AircraftPosition]:
    """Parse a single OpenSky state vector into an AircraftPosition.

    Returns None if the aircraft has no position data.
    """
    try:
        longitude = state[_IDX_LONGITUDE]
        latitude = state[_IDX_LATITUDE]
        if longitude is None or latitude is None:
            return None

        return AircraftPosition(
            icao24=state[_IDX_ICAO24] or "",
            callsign=(state[_IDX_CALLSIGN] or "").strip(),
            origin_country=state[_IDX_ORIGIN_COUNTRY] or "",
            longitude=longitude,
            latitude=latitude,
            altitude=state[_IDX_BARO_ALTITUDE],
            velocity=state[_IDX_VELOCITY],
            heading=state[_IDX_HEADING],
            vertical_rate=state[_IDX_VERTICAL_RATE],
            on_ground=bool(state[_IDX_ON_GROUND]),
            last_contact=state[_IDX_LAST_CONTACT],
        )
    except (IndexError, TypeError) as exc:
        logger.warning("Skipping malformed state vector: %s", exc)
        return None


async def fetch_aircraft() -> list[AircraftPosition]:
    """Fetch live aircraft positions from OpenSky for the configured bounding box.

    Returns an empty list on any network failure — never raises.
    Rate limits: 5 req/10s anonymous, higher with credentials.
    """
    params = {
        "lamin": settings.BBOX_LAMIN,
        "lomin": settings.BBOX_LOMIN,
        "lamax": settings.BBOX_LAMAX,
        "lomax": settings.BBOX_LOMAX,
    }

    auth = None
    if settings.OPENSKY_USERNAME and settings.OPENSKY_PASSWORD:
        auth = (settings.OPENSKY_USERNAME, settings.OPENSKY_PASSWORD)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(OPENSKY_URL, params=params, auth=auth)
            response.raise_for_status()
            data = response.json()

        states = data.get("states") or []
        aircraft = [_parse_state_vector(s) for s in states]
        result = [a for a in aircraft if a is not None]

        logger.info("Fetched %d aircraft from OpenSky", len(result))
        return result

    except httpx.TimeoutException:
        logger.error("OpenSky request timed out")
        return []
    except httpx.HTTPStatusError as exc:
        logger.error("OpenSky HTTP %s: %s", exc.response.status_code, exc.response.text[:200])
        return []
    except Exception as exc:
        logger.exception("Unexpected error fetching aircraft: %s", exc)
        return []
