import json
import logging
import os

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from time import sleep

SECRETS = {"connector1": "admin1", "connector2": "admin2"}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="EV Charger Service 2")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "service-2"}


class AuthRequestData(BaseModel):
    connectorId: str
    token: str


class AuthRequest(BaseModel):
    messageId: str
    messageData: AuthRequestData


@app.post("/authorize", status_code=200)
async def authorize(req: AuthRequest):
    if req.messageData.connectorId not in SECRETS.keys():
        raise HTTPException(status_code=403, detail="Forbidden")

    if SECRETS[req.messageData.connectorId] != req.messageData.token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    sleep(5)  # Simulate processing delay
    return {"status": "Authorized", "connectorId": req.messageData.connectorId}
