"""
Modèles de données (dataclasses) pour l'intégration eyeonsaur.
"""

import sqlite3
from dataclasses import dataclass
from typing import TYPE_CHECKING, NewType

if TYPE_CHECKING:
    from .device import Compteurs

StrDate = NewType("StrDate", str)


@dataclass(frozen=True, slots=True)
class ConsumptionData:
    """
    Représente les données de consommation d'énergie.

    Attributes:
        startDate (str): Date et heure de début de la période de consommation,
            au format 'AAAA-MM-JJ HH:MM:SS'.
        value (float): Valeur de la consommation d'énergie pour
            la période donnée.
        rangeType (str): Type de plage de consommation
            (par exemple, 'Day', 'Week', 'Month').
    """

    startDate: StrDate
    value: float
    rangeType: str


@dataclass(frozen=True, slots=True)
class AnchorData:
    """
    Représente les données d'ancrage (index de référence).

    Attributes:
        readingDate (StrDate): Date et heure de la lecture
            de l'index de référence, au format 'AAAA-MM-JJ HH:MM:SS'.
        indexValue (float): Valeur de l'index de référence.
    """

    readingDate: StrDate
    indexValue: float


@dataclass(frozen=True, slots=True)
class TheoreticalConsumptionData:
    """
    Représente une consommation théorique : date et valeur relative.

    Attributes:
        date (str): Date et heure de la consommation théorique,
            au format 'AAAA-MM-JJ HH:MM:SS'.
        indexValue (float): Valeur relative de la consommation théorique.
    """

    date: StrDate
    indexValue: float


@dataclass(frozen=True, slots=True)
class MissingDate:
    """
    Représente une date manquante (année, mois, jour).

    Attributes:
        year (int): Année de la date manquante.
        month (int): Mois de la date manquante.
        day (int): Jour de la date manquante.
    """

    year: int
    month: int
    day: int


@dataclass(slots=True, frozen=True)
class RelevePhysique:
    """Encapsule les données du relevé physique."""

    date: StrDate
    """Date du relevé (format AAAA-MM-JJTHH:MM:SS)."""
    valeur: float
    """Valeur du relevé."""


ContratId = NewType("ContratId", str)
SectionId = NewType("SectionId", str)

# @dataclass(slots=True, frozen=True)
# class Compteur:
#     """Représente les données d'un compteur."""
#     sectionId: SectionId
#     """Identifiant unique du compteur."""
#     clientReference: str
#     """Référence client."""
#     contractName: str
#     """Nom du contrat."""
#     contractId: ContratId
#     """Id du contrat."""
#     isContractTerminated: bool
#     """Indique si le contrat est terminé."""
#     date_installation: StrDate
#     """Date d'installation du compteur (format AAAA-MM-JJTHH:MM:SS)."""
#     adresse: str
#     """Adresse du compteur."""
#     pairingTechnologyCode: str
#     """Code de la technologie d'appairage."""
#     releve_physique: RelevePhysique
#     """Données du relevé physique."""
#     manufacturer: str
#     """Fabricant du compteur, peut être None."""
#     model: str
#     """Modèle du compteur, peut être None."""
#     serial_number: str
#     """Numéro de série du compteur, peut être None."""

# @dataclass(slots=True, frozen=True)
# class Compteur:
#     """Représente les données d'un compteur."""
#     sectionId: SectionId
#     """Identifiant unique du compteur."""
#     clientReference: str
#     """Référence client."""
#     contractName: str
#     """Nom du contrat."""
#     contractId: ContratId
#     """Id du contrat."""
#     isContractTerminated: bool
#     """Indique si le contrat est terminé."""
#     date_installation: StrDate
#     """Date d'installation du compteur (format AAAA-MM-JJTHH:MM:SS)."""
#     pairingTechnologyCode: str
#     """Code de la technologie d'appairage."""
#     releve_physique: RelevePhysique
#     """Données du relevé physique."""
#     manufacturer: str
#     """Fabricant du compteur."""
#     model: str
#     """Modèle du compteur."""
#     serial_number: str
#     """Numéro de série du compteur."""


JsonStr = NewType("JsonStr", str)
"""Représente une chaîne de caractères contenant une structure JSON."""


"""
Modèles de données (dataclasses) pour l'intégration eyeonsaur.
"""

SaurSqliteResponse = tuple[sqlite3.Row, ...] | None
"""Represents the result of a SQLite query.

This can be a list of sqlite3.Row objects (each
object representing a result row) or None if the query returned
no results or in case of an error.
"""

TheoreticalConsumptionDatas = NewType(
    "TheoreticalConsumptionDatas", list[TheoreticalConsumptionData]
)
"""
Représente une collection typée d'objets TheoreticalConsumptionData.

TheoreticalConsumptionDatas est un type distinct basé sur
list[TheoreticalConsumptionData], utilisé pour renforcer le typage et
améliorer la clarté du code.
"""

ConsumptionDatas = NewType("ConsumptionDatas", list[ConsumptionData])
"""
Représente une collection typée d'objets ConsumptionData.

ConsumptionDatas est un type distinct basé sur list[ConsumptionData],
utilisé pour renforcer le typage et améliorer la clarté du code.
"""

MissingDates = NewType("MissingDates", list[MissingDate])
"""
Représente une collection typée d'objets MissingDate.

MissingDates est un type distinct basé sur list[MissingDate],
utilisé pour renforcer le typage et améliorer la clarté du code.
"""


@dataclass(slots=True, frozen=True)
class Contract:
    """Représente les informations d'un contrat."""

    contract_id: ContratId
    contract_name: str
    isContractTerminated: bool


Contracts = NewType("Contracts", list[Contract])

ClientId = NewType("ClientId", str)


@dataclass(slots=True, frozen=True)
class SaurData:
    """
    Représente les données de l'intégration SAUR,
    incluant une liste de compteurs.
    """

    saurClientId: ClientId
    """Identifiant du client SAUR."""
    compteurs: "Compteurs"
    """Liste immuable contenant les compteurs associés au client."""
    contracts: Contracts
    """Dictionnaire des contrats, indexés par contract_id."""
