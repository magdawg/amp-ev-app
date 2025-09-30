import logging
import os
from datetime import datetime
from pydantic import ValidationError
import httpx
from fastapi import APIRouter, HTTPException, WebSocket

from .env import PENDING_MESSAGES
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
    async_req: bool = True,
):
    request_payload = AuthRequest(
        messageId=message.messageId,
        messageData=AuthRequestData(
            connectorId=message.messageData.get("connectorId"),
            token=message.messageData.get("token"),
        ),
    )
    auth_url = (
        f"{SERVICE_2_URL}/authorize-async"
        if async_req
        else f"{SERVICE_2_URL}/authorize"
    )
    try:
        result = await client.post(
            auth_url, json=request_payload.model_dump(), timeout=10.0
        )
        result_json = result.json()
        result_serialized = AuthResult(**result_json)
    except httpx.RequestError:
        logger.error("Error connecting to service-2", exc_info=True)
        auth_response = WebsocketResult(
            messageId=message.messageId,
            messageData={
                "authorized": False,
                "error": "service-2-unavailable",
                "errorCode": 503,
            },
        )
        await websocket.send_text(auth_response.model_dump_json())
        return
    except ValidationError:
        logger.error("Invalid response from service-2", exc_info=True)
        auth_response = WebsocketResult(
            messageId=message.messageId,
            messageData={
                "authorized": False,
                "error": "invalid-response",
                "errorCode": 502,
            },
        )
        await websocket.send_text(auth_response.model_dump_json())
        return

    if result.status_code in (
        200,
        202,
    ):
        message_data = {
            "authorized": result_serialized.authorized,
            "statusCode": result_serialized.statusCode,
            "status": result_serialized.status,
            "connectorId": result_serialized.connectorId,
        }
    else:
        message_data = {
            "authorized": False,
            "error": result_json.get("detail"),
            "errorCode": result.status_code,
        }

    logger.info(
        f"{datetime.now()} {result_serialized.connectorId} {result_serialized.status}"
    )

    auth_response = WebsocketResult(
        messageId=message.messageId,
        messageData=message_data,
    )
    await websocket.send_text(auth_response.model_dump_json())


@router.post("/result")
async def receive_result(result: AuthResult):
    messageId = result.messageId
    if messageId not in PENDING_MESSAGES:
        raise HTTPException(status_code=404, detail="messageId not found")

    if result.statusCode == 200:
        message_data = {
            "authorized": True,
            "statusCode": result.statusCode,
            "status": result.status,
            "connectorId": result.connectorId,
        }
    else:
        message_data = {
            "authorized": False,
            "error": result.status,
            "errorCode": result.statusCode,
        }

    logger.info(f"{datetime.now()} {result.connectorId} {result.status}")

    auth_response = WebsocketResult(
        messageId=messageId,
        messageData=message_data,
    )
    pending_msg_websocket = PENDING_MESSAGES[messageId]["websocket"]
    await pending_msg_websocket.send_text(auth_response.model_dump_json())
    del PENDING_MESSAGES[messageId]
    return
