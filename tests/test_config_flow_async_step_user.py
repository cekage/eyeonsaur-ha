"""Tests unitaires pour la méthode async_step_user du config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.eyeonsaur.config_flow import (
    STEP_USER_DATA_SCHEMA,
    EyeOnSaurConfigFlow,
)
from custom_components.eyeonsaur.helpers.const import (
    ENTRY_CLIENTID,
    ENTRY_COMPTEURID,
    ENTRY_LOGIN,
    ENTRY_PASS,
    ENTRY_TOKEN,
    ENTRY_UNDERSTAND,
)


@pytest.mark.asyncio
async def test_async_step_user_init_form(hass: HomeAssistant) -> None:
    """Test de async_step_user pour afficher le formulaire initial."""
    flow = EyeOnSaurConfigFlow()
    flow.hass = hass

    result = await flow.async_step_user()

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["data_schema"] == STEP_USER_DATA_SCHEMA
    assert result["errors"] == {}


@pytest.mark.asyncio
async def test_async_step_user_invalid_input(hass: HomeAssistant) -> None:
    """Test de async_step_user avec des données invalides."""
    flow = EyeOnSaurConfigFlow()
    flow.hass = hass

    # Simuler le retour d'erreurs par first_check_input
    with patch(
        "custom_components.eyeonsaur.config_flow.first_check_input",
        new_callable=AsyncMock,
        return_value=({"base": "invalid_input"}, None),
    ):
        result = await flow.async_step_user(
            user_input={ENTRY_LOGIN: "invalid"}
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {"base": "invalid_input"}
        assert result["data_schema"] == STEP_USER_DATA_SCHEMA


@pytest.mark.asyncio
async def test_async_step_user_invalid_auth(hass: HomeAssistant) -> None:
    """Test de async_step_user avec une authentification invalide."""
    flow = EyeOnSaurConfigFlow()
    flow.hass = hass

    # Simuler un échec d'authentification dans _check_online_credentials
    with patch.object(
        EyeOnSaurConfigFlow,
        "_check_online_credentials",
        new_callable=AsyncMock,
    ) as mock_check:
        mock_check.return_value = None  # Simulate authentication failure
        flow.client = MagicMock()
        flow.client.clientId = None  # Ensure that clientId is None

        result = await flow.async_step_user(
            user_input={ENTRY_LOGIN: "test", ENTRY_PASS: "test"}
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["data_schema"] == STEP_USER_DATA_SCHEMA
        assert result["errors"] == {
            ENTRY_LOGIN: "invalid_email"
        }  # Expect no error message, as in initial code


@pytest.mark.asyncio
async def test_async_step_user_auth_success_no_client_id(
    hass: HomeAssistant,
) -> None:
    """Test de async_step_user avec authentification réussie mais sans clientId."""
    flow = EyeOnSaurConfigFlow()
    flow.hass = hass

    # Simuler une authentification réussie dans _check_online_credentials
    with patch.object(
        EyeOnSaurConfigFlow,
        "_check_online_credentials",
        new_callable=AsyncMock,
    ) as mock_check:
        mock_check.return_value = (
            None  # Simulate successful authentication, no exception
        )

        # Créer un client mais forcer clientId à None
        flow.client = MagicMock()
        flow.client.clientId = None

        result = await flow.async_step_user(
            user_input={
                ENTRY_LOGIN: "test@example.com",
                ENTRY_PASS: "test_password",
            }
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["data_schema"] == STEP_USER_DATA_SCHEMA
        assert (
            result["errors"] == None
        )  # Expect empty errors, as in the original code


@pytest.mark.asyncio
async def test_async_step_user_update_user_input(hass: HomeAssistant) -> None:
    """Test de async_step_user pour vérifier la mise à jour de self._user_input."""
    flow = EyeOnSaurConfigFlow()
    flow.hass = hass

    # Simuler une authentification réussie dans _check_online_credentials
    with patch.object(
        EyeOnSaurConfigFlow,
        "_check_online_credentials",
        new_callable=AsyncMock,
    ) as mock_check:
        mock_check.return_value = None

        # Configurer les valeurs mockées pour le client
        flow.client = MagicMock()
        flow.client.access_token = "mocked_token"
        flow.client.clientId = "mocked_client_id"
        flow.client.default_section_id = "mocked_section_id"

        # Définir les données utilisateur de test
        test_user_input = {
            ENTRY_LOGIN: "test@example.com",
            ENTRY_PASS: "test_password",
        }  # on utilise email et password

        await flow.async_step_user(user_input=test_user_input)

        # Vérifier que self._user_input contient les données attendues
        assert flow._user_input == {
            ENTRY_LOGIN: "test@example.com",  # on utilise email
            ENTRY_PASS: "test_password",  # on utilise password
            ENTRY_TOKEN: "mocked_token",
            ENTRY_CLIENTID: "mocked_client_id",
            ENTRY_COMPTEURID: "mocked_section_id",
        }


@pytest.mark.asyncio
async def test_async_step_user_reauth(hass: HomeAssistant) -> None:
    """Test de async_step_user lors d'une reauthentication."""
    flow = EyeOnSaurConfigFlow()
    flow.hass = hass

    # Simuler une authentification réussie dans _check_online_credentials
    with (
        patch.object(
            EyeOnSaurConfigFlow,
            "_check_online_credentials",
            new_callable=AsyncMock,
        ) as mock_check,
        patch.object(
            hass.config_entries, "async_update_entry", new_callable=AsyncMock
        ) as mock_update,
        patch.object(
            hass.config_entries, "async_reload", new_callable=AsyncMock
        ) as mock_reload,
    ):
        mock_check.return_value = None

        # Configurer les valeurs mockées pour le client
        flow.client = MagicMock()
        flow.client.access_token = "mocked_token"
        flow.client.clientId = "mocked_client_id"
        flow.client.default_section_id = "mocked_section_id"

        # Simuler une entrée de réauthentification
        reauth_entry = MagicMock()
        reauth_entry.entry_id = "test_entry_id"  # MODIFICATION: set entry_id directly to the string value
        flow._reauth_entry = reauth_entry
        flow.context = {"entry_id": "test_entry_id"}  # Mock le contexte

        # Définir les données utilisateur de test
        test_user_input = {
            ENTRY_LOGIN: "test@example.com",
            ENTRY_PASS: "test_password",
        }

        result = await flow.async_step_user(user_input=test_user_input)

        # Vérifier les appels aux fonctions Home Assistant
        mock_update.assert_called_once_with(
            reauth_entry, data=flow._user_input
        )
        mock_reload.assert_called_once_with("test_entry_id")

        # Vérifier le résultat de l'étape
        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "reauth_successful"
