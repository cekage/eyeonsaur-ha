# tests/test_config_flow.py
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientError
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from saur_client import SaurApiError

from custom_components.eyeonsaur.config_flow import (
    EyeOnSaurConfigFlow,
    async_get_deliverypoints_data,
    create_saur_client,
)
from custom_components.eyeonsaur.helpers.const import (
    CONF_DISCOVERY,
    DOMAIN,
    ENTRY_ABSOLUTE_CONSUMPTION,
    ENTRY_CREATED_AT,
    ENTRY_LOGIN,
    ENTRY_MANUFACTURER,
    ENTRY_MODEL,
    ENTRY_PASS,
    ENTRY_SERIAL_NUMBER,
    ENTRY_TOKEN,
    ENTRY_UNIQUE_ID,
)

# Données de test simulées
TEST_USER_INPUT = {
    ENTRY_LOGIN: "test_login@test.com",
    ENTRY_PASS: "test_password",
    CONF_DISCOVERY: False,
}

MOCK_DELIVERY_POINT_DATA = {
    "deliveryPointId": "test_unique_id",
    "sectionSubscriptionId": "test_section_id",
    "meter": {
        "meterBrandCode": "test_manufacturer",
        "meterModelCode": "test_model",
        "serialNumber": "test_serial_number",
        "trueRegistrationNumber": "A12345Z",
        "installationDate": "2023-01-01T00:00:00",
    },
}


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


async def test_user_step_success(
    hass: HomeAssistant,
    mock_async_get_deliverypoints_data: MagicMock,
    mock_create_saur_client: MagicMock,
):
    """Teste l'étape utilisateur avec succès."""
    mock_client = MagicMock()
    mock_create_saur_client.return_value = mock_client
    mock_client.default_section_id = "test_unique_id"
    mock_client.access_token = "test_token"

    # Mock la réponse de async_get_deliverypoints_data
    mock_async_get_deliverypoints_data.return_value = MOCK_DELIVERY_POINT_DATA

    # On simule l'appel à async_setup_entry pour éviter l'appel au coordinator *après* le config flow
    with patch(
        "custom_components.eyeonsaur.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=TEST_USER_INPUT
        )

        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["title"] == "EyeOnSaur - test_unique_id"
        assert result["data"] == {
            **TEST_USER_INPUT,
            ENTRY_UNIQUE_ID: "test_unique_id",
            ENTRY_TOKEN: "test_token",
            ENTRY_ABSOLUTE_CONSUMPTION: None,
            ENTRY_MANUFACTURER: "test_manufacturer",
            ENTRY_MODEL: "test_model",
            ENTRY_SERIAL_NUMBER: "A12345Z",
            ENTRY_CREATED_AT: "2023-01-01T00:00:00",
        }

        # Vérifie que create_saur_client a été appelée avec les bons arguments
        mock_create_saur_client.assert_called_once_with(
            login=TEST_USER_INPUT[ENTRY_LOGIN],
            password=TEST_USER_INPUT[ENTRY_PASS],
        )

        # Vérifie que async_get_deliverypoints_data a été appelée avec le bon client
        mock_async_get_deliverypoints_data.assert_called_once_with(mock_client)


async def test_user_step_invalid_auth(
    hass: HomeAssistant,
    mock_async_get_deliverypoints_data: MagicMock,
    mock_create_saur_client: MagicMock,
):
    """Teste l'étape utilisateur avec des identifiants invalides."""
    mock_client = MagicMock()
    mock_create_saur_client.return_value = mock_client
    mock_async_get_deliverypoints_data.side_effect = SaurApiError(
        "unauthorized"
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=TEST_USER_INPUT
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_user_step_cannot_connect(hass: HomeAssistant):
    """Teste l'étape utilisateur avec une erreur de connexion."""
    with patch(
        "custom_components.eyeonsaur.config_flow.async_get_deliverypoints_data",
        side_effect=OSError("Simulated connection error"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=TEST_USER_INPUT
        )

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}
