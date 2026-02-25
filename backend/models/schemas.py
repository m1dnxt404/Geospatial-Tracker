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


class GeoJSONPoint(BaseModel):
    type: str = "Point"
    coordinates: list[float]  # [longitude, latitude]


class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: GeoJSONPoint
    properties: dict


class GeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: list[GeoJSONFeature]


class LivePayload(BaseModel):
    geojson: GeoJSONFeatureCollection
    aircraft_count: int
    timestamp: float = Field(default_factory=time.time)
