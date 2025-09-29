from enum import Enum

from pydantic import BaseModel


class MessageType(str, Enum):
    AUTHORIZATION = "Authorization"
    ASYNC_AUTHORIZATION = "Async_Authorization"


class WebsocketMessage(BaseModel):
    messageType: MessageType
    messageId: str
    messageData: dict


class WebsocketResult(BaseModel):
    messageId: str
    success: bool
    messageData: dict


class AuthRequestData(BaseModel):
    connectorId: str
    token: str


class AuthRequest(BaseModel):
    messageId: str
    messageData: AuthRequestData


class AuthResult(BaseModel):
    messageId: str
    statusCode: int
    status: str
    connectorId: str | None = None
