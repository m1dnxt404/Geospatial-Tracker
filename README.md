# OrbitalView — Real-Time 3D Geospatial Surveillance Platform

A live 3D geospatial tracker that displays **aircraft, military flights, satellites, earthquakes, and weather overlays** on a rotating globe in real time. Built with FastAPI (WebSocket backend) and React + CesiumJS (3D frontend). Includes CRT, Night Vision, and FLIR thermal visual modes.

**Running cost: $0.** A free OpenSky account is recommended for reliable aircraft data (anonymous access is heavily rate-limited). Weather overlays require a free OpenWeatherMap API key. All other sources need no registration.

---

## Architecture

```text
CelesTrak TLE   OpenSky   ADS-B Exchange   USGS Earthquakes
      │             │            │                 │
      └─────────────▼────────────▼─────────────────▼──────┐
                       FastAPI Backend                      │
           ingestion/opensky.py      — civil aircraft       │
           ingestion/adsb_exchange.py — military aircraft   │
           ingestion/celestrak.py   — TLE records (cached)  │
           ingestion/usgs.py        — earthquake events     │
                                                            │
           broadcast_loop() → WorldPayload                  │
      ┌────────────────────────────────────────────────────┘
      │  WebSocket /ws/live
      ▼
React Frontend
  GlobeView.tsx  (CesiumJS 3D globe, ESRI World Imagery, sun lighting)
  ├── Aircraft layer   — white/cyan dots coloured by altitude
  ├── Military layer   — red dots (ADS-B Exchange or ICAO filter)
  ├── Satellite layer  — billboard icon + name label + 30-min orbital trail
  │     satellite.js runs SGP4 on the client; Cesium SampledPositionProperty
  │     interpolates smooth motion between samples
  ├── Earthquake layer — orange/red dots sized by magnitude
  ├── Weather overlays — OpenWeatherMap tile layers (clouds/rain/wind/temp/pressure)
  │     Cesium ImageryLayer per type; toggled independently; no backend required
  └── PostProcessStage — CRT / Night Vision / FLIR shaders
  ControlPanel.tsx — layer toggles + visual mode + weather toggles
  CameraPresets.tsx — one-click flyTo for 8 world cities
```

---

## Data Sources

| Layer | Source | Endpoint | Cost | Refresh |
| --- | --- | --- | --- | --- |
| Aircraft | OpenSky Network | `/api/states/all` | Free | 10 s |
| Military | ADS-B Exchange | `/v2/mil/` (fallback: ICAO prefix filter) | Free | 10 s |
| Satellites | CelesTrak | `celestrak.org/pub/TLE/active.txt` | Free | TLE cache 30 min |
| Earthquakes | USGS FDSNWS | `/fdsnws/event/1/query?minmagnitude=2.5` | Free | 60 s |
| Weather | OpenWeatherMap | `tile.openweathermap.org/map/{layer}/{z}/{x}/{y}.png` | Free (API key) | Browser tile cache |

---

## Prerequisites

- **Python 3.11+**
- **Node.js 20+** and **npm**
- **Docker + Docker Compose** (optional)

