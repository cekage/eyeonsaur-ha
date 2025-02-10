"""Tests pour le config flow de l'intégration EyeOnSaur."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from saur_client import SaurApiError

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

INVALID_EMAIL_INPUT = {
    ENTRY_LOGIN: "invalid_email",
    ENTRY_PASS: "test_password",
    CONF_DISCOVERY: False,
}

EMPTY_PASSWORD_INPUT = {
    ENTRY_LOGIN: "test_login@test.com",
    ENTRY_PASS: "",
    CONF_DISCOVERY: False,
}

# On utilise maintenant la *vraie* structure de la réponse de l'API (simplifiée)
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

TEST_OPTIONS_INPUT = {
    "water_m3_price": 2.5,
    "hours_between_reading": 12,
}


@pytest.fixture
def mock_saur_client():
    """Mock la classe SaurClient."""
    with patch(
        "custom_components.eyeonsaur.config_flow.SaurClient"
    ) as mock_client:
        yield mock_client


async def test_user_step_success(
    hass: HomeAssistant, mock_saur_client: MagicMock
):
    """Teste l'étape utilisateur avec succès."""
    mock_instance = AsyncMock()
    mock_saur_client.return_value = mock_instance

    # On mocke la réponse avec la *vraie* structure
    mock_instance.get_deliverypoints_data.return_value = (
        MOCK_DELIVERY_POINT_DATA
    )
    mock_instance.default_section_id = "test_unique_id"
    mock_instance.access_token = "test_token"

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
        # Assertion correcte, basée sur la *vraie* structure et la logique de config_flow.py
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


async def test_user_step_invalid_auth(
    hass: HomeAssistant, mock_saur_client: MagicMock
):
    """Teste l'étape utilisateur avec des identifiants invalides."""
    mock_instance = AsyncMock()
    mock_saur_client.return_value = mock_instance
    # On simule une erreur d'authentification.
    mock_instance.get_deliverypoints_data.side_effect = SaurApiError(
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
    # On vérifie que le flux retourne un formulaire avec une erreur "invalid_auth"
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_user_step_unknown_error(
    hass: HomeAssistant, mock_saur_client: MagicMock
):
    """Teste l'étape utilisateur avec une erreur inconnue."""
    mock_instance = AsyncMock()
    mock_saur_client.return_value = mock_instance
    # On simule une erreur inconnue.
    mock_instance.get_deliverypoints_data.side_effect = SaurApiError(
        "Unknown error"
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
    assert result["errors"] == {"base": "unknown"}


async def test_user_step_invalid_email(hass: HomeAssistant):
    """Teste l'étape utilisateur avec une adresse e-mail invalide."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=INVALID_EMAIL_INPUT
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {ENTRY_LOGIN: "invalid_email"}


async def test_user_step_empty_password(hass: HomeAssistant):
    """Teste l'étape utilisateur avec un mot de passe vide."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=EMPTY_PASSWORD_INPUT
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {ENTRY_PASS: "required"}


async def test_user_step_default_section_id_none(
    hass: HomeAssistant, mock_saur_client: MagicMock
):
    """Teste l'étape utilisateur avec default_section_id à None."""
    mock_instance = AsyncMock()
    mock_saur_client.return_value = mock_instance
    mock_instance.get_deliverypoints_data.return_value = {}  # Réponse valide, mais...
    mock_instance.default_section_id = None  # ...default_section_id est None

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=TEST_USER_INPUT
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_options_flow(hass: HomeAssistant, mock_saur_client: MagicMock):
    """Teste le flux des options (intégration)."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=TEST_USER_INPUT, options={}
    )
    config_entry.add_to_hass(hass)

    # Pas besoin de mocker SaurClient ici, car nous ne passons pas par le config flow

    # Initialise le flux d'options.  Le 'handler' est l'ID de l'entrée.
    result = await hass.config_entries.options.async_init(
        config_entry.entry_id
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "init"

    # Configure le flux avec les données utilisateur.
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input=TEST_OPTIONS_INPUT
    )

    # Vérifie que l'entrée a été créée/mise à jour.
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert config_entry.options == TEST_OPTIONS_INPUT
