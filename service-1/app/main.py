from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict
import httpx
import json
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="EV Charger Service")

# Configuration
SERVICE_2_URL = os.getenv("SERVICE_2_URL", "http://localhost:8000")

# Store active connections
active_connections: Dict[str, WebSocket] = {}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "service-1"}


@app.websocket("/ws/{charger_id}")
async def websocket_endpoint(websocket: WebSocket, charger_id: str):
    await websocket.accept()
    active_connections[charger_id] = websocket
    logger.info(f"Charger {charger_id} connected")
