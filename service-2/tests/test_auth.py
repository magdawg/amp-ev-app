import pytest

from app.auth import validate_credentials


@pytest.fixture
def mock_secrets(mocker):
    mocker.patch("app.auth.SECRETS", {"test1": "admin1", "test2": "admin2"})
    
@pytest.mark.asyncio
async def test_validate_credentials(mock_secrets):

    # Valid credentials
    status_code, status = await validate_credentials("admin1", "test1")
    assert status_code == 200
    assert status == "Authorized"

    # Invalid token
    status_code, status = await validate_credentials("invalid_token", "test1")
    assert status_code == 401
    assert status == "Unauthorized"

    # Invalid connectorId
    status_code, status = await validate_credentials("admin2", "invalid_connector")
    assert status_code == 403
    assert status == "Forbidden"
