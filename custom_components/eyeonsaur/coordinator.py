"""Data update coordinator for the EyeOnSaur integration."""

import asyncio
import logging
import random
from asyncio import Task
from datetime import datetime, timedelta

from aiohttp import ClientResponseError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_registry import async_get
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)
from homeassistant.util.dt import as_local
from homeassistant.util.dt import now as hass_now
from saur_client import (
    SaurClient,
    SaurResponseContracts,
    SaurResponseDelivery,
    SaurResponseLastKnow,
    SaurResponseMonthly,
    SaurResponseWeekly,
)

from .device import Compteur, Compteurs, extract_compteurs_from_area
from .helpers.const import (
    DEV,
    DOMAIN,
    ENTRY_CLIENTID,
    ENTRY_COMPTEURID,
    ENTRY_LOGIN,
    ENTRY_PASS,
    ENTRY_TOKEN,
    POLLING_INTERVAL,
)
from .helpers.dateutils import find_missing_dates, sync_reduce_missing_dates
from .helpers.saur_db import SaurDatabaseHelper
from .models import (
    ConsumptionData,
    ConsumptionDatas,
    Contract,
    Contracts,
    ContratId,
    MissingDates,
    RelevePhysique,
    SaurData,
    SectionId,
    StrDate,
    TheoreticalConsumptionDatas,
)
from .recorder import SaurRecorder

# Configuration du logging
_LOGGER = logging.getLogger(__name__)


