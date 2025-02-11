"""Date manipulator for the EyeOnSaur integration."""

import logging
from datetime import datetime, timedelta

from ..models import MissingDate, MissingDates, TheoreticalConsumptionDatas

_LOGGER = logging.getLogger(__name__)


def find_missing_dates(
    consumption_datas: TheoreticalConsumptionDatas,
) -> MissingDates:
    """Identifie les dates manquantes.

    Identifie les dates manquantes dans un tableau de données de
    type [(date, valeur)].
    Retourne les dates manquantes entre la première date existante et
    la dernière date existante, en excluant les dates où des données existent.

    Args:
        consumption_datas: Liste de tuples, où chaque tuple contient une date
        au format "YYYY-MM-DD HH:MM:SS" et une valeur (float) associée.

    Returns:
        Une liste de tuples, où chaque tuple contient l'année, le mois et
        le jour des dates manquantes, sous la forme (année, mois, jour).

    """
    if not consumption_datas:
        response: MissingDates = MissingDates([])
        return response

    # Convertir les dates en objets datetime
    dates = [
        datetime.fromisoformat(consumption_data.date)
        for consumption_data in consumption_datas
    ]

    # Trier les dates
    dates.sort()

    # Créer un ensemble de toutes les dates manquantes
    missing_dates: MissingDates = MissingDates([])

    # La première date existante
    current_date = dates[0]

    # Parcourir les dates et trouver celles manquantes
    for i in range(1, len(dates)):
        next_date = dates[i]

        # Ajouter les dates manquantes entre current_date et next_date
        while current_date + timedelta(days=1) < next_date:
            current_date += timedelta(days=1)
            missing_date = MissingDate(
                current_date.year, current_date.month, current_date.day
            )
            missing_dates.append(missing_date)

        # Passer à la prochaine date
        current_date = next_date

    return missing_dates


def sync_reduce_missing_dates(
    unreduced_dates: MissingDates, blacklisted_months: set[tuple[int, int]]
) -> MissingDates:
    """Optimise les dates manquantes.

    Optmise les dates manquantes en ne gardant que celles qui sont
    séparées par plus de 6 jours par rapport à la précédente date ajoutée.

    Args:
        unreduced_dates: Liste de tuples contenant les dates manquantes sous
        forme (année, mois, jour).

    Returns:
        Une liste optimisée de dates manquantes.

    """
    if not unreduced_dates:
        return MissingDates([])

    optimized_dates: MissingDates = MissingDates([])
    last_added_date: datetime | None = None

    # Trier les dates avant de commencer
    sorted_dates = sorted(
        unreduced_dates,
        key=lambda missing_date: datetime(
            missing_date.year, missing_date.month, missing_date.day
        ),
    )

    for date in sorted_dates:
        # Vérifier si le mois est blacklisté
        if (date.year, date.month) in blacklisted_months:
            continue  # Passe à la date suivante si le mois est blacklisté

        # Convertir la date (année, mois, jour) en un objet datetime
        current_date = datetime(date.year, date.month, date.day)

        if last_added_date is None:
            # Ajouter la première date sans vérification
            optimized_dates.append(date)
            last_added_date = current_date
        # Vérifier si l'écart est supérieur à 6 jours
        elif current_date > last_added_date + timedelta(days=6):
            optimized_dates.append(date)
            last_added_date = current_date

    return optimized_dates
