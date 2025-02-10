"""Usefull constants for the EyeOnSaur integration."""

# pylint: disable=E0401

from datetime import timedelta
from typing import TYPE_CHECKING, Final

from homeassistant.const import (
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_SERIAL_NUMBER,
    CONF_DISCOVERY,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_TOKEN,
    CONF_UNIQUE_ID,
)

DOMAIN: Final = "eyeonsaur"
PLATFORMS: Final = ["sensor"]

if TYPE_CHECKING:
    DEV: Final[bool] = False  # During type checking, DEV is False
else:
    DEV: Final[bool] = False  # At runtime !

DEFAULT_POLLING_INTERVAL = timedelta(hours=12)
DEV_POLLING_INTERVAL = timedelta(minutes=5)

POLLING_INTERVAL = DEV_POLLING_INTERVAL if DEV else DEFAULT_POLLING_INTERVAL

ENTRY_LOGIN: Final = CONF_EMAIL
ENTRY_PASS: Final = CONF_PASSWORD
ENTRY_UNDERSTAND: Final = CONF_DISCOVERY
ENTRY_TOKEN: Final = CONF_TOKEN
ENTRY_UNIQUE_ID: Final = CONF_UNIQUE_ID
ENTRY_MANUFACTURER: Final = ATTR_MANUFACTURER
ENTRY_MODEL: Final = ATTR_MODEL
ENTRY_SERIAL_NUMBER: Final = ATTR_SERIAL_NUMBER
ENTRY_CREATED_AT: Final = "created_at"
ENTRY_ABSOLUTE_CONSUMPTION: Final = "absolute_consumption"

USERNAME: Final = "john@example.com"  # Adresse email du client
PASSWORD: Final = "FAKEPASSWORD"  # Mot de passe du client
# PLATFORMS: list[Platform]: Final = [Platform.SENSOR]
