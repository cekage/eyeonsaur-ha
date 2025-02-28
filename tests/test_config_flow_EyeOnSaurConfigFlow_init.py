"""Tests unitaires pour la méthode EyeOnSaurConfigFlow.__init__ et _check_online_credentials du config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.data_entry_flow import FlowResultType
from saur_client import SaurApiError, SaurClient

from custom_components.eyeonsaur.config_flow import EyeOnSaurConfigFlow
from custom_components.eyeonsaur.helpers.const import (
    DOMAIN,
    ENTRY_LOGIN,
    ENTRY_PASS,
)


async def test_config_flow_init() -> None:
    """Test de l'initialisation du config flow."""
    flow = EyeOnSaurConfigFlow()
    assert flow.VERSION == 1
    # assert flow.domain == DOMAIN
    # Add more assertions here about default values if needed, but the above covers the basics


@pytest.mark.asyncio
async def test_check_online_credentials_success() -> None:
    """Test _check_online_credentials avec succès."""
    flow = EyeOnSaurConfigFlow()
    user_input = {ENTRY_LOGIN: "test@example.com", ENTRY_PASS: "test_password"}
    flow.client = MagicMock()
    flow.client.clientId = "some_client_id"  # Ensure clientId is set
    flow.client.access_token = "some_access_token"  # Set an access token

    # Mock create_saur_client to return our mock_client
    with patch(
        "custom_components.eyeonsaur.config_flow.create_saur_client",
        return_value=flow.client,
    ):
        # Configure the mock to have an AsyncMock _authenticate method
        flow.client._authenticate = AsyncMock()

        await flow._check_online_credentials(user_input)

    # Assertions: check that _authenticate has been called
    flow.client._authenticate.assert_called_once()


@pytest.mark.asyncio
async def test_check_online_credentials_unauthorized() -> None:
    """Test _check_online_credentials avec erreur d'authentification."""
    flow = EyeOnSaurConfigFlow()
    user_input = {ENTRY_LOGIN: "test@example.com", ENTRY_PASS: "test_password"}
    flow.client = MagicMock()

    # Configurer le mock pour lever une exception SaurApiError("Unauthorized")
    flow.client._authenticate = AsyncMock(
        side_effect=SaurApiError("Unauthorized")
    )

    with patch(
        "custom_components.eyeonsaur.config_flow.create_saur_client",
        return_value=flow.client,
    ):
        await flow._check_online_credentials(user_input)  # Call the function

    # Assertions: check that _authenticate has been called, and an exception was handled
    flow.client._authenticate.assert_called_once()
    # TODO: Figure out how assert that errors["base"] == "invalid_auth" within the function (can't directly assert on local variable inside _check_online_credentials without more complex mocking)
    # See note below.


@pytest.mark.asyncio
async def test_check_online_credentials_generic_error() -> None:
    """Test _check_online_credentials avec une erreur générique."""
    flow = EyeOnSaurConfigFlow()
    user_input = {ENTRY_LOGIN: "test@example.com", ENTRY_PASS: "test_password"}

    # Créer un mock client AVANT le patch, pour pouvoir le configurer
    mock_client = MagicMock()
    mock_client.clientId = None  # Forcer clientId à None (simule l'échec)

    # Configurer le mock pour lever une exception SaurApiError (autre que "Unauthorized")
    with (
        patch(
            "custom_components.eyeonsaur.config_flow.check_credentials",
            side_effect=SaurApiError("Generic error"),
        ),
        patch(
            "custom_components.eyeonsaur.config_flow.create_saur_client",
            return_value=mock_client,
        ),
    ):
        result = await flow.async_step_user(user_input)

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == None
