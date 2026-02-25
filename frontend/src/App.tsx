import React, { useCallback, useMemo, useRef, useState } from "react";
import * as Cesium from "cesium";
import GlobeView from "./components/GlobeView";
import { ControlPanel } from "./components/ControlPanel";
import { CameraPresets } from "./components/CameraPresets";
import { useWebSocket } from "./hooks/useWebSocket";
import type { LayerVisibility, VisualMode } from "./types";

const WS_URL = (import.meta.env.VITE_WS_URL as string) ?? "ws://localhost:8000/ws/live";

const DEFAULT_LAYERS: LayerVisibility = {
  aircraft: true,
  military: true,
  satellites: true,
  earthquakes: true,
};

export default function App(): React.ReactElement {
  const { payload, status } = useWebSocket(WS_URL);

  const [layers, setLayers] = useState<LayerVisibility>(DEFAULT_LAYERS);
  const [visualMode, setVisualMode] = useState<VisualMode>("normal");
  const viewerRef = useRef<Cesium.Viewer | null>(null);

  const lastUpdated = useMemo(
    () => (payload ? new Date(payload.timestamp * 1000) : null),
    [payload]
  );

  const counts = useMemo(
    () =>
      payload?.counts ?? {
        aircraft: 0,
        military: 0,
        satellites: 0,
        earthquakes: 0,
      },
    [payload]
  );

  const handleLayerToggle = useCallback((layer: keyof LayerVisibility) => {
    setLayers((prev) => ({ ...prev, [layer]: !prev[layer] }));
  }, []);

  const handleViewerReady = useCallback((viewer: Cesium.Viewer) => {
    viewerRef.current = viewer;
  }, []);

  return (
    <div style={{ width: "100vw", height: "100vh", position: "relative", overflow: "hidden" }}>
      <GlobeView
        payload={payload}
        layers={layers}
        visualMode={visualMode}
        onViewerReady={handleViewerReady}
      />
      <ControlPanel
        counts={counts}
        status={status}
        lastUpdated={lastUpdated}
        layers={layers}
        onLayerToggle={handleLayerToggle}
        visualMode={visualMode}
        onVisualModeChange={setVisualMode}
      />
      <CameraPresets viewer={viewerRef.current} />
    </div>
  );
}
