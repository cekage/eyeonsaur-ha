"""Data update coordinator for the EyeOnSaur integration."""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from saur_client import SaurClient

from .helpers.const import (
    DEV,
    ENTRY_LOGIN,
    ENTRY_PASS,
    ENTRY_TOKEN,
    ENTRY_UNIQUE_ID,
    POLLING_INTERVAL,
)
from .helpers.dateutils import find_missing_dates, sync_reduce_missing_dates
from .helpers.saur_db import SaurDatabaseError, SaurDatabaseHelper
from .recorder import SaurRecorder

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)


class SaurCoordinator(DataUpdateCoordinator):
    """Data update coordinator for the EyeOnSaur integration."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        db_helper: SaurDatabaseHelper,
        recorder: SaurRecorder,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="EyeOnSaur Coordinator",
            update_interval=POLLING_INTERVAL,
            always_update=True,
        )
        self.hass = hass
        self.entry = entry
        self.client = SaurClient(
            login=self.entry.data[ENTRY_LOGIN],
            password=self.entry.data[ENTRY_PASS],
            token=self.entry.data[ENTRY_TOKEN],
            unique_id=self.entry.data[ENTRY_UNIQUE_ID],
            dev_mode=DEV == 1,
        )
        self.db_helper = db_helper
        self.recorder = recorder
        self.prochainedate = None
        self.base_data: dict[str, Any] = {}

    async def async_config_entry_first_refresh(self) -> None:
        """Handle the first refresh."""

        try:
            await self.db_helper.async_init_db()
        except SaurDatabaseError as e:
            _LOGGER.exception("Error initializing database: %s", e)
            raise UpdateFailed(f"Error initializing database: {e}") from e

        # On n'appelle plus authenticate() ici.
        # La première requête réussira car le token et l'unique_id sont déjà connus.

        deliverypoints = await self.client.get_deliverypoints_data()
        _LOGGER.debug("🔥🔥 deliverypoints %s 🔥🔥", deliverypoints)

        _update_token_in_config_entry(self.hass, self.entry, self.client)

        self.base_data = {
            "releve_physique": {"date": None, "valeur": None},
            "created_at": deliverypoints.get(
                "meter",
                {},
            ).get("installationDate"),
            "section_id": self.client.default_section_id,
            "manufacturer": deliverypoints.get(
                "meter",
                {},
            ).get("meterBrandCode"),
            "model": deliverypoints.get("meter", {}).get("meterModelCode"),
            "serial_number": deliverypoints.get("meter", {}).get(
                "trueRegistrationNumber",
            ),
        }
        self.hass.async_create_task(self._async_update_data())
        await super().async_config_entry_first_refresh()

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the API and update the database."""
        _LOGGER.debug(
            "🔥🔥🔥🔥🔥🔥 _async_update_data 🔥🔥🔥🔥🔥🔥",
        )
        await self._async_fetch_last_known_data()
        await self._async_fetch_missing_data()
        return self.base_data

    async def _async_fetch_last_known_data(self):
        """Fetch the last known data from the API."""
        last_known_data = await self.client.get_lastknown_data()
        _LOGGER.debug(
            "🔥🔥 _async_fetch_last_known_data %s 🔥🔥",
            last_known_data,
        )

        if last_known_data:
            self.base_data.setdefault("releve_physique", {})["date"] = (
                last_known_data.get(
                    "readingDate",
                )
            )
            self.base_data.setdefault("releve_physique", {})["valeur"] = (
                last_known_data.get(
                    "indexValue",
                )
            )
            await self.db_helper.async_update_anchor(last_known_data)

    async def _async_fetch_missing_data(self):
        """Fetch missing data."""
        now = datetime.utcnow() - timedelta(days=8) - timedelta(hours=10)
        self.hass.async_add_executor_job(
            self._sync_fetch_periodic_data,
            now.year,
            now.month,
            now.day,
        )

    async def _async_fetch_periodic_data(
        self,
        year: int,
        month: int,
        day: int,
    ) -> None:
        """Wrapper pour la récupération des données hebdomadaires."""
        _LOGGER.debug(
            "🔥🔥 _async_fetch_periodic_data %s %s %s 🔥🔥",
            year,
            month,
            day,
        )
        await self._async_fetch_and_store_data(year, month)  # Ajout de await
        all_consumptions = (
            await self.db_helper.async_get_all_consumptions_with_absolute()
        )
        await self._async_inject_historical_data(all_consumptions)
        await self._async_handle_missing_dates(all_consumptions)

    async def _async_fetch_and_store_data(self, year: int, month: int):
        """Récupère et stocke les données mensuelles."""
        monthly_data = await self.client.get_monthly_data(year, month)
        if not monthly_data:
            return
        await self.db_helper.async_write_consumptions(
            monthly_data["consumptions"],
        )

    async def _async_inject_historical_data(self, all_consumptions):
        """Injecte les données historiques dans le recorder."""
        default_section_id = f"{self.client.default_section_id}"
        if all_consumptions:
            for date, value in all_consumptions:
                date_formatted = datetime.fromisoformat(date)
                _LOGGER.debug(
                    "🔥🔥 all_consumptions self.client.default_section_id:"
                    " %s %s %s 🔥🔥",
                    self.client.default_section_id,
                    date_formatted,
                    value,
                )
                await self.recorder.async_inject_historical_data(
                    default_section_id,
                    date_formatted,
                    value,
                )

    async def _async_handle_missing_dates(self, all_consumptions):
        """Gère les dates manquantes."""
        missing_dates = find_missing_dates(all_consumptions)
        _LOGGER.debug("🔥🔥 missing_dates: %s 🔥🔥", missing_dates)

        reduced_missing_dates = sync_reduce_missing_dates(missing_dates)
        _LOGGER.debug(
            "🔥🔥 reduced_missing_dates: %s 🔥🔥", reduced_missing_dates
        )
        if reduced_missing_dates and len(reduced_missing_dates) > 0:
            y, m, d = reduced_missing_dates.pop()
            delay = random.uniform(8, 35)
            _LOGGER.debug("Temporisation de %s secondes", delay)
            await asyncio.sleep(1)
            self.hass.async_add_executor_job(
                self._sync_fetch_periodic_data,
                y,
                m,
                d,
            )

    def _sync_fetch_periodic_data(
        self,
        year: int,
        month: int,
        day: int,
    ) -> None:
        """Fonction synchrone pour la récupération des données hebdo."""
        # Exécuter la coroutine dans le contexte Home Assistant
        future = asyncio.run_coroutine_threadsafe(
            self._async_fetch_periodic_data(year, month, day),
            self.hass.loop,
        )
        # Attendre que le futur soit terminé, sans rien retourner
        future.result()


def _update_token_in_config_entry(
    hass: HomeAssistant, entry: ConfigEntry, client: SaurClient
) -> None:
    """Met à jour le token dans l'entrée de configuration si nécessaire."""
    if client.access_token != entry.data[ENTRY_TOKEN]:
        new_data = entry.data.copy()
        new_data[ENTRY_TOKEN] = client.access_token
        hass.config_entries.async_update_entry(entry, data=new_data)
