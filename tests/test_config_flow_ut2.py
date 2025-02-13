# tests/test_config_flow_ut2.py
"""Tests pour le config flow de l'intégration EyeOnSaur - UT2."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.eyeonsaur.config_flow import (
    EyeOnSaurConfigFlow,
    OptionsFlowHandler,
    validate_input,
)
from custom_components.eyeonsaur.helpers.const import (
    DOMAIN,
    ENTRY_LOGIN,
    ENTRY_PASS,
)

TEST_OPTIONS_INPUT = {"water_m3_price": 2.5, "hours_between_reading": 12}


async def test_validate_input_invalid_email(hass: HomeAssistant):
    """Teste la validation d'entrée avec une adresse e-mail invalide."""
    user_input = {ENTRY_LOGIN: "invalid-email", ENTRY_PASS: "test_password"}
    errors, exception = await validate_input(user_input)
    assert errors == {ENTRY_LOGIN: "invalid_email"}
    assert isinstance(exception, ValueError)
    assert "Invalid email" in str(exception)


async def test_validate_input_empty_password(hass: HomeAssistant):
    """Teste la validation d'entrée avec un mot de passe vide."""
    user_input = {ENTRY_LOGIN: "test@example.com", ENTRY_PASS: ""}
    errors, exception = await validate_input(user_input)
    assert errors == {ENTRY_PASS: "required"}
    assert isinstance(exception, ValueError)
    assert ENTRY_PASS in str(exception)
    assert "required" in str(exception)


# tests/test_config_flow_ut2.py
"""Tests pour le config flow de l'intégration EyeOnSaur - UT2."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.eyeonsaur.config_flow import (
    OptionsFlowHandler,
    validate_input,
)
from custom_components.eyeonsaur.helpers.const import (
    DOMAIN,
    ENTRY_LOGIN,
    ENTRY_PASS,
)

TEST_OPTIONS_INPUT = {"water_m3_price": 2.5, "hours_between_reading": 12}


async def test_validate_input_invalid_email(hass: HomeAssistant):
    """Teste la validation d'entrée avec une adresse e-mail invalide."""
    user_input = {ENTRY_LOGIN: "invalid-email", ENTRY_PASS: "test_password"}
    errors, exception = await validate_input(user_input)
    assert errors == {ENTRY_LOGIN: "invalid_email"}
    assert isinstance(exception, ValueError)
    assert "Invalid email" in str(exception)


async def test_validate_input_empty_password(hass: HomeAssistant):
    """Teste la validation d'entrée avec un mot de passe vide."""
    user_input = {ENTRY_LOGIN: "test@example.com", ENTRY_PASS: ""}
    errors, exception = await validate_input(user_input)
    assert errors == {ENTRY_PASS: "required"}
    assert isinstance(exception, ValueError)
    assert ENTRY_PASS in str(exception)
    assert "required" in str(exception)


async def test_options_flow_init_step(hass: HomeAssistant):
    """Test the options flow init step."""
    # Crée une entrée de configuration mockée
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data={ENTRY_LOGIN: "test@example.com", ENTRY_PASS: "testpassword"},
        options={},
        unique_id="test_unique_id",
    )
    mock_entry.add_to_hass(hass)

    # Crée un OptionsFlowHandler
    options_flow = OptionsFlowHandler(mock_entry)
    options_flow.hass = hass

    # Simule l'appel à async_step_init sans user_input
    result = await options_flow.async_step_init()

    # Vérifie que le résultat est un formulaire
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "init"

    # Simule l'appel à async_step_init avec user_input
    with (
        patch.object(
            hass.config_entries, "async_update_entry", return_value=None
        ) as mock_update_entry,
        patch.object(
            options_flow,
            "async_create_entry",
            return_value={
                "type": data_entry_flow.FlowResultType.CREATE_ENTRY,
                "data": TEST_OPTIONS_INPUT,
            },
        ) as mock_create_entry,
    ):
        result = await options_flow.async_step_init(
            user_input=TEST_OPTIONS_INPUT
        )

        # Vérifie que l'entrée a été créée avec les options
        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["data"] == TEST_OPTIONS_INPUT
        # Vérifie que async_update_entry a été appelée avec les bonnes options
        mock_update_entry.assert_called_once_with(
            mock_entry,
            options={**mock_entry.options, **TEST_OPTIONS_INPUT},
        )
