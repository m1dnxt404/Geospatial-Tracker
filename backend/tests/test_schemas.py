import pytest
from pydantic import ValidationError
from models.schemas import AircraftPosition, GeoJSONFeatureCollection, LivePayload


def test_aircraft_position_minimal():
    a = AircraftPosition(icao24="abc123")
    assert a.icao24 == "abc123"
    assert a.latitude is None
    assert a.on_ground is False


def test_aircraft_position_full():
    a = AircraftPosition(
        icao24="a1b2c3",
        callsign="UAL123",
        origin_country="United States",
        longitude=-73.9,
        latitude=40.7,
        altitude=10000.0,
        velocity=250.0,
        heading=270.0,
        on_ground=False,
    )
    assert a.callsign == "UAL123"
    assert a.longitude == -73.9


def test_live_payload_timestamp_auto():
    payload = LivePayload(
        geojson=GeoJSONFeatureCollection(features=[]),
        aircraft_count=0,
    )
    assert payload.timestamp > 0
    assert payload.aircraft_count == 0
