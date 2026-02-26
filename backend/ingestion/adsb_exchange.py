import httpx
import logging

from models.schemas import AircraftPosition
from config import settings

logger = logging.getLogger(__name__)

ADSB_MILITARY_URL = "https://api.adsbexchange.com/v2/mil/"

# Known military ICAO hex prefix ranges used as fallback when no API key is set.
# These cover major air forces (USAF, USN, USMC, RAF, French AF, German AF, etc.)
MILITARY_ICAO_PREFIXES = (
    "ae",  # United States military (USAF, USN, USMC)
    "43",  # France military
    "3a",  # Germany military
    "43c", # France additional
    "7c1", # Australia military
    "710", # China military
    "154", # Russia military
)


def _is_military_icao(icao24: str) -> bool:
    """Return True if the ICAO24 hex address matches a known military prefix."""
    return icao24.lower().startswith(MILITARY_ICAO_PREFIXES)


async def fetch_military_aircraft(
    all_aircraft: list[AircraftPosition] | None = None,
) -> list[AircraftPosition]:
    """Fetch military aircraft positions.

    Tries ADS-B Exchange API if ADSB_API_KEY is configured.
    Otherwise filters ``all_aircraft`` (if provided) or falls back to a
    fresh OpenSky fetch.  Passing pre-fetched aircraft avoids a redundant
    API call when the caller already holds the global aircraft list.
    Returns an empty list on failure — never raises.
    """
    if settings.ADSB_API_KEY:
        return await _fetch_from_adsb_exchange(settings.ADSB_API_KEY)
    if all_aircraft is not None:
        military = [a for a in all_aircraft if _is_military_icao(a.icao24)]
        logger.info("Filtered %d military aircraft from pre-fetched data", len(military))
        return military
    return await _fetch_from_opensky_filter()


async def _fetch_from_adsb_exchange(api_key: str) -> list[AircraftPosition]:
    """Fetch from ADS-B Exchange military endpoint."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                ADSB_MILITARY_URL,
                headers={"api-auth": api_key},
            )
            resp.raise_for_status()
            data = resp.json()

        aircraft_list = []
        for ac in data.get("ac") or []:
            try:
                lat = ac.get("lat")
                lon = ac.get("lon")
                if lat is None or lon is None:
                    continue
                aircraft_list.append(AircraftPosition(
                    icao24=ac.get("hex", ""),
                    callsign=(ac.get("flight") or "").strip(),
                    origin_country="",
                    longitude=float(lon),
                    latitude=float(lat),
                    altitude=float(ac["alt_baro"]) * 0.3048 if ac.get("alt_baro") else None,
                    velocity=float(ac["gs"]) * 0.514444 if ac.get("gs") else None,
                    heading=float(ac["track"]) if ac.get("track") else None,
                    on_ground=ac.get("alt_baro") == "ground",
                ))
            except (KeyError, TypeError, ValueError):
                continue

        logger.info("Fetched %d military aircraft from ADS-B Exchange", len(aircraft_list))
        return aircraft_list

    except httpx.TimeoutException:
        logger.error("ADS-B Exchange request timed out")
        return []
    except Exception as exc:
        logger.exception("ADS-B Exchange fetch failed: %s", exc)
        return []


async def _fetch_from_opensky_filter() -> list[AircraftPosition]:
    """Filter the OpenSky global feed for known military ICAO prefixes."""
    from ingestion.opensky import fetch_aircraft
    all_aircraft = await fetch_aircraft()
    military = [a for a in all_aircraft if _is_military_icao(a.icao24)]
    logger.info("Filtered %d military aircraft from OpenSky", len(military))
    return military
