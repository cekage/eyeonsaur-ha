from __future__ import annotations

import logging
from typing import NewType, override

from homeassistant.exceptions import HomeAssistantError
from saur_client import (
    SaurResponseContracts,
    SaurResponseDelivery,
    SaurResponseLastKnow,
)

from .models import (
    ClientId,
    ContratId,
    RelevePhysique,
    SectionId,
    StrDate,
)

_LOGGER = logging.getLogger(__name__)


class Compteur:
    """Représente les données d'un compteur."""

    @override
    def __init__(
        self,
        sectionId: SectionId,
        clientReference: str,
        clientId: ClientId,
        contractName: str,
        contractId: ContratId,
        isContractTerminated: bool,
        date_installation: StrDate,
        pairingTechnologyCode: str,
        releve_physique: RelevePhysique,
        manufacturer: str,
        model: str,
        serial_number: str,
    ) -> None:
        """Initialise un nouveau compteur."""
        self.sectionId: SectionId = sectionId
        self.clientReference = clientReference
        self.contractName: str = contractName
        self.clientId: ClientId = clientId

        self.contractId: ContratId = contractId
        self.isContractTerminated: bool = isContractTerminated
        self.date_installation: StrDate = date_installation
        self.pairingTechnologyCode: str = pairingTechnologyCode
        self.releve_physique = releve_physique
        self.manufacturer: str = manufacturer
        self.model: str = model
        self.serial_number: str = serial_number

    def update_delivery(self, delivery_response: SaurResponseDelivery) -> None:
        """Met à jour les données du compteur avec les informations
        de l'endpoint DELIVERY."""
        meter: dict[str, str] = delivery_response.get("meter", {})
        if meter:
            self.date_installation = StrDate(meter.get("installationDate", ""))
            self.manufacturer = meter.get("meterBrandCode", "")
            self.model = meter.get("meterModelCode", "")
            self.serial_number = meter.get("serialNumber", "")
        else:
            _LOGGER.warning(
                "Meter data not found in delivery response for sectionId: %s",
                self.sectionId,
            )

    def update_last(self, last_response: SaurResponseLastKnow) -> None:
        """Met à jour les données du compteur avec les informations
        de l'endpoint LAST."""
        index_value: float = last_response.get("indexValue", 0.0)
        reading_date: str = last_response.get("readingDate", "")

        self.releve_physique = RelevePhysique(
            date=StrDate(reading_date), valeur=index_value
        )

    @override
    def __str__(self) -> str:
        return (
            f"Compteur({self.sectionId=}, {self.clientReference=},"
            f"{self.clientId=}, {self.contractName=}, "
            f"{self.contractId=}, {self.isContractTerminated=}, "
            f"{self.date_installation=}, {self.pairingTechnologyCode=},"
            f"{self.releve_physique=}, {self.manufacturer=}, "
            f"{self.model=}, {self.serial_number=})"
        )


def extract_compteurs_from_area(
    area_response: SaurResponseContracts,
) -> Compteurs:
    """
    Extrait les données des compteurs depuis la réponse de l'endpoint AREA
    et retourne une liste d'objets Compteur.
    """
    compteurs: Compteurs = Compteurs([])

    try:
        for client_area in area_response.get("clients", []):
            for customer_account in client_area.get("customerAccounts", []):
                for product_contract in customer_account.get(
                    "productContracts", []
                ):
                    for section_subscription in customer_account.get(
                        "sectionSubscriptions", []
                    ):
                        isContractTerminated: bool = bool(
                            section_subscription.get(
                                "isContractTerminated", False
                            )
                        )
                        if isContractTerminated:
                            continue
                        compteur = Compteur(
                            sectionId=SectionId(
                                section_subscription.get(
                                    "sectionSubscriptionId", ""
                                )
                            ),
                            clientReference=client_area.get(
                                "clientReference", ""
                            ),
                            clientId=client_area.get("clientId", ""),
                            contractName=client_area.get("contractName", ""),
                            contractId=ContratId(
                                product_contract.get("productContractId", "")
                            ),
                            isContractTerminated=isContractTerminated,
                            date_installation=StrDate(
                                section_subscription.get(
                                    "contractTerminationDate", ""
                                )
                            ),
                            pairingTechnologyCode=section_subscription.get(
                                "pairingTechnologyCode", ""
                            ),
                            releve_physique=RelevePhysique(
                                date=StrDate(""), valeur=0.0
                            ),
                            manufacturer="",
                            model="",
                            serial_number=section_subscription.get(
                                "serialNumber", ""
                            ),
                        )
                        compteurs.append(compteur)

    except Exception as e:
        _LOGGER.exception(
            "Erreur lors de l'extraction des données AREA : %s", e
        )
        raise HomeAssistantError(
            f"Erreur lors de l'extraction des données AREA: {e}"
        )

    return compteurs


Compteurs = NewType("Compteurs", list[Compteur])
"""
Représente une collection typée d'objets Compteur.

Compteurs est un type distinct basé sur list[Compteur],
utilisé pour renforcer le typage et améliorer la clarté du code.
"""
