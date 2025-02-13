# tests/test_config_flow_ut1.py
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import MockConfigEntry
from saur_client import SaurApiError

from custom_components.eyeonsaur.config_flow import (
    EyeOnSaurConfigFlow,
)
from custom_components.eyeonsaur.helpers.const import (
    CONF_DISCOVERY,
    DOMAIN,
    ENTRY_LOGIN,
    ENTRY_PASS,
    ENTRY_TOKEN,
    ENTRY_UNIQUE_ID,
    ENTRY_MANUFACTURER,
    ENTRY_MODEL,
    ENTRY_SERIAL_NUMBER,
    ENTRY_CREATED_AT,
    ENTRY_ABSOLUTE_CONSUMPTION,
)


@pytest.fixture
def mock_async_get_deliverypoints_data():
    """Mock la fonction async_get_deliverypoints_data."""
    with patch(
        "custom_components.eyeonsaur.config_flow.async_get_deliverypoints_data"
    ) as mock:
        yield mock


@pytest.fixture
def mock_create_saur_client():
    """Mock la fonction create_saur_client."""
    with patch(
        "custom_components.eyeonsaur.config_flow.create_saur_client"
    ) as mock:
        yield mock


async def test_user_step_deliverypoints_none(
    hass: HomeAssistant,
    mock_async_get_deliverypoints_data: MagicMock,
    mock_create_saur_client: MagicMock,
):
    """Teste l'étape utilisateur quand l'API retourne None pour deliverypoints."""
    mock_client = MagicMock()
    mock_create_saur_client.return_value = mock_client
    mock_async_get_deliverypoints_data.return_value = None

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"

    with pytest.raises(HomeAssistantError) as exc_info:
        await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                ENTRY_LOGIN: "test@example.com",
                ENTRY_PASS: "testpassword",
                CONF_DISCOVERY: True,
            },
        )
    assert (
        str(exc_info.value) == "Impossible de récupérer les données de l'API"
    )


async def test_async_step_reauth(
    hass: HomeAssistant,
    mock_async_get_deliverypoints_data: MagicMock,
    mock_create_saur_client: MagicMock,
):
    """Test that reauthentication flow is correctly setup."""
    # Create a mock config entry
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            ENTRY_LOGIN: "test@example.com",
            ENTRY_PASS: "old_password",
            CONF_DISCOVERY: False,
            ENTRY_UNIQUE_ID: "test_unique_id",
            ENTRY_TOKEN: "old_test_token",
            ENTRY_MANUFACTURER: "test_manufacturer",
            ENTRY_MODEL: "test_model",
            ENTRY_SERIAL_NUMBER: "test_serial_number",
            ENTRY_CREATED_AT: "2023-01-01T00:00:00",
        },
        unique_id="test_unique_id",
    )

    with patch(
        "custom_components.eyeonsaur.__init__.SaurCoordinator.async_config_entry_first_refresh",
        return_value=None,
    ):
        mock_entry.add_to_hass(hass)

        # Mock _handle_api_call pour simuler un échec de réauthentification
        with patch(
            "custom_components.eyeonsaur.config_flow.EyeOnSaurConfigFlow._handle_api_call"
        ) as mock_handle_api_call:
            mock_handle_api_call.return_value = (
                None,  # Simule une erreur d'authentification
                {"base": "invalid_auth"},
            )

            # Initialize a reauthentication flow
            result = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={
                    "source": config_entries.SOURCE_REAUTH,
                    "entry_id": mock_entry.entry_id,
                },
                data=mock_entry.data,
            )

            # Soumettre le formulaire avec les mêmes données
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={
                    ENTRY_LOGIN: "test@example.com",
                    ENTRY_PASS: "old_password",
                    CONF_DISCOVERY: False,
                },
            )

            # Vérifier que le flux affiche le formulaire
            assert result["type"] == data_entry_flow.FlowResultType.FORM
            assert result["errors"] == {"base": "invalid_auth"}


async def test_async_get_options_flow(hass: HomeAssistant):
    """Test that options flow is correctly setup."""
    # Create a mock config entry
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            ENTRY_LOGIN: "test@example.com",
            ENTRY_PASS: "old_password",
        },
        unique_id="test_unique_id",
    )
    mock_entry.add_to_hass(hass)

    # Initialize options flow
    options_flow = EyeOnSaurConfigFlow.async_get_options_flow(mock_entry)
    # Check that we return a OptionsFlowHandler instance
    assert isinstance(
        options_flow,
        EyeOnSaurConfigFlow.async_get_options_flow.__annotations__["return"],
    )
