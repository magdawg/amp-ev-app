from fastapi import WebSocket

PENDING_MESSAGES: dict[str, dict] = {}

ACTIVE_CONNECTIONS: dict[str, WebSocket] = {}
