export interface GeoJSONPoint {
  type: "Point";
  coordinates: [number, number] | [number, number, number];
}

export interface AircraftProperties {
  icao24: string;
  callsign: string;
  origin_country: string;
  altitude: number | null;
  velocity: number | null;
  heading: number | null;
  vertical_rate: number | null;
  on_ground: boolean;
}

export interface SatelliteProperties {
  norad_id: string;
  name: string;
  altitude_km: number;
  velocity_km_s: number;
}

export interface EarthquakeProperties {
  id: string;
  magnitude: number;
  place: string;
  depth_km: number;
  time_ms: number;
}

export interface GeoJSONFeature {
  type: "Feature";
  geometry: GeoJSONPoint;
  properties: Record<string, unknown>;
}

export interface GeoJSONFeatureCollection {
  type: "FeatureCollection";
  features: GeoJSONFeature[];
}

export interface WorldPayload {
  aircraft: GeoJSONFeatureCollection;
  military: GeoJSONFeatureCollection;
  satellites: GeoJSONFeatureCollection;
  earthquakes: GeoJSONFeatureCollection;
  counts: {
    aircraft: number;
    military: number;
    satellites: number;
    earthquakes: number;
  };
  timestamp: number;
}

export interface LayerVisibility {
  aircraft: boolean;
  military: boolean;
  satellites: boolean;
  earthquakes: boolean;
}

export type VisualMode = "normal" | "crt" | "nightvision" | "flir";

export type ConnectionStatus = "connecting" | "connected" | "disconnected" | "error";
