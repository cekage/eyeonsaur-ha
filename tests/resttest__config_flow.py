"""Tests pour le config flow de l'intégration EyeOnSaur."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.eyeonsaur.helpers.const import (
    CONF_DISCOVERY,
    DOMAIN,
    ENTRY_LOGIN,
    ENTRY_PASS,
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


async def test_reauth_step(hass: HomeAssistant, mock_saur_client: MagicMock):
    """Teste le flux de réauthentification."""
    mock_instance = AsyncMock()
    mock_saur_client.return_value = mock_instance
    mock_instance.get_deliverypoints_data.return_value = (
        MOCK_DELIVERY_POINT_DATA
    )
    mock_instance.default_section_id = "test_unique_id"
    mock_instance.access_token = (
        "new_token"  # On imagine que le token a changé
    )

    # 1. On crée d'abord une entrée existante (comme si l'utilisateur s'était déjà authentifié)
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data=TEST_USER_INPUT,
        unique_id="test_unique_id",
    )
    mock_entry.add_to_hass(hass)

    # 2. On simule une tentative de réauthentification
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": mock_entry.entry_id,
        },
        data=TEST_USER_INPUT,  # On fournit les mêmes identifiants (on pourrait en tester d'autres)
    )

    assert (
        result["type"] == data_entry_flow.FlowResultType.FORM
    )  # On s'attend à un formulaire
    assert result["step_id"] == "user"  # On revient à l'étape "user"

    # 3. On re-soumet le formulaire (avec les mêmes ou de nouveaux identifiants)
    with patch(
        "custom_components.eyeonsaur.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=TEST_USER_INPUT
        )

    assert (
        result["type"] == data_entry_flow.FlowResultType.ABORT
    )  # MODIF: type = ABORT
    assert (
        result["reason"] == "reauth_successful"
    )  # MODIF: reason = reauth_successful


async def test_user_step_cannot_connect(
    hass: HomeAssistant, mock_saur_client: MagicMock
):
    """Teste l'étape utilisateur avec une erreur de connexion."""
    mock_instance = AsyncMock()
    mock_saur_client.return_value = mock_instance
    # On simule une OSError, c'est suffisant.
    mock_instance.get_deliverypoints_data.side_effect = OSError(
        "Simulated OSError"
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
    assert result["errors"] == {"base": "cannot_connect"}
