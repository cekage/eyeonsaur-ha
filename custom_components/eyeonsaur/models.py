"""
Modèles de données (dataclasses) pour l'intégration eyeonsaur.
"""

import sqlite3
from dataclasses import dataclass, field
from typing import NewType


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

    startDate: str
    value: float
    rangeType: str


@dataclass(frozen=True, slots=True)
class AnchorData:
    """
    Représente les données d'ancrage (index de référence).

    Attributes:
        readingDate (str): Date et heure de la lecture de l'index de référence,
            au format 'AAAA-MM-JJ HH:MM:SS'.
        indexValue (float): Valeur de l'index de référence.
    """

    readingDate: str
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

    date: str
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

    #    date: str | None = None
    date: str
    valeur: float | None = None


# @dataclass(frozen=True, slots=True)
# class RelevePhysique:
#     """
#     Encapsule les données du relevé physique.
#     """

#     data: dict[str, str | float | None] = field(
#         default_factory=lambda: {"date": None, "valeur": None}
#     )


@dataclass(slots=True, frozen=False)
class BaseData:
    """
    Représente les données de base d'un point de livraison.

    Attributes:
        releve_physique (dict[str, Optional[str | float]]): Dictionnaire
            contenant la date et la valeur du relevé physique.
        created_at (Optional[str]): Date de création du point de livraison,
            au format 'AAAA-MM-JJ HH:MM:SS'.
        section_id (Optional[str]): Identifiant de la section.
        manufacturer (Optional[str]): Fabricant du compteur.
        model (Optional[str]): Modèle du compteur.
        serial_number (Optional[str]): Numéro de série du compteur.
    """

    # releve_physique: "RelevePhysique" = field(default_factory=RelevePhysique)
    releve_physique: "RelevePhysique" = field(
        default_factory=lambda: RelevePhysique(date="")
    )
    created_at: str | None = None
    section_id: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    serial_number: str | None = None


JsonStr = NewType("JsonStr", str)
"""Représente une chaîne de caractères contenant une structure JSON."""


"""
Modèles de données (dataclasses) pour l'intégration eyeonsaur.
"""

SaurSqliteResponse = list[sqlite3.Row] | None
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
