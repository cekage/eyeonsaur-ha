"""Config flow pour l'intégration EyeOnSaur."""

import logging
from typing import Any

import voluptuous as vol
from aiohttp.client_exceptions import ClientConnectorError, ClientError
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    TextSelector,  # pyright: ignore[reportUnknownVariableType]
    TextSelectorConfig,
    TextSelectorType,
)
from saur_client import SaurApiError, SaurClient

from .helpers.const import (
    DEV,
    DOMAIN,
    ENTRY_CLIENTID,
    ENTRY_COMPTEURID,
    ENTRY_LOGIN,
    ENTRY_PASS,
    ENTRY_TOKEN,
    ENTRY_UNDERSTAND,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(ENTRY_LOGIN): TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.EMAIL, autocomplete="username"
            )
        ),
        vol.Required(ENTRY_PASS): TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.PASSWORD, autocomplete="current-password"
            )
        ),
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


async def first_check_input(
    data: dict[str, Any],
) -> tuple[dict[str, str], Exception | None]:
    """Validate the user input."""
    errors: dict[str, str] = {}
    exception = None

    if "@" not in data[ENTRY_LOGIN]:
        errors[ENTRY_LOGIN] = "invalid_email"
        exception = ValueError(f"Invalid email: {data[ENTRY_LOGIN]}")

    if not data[ENTRY_PASS]:
        errors[ENTRY_PASS] = "required"
        exception = ValueError(f"{ENTRY_PASS} is required")

    return errors, exception


async def check_credentials(
    client: SaurClient,
) -> None:
    """Encapsulation de l'appel API, pour le mocking."""
    _LOGGER.debug("1/x _async_get_deliverypoints_data")
    try:
        await client._authenticate()
        _LOGGER.debug("2/x _async_get_deliverypoints_data")
    except SaurApiError as err:
        if "unauthorized" in str(err).lower():
            _LOGGER.error(
                "Erreur lors de la récupération des données: %s", err
            )  # Utilise _LOGGER.error au lieu de .exception
            raise  # Pour l'authentification, on relance
        else:
            # Unexpected SaurApiError: log the exception and re-raise
            _LOGGER.exception(
                "Erreur lors de la récupération des données: %s", err
            )  # Utilise _LOGGER.exception
            raise  # Pour toute autre erreur, on relance
    except ClientConnectorError as err:
        # Connection error: log the exception and re-raise
        _LOGGER.exception(
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

    async def _check_online_credentials(
        self, user_input: dict[str, Any]
    ) -> None:
        """Gère l'appel à l'API et la récupération des données."""
        errors: dict[str, str] = {}
        self.client = create_saur_client(
            login=user_input[ENTRY_LOGIN],
            password=user_input[ENTRY_PASS],
        )
        try:
            # Appel à la méthode encapsulée
            _LOGGER.debug(" 1/x _check_online_credentials pending ")

            await check_credentials(self.client)

            _LOGGER.debug(" 2/x _check_online_credentials done ")
            return

        except SaurApiError as err:
            # Seule vérification : "unauthorized" (insensible à la casse)
            if "unauthorized" in str(err).lower():
                errors["base"] = "invalid_auth"
            else:
                errors["base"] = "unknown"
            return

        except (ClientError, OSError):
            return

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

        errors, exception = await first_check_input(user_input)
        if errors:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors=errors,
                description_placeholders={
                    "error_detail": str(exception) if exception else ""
                },
            )

        await self._check_online_credentials(user_input)
        if not self.client.clientId:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        self._user_input.update(user_input)
        user_data = {
            ENTRY_TOKEN: self.client.access_token,
            ENTRY_CLIENTID: self.client.clientId,
            ENTRY_COMPTEURID: self.client.default_section_id,
        }
        self._user_input.update(user_data)

        if not self._reauth_entry:
            return self.async_create_entry(
                title=(f"EyeOnSaur - {self._user_input[ENTRY_LOGIN]}"),
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
        # self._reauth_entry = self.hass.config_entries.async_get_entry(
        #     self.context["entry_id"]
        # )
        entry_id = self.context.get("entry_id")
        if entry_id is not None:
            self._reauth_entry = self.hass.config_entries.async_get_entry(
                entry_id
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
