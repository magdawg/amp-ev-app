from fastapi import WebSocket

PENDING_CONNECTIONS: dict[str, dict] = {}

ACTIVE_CONNECTIONS: dict[str, WebSocket] = {}
