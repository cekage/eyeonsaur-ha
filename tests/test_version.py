import asyncio
import aiohttp
import pytest
import socket
import pytest_socket


async def get_ha_version(hass_url: str, access_token: str) -> str:
    """Récupère la version de Home Assistant via l'API."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(f"{hass_url}/api") as resp:
            resp.raise_for_status()  # Lève une exception en cas d'erreur HTTP
            return await resp.text()


@pytest.mark.asyncio
async def test_home_assistant_version():
    """Teste que la version de Home Assistant est correcte."""
    ha_url = "http://192.168.1.116:8123"  # URL de ton instance Home Assistant
    access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkMmFhMTEwZjAzZGQ0ZDc5YTgxOTc0OWI0NTJjNjM3ZSIsImlhdCI6MTc0MDYwMzEyNywiZXhwIjoyMDU1OTYzMTI3fQ.P6jky1Pn-mbRZlw1hFYMk9SwnpzHp7SX61Z_Bzap5l8"  # Remplace par ton token
    expected_version = "2024.12.5"  # Remplace par la version attendue

    try:
        actual_version = await get_ha_version(ha_url, access_token)
        assert actual_version == expected_version, (
            f"Version incorrecte: attendue {expected_version}, obtenue {actual_version}"
        )
    except aiohttp.ClientError as e:
        pytest.fail(f"Erreur de connexion à Home Assistant: {e}")
