import React, { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { GeoJSONFeatureCollection, AircraftProperties } from "../types";

interface LiveMapProps {
  data: GeoJSONFeatureCollection | null;
}

function altitudeColor(props: AircraftProperties): string {
  if (props.on_ground) return "#94a3b8";
  const alt = props.altitude ?? 0;
  if (alt < 1000) return "#22c55e";
  if (alt < 7000) return "#f59e0b";
  return "#ef4444";
}

function buildPopupHTML(props: AircraftProperties): string {
  const label = props.callsign || props.icao24;
  const alt = props.altitude != null ? `${Math.round(props.altitude)} m` : "—";
  const vel = props.velocity != null ? `${Math.round(props.velocity)} m/s` : "—";
  const hdg = props.heading != null ? `${Math.round(props.heading)}°` : "—";
  const groundTag = props.on_ground
    ? '<span style="color:#f59e0b">On ground</span><br/>'
    : "";

  return `
    <div style="font-family:monospace;font-size:12px;line-height:1.7;min-width:160px">
      <strong style="font-size:14px">${label}</strong><br/>
      <span style="color:#888">${props.origin_country}</span>
      <hr style="margin:5px 0;border-color:#ddd"/>
      Altitude: ${alt}<br/>
      Speed: ${vel}<br/>
      Heading: ${hdg}<br/>
      ${groundTag}
    </div>
  `;
}

export const LiveMap: React.FC<LiveMapProps> = ({ data }) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<L.Map | null>(null);
  const layerGroupRef = useRef<L.LayerGroup | null>(null);

  // Initialise map once
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = L.map(containerRef.current, {
      center: [20, 0],
      zoom: 2,
      zoomControl: false,
      minZoom: 2,
    });

    // Carto Dark Matter — free, no API key required
    L.tileLayer(
      "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
      {
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors ' +
          '&copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: "abcd",
        maxZoom: 19,
      }
    ).addTo(map);

    L.control.zoom({ position: "bottomright" }).addTo(map);
    L.control.scale({ position: "bottomleft" }).addTo(map);

    layerGroupRef.current = L.layerGroup().addTo(map);
    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
      layerGroupRef.current = null;
    };
  }, []);

  // Redraw markers on each data update
  useEffect(() => {
    if (!layerGroupRef.current || !data) return;

    layerGroupRef.current.clearLayers();

    for (const feature of data.features) {
      const [lng, lat] = feature.geometry.coordinates;
      const props = feature.properties;

      const marker = L.circleMarker([lat, lng], {
        radius: 6,
        fillColor: altitudeColor(props),
        fillOpacity: 0.9,
        color: "#ffffff",
        weight: 1.5,
      });

      marker.bindPopup(buildPopupHTML(props), { maxWidth: 220 });
      marker.addTo(layerGroupRef.current);
    }
  }, [data]);

  return (
    <div
      ref={containerRef}
      style={{ width: "100%", height: "100%", isolation: "isolate" }}
    />
  );
};
