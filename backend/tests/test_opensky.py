import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from ingestion.opensky import fetch_aircraft, _parse_state_vector


def _make_state(icao="a1b2c3", lat=40.7, lon=-73.9, callsign="UAL123 "):
    """Build a minimal OpenSky state vector list."""
    return [icao, callsign, "United States", 1700000000, 1700000001,
            lon, lat, 10000.0, False, 250.0, 270.0, 0.0]


def test_parse_state_vector_valid():
    sv = _make_state()
    aircraft = _parse_state_vector(sv)
    assert aircraft is not None
    assert aircraft.icao24 == "a1b2c3"
    assert aircraft.callsign == "UAL123"  # stripped


def test_parse_state_vector_no_position():
    sv = _make_state()
    sv[5] = None  # longitude
    assert _parse_state_vector(sv) is None


def test_parse_state_vector_no_latitude():
    sv = _make_state()
    sv[6] = None  # latitude
    assert _parse_state_vector(sv) is None


def test_parse_state_vector_malformed():
    assert _parse_state_vector([]) is None


@pytest.mark.asyncio
async def test_fetch_aircraft_timeout():
    with patch("ingestion.opensky.httpx.AsyncClient") as mock_cls:
        instance = MagicMock()
        instance.__aenter__ = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        mock_cls.return_value = instance
        result = await fetch_aircraft()
    assert result == []


@pytest.mark.asyncio
async def test_fetch_aircraft_http_error():
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.text = "Too Many Requests"

    with patch("ingestion.opensky.httpx.AsyncClient") as mock_cls:
        instance = MagicMock()
        get_mock = AsyncMock()
        get_mock.return_value = mock_response
        mock_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError("429", request=MagicMock(), response=mock_response)
        )
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        instance.get = get_mock
        mock_cls.return_value = instance
        result = await fetch_aircraft()
    assert result == []


@pytest.mark.asyncio
async def test_fetch_aircraft_success():
    mock_data = {
        "states": [
            _make_state("abc", 40.7, -73.9, "UAL1  "),
            _make_state("xyz", 40.8, -74.0, "DAL2  "),
        ]
    }
    mock_response = MagicMock()
    mock_response.json = MagicMock(return_value=mock_data)
    mock_response.raise_for_status = MagicMock()

    with patch("ingestion.opensky.httpx.AsyncClient") as mock_cls:
        instance = MagicMock()
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        instance.get = AsyncMock(return_value=mock_response)
        mock_cls.return_value = instance
        result = await fetch_aircraft()

    assert len(result) == 2
    assert result[0].icao24 == "abc"
    assert result[1].callsign == "DAL2"
