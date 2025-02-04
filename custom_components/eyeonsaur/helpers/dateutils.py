"""Date manipulator for the EyeOnSaur integration."""

import logging
from datetime import datetime, timedelta

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)


def find_missing_dates(
    consumption_datas: list[tuple[str, float]],
) -> list[tuple[int, int, int]]:
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
        return []

    # Convertir les dates en objets datetime
    dates = [datetime.fromisoformat(item[0]) for item in consumption_datas]

    # Trier les dates
    dates.sort()

    # Créer un ensemble de toutes les dates manquantes
    missing_dates = []

    # La première date existante
    current_date = dates[0]

    # Parcourir les dates et trouver celles manquantes
    for i in range(1, len(dates)):
        next_date = dates[i]

        # Ajouter les dates manquantes entre current_date et next_date
        while current_date + timedelta(days=1) < next_date:
            current_date += timedelta(days=1)
            missing_dates.append(
                (current_date.year, current_date.month, current_date.day),
            )

        # Passer à la prochaine date
        current_date = next_date

    return missing_dates


def sync_reduce_missing_dates(
    unreduced_dates: list[tuple[int, int, int]],
) -> list[tuple[int, int, int]]:
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
        return []

    optimized_dates = []
    last_added_date = None

    # Trier les dates avant de commencer
    sorted_dates = sorted(unreduced_dates)

    for date in sorted_dates:
        # Convertir la date (année, mois, jour) en un objet datetime
        current_date = datetime(date[0], date[1], date[2])

        if last_added_date is None:
            # Ajouter la première date sans vérification
            optimized_dates.append(date)
            last_added_date = current_date
        # Vérifier si l'écart est supérieur à 6 jours
        elif current_date > last_added_date + timedelta(days=6):
            optimized_dates.append(date)
            last_added_date = current_date

    return optimized_dates
