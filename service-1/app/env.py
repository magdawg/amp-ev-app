from fastapi import WebSocket

PENDING: dict[str, WebSocket] = {}

ACTIVE_CONNECTIONS: dict[str, WebSocket] = {}
