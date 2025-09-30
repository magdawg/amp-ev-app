import json
import logging
from datetime import datetime

import httpx
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from .auth import process_auth
from .env import ACTIVE_CONNECTIONS, PENDING_MESSAGES
from .types import MessageType, WebsocketMessage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter()


async def remove_active_connection(charger_id: str):
    if charger_id in ACTIVE_CONNECTIONS:
        del ACTIVE_CONNECTIONS[charger_id]


@router.websocket("/{charger_id}")
async def websocket_endpoint(websocket: WebSocket, charger_id: str):
    await websocket.accept()
    ACTIVE_CONNECTIONS[charger_id] = websocket
    try:
        async with httpx.AsyncClient() as client:
            while True:
                raw = await websocket.receive_text()
                try:
                    data = json.loads(raw)
                    message = WebsocketMessage(**data)
                except json.JSONDecodeError:
                    await websocket.send_text(json.dumps({"error": "invalid-json"}))
                    continue
                except ValidationError as e:
                    await websocket.send_text(
                        json.dumps({"error": "unsupported-messageType"})
                    )
                    continue

                if message.messageType == MessageType.AUTHORIZATION:
                    await process_auth(message, client, websocket, async_req=False)

                if (
                    message.messageType == MessageType.ASYNC_AUTHORIZATION
                    and message.messageId not in PENDING_MESSAGES.keys()
                ):
                    PENDING_MESSAGES[message.messageId] = {
                        "websocket": websocket,
                        "created_at": datetime.now(),
                    }
                    await process_auth(message, client, websocket)

    except WebSocketDisconnect:
        await remove_active_connection(charger_id)
    except Exception:
        logger.error(f"Error with charger {charger_id}", exc_info=True)
        await remove_active_connection(charger_id)
        await websocket.close()
