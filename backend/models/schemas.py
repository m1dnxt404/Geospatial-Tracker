from pydantic import BaseModel, Field
from typing import Optional
import time


class AircraftPosition(BaseModel):
    icao24: str
    callsign: str = ""
    origin_country: str = ""
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    altitude: Optional[float] = None
    velocity: Optional[float] = None
    heading: Optional[float] = None
    vertical_rate: Optional[float] = None
    on_ground: bool = False
    last_contact: Optional[int] = None


class SatellitePosition(BaseModel):
    norad_id: str
    name: str
    longitude: float
    latitude: float
    altitude_km: float
    velocity_km_s: float


class EarthquakeEvent(BaseModel):
    id: str
    magnitude: float
    place: str
    longitude: float
    latitude: float
    depth_km: float
    time_ms: int


class GeoJSONPoint(BaseModel):
    type: str = "Point"
    coordinates: list[float]  # [longitude, latitude] or [longitude, latitude, altitude]


class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: GeoJSONPoint
    properties: dict


class GeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: list[GeoJSONFeature]


class WorldPayload(BaseModel):
    aircraft: GeoJSONFeatureCollection
    military: GeoJSONFeatureCollection
    satellites: GeoJSONFeatureCollection
    earthquakes: GeoJSONFeatureCollection
    counts: dict
    timestamp: float = Field(default_factory=time.time)


# Kept for backwards compatibility with existing tests
class LivePayload(BaseModel):
    geojson: GeoJSONFeatureCollection
    aircraft_count: int
    timestamp: float = Field(default_factory=time.time)
