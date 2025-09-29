import asyncio
import json
import logging
import os
from typing import Dict

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from .auth import router as auth_router
from .env import ACTIVE_CONNECTIONS
from .utils import cleanup_pending
from .websocket import router as ws_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(title="EV Charger Service 1")
app.include_router(ws_router, prefix="/ws")
app.include_router(auth_router, prefix="/auth")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "service-1"}


@app.get("/connections")
async def get_connections():
    return {"active_connections": list(ACTIVE_CONNECTIONS.keys())}


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_pending())
