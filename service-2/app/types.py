from pydantic import BaseModel


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
    authorized: bool
    connectorId: str | None = None
