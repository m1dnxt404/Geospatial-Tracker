# WorldView — Real-Time 3D Geospatial Surveillance Platform

A live 3D geospatial tracker that displays **aircraft, military flights, satellites, and earthquakes** on a rotating globe in real time. Built with FastAPI (WebSocket backend) and React + CesiumJS (3D frontend). Includes CRT, Night Vision, and FLIR thermal visual modes.

**Running cost: $0 — no API keys, no accounts required.**

---

## Architecture

```text
CelesTrak TLE   OpenSky   ADS-B Exchange   USGS Earthquakes
      │             │            │                 │
      └─────────────▼────────────▼─────────────────▼──────┐
                       FastAPI Backend                      │
           ingestion/opensky.py      — civil aircraft       │
           ingestion/adsb_exchange.py — military aircraft   │
           ingestion/celestrak.py   — satellite positions   │
           ingestion/usgs.py        — earthquake events     │
                                                            │
           broadcast_loop() → WorldPayload (4× GeoJSON)     │
      ┌────────────────────────────────────────────────────┘
      │  WebSocket /ws/live
      ▼
React Frontend
  GlobeView.tsx  (CesiumJS 3D globe, CartoDB dark tiles)
  ├── Aircraft layer   — white/cyan dots coloured by altitude
  ├── Military layer   — red dots (ADS-B Exchange or ICAO filter)
  ├── Satellite layer  — cyan dots at real orbital altitude
  ├── Earthquake layer — orange/red dots sized by magnitude
  └── PostProcessStage — CRT / Night Vision / FLIR shaders
  ControlPanel.tsx — layer toggles + visual mode buttons
  CameraPresets.tsx — one-click flyTo for 8 world cities
```

---

## Data Sources

| Layer | Source | Endpoint | Cost | Refresh |
| --- | --- | --- | --- | --- |
| Aircraft | OpenSky Network | `/api/states/all` | Free | 10 s |
| Military | ADS-B Exchange | `/v2/mil/` (fallback: ICAO prefix filter) | Free | 10 s |
| Satellites | CelesTrak + sgp4 | `celestrak.org/SOCRATES/active.txt` | Free | TLE 30 min, positions live |
| Earthquakes | USGS FDSNWS | `/fdsnws/event/1/query?minmagnitude=2.5` | Free | 60 s |

---

## Prerequisites

- **Python 3.11+**
- **Node.js 20+** and **npm**
- **Docker + Docker Compose** (optional)

No API keys or accounts needed.

---

## Setup

### 1. Configure environment

```bash
cd "Geospatial Tracker"
cp .env.example .env
```

The default `.env` works out of the box. Optional extras:

```text
# Higher OpenSky rate limits
OPENSKY_USERNAME=your_opensky_username
OPENSKY_PASSWORD=your_opensky_password

# Military aircraft via ADS-B Exchange (falls back to ICAO prefix filter without this)
ADSB_API_KEY=your_adsb_exchange_key
```

### 2. Run locally (without Docker)

**Terminal 1 — Backend:**

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Terminal 2 — Frontend:**

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

### 3. Run with Docker

```bash
docker compose up --build
```

