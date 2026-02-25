import asyncio
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from ingestion.opensky import fetch_aircraft
from models.schemas import (
    GeoJSONFeature,
    GeoJSONFeatureCollection,
    GeoJSONPoint,
    LivePayload,
)
from config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)
        logger.info("Client connected. Total: %d", len(self._connections))

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)
        logger.info("Client disconnected. Total: %d", len(self._connections))

    async def broadcast(self, message: str) -> None:
        dead: set[WebSocket] = set()
        for ws in self._connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.add(ws)
        self._connections -= dead

    @property
    def connection_count(self) -> int:
        return len(self._connections)


manager = ConnectionManager()


def _build_geojson(aircraft_list: list) -> GeoJSONFeatureCollection:
    features = []
    for ac in aircraft_list:
        if ac.latitude is None or ac.longitude is None:
            continue
        features.append(
            GeoJSONFeature(
                geometry=GeoJSONPoint(coordinates=[ac.longitude, ac.latitude]),
                properties={
                    "icao24": ac.icao24,
                    "callsign": ac.callsign,
                    "origin_country": ac.origin_country,
                    "altitude": ac.altitude,
                    "velocity": ac.velocity,
                    "heading": ac.heading,
                    "vertical_rate": ac.vertical_rate,
                    "on_ground": ac.on_ground,
                },
            )
        )
    return GeoJSONFeatureCollection(features=features)


async def broadcast_loop() -> None:
    logger.info("Broadcast loop started. Interval: %ds", settings.POLLING_INTERVAL_SECONDS)
    while True:
        cycle_start = time.monotonic()
        try:
            if manager.connection_count > 0:
                aircraft = await fetch_aircraft()
                geojson = _build_geojson(aircraft)
                payload = LivePayload(
                    geojson=geojson,
                    aircraft_count=len(geojson.features),
                )
                await manager.broadcast(payload.model_dump_json())
                logger.info(
                    "Broadcast: %d aircraft to %d client(s)",
                    len(geojson.features),
                    manager.connection_count,
                )
            else:
                logger.debug("No clients — skipping cycle")
        except Exception as exc:
            logger.exception("Broadcast cycle error: %s", exc)

        elapsed = time.monotonic() - cycle_start
        await asyncio.sleep(max(0.0, settings.POLLING_INTERVAL_SECONDS - elapsed))


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(broadcast_loop())
    logger.info("World Monitor backend started")
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        logger.info("Broadcast loop stopped")


app = FastAPI(title="World Monitor API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {
        "status": "healthy",
        "connections": manager.connection_count,
        "polling_interval": settings.POLLING_INTERVAL_SECONDS,
    }


@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:
        logger.warning("WebSocket error: %s", exc)
        manager.disconnect(websocket)
