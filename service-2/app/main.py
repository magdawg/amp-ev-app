from fastapi import FastAPI
from typing import Dict
import httpx
import json
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="EV Charger Service 2")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "service-2"}
