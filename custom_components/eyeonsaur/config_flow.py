"""Config flow pour l'intégration EyeOnSaur."""

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from aiohttp.client_exceptions import ClientError
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.loader import async_get_integration
from saur_client import SaurApiError, SaurClient, SaurResponseDelivery

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
    ENTRY_UNDERSTAND,
    ENTRY_UNIQUE_ID,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(ENTRY_LOGIN): str,
        vol.Required(ENTRY_PASS): str,
        vol.Required(ENTRY_UNDERSTAND): bool,
    }
)

# Schema for options flow
STEP_OPTIONS_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("water_m3_price"): float,
        vol.Required("hours_between_reading"): int,
    }
)


async def validate_input(
    data: dict[str, Any],
) -> tuple[dict[str, str], Exception | None]:
    """Validate the user input."""
    errors = {}
    exception = None

    if "@" not in data[ENTRY_LOGIN]:
        errors[ENTRY_LOGIN] = "invalid_email"
        exception = ValueError(f"Invalid email: {data[ENTRY_LOGIN]}")

    if not data[ENTRY_PASS]:
        errors[ENTRY_PASS] = "required"
        exception = ValueError(f"{ENTRY_PASS} is required")

    return errors, exception


async def async_get_deliverypoints_data(
    client: SaurClient,
) -> SaurResponseDelivery | None:
    """Encapsulation de l'appel API, pour le mocking."""
    _LOGGER.debug("1/x _async_get_deliverypoints_data")
    try:
        await client._authenticate()
        reponse: SaurResponseDelivery = await client.get_deliverypoints_data()
        _LOGGER.debug("2/x _async_get_deliverypoints_data")
        return reponse
    except SaurApiError as err:
        _LOGGER.error(  # Utilise _LOGGER.error au lieu de .exception
            "Erreur lors de la récupération des données: %s", err
        )
        if "unauthorized" in str(err).lower():
            raise  # Pour l'authentification, on relance
        raise  # Pour toute autre erreur, on relance
    except aiohttp.client_exceptions.ClientConnectorError as err:
        _LOGGER.error(
            "Erreur de connexion lors de la récupération des données : %s",
            err,
        )
        raise  # On relance pour laisser un niveau supérieur gérer


def create_saur_client(login: str, password: str) -> SaurClient:
    """Factory pour créer une instance de SaurClient."""
    return SaurClient(login=login, password=password, dev_mode=DEV)


class EyeOnSaurConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow pour l'intégration EyeOnSaur."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialise le ConfigFlow"""
        super().__init__()
        self.client: SaurClient
        self._reauth_entry: ConfigEntry[Any] | None = None
        self._user_input: dict[str, Any] = {}

    async def _handle_api_call(
        self, user_input: dict[str, Any]
    ) -> tuple[dict[str, Any] | None, dict[str, str]]:
        """Gère l'appel à l'API et la récupération des données."""
        errors = {}
        self.client = create_saur_client(
            login=user_input[ENTRY_LOGIN],
            password=user_input[ENTRY_PASS],
        )
        try:
            # Appel à la méthode encapsulée
            deliverypoints = await async_get_deliverypoints_data(self.client)

            # Gère le cas où _async_get_deliverypoints_data retourne None
            if deliverypoints is None:
                _LOGGER.critical(
                    "L'API SAUR a retourné des données invalides (None)."
                )
                raise HomeAssistantError(
                    "Impossible de récupérer les données de l'API"
                )
            _LOGGER.debug(
                " 2/x _handle_api_call deliverypoints = %s ", deliverypoints
            )
            unique_id = self.client.default_section_id

            meter = deliverypoints.get("meter", {})
            user_data = {
                ENTRY_UNIQUE_ID: unique_id,
                ENTRY_TOKEN: self.client.access_token,
                ENTRY_ABSOLUTE_CONSUMPTION: None,
                ENTRY_MANUFACTURER: meter.get("meterBrandCode"),
                ENTRY_MODEL: meter.get("meterModelCode"),
                ENTRY_SERIAL_NUMBER: meter.get("trueRegistrationNumber"),
                ENTRY_CREATED_AT: meter.get("installationDate"),
            }
            _LOGGER.debug(" 3/x _handle_api_call ")
            return user_data, {}

        except SaurApiError as err:
            # Seule vérification : "unauthorized" (insensible à la casse)
            if "unauthorized" in str(err).lower():
                errors["base"] = "invalid_auth"
            else:
                errors["base"] = "unknown"
            return None, errors

        except (ClientError, OSError):
            return None, {"base": "cannot_connect"}

    # core/homeassistant/components/tplink_omada/config_flow.py
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Gère l'étape initiale du config flow (déclenchée par l'user)."""

        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors={},
            )

        errors, exception = await validate_input(user_input)
        if errors:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors=errors,
                description_placeholders={
                    "error_detail": str(exception) if exception else ""
                },
            )

        user_data, api_errors = await self._handle_api_call(user_input)
        if api_errors:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors=api_errors,
                description_placeholders={
                    "error_detail": (
                        next(iter(api_errors.values())) if api_errors else ""
                    )
                },
            )

        self._user_input.update(user_input)
        if user_data:
            self._user_input.update(user_data)

        integration = await async_get_integration(self.hass, DOMAIN)

        if not self._reauth_entry:
            return self.async_create_entry(
                title=(
                    f"{integration.name} - {self._user_input[ENTRY_UNIQUE_ID]}"
                ),
                data=self._user_input,
            )
        self.hass.config_entries.async_update_entry(
            self._reauth_entry, data=self._user_input
        )
        await self.hass.config_entries.async_reload(
            self._reauth_entry.entry_id
        )
        return self.async_abort(reason="reauth_successful")

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauthentication."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_user(user_input=entry_data)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
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