class SaurCoordinator(DataUpdateCoordinator[SaurData]):
    """Data update coordinator for the EyeOnSaur integration."""

    UPDATE_DEBOUNCE = POLLING_INTERVAL

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
            unique_id=self.entry.data[ENTRY_COMPTEURID],
            token=self.entry.data[ENTRY_TOKEN],
            clientId=self.entry.data[ENTRY_CLIENTID],
            dev_mode=DEV,
        )
        self.db_helper = db_helper
        self.recorder = recorder
        self._cached_data: SaurData = SaurData(
            saurClientId=self.entry.data[ENTRY_CLIENTID],
            compteurs=Compteurs([]),
            contracts=Contracts([]),
        )
        self._last_update_time: datetime = datetime.min

        # Ajout de la blacklist
        self.blacklisted_months: set[tuple[int, int]] = set()
        self._background_tasks: list[Task[None]] = []

    async def async_shutdown(self) -> None:
        """
        Arrête le coordinateur et ferme la session aiohttp."""
        _LOGGER.debug("Arrêt du coordinateur")
        for task in self._background_tasks:
            task.cancel()
        if self.client:
            await self.client.close_session()

    async def async_config_entry_first_refresh(self) -> None:
        """Handle the first refresh."""

        _LOGGER.debug("🔥🔥 async_config_entry_first_refresh 🔥🔥")
        await self.db_helper.async_init_db()

        response_contrats: SaurResponseContracts = (
            await self.client.get_contracts()
        )
        if response_contrats is None:
            raise HomeAssistantError(
                "Impossible de récupérer les contrats depuis l'API SAUR."
            )
        _LOGGER.debug("🔥🔥 response_contrats %s 🔥🔥", response_contrats)
        _update_token_in_config_entry(self.hass, self.entry, self.client)

        # Extraction des contrats
        clients = response_contrats.get("clients", [])
        if not clients:
            raise HomeAssistantError(
                "Aucun client trouvé dans la réponse des contrats."
            )

        contracts: list[Contract] = [
            Contract(
                contract_id=ContratId(client.get("clientId", "")),
                contract_name=client.get("contractName", ""),
                isContractTerminated=False,  # TODO
            )
            for client in clients
        ]

        compteurs: Compteurs = extract_compteurs_from_area(response_contrats)
        for compteur in compteurs:
            _LOGGER.debug(" J'AI UN COMPTEUR : %s", compteur)

        self._cached_data = SaurData(
            saurClientId=self._cached_data.saurClientId,
            compteurs=compteurs,
            contracts=Contracts(contracts),
        )
        # Update With delivery points AND Last
        self._cached_data = await self.update_compteurs_with_delivery_points(
            self._cached_data
        )

        _LOGGER.debug("🔥🔥 self._cached_data %s 🔥🔥", self._cached_data)

        # now: datetime = (
        #     datetime.now(UTC) - timedelta(days=1) - timedelta(hours=10)
        # )

        device_registry = dr.async_get(self.hass)  # MODIF
        # Créer une tâche pour chaque compteur
        for compteur in self._cached_data.compteurs:
            if compteur.isContractTerminated:
                continue

            # Créer un device pour le compteur
            device_info = DeviceInfo(
                identifiers={(DOMAIN, compteur.clientReference)},
                name=f"Contrat {compteur.clientReference}",
                manufacturer="EyeOnSaur",
                model="Contrat",
                entry_type=DeviceEntryType.SERVICE,
                serial_number=compteur.clientId,
                configuration_url="https://mon-espace.saurclient.fr/",
            )

            # Enregistrer le device dans le device registry
            device_registry.async_get_or_create(
                config_entry_id=self.entry.entry_id,
                **device_info,  # MODIFclientId
            )

            date_installation = as_local(
                datetime.fromisoformat(compteur.releve_physique.date)
            )

            # --- Correctif ---
            # Le backfill automatique via "missing_dates" ne progresse
            # que s'il y a déjà des données pour détecter des trous.
            # Si le mois d'installation est vide, il ne va jamais
            # chercher les mois suivants. On force donc ici la
            # récupération de TOUS les mois entre l'installation
            # et aujourd'hui.
            year_cursor, month_cursor = (
                date_installation.year,
                date_installation.month,
            )
            now_local = as_local(datetime.now())
            while (year_cursor, month_cursor) <= (
                now_local.year,
                now_local.month,
            ):
                task = self.hass.async_create_task(
                    self._async_fetch_monthly_data(
                        year=year_cursor,
                        month=month_cursor,
                        compteur=compteur,
                    )
                )
                self._background_tasks.append(task)
                if month_cursor == 12:
                    year_cursor += 1
                    month_cursor = 1
                else:
                    month_cursor += 1
        # await asyncio.gather(*self._background_tasks)
        await super().async_config_entry_first_refresh()

    async def _async_update_data(self) -> SaurData:
        """Fetch data from the API and update the database."""
        _LOGGER.debug(
            "🔥🔥🔥🔥 _async_update_data 🔥🔥🔥🔥",
        )
        now: datetime = datetime.now()

        if (
            self._last_update_time is not None
            and (now - self._last_update_time) < self.UPDATE_DEBOUNCE
        ):
            _LOGGER.debug(
                "Debouncing _async_update_data. Returning cached data."
            )
            return self._cached_data

        self._last_update_time = now

        # Lancer les tâches de fond pour chaque compteur
        for compteur in self._cached_data.compteurs:
            # Récupérer et stocker les données hebdomadaires
            await self._async_fetch_and_store_weekly_data(compteur=compteur)

            task = self.hass.async_create_task(
                self._async_backgroundupdate_data(compteur)
            )
            self._background_tasks.append(task)
        await asyncio.gather(*self._background_tasks)

        return self._cached_data

    async def _async_fetch_and_store_weekly_data(
        self, compteur: Compteur
    ) -> None:
        """Récupère les données hebdomadaires et les stocke dans
        la base de données."""
        now: datetime = hass_now() - timedelta(days=2, hours=10)
        try:
            weekly_data: SaurResponseWeekly = (
                await self.client.get_weekly_data(
                    now.year,
                    now.month,
                    now.day,
                    compteur.sectionId,
                )
            )
            if weekly_data and weekly_data.get("consumptions"):
                # Transformer les données hebdomadaires en ConsumptionDatas
                consumptiondatas = ConsumptionDatas(
                    [
                        ConsumptionData(
                            startDate=item["startDate"],
                            value=item["value"],
                            rangeType=item["rangeType"],
                        )
                        for item in weekly_data["consumptions"]
                    ]
                )

                # Écrire les données dans la base de données
                await self.db_helper.async_write_consumptions(
                    consumptiondatas, SectionId(compteur.sectionId)
                )
                _LOGGER.debug(
                    "🔥🔥 Données hebdomadaires stockées dans la base"
                    "de données pour %s 🔥🔥",
                    compteur.sectionId,
                )
            else:
                _LOGGER.debug(
                    "Aucune donnée hebdomadaire à stocker pour %s",
                    compteur.sectionId,
                )
        except Exception as e:
            _LOGGER.error(
                "Erreur lors de la récupération des données hebdomadaires"
                f"pour {compteur.sectionId}: {e}"
            )

    async def _async_backgroundupdate_data(self, compteur: Compteur) -> None:
        """Background task to fetch data from API and update."""
        _LOGGER.debug(
            "🔥🔥🔥🔥🔥🔥 _async_backgroundupdate_data 🔥🔥🔥🔥🔥🔥",
        )
        # Récupération de l'ancre
        await self._async_apifetch_lastknown_data(compteur)

        # Récupération de la semaine passée
        # await self._async_fetch_last_week_data()
        # datetime.utcnow() - timedelta(days=1) - timedelta(hours=10)
        # (await self.i(now.year, now.month),)

    async def _async_apifetch_lastknown_data(self, compteur: Compteur) -> None:
        """Fetch the last known data from the API."""
        lastknown_data: SaurResponseLastKnow = (
            await self.client.get_lastknown_data(compteur.sectionId)
        )
        _LOGGER.debug(
            "🔥🔥 _async_apifetch_lastknown_data %s 🔥🔥",
            lastknown_data,
        )

        if lastknown_data and "readingDate" in lastknown_data:
            releve_physique = RelevePhysique(
                date=StrDate(str(lastknown_data.get("readingDate"))),
                valeur=lastknown_data.get("indexValue", 0.0),
            )
            await self.db_helper.async_update_anchor(
                releve_physique, compteur.sectionId
            )

            # Mise à jour directe de l'attribut
            self.updateRelevePhysique(compteur, releve_physique)
            # self.cached_data.releve_physique = releve_physique

    async def _async_apifetch_and_sqlstore_monthly_data(
        self, year: int, month: int, section_id: SectionId
    ) -> None:
        """Récupère et stocke les données mensuelles."""
        try:
            monthly_data: SaurResponseMonthly = (
                await self.client.get_monthly_data(year, month, section_id)
            )
        except ClientResponseError:
            # Ajoute à la blacklist en cas d'erreur
            self.blacklisted_months.add((year, month))
            _LOGGER.warning(
                f"""Mois blacklisted ({year}, {month})
                car non disponible"""
            )
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
            consumptiondatas, section_id
        )

    # async def _async_fetch_monthly_data(
    #     self, year: int, month: int, compteur: Compteur
    # ) -> None:
    #     raise HomeAssistantError

    async def _async_fetch_monthly_data(
        self, year: int, month: int, compteur: Compteur
    ) -> None:
        """Wrapper pour la récupération des données hebdomadaires."""
        _LOGGER.debug(
            "🔥🔥 _async_fetch_monthly_data  %s %s no_day for %s 🔥🔥",
            year,
            month,
            compteur.sectionId,
        )
        await self._async_apifetch_and_sqlstore_monthly_data(
            year, month, compteur.sectionId
        )
        _LOGGER.debug(
            "🔥🔥 async_get_all_consumptions_with_absolute  %s 🔥🔥",
            compteur.sectionId,
        )
        # Get all consumptions from SQLITE
        all_consumptions: TheoreticalConsumptionDatas = (
            await self.db_helper.async_get_all_consumptions_with_absolute(
                compteur.sectionId
            )
        )
        _LOGGER.debug(
            "🔥🔥 TheoreticalConsumptionDatas  %s 🔥🔥",
            all_consumptions,
        )
        # Recalculate all historical data
        await self._async_inject_historical_data(all_consumptions, compteur)

        # Détecte et traite les jours manquants
        await self._async_handle_missing_dates(all_consumptions, compteur)

    async def _async_inject_historical_data(
        self,
        all_consumptions: TheoreticalConsumptionDatas,
        compteur: Compteur,
    ) -> None:
        """Injecte les données historiques dans le recorder."""
        if not all_consumptions:
            return

        # Accéder à l'enregistrement des entités
        entity_registry = async_get(self.hass)

        # Récupérer l'entité via l'ID unique
        entity_entry = entity_registry.async_get_entity_id(
            "sensor", DOMAIN, f"{compteur.serial_number}_water_statistics"
        )

        if entity_entry:
            # Entité trouvée
            _LOGGER.debug(
                "_async_inject_historical_data : Entité trouvée : %s",
                entity_entry,
            )
        else:
            # Entité non trouvée
            _LOGGER.debug(
                "_async_inject_historical_data : Entité non trouvée."
            )
            return

        # default_section_id = f"{compteur.sectionId}"
        # entity_entry = f"{compteur.serial_number}"
        for a_consumption in all_consumptions:
            date_formatted = datetime.fromisoformat(a_consumption.date)
            _LOGGER.debug(
                "🔥🔥 all_consumptions compteur.sectionId: %s %s %s 🔥🔥",
                compteur.sectionId,
                date_formatted,
                a_consumption.indexValue,
            )
            await self.recorder.async_inject_historical_data(
                entity_entry,
                date_formatted,
                a_consumption.indexValue,
            )

    async def _async_handle_missing_dates(
        self,
        all_consumptions: TheoreticalConsumptionDatas,
        compteur: Compteur,
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
                compteur,
            )

    def updateRelevePhysique(
        self, compteur: Compteur, releve_physique: RelevePhysique
    ) -> None:
        """
        Met à jour le relevé physique d'un compteur dans self.cached_data.
        """
        for i, c in enumerate(self._cached_data.compteurs):
            if c.sectionId == compteur.sectionId:
                self._cached_data.compteurs[i] = Compteur(
                    sectionId=c.sectionId,
                    clientReference=c.clientReference,
                    clientId=c.clientId,
                    contractName=c.contractName,
                    contractId=c.contractId,
                    isContractTerminated=c.isContractTerminated,
                    date_installation=c.date_installation,
                    pairingTechnologyCode=c.pairingTechnologyCode,
                    releve_physique=releve_physique,  # Update
                    manufacturer=c.manufacturer,
                    model=c.model,
                    serial_number=c.serial_number,
                )
                return  # Met à jour et sort de la fonction

        print(f"Compteur non trouvé dans le cache: {compteur.sectionId}")

    def _sync_fetch_monthly_data(
        self, year: int, month: int, compteur: Compteur
    ) -> None:
        """Fonction synchrone pour la récupération des données hebdo."""

        # Exécuter la coroutine dans le contexte Home Assistant
        future = asyncio.run_coroutine_threadsafe(
            self._async_fetch_monthly_data(year, month, compteur),
            self.hass.loop,
        )
        # Attendre que le futur soit terminé, sans rien retourner
        future.result()

    async def update_compteurs_with_delivery_points(
        self, saur_data: SaurData
    ) -> SaurData:
        """
        Met à jour les données des compteurs avec les informations
        des points de livraison.
        """
        compteurs = saur_data.compteurs
        for compteur in compteurs:
            _LOGGER.debug(" J'AI UN COMPTEUR : %s", compteur)

        # 1. Lancer toutes les requêtes DELIVERY en parallèle
        delivery_tasks = [
            async_get_delivery_data(self.client, compteur.sectionId)
            for compteur in compteurs
        ]
        delivery_results = await asyncio.gather(
            *delivery_tasks, return_exceptions=True
        )

        # 2. Lancer toutes les requêtes LAST en parallèle
        last_tasks = [
            async_get_last_data(self.client, compteur.sectionId)
            for compteur in compteurs
        ]
        last_results = await asyncio.gather(
            *last_tasks, return_exceptions=True
        )

        filtered_delivery_results = [
            d for d in delivery_results if isinstance(d, dict)
        ]
        filtered_last_results = [
            d for d in last_results if isinstance(d, dict)
        ]

        # 3. Mettre à jour les compteurs avec les données DELIVERY et LAST
        updated_compteurs: list[Compteur] = []
        for i, (delivery_data, last_data) in enumerate(
            zip(filtered_delivery_results, filtered_last_results, strict=False)
            # zip(delivery_results, last_results, strict=False)
        ):
            compteur = compteurs[i]

            if isinstance(delivery_data, HomeAssistantError):
                # Gestion de l'erreur DELIVERY : on log mais on continue
                _LOGGER.error(
                    "Erreur lors de la mise à jour du compteur %s avec les "
                    "données DELIVERY: %s. Utilisation des anciennes données.",
                    compteur.sectionId,
                    delivery_data,
                )
            else:
                # on utilise la methode update_delivery de la class Compteur
                compteur.update_delivery(delivery_data)

            if isinstance(last_data, HomeAssistantError):
                # Gestion de l'erreur LAST : on log l'erreur mais on continue
                _LOGGER.error(
                    "Erreur lors de la mise à jour du compteur %s avec les "
                    "données LAST: %s. Utilisation des anciennes données.",
                    compteur.sectionId,
                    last_data,
                )
            else:
                # on utilise la methode update_last de la class Compteur
                compteur.update_last(last_data)

            updated_compteurs.append(compteur)

        # 4. Créer une nouvelle instance de SaurData avec la liste mise à jour
        new_base_data = SaurData(
            saurClientId=saur_data.saurClientId,
            compteurs=Compteurs(updated_compteurs),
            contracts=saur_data.contracts,
        )
        return new_base_data


