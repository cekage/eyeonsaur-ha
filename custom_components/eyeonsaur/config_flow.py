"""Config flow pour l'intégration EyeOnSaur."""

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.loader import async_get_integration
from saur_client import SaurClient

from .helpers.const import (
    DEV,
    DOMAIN,
    ENTRY_ABSOLUTE_CONSUMPTION,
    ENTRY_CREATED_AT,
    ENTRY_MANUFACTURER,
    ENTRY_MODEL,
    ENTRY_SERIAL_NUMBER,
    ENTRY_TOKEN,
    ENTRY_UNIQUE_ID,
)

_LOGGER = logging.getLogger(__name__)

# Schema for initial configuration step (user step)
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("email"): str,
        vol.Required("password"): str,
        vol.Required("discovery", default=False): bool,
    }
)

# Schema for options flow
STEP_OPTIONS_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("water_m3_price", default=0.0): vol.Coerce(float),
        vol.Required("hours_between_reading", default=24): vol.Coerce(int),
    }
)


class EyeOnSaurConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow pour l'intégration EyeOnSaur."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialise le ConfigFlow"""
        super().__init__()
        self.client = None
        self._reauth_entry = None
        self._user_input: dict = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Gère l'étape initiale du config flow (déclenchée par l'utilisateur)."""
        errors: dict[str, str] = {}
        if user_input is not None:
            # Validation des données utilisateur
            errors = await self.validate_input(
                user_input, STEP_USER_DATA_SCHEMA
            )
            if not errors:
                self._user_input.update(user_input)

                # Initialisation du client
                self.client = SaurClient(
                    login=user_input["email"],
                    password=user_input["password"],
                    dev_mode=DEV == 1,
                )

                # Test de connexion
                try:
                    await self.client.authenticate()
                    _LOGGER.debug("auth_result = %s", self.client.access_token)
                except Exception as e:
                    _LOGGER.exception(
                        "Erreur lors de l'authentification : %s", e
                    )
                    errors["base"] = "cannot_connect"

                if not errors:
                    # Récupération des informations de l'utilisateur
                    self._user_input[ENTRY_TOKEN] = self.client.access_token
                    unique_id = self.client.default_section_id

                    if not self._reauth_entry:
                        await self.async_set_unique_id(unique_id)
                        self._abort_if_unique_id_configured()

                    self._user_input[ENTRY_UNIQUE_ID] = unique_id

                    deliverypoints = (
                        await self.client.get_deliverypoints_data()
                    )
                    self._user_input[ENTRY_MANUFACTURER] = deliverypoints.get(
                        "meter", {}
                    ).get("meterBrandCode")
                    self._user_input[ENTRY_MODEL] = deliverypoints.get(
                        "meter", {}
                    ).get("meterModelCode")
                    self._user_input[ENTRY_SERIAL_NUMBER] = deliverypoints.get(
                        "meter", {}
                    ).get("trueRegistrationNumber")
                    self._user_input[ENTRY_CREATED_AT] = deliverypoints.get(
                        "meter", {}
                    ).get("installationDate")

                    self._user_input[ENTRY_ABSOLUTE_CONSUMPTION] = None
                    integration = await async_get_integration(
                        self.hass, DOMAIN
                    )

                    # Création ou mise à jour de l'entrée
                    if not self._reauth_entry:
                        return self.async_create_entry(
                            title=f"{integration.name} - {self._user_input[ENTRY_UNIQUE_ID]}",
                            data=self._user_input,
                        )
                    else:
                        self.hass.config_entries.async_update_entry(
                            self._reauth_entry,
                            data={
                                **self._reauth_entry.data,
                                **self._user_input,
                            },
                        )
                        self.hass.async_create_task(
                            self.hass.config_entries.async_reload(
                                self._reauth_entry.entry_id
                            )
                        )
                        return self.async_abort(reason="reauth_successful")

        # Affichage du formulaire (initial ou avec erreurs) avec description
        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> FlowResult:
        """Handle reauthentication."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        self._user_input = entry_data
        return await self.async_step_user()

    async def validate_input(
        self, data: dict[str, Any], schema: vol.Schema
    ) -> dict[str, Any]:
        """Validate the user input allows us to connect.

        Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
        """
        errors = {}
        try:
            # Validation avec le schema fourni
            schema(data)

        except vol.MultipleInvalid as er:
            # Gestion des erreurs de validation
            for error in er.errors:
                if isinstance(error, vol.Invalid) and error.path == ["email"]:
                    errors["base"] = (
                        "invalid_email"  # Message d'erreur pour email invalide
                    )
                elif isinstance(error, vol.RequiredFieldInvalid):
                    errors[error.path[0]] = "required"
                else:
                    _LOGGER.exception("Erreur de validation inattendue")
                    errors["base"] = "unknown"

        return errors

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Mettre à jour les options de l'entrée de configuration
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                options={**self.config_entry.options, **user_input},
            )
            return self.async_create_entry(title="", data=user_input)

        # Afficher le formulaire des options
        return self.async_show_form(
            step_id="init",
            data_schema=STEP_OPTIONS_DATA_SCHEMA,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
