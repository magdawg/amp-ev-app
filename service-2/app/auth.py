from .env import SECRETS


async def validate_credentials(token: str, connector_id: str) -> (int, str):
    if connector_id not in SECRETS.keys():
        return 403, "Forbidden"

    if SECRETS[connector_id] != token:
        return 401, "Unauthorized"

    return 200, "Success"
