import json
import logging
import os
from typing import Dict

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from .env import ACTIVE_CONNECTIONS
from .websocket import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(title="EV Charger Service 1")
app.include_router(router, prefix="/ws")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "service-1"}


@app.get("/connections")
async def get_connections():
    return {"active_connections": list(ACTIVE_CONNECTIONS.keys())}