A free [OpenSky Network](https://opensky-network.org) account is strongly recommended. All other data sources need no credentials.

---

## Setup

### 1. Configure environment

```bash
cd "Geospatial Tracker"
cp .env.example .env
```

The default `.env` works out of the box. Optional extras:

```text
# OpenSky OAuth2 credentials (recommended — from your OpenSky account settings page)
OPENSKY_CLIENT_ID=your_client_id
OPENSKY_CLIENT_SECRET=your_client_secret

# Military aircraft via ADS-B Exchange (falls back to ICAO prefix filter without this)
ADSB_API_KEY=your_adsb_exchange_key

# OpenWeatherMap API key — enables weather tile overlays on the globe
# Register for free at https://openweathermap.org/api
VITE_OWM_API_KEY=your_owm_key
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
| Satellites | Cyan | Up to 500 active satellites, animated in real time with a 30-minute orbital trail |
| Earthquakes | Orange → Red | M2.5+ events sized by magnitude |

Click the coloured button beside each layer name to toggle it on or off.

### Visual Modes (left panel)

| Mode | Effect |
| --- | --- |
| **NORMAL** | Default rendering |
| **CRT** | Scanlines + vignette + green tint |
| **NV** | Night Vision — green monochrome with film grain |
| **FLIR** | Thermal palette — black → purple → red → yellow → white |

### Weather Overlays (left panel)

Requires `VITE_OWM_API_KEY` set in `.env`. Multiple overlays can be active simultaneously.

| Overlay | Description |
| --- | --- |
| **Clouds** | Cloud cover (opacity-based) |
| **Rain** | Precipitation intensity |
| **Wind** | Wind speed and direction |
| **Temp** | Surface temperature gradient |
| **Pressure** | Atmospheric pressure contours |

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
│   │   ├── celestrak.py         # CelesTrak — raw TLE records (no server-side SGP4)
│   │   └── usgs.py              # USGS FDSNWS — earthquake events
│   ├── models/
│   │   └── schemas.py           # Pydantic v2 models (WorldPayload + all layers)
│   └── tests/                   # Unit tests (pytest + pytest-asyncio)
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Root — wires layers, visualMode, viewer ref
│   │   ├── types.ts             # TypeScript interfaces (WorldPayload, TLERecord, etc.)
│   │   ├── vite-env.d.ts        # Vite client type reference
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts  # WS hook with exponential backoff reconnect
│   │   └── components/
│   │       ├── GlobeView.tsx    # CesiumJS 3D globe + 4 data layers + weather imagery + GLSL shaders
│   │       ├── ControlPanel.tsx # Layer toggles + visual mode + weather toggles
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
| `OPENSKY_CLIENT_ID` | Recommended | — | OAuth2 client ID from OpenSky account settings (preferred auth method) |
| `OPENSKY_CLIENT_SECRET` | Recommended | — | OAuth2 client secret paired with the above |
| `OPENSKY_USERNAME` | No | — | Legacy Basic Auth username (used only if OAuth2 credentials are absent) |
| `OPENSKY_PASSWORD` | No | — | Legacy Basic Auth password |
| `ADSB_API_KEY` | No | — | ADS-B Exchange key; falls back to ICAO filter without it |
| `POLLING_INTERVAL_SECONDS` | No | `10` | How often to fetch all data sources |
| `VITE_WS_URL` | No | `ws://localhost:8000/ws/live` | WebSocket URL override (frontend) |
| `VITE_OWM_API_KEY` | No | — | OpenWeatherMap API key; enables weather tile overlays (free tier) |

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
  "tles": [
    { "norad_id": "25544", "name": "ISS (ZARYA)", "line1": "1 25544U ...", "line2": "2 25544 ..." },
    ...
  ],
  "earthquakes":{ "type": "FeatureCollection", "features": [...] },
  "counts": {
    "aircraft": 8241,
    "military": 87,
    "satellites": 500,
    "earthquakes": 47
  },
  "timestamp": 1700000000.0
}
```

Satellite data is sent as raw TLE strings. The frontend uses [satellite.js](https://github.com/shashwatak/satellite-js) to run SGP4 propagation in the browser, producing a `SampledPositionProperty` per satellite that Cesium animates in real time.

---

## Rate Limits

### OpenSky Network

| Access type | Limit | How to enable |
| --- | --- | --- |
| Anonymous | 400 credits/day (~40 requests) | Default, no setup needed |
| Registered (free) | 4,000 credits/day | Add credentials to `.env` |

At 10 s polling, anonymous access far exceeds the daily credit limit — aircraft will consistently return 0 results. Register a free account at [opensky-network.org](https://opensky-network.org) and add credentials to `.env`.

### CelesTrak

TLE data is cached for **30 minutes** per fetch to respect CelesTrak's free tier. The raw TLE strings are forwarded to connected clients, which run SGP4 locally. The cache is reused across broadcast cycles and survives transient network failures.

### USGS Earthquakes

Earthquake data is cached for **60 seconds**. The USGS endpoint is free with no authentication.

### OpenWeatherMap

Weather tile requests are made directly by the browser (no backend involvement). The free tier allows up to **1,000,000 tile calls/month** — far more than any single user will generate. Tiles are cached by the browser; no server-side caching is needed. Without `VITE_OWM_API_KEY` set, the weather toggle buttons are still shown but no tile requests are made.

---

## Extending the Project

See [Enhancements.md](Enhancements.md) for the full roadmap. Quick wins:

- **Faster updates** — lower `POLLING_INTERVAL_SECONDS` in `.env` (respect rate limits above)
- **More satellites** — raise `MAX_SATELLITES` in [backend/ingestion/celestrak.py](backend/ingestion/celestrak.py) (currently 500; raising it increases frontend SGP4 compute time on TLE refresh)
- **Different basemap** — swap the ESRI URL in [frontend/src/components/GlobeView.tsx](frontend/src/components/GlobeView.tsx) for any `{z}/{x}/{y}` tile server
- **Aircraft trails** — store position history per `icao24` and draw `Polyline` primitives in GlobeView
