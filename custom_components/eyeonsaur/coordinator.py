"""Data update coordinator for the EyeOnSaur integration."""

import asyncio
import logging
import random
from asyncio import Task
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Any

from aiohttp import ClientResponseError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import IntegrationError
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)
from saur_client import (
    SaurClient,
    SaurResponseDelivery,
    SaurResponseLastKnow,
    SaurResponseMonthly,
)

from .helpers.const import (
    DEV,
    ENTRY_LOGIN,
    ENTRY_PASS,
    ENTRY_TOKEN,
    ENTRY_UNIQUE_ID,
    POLLING_INTERVAL,
)
from .helpers.dateutils import find_missing_dates, sync_reduce_missing_dates
from .helpers.saur_db import SaurDatabaseHelper
from .models import (
    BaseData,
    ConsumptionData,
    ConsumptionDatas,
    MissingDates,
    RelevePhysique,
    TheoreticalConsumptionDatas,
)
from .recorder import SaurRecorder

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG,
    format="""%(asctime)s - %(name)s - %(funcName)s[n°%(lineno)d]
            - %(levelname)s - %(message)s""",
)
_LOGGER = logging.getLogger(__name__)

# class SaurCoordinator(DataUpdateCoordinator[BaseData]):


class SaurCoordinator(DataUpdateCoordinator):
    """Data update coordinator for the EyeOnSaur integration."""

    UPDATE_DEBOUNCE = 30

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
            dev_mode=DEV,
        )
        self.db_helper = db_helper
        self.recorder = recorder
        self.base_data: BaseData = BaseData()
        self._last_update_time: datetime = datetime.now()

        # Ajout de la blacklist
        self.blacklisted_months: set[tuple[int, int]] = set()
        self._background_tasks: list[Task[None]] = []

    async def async_shutdown(self) -> None:
        """Arrête le coordinateur et ferme la session aiohttp."""
        _LOGGER.debug("Arrêt du coordinateur")
        for task in self._background_tasks:
            task.cancel()
        if self.client:
            await self.client.close_session()

    async def async_config_entry_first_refresh(self) -> None:
        """Handle the first refresh."""

        _LOGGER.debug("🔥🔥 async_config_entry_first_refresh 🔥🔥")
        await self.db_helper.async_init_db()

        deliverypoints: SaurResponseDelivery = (
            await self.client.get_deliverypoints_data()
        )
        if deliverypoints is None:
            raise IntegrationError(
                "Impossible de récupérer les points de livraison"
                "depuis l'API SAUR."
            )
        _LOGGER.debug("🔥🔥 deliverypoints %s 🔥🔥", deliverypoints)

        _update_token_in_config_entry(self.hass, self.entry, self.client)

        # Extraction des données
        meter = deliverypoints.get("meter", {})
        releve_physique = RelevePhysique(date="1970-01-01 00:00:00")
        created_at = meter.get("installationDate")
        section_id = self.client.default_section_id
        manufacturer = meter.get("meterBrandCode")
        model = meter.get("meterModelCode")
        serial_number = meter.get("trueRegistrationNumber")

        # Création de l'instance BaseData
        self.base_data = BaseData(
            releve_physique=releve_physique,
            created_at=created_at,
            section_id=section_id,
            manufacturer=manufacturer,
            model=model,
            serial_number=serial_number,
        )

        _LOGGER.debug("🔥🔥 self.base_data %s 🔥🔥", self.base_data)

        now: datetime = (
            datetime.utcnow() - timedelta(days=1) - timedelta(hours=10)
        )
        task = self.hass.async_create_task(
            self._async_fetch_monthly_data(now.year, now.month)
        )
        self._background_tasks.append(task)
        task = self.hass.async_create_task(self._async_backgroundupdate_data())
        self._background_tasks.append(task)
        await super().async_config_entry_first_refresh()

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the API and update the database."""
        _LOGGER.debug(
            "🔥🔥🔥🔥 _async_update_data 🔥🔥🔥🔥",
        )
        now: datetime = datetime.now()

        if (
            now - self._last_update_time
        ).total_seconds() >= self.UPDATE_DEBOUNCE:
            task = self.hass.async_create_task(
                self._async_backgroundupdate_data()
            )
            self._background_tasks.append(task)
            self._last_update_time = now

        return asdict(self.base_data)

    async def _async_backgroundupdate_data(self) -> None:
        """Background task to fetch data from API and update."""
        _LOGGER.debug(
            "🔥🔥🔥🔥🔥🔥 _async_backgroundupdate_data 🔥🔥🔥🔥🔥🔥",
        )
        # Récupération de l'ancre
        await self._async_apifetch_lastknown_data()

        # Récupération de la semaine passée
        # await self._async_fetch_last_week_data()
        datetime.utcnow() - timedelta(days=1) - timedelta(hours=10)
        # (await self.i(now.year, now.month),)

    async def _async_apifetch_lastknown_data(self) -> None:
        """Fetch the last known data from the API."""
        lastknown_data: SaurResponseLastKnow = (
            await self.client.get_lastknown_data()
        )
        _LOGGER.debug(
            "🔥🔥 _async_apifetch_lastknown_data %s 🔥🔥",
            lastknown_data,
        )

        if lastknown_data and "readingDate" in lastknown_data:
            releve_physique = RelevePhysique(
                date=str(lastknown_data.get("readingDate")),
                valeur=lastknown_data.get("indexValue"),
            )
            await self.db_helper.async_update_anchor(releve_physique)

    async def _async_apifetch_and_sqlstore_monthly_data(
        self, year: int, month: int
    ) -> None:
        """Récupère et stocke les données mensuelles."""
        try:
            monthly_data: SaurResponseMonthly = (
                await self.client.get_monthly_data(year, month)
            )
        except ClientResponseError:
            # Ajoute à la blacklist en cas d'erreur
            self.blacklisted_months.add((year, month))
            _LOGGER.warning(f"""Mois blacklisted ({year}, {month})
                car non disponible""")
            return
        if not monthly_data:
            return
        consumptiondatas: ConsumptionDatas = ConsumptionDatas(
            [
                ConsumptionData(
                    startDate=item["startDate"],
                    value=item["value"],
                    rangeType=item["rangeType"],
                )
                for item in monthly_data["consumptions"]
            ]
        )
        await self.db_helper.async_write_consumptions(
            consumptiondatas,
        )

    async def _async_fetch_monthly_data(
        self,
        year: int,
        month: int,
    ) -> None:
        """Wrapper pour la récupération des données hebdomadaires."""
        _LOGGER.debug(
            "🔥🔥 _async_fetch_monthly_data %s %s no_day 🔥🔥",
            year,
            month,
        )
        await self._async_apifetch_and_sqlstore_monthly_data(year, month)

        # Get all consumptions from SQLITE
        all_consumptions: TheoreticalConsumptionDatas = (
            await self.db_helper.async_get_all_consumptions_with_absolute()
        )

        # Recalculate all historical data
        await self._async_inject_historical_data(all_consumptions)

        # Détecte et traite les jours manquants
        await self._async_handle_missing_dates(all_consumptions)

    async def _async_inject_historical_data(
        self, all_consumptions: TheoreticalConsumptionDatas
    ) -> None:
        """Injecte les données historiques dans le recorder."""
        if not all_consumptions:
            return
        default_section_id = f"{self.client.default_section_id}"
        for a_consumption in all_consumptions:
            date_formatted = datetime.fromisoformat(a_consumption.date)
            _LOGGER.debug(
                "🔥🔥 all_consumptions self.client.default_section_id:"
                " %s %s %s 🔥🔥",
                self.client.default_section_id,
                date_formatted,
                a_consumption.indexValue,
            )
            await self.recorder.async_inject_historical_data(
                default_section_id,
                date_formatted,
                a_consumption.indexValue,
            )

    async def _async_handle_missing_dates(
        self, all_consumptions: TheoreticalConsumptionDatas
    ) -> None:
        """Gère les dates manquantes."""
        _LOGGER.debug("🔥🔥 missing_dates 1/3: %s 🔥🔥", all_consumptions)
        missing_dates: MissingDates = find_missing_dates(all_consumptions)
        _LOGGER.debug("🔥🔥 missing_dates 2/3: %s 🔥🔥", missing_dates)

        reduced_missing_dates = sync_reduce_missing_dates(
            missing_dates, self.blacklisted_months
        )
        _LOGGER.debug(
            "🔥🔥 reduced_missing_dates 3/3: %s 🔥🔥", reduced_missing_dates
        )
        if reduced_missing_dates and len(reduced_missing_dates) > 0:
            # y, m, d = reduced_missing_dates.pop()
            missing_date = reduced_missing_dates.pop()
            y, m = missing_date.year, missing_date.month
            delay = random.uniform(8, 35)
            _LOGGER.debug("Temporisation de %s secondes", delay)
            await asyncio.sleep(1)
            self.hass.async_add_executor_job(
                self._sync_fetch_monthly_data,
                y,
                m,
            )

    def _sync_fetch_monthly_data(
        self,
        year: int,
        month: int,
    ) -> None:
        """Fonction synchrone pour la récupération des données hebdo."""

        # Exécuter la coroutine dans le contexte Home Assistant
        future = asyncio.run_coroutine_threadsafe(
            self._async_fetch_monthly_data(year, month),
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
