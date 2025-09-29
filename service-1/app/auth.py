import json
import logging
import os
from datetime import datetime

import httpx
from fastapi import APIRouter, HTTPException, WebSocket
from pydantic import BaseModel

from .env import PENDING_CONNECTIONS
from .types import (
    AuthRequest,
    AuthRequestData,
    AuthResult,
    WebsocketMessage,
    WebsocketResult,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SERVICE_2_URL = os.getenv("SERVICE_2_URL", "http://service-2:8000")

router = APIRouter()


async def process_auth(
    message: WebsocketMessage,
    client: httpx.AsyncClient,
    websocket: WebSocket,
    async_req: bool = False,
):
    request_payload = AuthRequest(
        messageId=message.messageId,
        messageData=AuthRequestData(
            connectorId=message.messageData.get("connectorId"),
            token=message.messageData.get("token"),
        ),
    )
    try:
        if not async_req:
            result = await client.post(
                f"{SERVICE_2_URL}/authorize", json=request_payload.dict(), timeout=10.0
            )
        else:
            result = await client.post(
                f"{SERVICE_2_URL}/authorize-async",
                json=request_payload.dict(),
                timeout=10.0,
            )
    except httpx.RequestError as e:
        logger.error("Error connecting to service-2", exc_info=True)
        auth_response = WebsocketResult(
            messageId=message.messageId,
            success=False,
            messageData={"error": "service-2-unavailable", "errorCode": 503},
        )
        await websocket.send_text(auth_response.json())
        return

    if result.status_code in (200, 202):
        message_data = result.json()
    else:
        message_data = {
            "error": result.json().get("detail"),
            "errorCode": result.status_code,
        }

    auth_response = WebsocketResult(
        messageId=message.messageId,
        success=True,
        messageData=message_data,
    )
    logger.info(
        f"{datetime.now()} {result.json().get('connectorId')} {result.json().get('status')}"
    )
    await websocket.send_text(auth_response.json())


@router.post("/result")
async def receive_result(result: AuthResult):
    messageId = result.messageId
    if messageId in PENDING_CONNECTIONS:
        ws = PENDING_CONNECTIONS[messageId]
        if result.statusCode == 200:
            success = True
            message_data = {
                "messageId": messageId,
                "statusCode": result.statusCode,
                "status": result.status,
                "connectorId": result.connectorId,
            }
        else:
            success = False
            message_data = {"error": result.status, "errorCode": result.statusCode}

        auth_response = WebsocketResult(
            messageId=messageId,
            success=True,
            messageData=message_data,
        )
        logger.info(f"{datetime.now()} {result.connectorId} {result.status}")
        await ws.send_text(auth_response.json())
        del PENDING_CONNECTIONS[messageId]
    else:
        raise HTTPException(status_code=404, detail="messageId not found")

    return
