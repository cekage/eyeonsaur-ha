"""Config flow pour l'intégration EyeOnSaur."""

import logging
from collections.abc import Mapping
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.loader import async_get_integration
from saur_client import SaurApiError, SaurClient

from .helpers.const import (
    DEV,
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

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

# Schema for initial configuration step (user step)
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(ENTRY_LOGIN): str,
        vol.Required(ENTRY_PASS): str,
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
        """Gère l'étape initiale du config flow
        (déclenchée par l'utilisateur)."""

        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors={},
            )

        errors = await self.validate_input(user_input, STEP_USER_DATA_SCHEMA)
        if errors:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors=errors,
                description_placeholders={
                    "error_detail": str(err) if "err" in locals() else ""
                },
            )

        self._user_input.update(user_input)

        # Initialisation du client
        self.client = SaurClient(
            login=user_input[ENTRY_LOGIN],
            password=user_input[ENTRY_PASS],
            dev_mode=DEV == 1,
        )

        try:
            # Appel à l'API AVANT de récupérer l'ID
            deliverypoints = await self.client.get_deliverypoints_data()

            # Récupération des informations de l'utilisateur APRÈS l'appel à l'API
            unique_id = self.client.default_section_id
            self._user_input[ENTRY_UNIQUE_ID] = unique_id
            self._user_input[ENTRY_TOKEN] = self.client.access_token
            self._user_input[ENTRY_ABSOLUTE_CONSUMPTION] = None

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

            integration = await async_get_integration(self.hass, DOMAIN)

            if not self._reauth_entry:
                # Création de l'entrée avec token et unique_id
                return self.async_create_entry(
                    title=f"{integration.name} - {unique_id}",
                    data=self._user_input,
                )
            else:
                # Mise à jour de l'entrée existante avec le nouveau token
                self.hass.config_entries.async_update_entry(
                    self._reauth_entry, data=self._user_input
                )
                await self.hass.config_entries.async_reload(
                    self._reauth_entry.entry_id
                )
                return self.async_abort(reason="reauth_successful")

        except SaurApiError as err:
            _LOGGER.exception(
                "Erreur lors de la récupération des données: %s", err
            )
            # On infère le type d'erreur à partir du message.
            if "401" in str(err) or "403" in str(err):
                errors["base"] = "cannot_connect"
            else:
                errors["base"] = "unknown"

            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors=errors,
                description_placeholders={"error_detail": str(err)},
            )
        except aiohttp.client_exceptions.ClientConnectorError as err:
            _LOGGER.exception(
                "Erreur de connexion lors de la récupération des données: %s",
                err,
            )
            errors["base"] = "cannot_connect"

            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors=errors,
                description_placeholders={"error_detail": str(err)},
            )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> FlowResult:
        """Handle reauthentication."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_user(user_input=entry_data)

    async def validate_input(
        self, data: dict[str, Any], schema: vol.Schema
    ) -> dict[str, Any]:
        """Validate the user input allows us to connect.

        Data has the keys from STEP_USER_DATA_SCHEMA
        with values provided by the user.
        """
        errors = {}
        try:
            # Validation avec le schema fourni
            schema(data)

        except vol.MultipleInvalid as er:
            # Gestion des erreurs de validation
            for error in er.errors:
                if isinstance(error, vol.Invalid) and error.path == [
                    ENTRY_LOGIN
                ]:
                    # Message d'erreur pour email invalide
                    errors["base"] = "invalid_email"
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
                self._config_entry,
                options={**self._config_entry.options, **user_input},
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
