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
           ingestion/opensky.py      — civil aircraft (429 backoff)       │
           ingestion/adsb_exchange.py — military aircraft (429 backoff)   │
           ingestion/celestrak.py   — TLE records (30 min cache, 429 backoff) │
           ingestion/usgs.py        — earthquake events (429 backoff)     │
                                                                          │
           broadcast_loop() → WorldPayload                                │
           GET /health/detailed   → per-source status                     │
      ┌────────────────────────────────────────────────────┘
      │  WebSocket /ws/live
      ▼
React Frontend
  GlobeView.tsx  (CesiumJS 3D globe, ESRI World Imagery, sun lighting)
  ├── Aircraft layer   — silhouette icons (zoomed in) or dots (zoomed out)
  │     5 icon categories (WIDE/NARROW/REGIONAL/HELI/GENERAL) rotated by heading
  │     GPU-side zoom switching via distanceDisplayCondition at 3,000 km
  │     Colour gradient green→yellow→cyan (0–15,000 m) via Cesium.Color.lerp()
  │     Typecode + full model name (e.g. "Boeing 737-800") from OpenSky metadata API; permanently cached
  ├── Aircraft trails  — fading PolylineCollection, last 10 positions per icao24
  ├── Heatmap layer    — 1°×1° density grid rasterised to canvas → SingleTileImageryProvider
  ├── Military layer   — red silhouette icons / dots (ADS-B Exchange or ICAO filter)
  ├── Satellite layer  — billboard icon + name label + 30-min orbital trail
  │     satellite.js runs SGP4 on the client; Cesium SampledPositionProperty
  │     interpolates smooth motion; altitude & velocity shown in info panel
  ├── Earthquake layer — orange/red dots sized by magnitude
  ├── Weather overlays — OpenWeatherMap tile layers (clouds/rain/wind/temp/pressure)
  │     Cesium ImageryLayer per type; toggled independently; no backend required
  └── PostProcessStage — CRT / Night Vision / FLIR shaders
  ErrorBoundary.tsx — catches GlobeView render errors; shows "Rendering error — click to retry" fallback
  ControlPanel.tsx — layer toggles (incl. Trails) + visual mode + weather toggles + per-source health dots
  CameraPresets.tsx — one-click flyTo for 8 world cities
  useWebSocket.ts  — WS hook; validates every message with Zod schema before updating state
  useHealthPoll.ts — polls /health/detailed every 30 s; feeds green/amber/red dots into ControlPanel
```

---

## Data Sources

| Layer                 | Source           | Endpoint                                              | Cost           | Refresh            |
| --------------------- | ---------------- | ----------------------------------------------------- | -------------- | ------------------ |
| Aircraft              | OpenSky Network  | `/api/states/all`                                     | Free           | 10 s               |
| Aircraft type & model | OpenSky Metadata | `/api/metadata/aircraft/icao/{icao24}`                | Free           | Permanent cache    |
| Military              | ADS-B Exchange   | `/v2/mil/` (fallback: ICAO prefix filter)             | Free           | 10 s               |
| Satellites            | CelesTrak        | `celestrak.org/pub/TLE/active.txt`                    | Free           | TLE cache 30 min   |
| Earthquakes           | USGS FDSNWS      | `/fdsnws/event/1/query?minmagnitude=2.5`              | Free           | 60 s               |
| Weather               | OpenWeatherMap   | `tile.openweathermap.org/map/{layer}/{z}/{x}/{y}.png` | Free (API key) | Browser tile cache |

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

| Layer       | Colour                | Description                                                                                                         |
| ----------- | --------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Aircraft    | Green → Yellow → Cyan | Civil flights; top-down silhouette icons (zoomed in) or dots (zoomed out); colour encodes altitude 0–15,000 m       |
| Military    | Red                   | Military aircraft via ADS-B Exchange or ICAO prefix fallback; red silhouette icons or dots                          |
| Satellites  | Cyan                  | Up to 500 active satellites, animated in real time with a 30-minute orbital trail; click to see altitude & velocity |
| Earthquakes | Orange → Red          | M2.5+ events sized by magnitude                                                                                     |
| Trails      | Green → Yellow → Cyan | Fading polyline trail behind each aircraft showing the last 10 positions (~100 s of history)                        |
| Heatmap     | Blue → Red            | Aircraft density overlay; filterable by altitude band via Min/Max sliders                                           |

Click the coloured button beside each layer name to toggle it on or off.

### Visual Modes (left panel)

| Mode       | Effect                                                  |
| ---------- | ------------------------------------------------------- |
| **NORMAL** | Default rendering                                       |
| **CRT**    | Scanlines + vignette + green tint                       |
| **NV**     | Night Vision — green monochrome with film grain         |
| **FLIR**   | Thermal palette — black → purple → red → yellow → white |

### Weather Overlays (left panel)

Requires `VITE_OWM_API_KEY` set in `.env`. Multiple overlays can be active simultaneously.

| Overlay      | Description                   |
| ------------ | ----------------------------- |
| **Clouds**   | Cloud cover (opacity-based)   |
| **Rain**     | Precipitation intensity       |
| **Wind**     | Wind speed and direction      |
| **Temp**     | Surface temperature gradient  |
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
│   ├── cache.py                 # Async Redis wrapper with no-op fallback (optional persistence)
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── ingestion/
│   │   ├── opensky.py           # OpenSky Network — civil aircraft (global)
│   │   ├── adsb_exchange.py     # ADS-B Exchange — military aircraft
│   │   ├── aircraft_metadata.py # OpenSky metadata API — typecode + model name cache (permanent)
│   │   ├── celestrak.py         # CelesTrak — raw TLE records (no server-side SGP4)
│   │   └── usgs.py              # USGS FDSNWS — earthquake events
│   ├── models/
│   │   └── schemas.py           # Pydantic v2 models (WorldPayload + all layers)
│   └── tests/                   # Unit tests (pytest + pytest-asyncio)
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Root — wires layers, visualMode, viewer ref
│   │   ├── settings.ts          # Centralised frontend tuning constants
│   │   ├── types.ts             # TypeScript interfaces (WorldPayload, TLERecord, etc.)
│   │   ├── vite-env.d.ts        # Vite client type reference
│   │   ├── schemas.ts           # Zod schema for runtime WorldPayload validation
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts  # WS hook with exponential backoff reconnect + Zod validation
│   │   │   └── useHealthPoll.ts # Polls /health/detailed every 30 s for source status dots
│   │   └── components/
│   │       ├── GlobeView.tsx    # CesiumJS 3D globe + 4 data layers + weather imagery + GLSL shaders
│   │       ├── ErrorBoundary.tsx# Catches GlobeView render errors; shows retry fallback
│   │       ├── ControlPanel.tsx # Layer toggles + visual mode + weather toggles + source health dots
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

| Variable                   | Required    | Default                       | Description                                                                                                          |
| -------------------------- | ----------- | ----------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `OPENSKY_CLIENT_ID`        | Recommended | —                             | OAuth2 client ID from OpenSky account settings (preferred auth method)                                               |
| `OPENSKY_CLIENT_SECRET`    | Recommended | —                             | OAuth2 client secret paired with the above                                                                           |
| `OPENSKY_USERNAME`         | No          | —                             | Legacy Basic Auth username (used only if OAuth2 credentials are absent)                                              |
| `OPENSKY_PASSWORD`         | No          | —                             | Legacy Basic Auth password                                                                                           |
| `ADSB_API_KEY`             | No          | —                             | ADS-B Exchange key; falls back to ICAO filter without it                                                             |
| `POLLING_INTERVAL_SECONDS` | No          | `10`                          | How often to fetch all data sources                                                                                  |
| `MAX_SATELLITES`           | No          | `500`                         | Max TLE records sent per broadcast (backend cap)                                                                     |
| `TRAIL_MAX_LENGTH`         | No          | `10`                          | Max position history points per aircraft (≈ 10 s each)                                                               |
| `METADATA_FETCH_PER_CYCLE` | No          | `5`                           | Max new aircraft typecodes fetched per broadcast cycle                                                               |
| `REDIS_URL`                | No          | —                             | Redis connection string (e.g. `redis://localhost:6379/0`); leave empty to disable — all caches remain in-memory only |
| `VITE_WS_URL`              | No          | `ws://localhost:8000/ws/live` | WebSocket URL override (frontend)                                                                                    |
| `VITE_OWM_API_KEY`         | No          | —                             | OpenWeatherMap API key; enables weather tile overlays (free tier)                                                    |

