import React, { useMemo } from "react";
import { LiveMap } from "./components/LiveMap";
import { HUD } from "./components/HUD";
import { useWebSocket } from "./hooks/useWebSocket";

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN as string;
const WS_URL = (import.meta.env.VITE_WS_URL as string) ?? "ws://localhost:8000/ws/live";

if (!MAPBOX_TOKEN) {
  throw new Error("VITE_MAPBOX_TOKEN is not set. Add it to your .env file.");
}

export default function App(): React.ReactElement {
  const { payload, status } = useWebSocket(WS_URL);

  const lastUpdated = useMemo(
    () => (payload ? new Date(payload.timestamp * 1000) : null),
    [payload]
  );

  return (
    <div style={{ width: "100vw", height: "100vh", position: "relative" }}>
      <LiveMap data={payload?.geojson ?? null} mapboxToken={MAPBOX_TOKEN} />
      <HUD
        aircraftCount={payload?.aircraft_count ?? 0}
        status={status}
        lastUpdated={lastUpdated}
      />
    </div>
  );
}
