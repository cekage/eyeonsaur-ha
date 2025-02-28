"""Tests unitaires pour la fonction check_credentials du config flow."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from custom_components.eyeonsaur.config_flow import check_credentials
from saur_client import SaurApiError


async def test_check_credentials_success() -> None:
    """Test avec des credentials valides (mock de SaurClient)."""
    mock_client = MagicMock()
    # Configure le mock pour simuler une authentification réussie (pas d'erreur levée)
    mock_client._authenticate = AsyncMock()

    await check_credentials(
        mock_client
    )  # Appel de check_credentials avec le client mocké

    # Vérifie que _authenticate a été appelée (pour s'assurer que check_credentials appelle bien l'authentification)
    mock_client._authenticate.assert_called_once()


async def test_check_credentials_invalid_auth() -> None:
    """Test avec des credentials invalides (mock de SaurClient simulant SaurApiError "unauthorized")."""
    mock_client = MagicMock()
    # Configure le mock pour simuler une erreur d'authentification "unauthorized"
    mock_client._authenticate = AsyncMock(
        side_effect=SaurApiError("Unauthorized")
    )

    with pytest.raises(
        SaurApiError
    ) as exc_info:  # Vérifie que check_credentials LÈVE bien une SaurApiError
        await check_credentials(mock_client)

    # Vérifie que l'exception levée est bien SaurApiError et contient "unauthorized" (pour s'assurer que c'est bien l'erreur attendue)
    assert "unauthorized" in str(exc_info.value).lower()


async def test_check_credentials_connection_error() -> None:
    """Test avec une erreur de connexion (mock de SaurClient simulant ClientConnectorError)."""
    mock_client = MagicMock()
    # Configure le mock pour simuler une erreur de connexion ClientConnectorError (générique, on utilise Exception pour simplifier)
    mock_client._authenticate = AsyncMock(
        side_effect=Exception("Connection error")
    )

    with (
        pytest.raises(Exception) as exc_info
    ):  # Vérifie que check_credentials LÈVE bien une Exception (générique, car ClientConnectorError n'est pas importable ici facilement)
        await check_credentials(mock_client)

    # Vérifie que l'exception levée est bien de type Exception (générique) et contient "connection error" (pour s'assurer que c'est bien l'erreur attendue)
    assert "connection error" in str(exc_info.value).lower()