---

## Running Tests

```bash
cd backend
pytest tests/ -v
```

---

## API Endpoints

| Endpoint           | Method    | Description                                                                                        |
| ------------------ | --------- | -------------------------------------------------------------------------------------------------- |
| `/health`          | GET       | Returns connection count and polling interval                                                      |
| `/health/detailed` | GET       | Per-source status: last-success timestamp, rate-limit state for OpenSky / CelesTrak / USGS / ADS-B |
| `/ws/live`         | WebSocket | WorldPayload pushed every 10 s                                                                     |

**WebSocket message format:**

```json
{
  "aircraft": {
    "type": "FeatureCollection",
    "features": [{
      "type": "Feature",
      "geometry": { "type": "Point", "coordinates": [-73.78, 40.64] },
      "properties": {
        "icao24": "a1b2c3", "callsign": "UAL123", "origin_country": "United States",
        "altitude": 11278, "velocity": 245, "heading": 83, "vertical_rate": 0,
        "on_ground": false, "trail": [[-73.9, 40.6], [-73.85, 40.62], [-73.78, 40.64]],
        "typecode": "B738", "model_name": "Boeing 737-800"
      }
    }]
  },
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

| Access type       | Limit                          | How to enable             |
| ----------------- | ------------------------------ | ------------------------- |
| Anonymous         | 400 credits/day (~40 requests) | Default, no setup needed  |
| Registered (free) | 4,000 credits/day              | Add credentials to `.env` |

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
- **More satellites** — raise `MAX_SATELLITES` in `.env` or [frontend/src/settings.ts](frontend/src/settings.ts) (default 500; raising it increases frontend SGP4 compute time)
- **Longer trails** — raise `TRAIL_MAX_LENGTH` in `.env` (default 10 positions ≈ 100 s of history)
- **Icon zoom threshold** — change `ICON_MAX_DISTANCE` in [frontend/src/settings.ts](frontend/src/settings.ts) (default 3,000 km camera height)
- **Satellite trail / window** — tune `SATELLITE_TRAIL_TIME_SEC` and `SATELLITE_HALF_WINDOW_SEC` in [frontend/src/settings.ts](frontend/src/settings.ts)
- **Different basemap** — swap the ESRI URL in [frontend/src/components/GlobeView.tsx](frontend/src/components/GlobeView.tsx) for any `{z}/{x}/{y}` tile server
- **Typecode fetch rate** — raise `METADATA_FETCH_PER_CYCLE` in `.env` (default 5 new aircraft types per broadcast cycle)
