from fastapi import WebSocket

PENDING_CONNECTIONS: dict[str, WebSocket] = {}

ACTIVE_CONNECTIONS: dict[str, WebSocket] = {}
