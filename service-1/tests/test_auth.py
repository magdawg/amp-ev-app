import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.auth import WebsocketMessage, WebsocketResult, process_auth


@pytest.mark.asyncio
async def test_process_auth_success(monkeypatch):
    # Arrange
    message = WebsocketMessage(
        messageId="123",
        messageType="Async_Authorization",
        messageData={"connectorId": "c-1", "token": "abc"},
    )

    # Fake response from service-2
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {"connectorId": "c-1", "status": "Pending"}

    # Mock AsyncClient.post
    async def mock_post(*args, **kwargs):
        return fake_response

    client = MagicMock()
    client.post = AsyncMock(side_effect=mock_post)

    # Fake websocket
    sent_messages = []

    class FakeWebSocket:
        async def send_text(self, text):
            sent_messages.append(text)

    websocket = FakeWebSocket()

    # Act
    await process_auth(message, client, websocket, async_req=False)

    # Assert
    assert len(sent_messages) == 1
    response = WebsocketResult.parse_raw(sent_messages[0])
    assert response.success is True
    assert response.messageData["status"] == "Pending"


@pytest.mark.asyncio
async def test_process_auth_http_error(monkeypatch):
    # Arrange
    message = WebsocketMessage(
        messageId="456",
        messageType="Async_Authorization",
        messageData={"connectorId": "c-2", "token": "def"},
    )

    fake_response = MagicMock()
    fake_response.status_code = 400
    fake_response.json.return_value = {"detail": "Invalid token"}

    async def mock_post(*args, **kwargs):
        return fake_response

    client = MagicMock()
    client.post = AsyncMock(side_effect=mock_post)

    sent_messages = []

    class FakeWebSocket:
        async def send_text(self, text):
            sent_messages.append(text)

    websocket = FakeWebSocket()

    # Act
    await process_auth(message, client, websocket, async_req=False)

    # Assert
    response = WebsocketResult.parse_raw(sent_messages[0])
    assert response.success is True
    assert response.messageData["error"] == "Invalid token"
    assert response.messageData["errorCode"] == 400


@pytest.mark.asyncio
async def test_process_auth_connection_error(monkeypatch):
    # Arrange
    message = WebsocketMessage(
        messageId="789",
        messageType="Async_Authorization",
        messageData={"connectorId": "c-3", "token": "ghi"},
    )

    async def mock_post(*args, **kwargs):
        raise httpx.RequestError("boom")

    client = MagicMock()
    client.post = AsyncMock(side_effect=mock_post)

    sent_messages = []

    class FakeWebSocket:
        async def send_text(self, text):
            sent_messages.append(text)

    websocket = FakeWebSocket()

    # Act
    await process_auth(message, client, websocket, async_req=False)

    # Assert
    response = WebsocketResult.parse_raw(sent_messages[0])
    assert response.success is False
    assert response.messageData["error"] == "service-2-unavailable"
    assert response.messageData["errorCode"] == 503
