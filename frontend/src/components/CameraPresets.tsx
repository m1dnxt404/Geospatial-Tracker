import React from "react";
import * as Cesium from "cesium";

interface CameraPresetsProps {
  viewer: Cesium.Viewer | null;
}

interface CityPreset {
  label: string;
  lon: number;
  lat: number;
  altM: number;
}

const PRESETS: CityPreset[] = [
  { label: "New York",   lon: -74.006,  lat: 40.713,  altM: 800_000 },
  { label: "London",     lon: -0.128,   lat: 51.507,  altM: 800_000 },
  { label: "Tokyo",      lon: 139.691,  lat: 35.689,  altM: 800_000 },
  { label: "Dubai",      lon: 55.271,   lat: 25.205,  altM: 800_000 },
  { label: "Los Angeles",lon: -118.243, lat: 34.052,  altM: 800_000 },
  { label: "Sydney",     lon: 151.209,  lat: -33.868, altM: 800_000 },
  { label: "Singapore",  lon: 103.820,  lat: 1.352,   altM: 800_000 },
  { label: "Cairo",      lon: 31.233,   lat: 30.033,  altM: 800_000 },
];

export function CameraPresets({ viewer }: CameraPresetsProps): React.ReactElement {
  const flyTo = (preset: CityPreset) => {
    if (!viewer || viewer.isDestroyed()) return;
    viewer.camera.flyTo({
      destination: Cesium.Cartesian3.fromDegrees(preset.lon, preset.lat, preset.altM),
      duration: 2.0,
    });
  };

  return (
    <div style={styles.container}>
      <span style={styles.label}>JUMP TO</span>
      <div style={styles.row}>
        {PRESETS.map((preset) => (
          <button
            key={preset.label}
            style={styles.btn}
            onClick={() => flyTo(preset)}
            title={preset.label}
          >
            {preset.label}
          </button>
        ))}
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    position: "absolute",
    bottom: 16,
    left: "50%",
    transform: "translateX(-50%)",
    zIndex: 1000,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 6,
  },
  label: {
    fontSize: 9,
    letterSpacing: "0.2em",
    color: "#475569",
    fontFamily: "'Courier New', Courier, monospace",
  },
  row: {
    display: "flex",
    gap: 6,
    flexWrap: "wrap",
    justifyContent: "center",
  },
  btn: {
    backgroundColor: "rgba(2, 6, 23, 0.80)",
    border: "1px solid #1E293B",
    borderRadius: 4,
    color: "#94A3B8",
    cursor: "pointer",
    fontFamily: "'Courier New', Courier, monospace",
    fontSize: 10,
    letterSpacing: "0.06em",
    padding: "5px 10px",
    backdropFilter: "blur(8px)",
    transition: "background-color 0.15s, color 0.15s, border-color 0.15s",
  },
};
