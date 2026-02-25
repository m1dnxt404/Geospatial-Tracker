import React, { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import type { GeoJSONFeatureCollection } from "../types";

interface LiveMapProps {
  data: GeoJSONFeatureCollection | null;
  mapboxToken: string;
}

const SOURCE_ID = "aircraft";
const LAYER_ICON = "aircraft-icons";
const LAYER_LABEL = "aircraft-labels";

export const LiveMap: React.FC<LiveMapProps> = ({ data, mapboxToken }) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const popupRef = useRef<mapboxgl.Popup | null>(null);
  const [mapReady, setMapReady] = useState(false);

  // Initialise map once
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    mapboxgl.accessToken = mapboxToken;

    const map = new mapboxgl.Map({
      container: containerRef.current,
      style: "mapbox://styles/mapbox/dark-v11",
      center: [-74.006, 40.7128],
      zoom: 10,
    });

    map.addControl(new mapboxgl.NavigationControl(), "bottom-right");
    map.addControl(new mapboxgl.ScaleControl(), "bottom-left");

    map.on("load", () => {
      map.addSource(SOURCE_ID, {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });

      // Aircraft symbol layer — rotated plane icon
      map.addLayer({
        id: LAYER_ICON,
        type: "circle",
        source: SOURCE_ID,
        paint: {
          "circle-radius": 6,
          "circle-color": [
            "case",
            ["==", ["get", "on_ground"], true], "#94a3b8",
            [
              "interpolate",
              ["linear"],
              ["coalesce", ["get", "altitude"], 0],
              0, "#22c55e",
              5000, "#f59e0b",
              12000, "#ef4444",
            ],
          ],
          "circle-stroke-width": 1.5,
          "circle-stroke-color": "#ffffff",
          "circle-opacity": 0.9,
        },
      });

      // Callsign labels
      map.addLayer({
        id: LAYER_LABEL,
        type: "symbol",
        source: SOURCE_ID,
        layout: {
          "text-field": ["get", "callsign"],
          "text-font": ["DIN Offc Pro Medium", "Arial Unicode MS Bold"],
          "text-size": 10,
          "text-offset": [0, 1.4],
          "text-anchor": "top",
          "text-optional": true,
        },
        paint: {
          "text-color": "#93c5fd",
          "text-halo-color": "#0f172a",
          "text-halo-width": 1.5,
        },
      });

      // Click popup
      map.on("click", LAYER_ICON, (e) => {
        if (!e.features || !e.features[0]) return;
        const props = e.features[0].properties as Record<string, unknown>;
        const coords = (e.features[0].geometry as GeoJSON.Point).coordinates as [number, number];

        popupRef.current?.remove();
        popupRef.current = new mapboxgl.Popup({ closeButton: true, maxWidth: "240px" })
          .setLngLat(coords)
          .setHTML(
            `<div style="font-family:monospace;font-size:12px;line-height:1.6">
              <strong style="font-size:14px">${props["callsign"] || props["icao24"]}</strong><br/>
              <span style="color:#94a3b8">${props["origin_country"]}</span><br/>
              <hr style="border-color:#334155;margin:6px 0"/>
              Altitude: ${props["altitude"] != null ? Math.round(Number(props["altitude"])) + " m" : "—"}<br/>
              Speed: ${props["velocity"] != null ? Math.round(Number(props["velocity"])) + " m/s" : "—"}<br/>
              Heading: ${props["heading"] != null ? Math.round(Number(props["heading"])) + "°" : "—"}<br/>
              ${props["on_ground"] ? '<span style="color:#f59e0b">On ground</span>' : ""}
            </div>`
          )
          .addTo(map);
      });

      map.on("mouseenter", LAYER_ICON, () => {
        map.getCanvas().style.cursor = "pointer";
      });
      map.on("mouseleave", LAYER_ICON, () => {
        map.getCanvas().style.cursor = "";
      });

      setMapReady(true);
    });

    mapRef.current = map;

    return () => {
      popupRef.current?.remove();
      map.remove();
      mapRef.current = null;
      setMapReady(false);
    };
  }, [mapboxToken]);

  // Update source data when payload arrives
  useEffect(() => {
    if (!mapReady || !mapRef.current || !data) return;
    const source = mapRef.current.getSource(SOURCE_ID) as mapboxgl.GeoJSONSource | undefined;
    source?.setData(data as unknown as GeoJSON.FeatureCollection);
  }, [mapReady, data]);

  return <div ref={containerRef} style={{ width: "100%", height: "100%" }} />;
};