- Backend: [http://localhost:8000](http://localhost:8000)
- Frontend: [http://localhost:5173](http://localhost:5173)

---

## Usage

### Globe Navigation

- **Drag** — rotate the globe
- **Scroll** — zoom in / out
- **Right-drag** — tilt the camera

### Data Layers (left panel)

| Layer | Colour | Description |
| --- | --- | --- |
| Aircraft | White → Cyan | Civil flights; cyan = high altitude (> 9,000 m) |
| Military | Red | Military aircraft via ADS-B Exchange or ICAO prefix fallback |
| Satellites | Cyan | Up to 2,000 active satellites at real orbital altitude |
| Earthquakes | Orange → Red | M2.5+ events sized by magnitude |

Click the coloured button beside each layer name to toggle it on or off.

### Visual Modes (left panel)

| Mode | Effect |
| --- | --- |
| **NORMAL** | Default rendering |
| **CRT** | Scanlines + vignette + green tint |
| **NV** | Night Vision — green monochrome with film grain |
| **FLIR** | Thermal palette — black → purple → red → yellow → white |

### Camera Presets (bottom bar)

Click any city to instantly fly the camera there:
**New York · London · Tokyo · Dubai · Los Angeles · Sydney · Singapore · Cairo**

---

## Project Structure

```text
Geospatial Tracker/
├── backend/
│   ├── main.py                  # FastAPI + WebSocket broadcast hub (WorldPayload)
│   ├── config.py                # Settings loaded from .env
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── ingestion/
│   │   ├── opensky.py           # OpenSky Network — civil aircraft (global)
│   │   ├── adsb_exchange.py     # ADS-B Exchange — military aircraft
│   │   ├── celestrak.py         # CelesTrak TLE + sgp4 — satellite positions
│   │   └── usgs.py              # USGS FDSNWS — earthquake events
│   ├── models/
│   │   └── schemas.py           # Pydantic v2 models (WorldPayload + all layers)
│   └── tests/                   # Unit tests (pytest + pytest-asyncio)
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Root — wires layers, visualMode, viewer ref
│   │   ├── types.ts             # TypeScript interfaces (WorldPayload, all layers)
│   │   ├── vite-env.d.ts        # Vite client type reference
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts  # WS hook with exponential backoff reconnect
│   │   └── components/
│   │       ├── GlobeView.tsx    # CesiumJS 3D globe + 4 data layers + GLSL shaders
│   │       ├── ControlPanel.tsx # Layer toggles + visual mode selector
│   │       └── CameraPresets.tsx# 8-city flyTo shortcuts
│   ├── vite.config.ts           # Vite + vite-plugin-cesium
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .env.example
├── Enhancements.md
└── README.md
```

---

## Configuration

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `OPENSKY_USERNAME` | No | — | OpenSky account for higher rate limits |
| `OPENSKY_PASSWORD` | No | — | OpenSky account password |
| `ADSB_API_KEY` | No | — | ADS-B Exchange key; falls back to ICAO filter without it |
| `POLLING_INTERVAL_SECONDS` | No | `10` | How often to fetch all data sources |
| `VITE_WS_URL` | No | `ws://localhost:8000/ws/live` | WebSocket URL override (frontend) |

---

## Running Tests

```bash
cd backend
pytest tests/ -v
```

---

## API Endpoints

| Endpoint | Method | Description |
| --- | --- | --- |
| `/health` | GET | Returns connection count and polling interval |
| `/ws/live` | WebSocket | WorldPayload pushed every 10 s |

**WebSocket message format:**

```json
{
  "aircraft":   { "type": "FeatureCollection", "features": [...] },
  "military":   { "type": "FeatureCollection", "features": [...] },
  "satellites": { "type": "FeatureCollection", "features": [...] },
  "earthquakes":{ "type": "FeatureCollection", "features": [...] },
  "counts": {
    "aircraft": 8241,
    "military": 87,
    "satellites": 1923,
    "earthquakes": 47
  },
  "timestamp": 1700000000.0
}
```

Satellite coordinates include altitude as the third element: `[lon, lat, altMeters]`.

---

## Rate Limits

### OpenSky Network

| Access type | Limit | How to enable |
| --- | --- | --- |
| Anonymous | 400 credits/day (~40 requests) | Default, no setup needed |
| Registered (free) | 4,000 credits/day | Add credentials to `.env` |

At 10 s polling, anonymous access uses ~8,640 requests/day — register a free account at [opensky-network.org](https://opensky-network.org).

### CelesTrak

TLE data is cached for **30 minutes** per fetch to respect CelesTrak's free tier. Satellite positions are re-computed from cached TLEs on every broadcast cycle.

### USGS Earthquakes

Earthquake data is cached for **60 seconds**. The USGS endpoint is free with no authentication.

---

## Extending the Project

See [Enhancements.md](Enhancements.md) for the full roadmap. Quick wins:

- **Faster updates** — lower `POLLING_INTERVAL_SECONDS` in `.env` (respect rate limits above)
- **More satellites** — raise `MAX_SATELLITES` in [backend/ingestion/celestrak.py](backend/ingestion/celestrak.py)
- **Different basemap** — swap the CartoDB URL in [frontend/src/components/GlobeView.tsx](frontend/src/components/GlobeView.tsx) for any `{z}/{x}/{y}` tile server
- **Aircraft trails** — store position history per `icao24` and draw `Polyline` primitives in GlobeView
- **Click info panel** — add a `screenSpaceEventHandler` in GlobeView to show entity details on click
