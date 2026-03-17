import asyncio
import logging
import time

import httpx

import cache as app_cache
from config import settings
from ingestion.opensky import _get_bearer_token

logger = logging.getLogger(__name__)

METADATA_URL = "https://opensky-network.org/api/metadata/aircraft/icao/{}"

# Permanent in-memory cache — aircraft type doesn't change, so no TTL needed.
_typecode_cache: dict[str, str] = {}   # icao24 → typecode (empty string = unknown/failed)
_model_cache: dict[str, str] = {}      # icao24 → "Manufacturer Model" (empty string = unknown/failed)
_redis_loaded: bool = False            # True after one-time bulk load from Redis

_rate_limited_until: float = 0.0
_backoff_seconds: float = 60.0
_MAX_RATE_LIMIT_BACKOFF: float = 300.0


async def fetch_new_typecodes(icao24_list: list[str]) -> None:
    """Fetch typecodes for aircraft not yet in cache.

    Capped at settings.METADATA_FETCH_PER_CYCLE requests per call to avoid rate-limiting.
    On any error or 404, caches an empty string to prevent retrying the same aircraft.
    """
    global _redis_loaded

    # One-time bulk load from Redis on first call — restores typecodes across restarts.
    if not _redis_loaded:
        _redis_loaded = True
        stored = await app_cache.hgetall("meta:typecodes")
        if stored:
            _typecode_cache.update(stored)
            logger.info("Loaded %d typecodes from Redis", len(stored))
        stored_models = await app_cache.hgetall("meta:models")
        if stored_models:
            _model_cache.update(stored_models)
            logger.info("Loaded %d model names from Redis", len(stored_models))

    now = time.monotonic()
    if now < _rate_limited_until:
        logger.info("OpenSky metadata rate-limited — skipping for %ds", int(_rate_limited_until - now))
        return

    unknown = [i for i in icao24_list if i and i not in _typecode_cache]
    if not unknown:
        return

    to_fetch = unknown[:settings.METADATA_FETCH_PER_CYCLE]
    async with httpx.AsyncClient(timeout=5.0) as client:
        await asyncio.gather(
            *[_fetch_one(client, icao24) for icao24 in to_fetch],
            return_exceptions=True,
        )
    logger.debug(
        "Metadata: resolved %d typecodes. Cache size: %d",
        len(to_fetch),
        len(_typecode_cache),
    )


async def _fetch_one(client: httpx.AsyncClient, icao24: str) -> None:
    url = METADATA_URL.format(icao24.lower())
    try:
        if settings.OPENSKY_CLIENT_ID and settings.OPENSKY_CLIENT_SECRET:
            token = await _get_bearer_token()
            resp = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        elif settings.OPENSKY_USERNAME and settings.OPENSKY_PASSWORD:
            resp = await client.get(url, auth=(settings.OPENSKY_USERNAME, settings.OPENSKY_PASSWORD))
        else:
            resp = await client.get(url)

        if resp.status_code == 200:
            data = resp.json()
            typecode = (data.get("typecode") or "").strip().upper()
            _typecode_cache[icao24] = typecode
            await app_cache.hset("meta:typecodes", icao24, typecode)
            manufacturer = (data.get("manufacturername") or "").strip()
            model = (data.get("model") or "").strip()
            model_name = f"{manufacturer} {model}".strip() if (manufacturer or model) else ""
            _model_cache[icao24] = model_name
            await app_cache.hset("meta:models", icao24, model_name)
        elif resp.status_code == 429:
            global _rate_limited_until, _backoff_seconds
            _rate_limited_until = time.monotonic() + _backoff_seconds
            logger.warning("Rate limited by OpenSky metadata — backing off for %ds", int(_backoff_seconds))
            _backoff_seconds = min(_backoff_seconds * 2, _MAX_RATE_LIMIT_BACKOFF)
            # Do not cache empty string — allow retry after cooldown
        else:
            _typecode_cache[icao24] = ""
            _model_cache[icao24] = ""
    except Exception:
        _typecode_cache[icao24] = ""
        _model_cache[icao24] = ""


def get_typecode(icao24: str) -> str:
    return _typecode_cache.get(icao24, "")


def get_model_name(icao24: str) -> str:
    """Return the full model name (e.g. 'Boeing 737-800'), or '' if not yet fetched."""
    return _model_cache.get(icao24, "")
