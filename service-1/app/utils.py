import asyncio
import json
from datetime import datetime

from .env import PENDING_CONNECTIONS
from .types import WebsocketResult

TIMEOUT_SECONDS = 15


async def cleanup_pending():
    while True:
        now = datetime.now()
        expired = [
            message_id
            for message_id, item in PENDING_CONNECTIONS.items()
            if (now - item["created_at"]).total_seconds() > TIMEOUT_SECONDS
        ]

        for message_id in expired:
            ws = PENDING_CONNECTIONS[message_id]["websocket"]
            auth_response = WebsocketResult(
                messageId=message_id,
                messageData={"authorized": False, "error": "Timeout", "errorCode": 408},
            )
            await ws.send_text(auth_response.json())
            del PENDING_CONNECTIONS[message_id]

        await asyncio.sleep(5)  # check every 5 seconds
