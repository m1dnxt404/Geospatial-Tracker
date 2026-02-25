# World Monitor — Real-Time Aircraft Tracker

A live geospatial tracker that displays aircraft positions over **New York City** using the OpenSky Network API. Built with FastAPI (WebSocket backend) and React + Mapbox GL JS (frontend).

**Running cost: $0** — all components use free tiers.

---

## Architecture

```text
OpenSky Network API (free)
        │  aircraft positions (JSON)
        ▼
  FastAPI Backend
  ├── ingestion/opensky.py   — fetches aircraft every 10s
  ├── main.py                — WebSocket hub, broadcasts GeoJSON
        │  GeoJSON FeatureCollection (WebSocket)
        ▼
  React Frontend
  ├── useWebSocket.ts        — live connection with auto-reconnect
  ├── LiveMap.tsx            — Mapbox GL JS dark map
  └── HUD.tsx                — overlay: count, status, timestamp
```

---

## Prerequisites

- **Python 3.11+**
- **Node.js 20+** and **npm**
- A **Mapbox** account (free) — get your token at [account.mapbox.com](https://account.mapbox.com)
- **Docker + Docker Compose** (optional, for containerised setup)

---

## Setup

### 1. Clone and configure environment

```bash
cd "Geospatial Tracker"
cp .env.example .env
```

Open `.env` and fill in:

```text
MAPBOX_TOKEN=pk.eyJ1IjoiL...          # from account.mapbox.com/access-tokens
VITE_MAPBOX_TOKEN=pk.eyJ1IjoiL...     # same token (needed by Vite build)
```

OpenSky credentials are optional — anonymous access works but has lower rate limits (5 req/10s):

```text
OPENSKY_USERNAME=your_opensky_username
OPENSKY_PASSWORD=your_opensky_password
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

- The map opens centred on **New York City** at zoom 10
- **Blue/green/red dots** = aircraft coloured by altitude (green = low, red = high altitude, grey = on ground)
- **Click any dot** → popup with callsign, origin, altitude, speed, heading
- The **HUD (top-left)** shows live aircraft count, connection status, and last update time
- Data refreshes every **10 seconds** automatically

---

## Project Structure

```text
geospatial-tracker/
├── backend/
│   ├── main.py              # FastAPI + WebSocket broadcast hub
│   ├── config.py            # Settings (env vars, NYC bbox)
│   ├── ingestion/
│   │   └── opensky.py       # OpenSky Network API client
│   ├── models/
│   │   └── schemas.py       # Pydantic data models
│   └── tests/               # Unit tests (pytest)
├── frontend/
│   └── src/
│       ├── App.tsx
│       ├── types.ts
│       ├── hooks/useWebSocket.ts
│       └── components/
│           ├── LiveMap.tsx
│           └── HUD.tsx
├── docker-compose.yml
└── .env.example
```

---

## Configuration

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `MAPBOX_TOKEN` | Yes | — | Mapbox public access token |
| `VITE_MAPBOX_TOKEN` | Yes | — | Same token (Vite build-time injection) |
| `OPENSKY_USERNAME` | No | — | OpenSky account (higher rate limits) |
| `OPENSKY_PASSWORD` | No | — | OpenSky password |
| `POLLING_INTERVAL_SECONDS` | No | `10` | How often to fetch aircraft data |
| `VITE_WS_URL` | No | `ws://localhost:8000/ws/live` | WebSocket URL |

---

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

---

## API Endpoints

| Endpoint | Method | Description |
| --- | --- | --- |
| `/health` | GET | Health check — returns connection count and poll interval |
| `/ws/live` | WebSocket | Live GeoJSON stream, pushed every 10s |

**WebSocket message format:**

```json
{
  "geojson": {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "geometry": { "type": "Point", "coordinates": [-73.9, 40.7] },
        "properties": {
          "icao24": "a1b2c3",
          "callsign": "UAL123",
          "origin_country": "United States",
          "altitude": 10000,
          "velocity": 250,
          "heading": 270,
          "on_ground": false
        }
      }
    ]
  },
  "aircraft_count": 42,
  "timestamp": 1700000000.0
}
```

---

## Extending the Project

- **Wider coverage**: Adjust `BBOX_LAMIN/LOMIN/LAMAX/LOMAX` in `.env` or `config.py`
- **Different city**: Change the bbox values and map center in [frontend/src/components/LiveMap.tsx](frontend/src/components/LiveMap.tsx#L28)
- **Faster updates**: Lower `POLLING_INTERVAL_SECONDS` (respect OpenSky rate limits)
- **Aircraft trails**: Add a `LineString` layer and store position history per `icao24`