def update_compteur(
    deliverypoints: SaurResponseDelivery,
    compteur_template: Compteur,
) -> Compteur:
    """Extrait les informations du compteur à partir du JSON
    deliverypoints et renvoie un objet Compteur."""

    meter = deliverypoints.get("meter", {})
    releve_physique = RelevePhysique(
        date=StrDate("1970-01-01T00:00:00"), valeur=0.0
    )

    compteur = Compteur(
        sectionId=deliverypoints.get("sectionSubscriptionId", "N/A"),
        clientReference=compteur_template.clientReference,
        clientId=compteur_template.clientId,
        contractName=compteur_template.contractName,
        contractId=compteur_template.contractId,
        isContractTerminated=compteur_template.isContractTerminated,
        date_installation=meter.get("installationDate", "1900-01-01T00:00:00"),
        pairingTechnologyCode=meter.get("pairingTechnologyCode", "N/A"),
        releve_physique=releve_physique,
        manufacturer=meter.get("meterBrandCode", None),
        model=meter.get("meterModelCode", None),
        serial_number=meter.get("trueRegistrationNumber", None),
    )
    return compteur


def _update_token_in_config_entry(
    hass: HomeAssistant, entry: ConfigEntry, client: SaurClient
) -> None:
    """Met à jour le token dans l'entrée de configuration si nécessaire."""
    if client.access_token != entry.data[ENTRY_TOKEN]:
        new_data = entry.data.copy()
        new_data[ENTRY_TOKEN] = client.access_token
        new_data[ENTRY_CLIENTID] = client.clientId
        hass.config_entries.async_update_entry(entry, data=new_data)


async def async_get_delivery_data(
    client: SaurClient, section_id: SectionId
) -> SaurResponseDelivery:
    """Récupère les données de l'endpoint DELIVERY pour un seul compteur."""
    try:
        if not (
            delivery_data := await client.get_deliverypoints_data(section_id)
        ):
            raise HomeAssistantError(
                f"Aucune donnée DELIVERY trouvée pour sectionId: {section_id}"
            )
        return delivery_data
    except Exception as e:
        raise HomeAssistantError(
            "Erreur lors de la récupération des données DELIVERY"
            f"pour {section_id}: {e}"
        )


async def async_get_last_data(
    client: SaurClient, section_id: SectionId
) -> SaurResponseLastKnow:
    """Récupère les données de l'endpoint LAST pour un seul compteur."""
    try:
        last_data: SaurResponseLastKnow = await client.get_lastknown_data(
            section_id
        )
        if last_data is None:
            raise HomeAssistantError(
                f"Aucune donnée LAST trouvée pour sectionId: {section_id}"
            )
        return last_data
    except Exception as e:
        raise HomeAssistantError(
            "Erreur lors de la récupération des données LAST pour"
            f"{section_id}: {e}"
        )
