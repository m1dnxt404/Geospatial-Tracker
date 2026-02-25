# World Monitor — Real-Time Global Aircraft Tracker

A live geospatial tracker that displays **all aircraft in the world** in real time using the OpenSky Network API. Built with FastAPI (WebSocket backend) and React + Leaflet + OpenStreetMap (frontend).

**Running cost: $0 — no API keys, no accounts required.**

---

## Architecture

```text
OpenSky Network API (free, no key)
        │  5,000–10,000 aircraft positions (JSON)
        ▼
  FastAPI Backend
  ├── ingestion/opensky.py   — fetches all global aircraft every 10s
  ├── main.py                — WebSocket hub, broadcasts GeoJSON
        │  GeoJSON FeatureCollection (WebSocket)
        ▼
  React Frontend
  ├── useWebSocket.ts        — live connection with auto-reconnect
  ├── LiveMap.tsx            — Leaflet + Carto Dark map
  └── HUD.tsx                — overlay: aircraft count, status, timestamp
```

---

## Prerequisites

- **Python 3.11+**
- **Node.js 20+** and **npm**
- **Docker + Docker Compose** (optional, for containerised setup)

No API keys or accounts needed.

---

## Setup

### 1. Configure environment

```bash
cd "Geospatial Tracker"
cp .env.example .env
```

The default `.env` works out of the box. Optionally add OpenSky credentials for higher rate limits:

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

- The map opens at **world view** showing all tracked aircraft globally
- **Dot colours** indicate altitude:
  - **Green** — low altitude (< 1,000 m) / approaching or departing
  - **Orange** — mid altitude (1,000–7,000 m)
  - **Red** — cruise altitude (> 7,000 m)
  - **Grey** — on the ground
- **Click any dot** → popup with callsign, origin country, altitude, speed, and heading
- The **HUD (top-left)** shows live aircraft count, connection status (`LIVE` / `CONNECTING` / `OFFLINE`), and last update time
- Data refreshes every **10 seconds** automatically
- The map reconnects automatically if the backend restarts

---

## Project Structure

```text
Geospatial Tracker/
├── backend/
│   ├── main.py              # FastAPI + WebSocket broadcast hub
│   ├── config.py            # Settings loaded from .env
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── ingestion/
│   │   └── opensky.py       # OpenSky Network API client (global fetch)
│   ├── models/
│   │   └── schemas.py       # Pydantic v2 data models
│   └── tests/               # Unit tests (pytest + pytest-asyncio)
├── frontend/
│   ├── src/
│   │   ├── App.tsx           # Root component
│   │   ├── types.ts          # TypeScript interfaces (mirrors backend schemas)
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts  # WS hook with exponential backoff reconnect
│   │   └── components/
│   │       ├── LiveMap.tsx   # Leaflet map + aircraft markers + popups
│   │       └── HUD.tsx       # Status overlay panel
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
| `POLLING_INTERVAL_SECONDS` | No | `10` | How often to fetch aircraft data |
| `VITE_WS_URL` | No | `ws://localhost:8000/ws/live` | WebSocket URL (frontend) |

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
| `/ws/live` | WebSocket | Live GeoJSON stream pushed every 10s |

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
  "aircraft_count": 8241,
  "timestamp": 1700000000.0
}
```

---

## OpenSky Rate Limits

| Access type | Limit | How to enable |
| --- | --- | --- |
| Anonymous | 400 API credits/day (~40 requests) | Default, no setup needed |
| Registered (free) | 4,000 credits/day | Add `OPENSKY_USERNAME` + `OPENSKY_PASSWORD` to `.env` |

At a 10-second polling interval, anonymous access uses ~8,640 requests/day — register a free account at [opensky-network.org](https://opensky-network.org) to avoid hitting the limit.

---

## Extending the Project

See [Enhancements.md](Enhancements.md) for the full roadmap. Quick wins:

- **Faster updates**: Lower `POLLING_INTERVAL_SECONDS` in `.env` (respect rate limits above)
- **Focus on a region**: Add bbox params to the OpenSky call in [backend/ingestion/opensky.py](backend/ingestion/opensky.py)
- **Smoother rendering**: Switch Leaflet to Canvas renderer in [frontend/src/components/LiveMap.tsx](frontend/src/components/LiveMap.tsx) for 10k+ markers
- **Aircraft trails**: Store position history per `icao24` and add a `LineString` layer
