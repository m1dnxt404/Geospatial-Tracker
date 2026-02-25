import httpx
import logging
import time
from math import degrees

from sgp4.api import Satrec, jday

from models.schemas import SatellitePosition

logger = logging.getLogger(__name__)

CELESTRAK_URL = "https://celestrak.org/pub/TLE/active.txt"
MAX_SATELLITES = 2000
CACHE_TTL_SECONDS = 1800  # 30 minutes

_tle_cache: list[tuple[str, str, str]] = []   # (name, line1, line2)
_cache_time: float = 0.0


def _parse_tle_text(text: str) -> list[tuple[str, str, str]]:
    """Parse raw TLE text into (name, line1, line2) tuples."""
    entries = []
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    i = 0
    while i + 2 < len(lines):
        name = lines[i]
        line1 = lines[i + 1]
        line2 = lines[i + 2]
        if line1.startswith("1 ") and line2.startswith("2 "):
            entries.append((name, line1, line2))
            i += 3
        else:
            i += 1
    return entries


def _compute_position(name: str, line1: str, line2: str) -> SatellitePosition | None:
    """Propagate a TLE to the current time and return geodetic position."""
    try:
        sat = Satrec.twoline2rv(line1, line2)
        norad_id = line1[2:7].strip()

        now = time.gmtime()
        jd, fr = jday(now.tm_year, now.tm_mon, now.tm_mday,
                      now.tm_hour, now.tm_min, now.tm_sec)

        e, r, v = sat.sgp4(jd, fr)
        if e != 0 or r is None:
            return None

        # Convert ECI (km) to geodetic manually (simplified spherical Earth)
        x, y, z = r
        vx, vy, vz = v

        lon = degrees(float.__truediv__(__import__('math').atan2(y, x), 1))
        lat = degrees(__import__('math').atan2(z, (x**2 + y**2) ** 0.5))
        alt_km = (x**2 + y**2 + z**2) ** 0.5 - 6371.0
        vel = (vx**2 + vy**2 + vz**2) ** 0.5

        if alt_km < 0 or alt_km > 100_000:
            return None

        import math
        lon_deg = math.degrees(math.atan2(y, x))
        lat_deg = math.degrees(math.atan2(z, math.sqrt(x**2 + y**2)))

        return SatellitePosition(
            norad_id=norad_id,
            name=name,
            longitude=round(lon_deg, 4),
            latitude=round(lat_deg, 4),
            altitude_km=round(alt_km, 1),
            velocity_km_s=round(vel, 3),
        )
    except Exception as exc:
        logger.debug("Skipping satellite %s: %s", name, exc)
        return None


async def fetch_satellites() -> list[SatellitePosition]:
    """Fetch TLE data from CelesTrak (cached 30 min) and compute current positions.

    Returns an empty list on failure — never raises.
    """
    global _tle_cache, _cache_time

    now = time.monotonic()
    if not _tle_cache or (now - _cache_time) > CACHE_TTL_SECONDS:
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.get(
                    CELESTRAK_URL,
                    headers={"User-Agent": "WorldView-Tracker/2.0 (geospatial research)"},
                )
                resp.raise_for_status()
                _tle_cache = _parse_tle_text(resp.text)
                _cache_time = now
                logger.info("Refreshed TLE cache: %d satellites", len(_tle_cache))
        except Exception as exc:
            logger.error("CelesTrak fetch failed: %s", exc)
            if not _tle_cache:
                return []

    entries = _tle_cache[:MAX_SATELLITES]
    positions = [_compute_position(name, l1, l2) for name, l1, l2 in entries]
    result = [p for p in positions if p is not None]
    logger.info("Computed %d satellite positions", len(result))
    return result
