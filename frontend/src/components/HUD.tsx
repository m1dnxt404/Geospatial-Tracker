import React from "react";
import type { ConnectionStatus } from "../types";

interface HUDProps {
  aircraftCount: number;
  status: ConnectionStatus;
  lastUpdated: Date | null;
}

const STATUS_COLOR: Record<ConnectionStatus, string> = {
  connected: "#22c55e",
  connecting: "#f59e0b",
  disconnected: "#ef4444",
  error: "#ef4444",
};

const STATUS_LABEL: Record<ConnectionStatus, string> = {
  connected: "LIVE",
  connecting: "CONNECTING",
  disconnected: "OFFLINE",
  error: "ERROR",
};

export const HUD: React.FC<HUDProps> = ({ aircraftCount, status, lastUpdated }) => {
  const color = STATUS_COLOR[status];

  return (
    <div
      style={{
        position: "absolute",
        top: 16,
        left: 16,
        zIndex: 10,
        background: "rgba(15, 23, 42, 0.85)",
        backdropFilter: "blur(8px)",
        border: "1px solid rgba(148, 163, 184, 0.15)",
        borderRadius: 12,
        padding: "14px 18px",
        minWidth: 200,
        fontFamily: "'Courier New', Courier, monospace",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
        <div
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            backgroundColor: color,
            boxShadow: `0 0 6px ${color}`,
            flexShrink: 0,
          }}
        />
        <span style={{ fontSize: 11, letterSpacing: "0.1em", color: "#94a3b8" }}>
          {STATUS_LABEL[status]}
        </span>
      </div>

      <div style={{ fontSize: 13, color: "#cbd5e1", marginBottom: 4 }}>
        WORLD MONITOR
      </div>

      <div style={{ fontSize: 22, fontWeight: 700, color: "#60a5fa", marginBottom: 8 }}>
        ✈ {aircraftCount}
        <span style={{ fontSize: 12, fontWeight: 400, color: "#64748b", marginLeft: 6 }}>
          aircraft
        </span>
      </div>

      {lastUpdated && (
        <div style={{ fontSize: 10, color: "#475569" }}>
          {lastUpdated.toLocaleTimeString()} · 10s refresh
        </div>
      )}
    </div>
  );
};
