import asyncio
import logging
import os

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .auth import validate_credentials
from .types import AuthRequest, AuthResult

CALLBACK_URL = os.getenv("SERVICE_1_CALLBACK_URL", "http://service-1:8765/auth/result")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="EV Charger Service 2")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "service-2"}


@app.post("/authorize", status_code=200, response_model=AuthResult)
async def authorize(req: AuthRequest):
    await asyncio.sleep(6)  # Simulate processing delay

    status_code, status = await validate_credentials(
        req.messageData.token, req.messageData.connectorId
    )
    if status_code != 200:
        raise HTTPException(status_code=status_code, detail=status)

    return AuthResult(
        messageId=req.messageId,
        connectorId=req.messageData.connectorId,
        statusCode=status_code,
        status=status,
        authorized=True,
    )


@app.post("/authorize-async", status_code=202, response_model=AuthResult)
async def authorize_async(req: AuthRequest):

    async def callback():
        await asyncio.sleep(6)  # Simulate processing delay

        status_code, status = await validate_credentials(
            req.messageData.token, req.messageData.connectorId
        )
        if status_code != 200:
            result = AuthResult(
                messageId=req.messageId,
                statusCode=status_code,
                status=status,
                connectorId=req.messageData.connectorId,
                authorized=False,
            )

        result = AuthResult(
            messageId=req.messageId,
            statusCode=status_code,
            status=status,
            connectorId=req.messageData.connectorId,
            authorized=True,
        )
        async with httpx.AsyncClient() as client:
            try:
                await client.post(CALLBACK_URL, json=result.dict())
            except httpx.RequestError as e:
                logger.error("Error sending callback to service-1", exc_info=True)

    asyncio.create_task(callback())
    return AuthResult(
        messageId=req.messageId,
        statusCode=202,
        status="Pending",
        connectorId=req.messageData.connectorId,
        authorized=False,
    )
