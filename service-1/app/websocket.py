import json
import logging
import os
from enum import Enum

import httpx
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ValidationError

from .env import ACTIVE_CONNECTIONS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SERVICE_2_URL = os.getenv("SERVICE_2_URL", "http://localhost:8000")


class MessageType(str, Enum):
    AUTHORIZATION = "Authorization"
    ASYNC_AUTHORIZATION = "Async_Authorization"


class WebsocketMessage(BaseModel):
    messageType: MessageType
    messageId: str
    messageData: dict


class WebsocketResult(BaseModel):
    messageId: str
    success: bool
    messageData: dict


router = APIRouter()


@router.websocket("/{charger_id}")
async def websocket_endpoint(websocket: WebSocket, charger_id: str):
    await websocket.accept()
    ACTIVE_CONNECTIONS[charger_id] = websocket
    logger.info(f"Charger {charger_id} connected")
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
                    await process_auth(message, client, websocket)

                logger.info("pending auth call")


    except WebSocketDisconnect:
        del ACTIVE_CONNECTIONS[charger_id]
        logger.info(f"Charger {charger_id} disconnected")
    except Exception:
        logger.error(f"Error with charger {charger_id}", exc_info=True)
        if charger_id in ACTIVE_CONNECTIONS:
            del ACTIVE_CONNECTIONS[charger_id]


class AuthRequestData(BaseModel):
    connectorId: str
    token: str


class AuthRequest(BaseModel):
    messageId: str
    messageData: AuthRequestData


async def process_auth(
    message: WebsocketMessage, client: httpx.AsyncClient, websocket: WebSocket
):
    request_payload = AuthRequest(
        messageId=message.messageId,
        messageData=AuthRequestData(
            connectorId=message.messageData.get("connectorId"),
            token=message.messageData.get("token"),
        ),
    )
    result = await client.post(
        f"{SERVICE_2_URL}/authorize", json=request_payload.dict(), timeout=10.0
    )

    if result.status_code == 200:
        auth_response = WebsocketResult(
            messageId=message.messageId,
            success=True,
            messageData=result.json(),
        )
    else:
        auth_response = WebsocketResult(
            messageId=message.messageId,
            success=False,
            messageData={"error": result.json().get("detail"), "error_code": result.status_code},
        )

    await websocket.send_text(auth_response.json())
