"""Serveur de test pour l'API SAUR avec FastAPI et Uvicorn."""

# pylint: disable=E0401

import json
import logging
import random
from calendar import monthrange
from datetime import UTC, datetime, timedelta
from typing import Any, Final

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

_LOGGER = logging.getLogger(__name__)

app = FastAPI()

DEFAULTCLIENTID: Final = "512345678901234560"

DEFAULTSECTIONSUBSCRIPTIONID: Final = "789012125678968230"

# CLIENTS: dict[str, dict[str, str]] = {
#     DEFAULTSECTIONSUBSCRIPTIONID: {"clientId": DEFAULTCLIENTID, "serial": "012340", "installationDate": "2024-08-15T00:00:00", "clientReference": "0030101520"},
#     "789012345678901781": {"clientId": "876543210987654381", "serial": "023481", "installationDate": "2024-09-20T00:00:01", "clientReference": "0032426781"},
#     "234567890123456782": {"clientId": "293847561092837482", "serial": "034582", "installationDate": "2024-10-25T00:00:02", "clientReference": "0039871282"},
#     "901234567890123453": {"clientId": "987654321012345673", "serial": "045673", "installationDate": "2024-11-30T00:00:03", "clientReference": "0036547823"},
#     "567890123456789014": {"clientId": "102938475654637284", "serial": "056784", "installationDate": "2024-12-05T00:00:04", "clientReference": "0038741254"},
#     "123456789012345675": {"clientId": "765432109889012345", "serial": "067895", "installationDate": "2024-12-31T00:00:05", "clientReference": "0035698745"},
#     "890123456789012346": {"clientId": "345678901223456786", "serial": "078906", "installationDate": "2025-01-05T00:00:06", "clientReference": "0032147856"},
#     "456789012345678907": {"clientId": "543210987667890127", "serial": "089017", "installationDate": "2025-01-10T00:00:07", "clientReference": "0036897417"},
#     "012345678901234568": {"clientId": "654321098778901238", "serial": "090128", "installationDate": "2025-01-14T00:00:08", "clientReference": "0034710258"},
#     "678901234567890129": {"clientId": "432109876556789019", "serial": "101239", "installationDate": "2025-01-15T00:00:09", "clientReference": "0038572149"}
# }

CLIENTS: dict[str, dict[str, str]] = {
    # 1 client 1 abonnement 1 compteur
    DEFAULTSECTIONSUBSCRIPTIONID: {
        "clientId": DEFAULTCLIENTID,
        "serial": "012340",
        "installationDate": "2023-12-15T00:00:00",
        "clientReference": "0030101520",
    },
    # 1 client 2 abonnement 2 compteur
    "789012345678901781": {
        "clientId": "876543210987654381",
        "serial": "023481",
        "installationDate": "2023-09-20T00:00:01",
        "clientReference": "0032426781",
    },
    "234567890123456782": {
        "clientId": "876543210987654381",
        "serial": "034582",
        "installationDate": "2024-01-25T00:00:02",
        "clientReference": "0039871282",
    },
    # # 1 client 1 abonnement 2 compteur
    # "901234567890123453": [
    #     {"clientId": "987654321012345673", "serial": "045673", "installationDate": "2024-11-30T00:00:03", "clientReference": "0036547823"},
    #     {"clientId": "987654321012345673", "serial": "056784", "installationDate": "2024-12-05T00:00:04", "clientReference": "0038741254"}
    # ],
}


def find_subscription_id_by_client_id(client_id: str) -> str:
    return next(k for k, v in CLIENTS.items() if v["clientId"] == client_id)


async def _handle_json_endpoint(
    method: str,
    file_path: str,
    detail: str | None = None,
) -> dict[str, Any]:
    """Fonction générique pour gérer les endpoints JSON."""
    _LOGGER.debug("Received %s request, processing %s", method, file_path)
    data = {}
    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        _LOGGER.debug(
            "Response from %s: %s",
            file_path,
            json.dumps(data, indent=4),
        )
    except FileNotFoundError:
        error_detail = (
            f"{detail}: {file_path} not found"
            if detail
            else f"{file_path} not found"
        )
        _LOGGER.exception(error_detail)
        raise HTTPException(status_code=404, detail=error_detail)
    except json.JSONDecodeError as e:
        error_detail = (
            f"{detail}: JSON decode error in {file_path}: {e}"
            if detail
            else f"JSON decode error in {file_path}: {e}"
        )
        _LOGGER.exception(error_detail)
        raise HTTPException(status_code=500, detail=error_detail)
    except Exception as e:
        error_detail = (
            f"{detail}: Unexpected error processing {file_path}: {e}"
            if detail
            else f"Unexpected error processing {file_path}: {e}"
        )
        _LOGGER.exception(error_detail)
        raise HTTPException(status_code=500, detail=error_detail)
    return data


@app.post("/admin/v2/auth", response_class=JSONResponse)
async def handle_auth() -> dict[str, Any]:
    """Handles the authentication endpoint."""
    return await _handle_json_endpoint(
        method="POST",
        file_path="./auth.json",
        detail="Erreur lors du traitement du endpoint /admin/v2/auth",
    )


@app.get(
    "/deli/section_subscriptions/{default_section_id}/delivery_points",
    response_class=JSONResponse,
)
async def handle_delivery_points(default_section_id: str) -> dict[str, Any]:
    """Handles the last meter index endpoint."""
    serial: str = CLIENTS[default_section_id]["serial"]
    installation_date: str = CLIENTS[default_section_id]["installationDate"]
    return generate_delivery_point(
        serial_number=serial, installation_date=installation_date
    )


@app.get(
    "/deli/section_subscriptions/{default_section_id}/meter_indexes/last",
    response_class=JSONResponse,
)
async def handle_last(default_section_id: str) -> dict[str, Any]:
    """Handles the last meter index endpoint."""
    installation_date: str = CLIENTS[default_section_id]["installationDate"]
    return generate_meter_index(installation_date)


@app.get(
    "/deli/section_subscription/{default_section_id}/consumptions/weekly",
    response_class=JSONResponse,
)
async def handle_weekly(
    default_section_id: str,
    year: int,
    month: int,
    day: int,
) -> dict[str, Any]:
    """Handles the last meter index endpoint."""
    installation_date: datetime = datetime.fromisoformat(
        CLIENTS[default_section_id]["installationDate"]
    )
    return generate_consumptions(installation_date, year, month, day)


@app.get(
    "/deli/section_subscription/{default_section_id}/consumptions/monthly",
    response_class=JSONResponse,
)
async def handle_monthly(
    default_section_id: str,
    year: int,
    month: int,
) -> dict[str, Any]:
    """Handles the last meter index endpoint."""
    installation_date: datetime = datetime.fromisoformat(
        CLIENTS[default_section_id]["installationDate"]
    )
    return generate_consumptions(installation_date, year, month, day=0)


@app.get(
    "/admin/users/v2/website_areas/{clientId}",
    response_class=JSONResponse,
)
async def handle_area(clientId: str) -> dict[str, Any]:
    """Handles the last meter index endpoint."""
    client_ids: list[str] = [
        str(client["clientId"]) for client in CLIENTS.values()
    ]
    return generate_fake_area_json(client_ids)


QTEMIN = 0.1  # Quantité minimale de consommation
QTEMAX = 1.0  # Quantité maximale de consommation


def generate_meter_index(reading_date: str) -> dict[str, Any]:
    index_value = round(random.uniform(1500, 2200), 2)

    date_obj = datetime.fromisoformat(reading_date)
    date_obj = date_obj.replace(tzinfo=UTC)  # Rendre `date_obj` aware
    max_offset_days = (datetime.now(UTC) - timedelta(days=2) - date_obj).days

    if max_offset_days > 0:
        random_offset = random.randint(0, max_offset_days)
        date_obj += timedelta(days=random_offset)

    return {
        "meterIndexId": None,
        "meterId": None,
        "previousMeterIndexId": None,
        "indexValue": index_value,
        "readingDate": date_obj.isoformat(),
        "sectionSubscriptionId": None,
    }


def generate_consumption_entries(
    start_date: datetime, max_entries: int = 7
) -> list[dict[str, Any]]:
    """
    Génère une liste de consommations à partir d'une date de début,
    en respectant la limite de 7 entrées et la contrainte de date.
    """
    today = datetime.today()
    consumptions: list[dict[str, Any]] = []

    for i in range(max_entries):
        entry_start = start_date + timedelta(days=i)
        entry_end = entry_start + timedelta(days=1)

        if entry_end >= today:
            break

        consumptions.append(
            {
                "quality": 0,
                "startDate": entry_start.strftime("%Y-%m-%dT00:00:00"),
                "endDate": entry_end.strftime("%Y-%m-%dT00:00:00"),
                "value": round(random.uniform(QTEMIN, QTEMAX), 2),
                "realConsumptionValue": 0,
                "estimateConsumptionValue": 0,
                "rangeType": "Day",
            }
        )

    return consumptions


def generate_consumptions(
    installationDate: datetime, year: int, month: int, day: int = 0
) -> dict[str, Any]:
    """
    Génère une réponse complète avec les consommations.
    Si day = 0, génère toutes les consommations du mois sans dépasser ses limites.
    Si installationDate est dans le mois, met value = 0 pour les jours avant.
    """
    start_date = datetime(year, month, 1)
    today = datetime.today()

    if start_date < installationDate.replace(
        day=1
    ):  # Vérifier si le mois est avant installationDate
        return {
            "consumptions": [],
            "isRemoteReading": True,
            "isEstimateConsumption": False,
            "isYearlyViewOnly": False,
        }

    # Trouver le dernier jour du mois
    _, last_day = monthrange(year, month)

    if day:  # Cas normal : on génère à partir d'un jour précis
        start_date = datetime(year, month, day)
        if start_date < installationDate:
            return {
                "consumptions": [],
                "isRemoteReading": True,
                "isEstimateConsumption": False,
                "isYearlyViewOnly": False,
            }
        return {
            "consumptions": generate_consumption_entries(start_date),
            "isRemoteReading": True,
            "isEstimateConsumption": False,
            "isYearlyViewOnly": False,
        }

    # Cas où day == 0 : génération pour tout le mois
    consumptions: list[dict[str, Any]] = []
    for d in range(1, last_day + 1):
        entry_start = datetime(year, month, d)
        entry_end = entry_start + timedelta(days=1)

        if entry_end >= today:
            break  # Ne pas dépasser aujourd’hui

        value = (
            0
            if entry_start < installationDate
            else round(random.uniform(QTEMIN, QTEMAX), 2)
        )

        consumptions.append(
            {
                "quality": 0,
                "startDate": entry_start.strftime("%Y-%m-%dT00:00:00"),
                "endDate": entry_end.strftime("%Y-%m-%dT00:00:00"),
                "value": value,
                "realConsumptionValue": 0,
                "estimateConsumptionValue": 0,
                "rangeType": "Day",
            }
        )

    return {
        "consumptions": consumptions,
        "isRemoteReading": True,
        "isEstimateConsumption": False,
        "isYearlyViewOnly": False,
    }


def generate_fake_area_json(client_ids: list[str]) -> dict[str, Any]:
    """
    Génère un JSON AREA simulé avec autant de clients que de client_ids fournis,
    et 1 compteur actif par client, avec des IDs aléatoires et des adresses basées sur l'index.
    """

    def get_client_reference(client_id: str) -> str | None:
        for _section_id, data in CLIENTS.items():
            if data["clientId"] == client_id:
                return data.get("clientReference")
        return None

    def generate_random_id(length: int) -> str:
        """Génère un ID aléatoire de la longueur spécifiée."""
        return "".join(random.choice("0123456789") for _ in range(length))

    def generate_partner_contract_reference() -> str:
        """Génère une référence de contrat partenaire aléatoire (ex: "110520000100")."""
        return generate_random_id(12)

    def generate_partner_contract_accounting_reference() -> str:
        """Génère une référence comptable de contrat partenaire aléatoire (ex: "110520/01")."""
        part1 = generate_random_id(6)
        part2 = generate_random_id(2)
        return f"{part1}/{part2}"

    def generate_fake_client(
        client_id: str, index_client: int, sectionid: str
    ) -> dict[str, Any]:
        """Génère un objet client factice avec des IDs aléatoires et une adresse basée sur l'index."""

        customer_account_id = generate_random_id(18)
        product_contract_id = generate_random_id(18)
        section_subscription_id = (
            sectionid  # find_subscription_id_by_client_id(client_id)
        )
        geographic_address_id = generate_random_id(18)
        partner_contract_id = generate_random_id(18)
        partner_contract_reference = generate_partner_contract_reference()
        partner_contract_accounting_reference = (
            generate_partner_contract_accounting_reference()
        )

        return {
            "identifiedUserId": "12345678",
            "clientReference": get_client_reference(client_id),
            "clientId": client_id,
            "contractName": "Factice",
            "webSiteClientAreaId": 866459,
            "customerAccounts": [
                {
                    "reference": "4905200062685",
                    "customerAccountId": customer_account_id,
                    "clientId": client_id,
                    "productContracts": [
                        {
                            "productContractId": product_contract_id,
                            "terminationDate": "1900-01-01T00:00:00Z",
                            "statusCode": "2",
                            "productCode": "EPOTA",
                            "partnerContractId": int(partner_contract_id),
                            "partnerContractReference": partner_contract_reference,
                            "partnerContractAccountingReference": partner_contract_accounting_reference,
                            "usage": "Alimentation des particuliers",
                        }
                    ],
                    "sectionSubscriptions": [
                        {
                            "sectionSubscriptionId": section_subscription_id,
                            "isContractTerminated": False,
                            "contractTerminationDate": "1900-01-01T00:00:00Z",
                            "contractStatusCode": "2",
                            "serialNumber": "100430",
                            "registrationNumber": "L24AA100430T",
                            "pairingTechnologyCode": "TeleCoronis",
                            "productContract": {
                                "productContractId": product_contract_id,
                                "terminationDate": "1900-01-01T00:00:00Z",
                                "statusCode": "2",
                                "productCode": "EPOTA",
                                "partnerContractId": int(partner_contract_id),
                                "partnerContractReference": partner_contract_reference,
                                "partnerContractAccountingReference": partner_contract_accounting_reference,
                                "usage": "Alimentation des particuliers",
                            },
                            "name": None,
                            "lastMeterIndexValue": 0,
                            "geographicAddress": {
                                "geographicAddressId": geographic_address_id,
                                "number": None,
                                "lane": None,
                                "streetAddress": str(index_client)
                                + ", RUE DE LA POMPE",
                                "addressComplement": "COMPLEMENT "
                                + str(index_client),
                                "inseeCode": "4910" + str(index_client),
                                "zipCode": "4952" + str(index_client),
                                "commune": "PARIS " + str(index_client),
                                "city": "PARIS " + str(index_client),
                                "country": None,
                                "countryCode": "France",
                                "building": None,
                                "floor": None,
                                "stairs": None,
                                "door": None,
                            },
                            "isEligibleCoachConso": False,
                            "isEligibleNewFeaturesMessage": False,
                            "isMultiTargetAlertsEnabled": False,
                        }
                    ],
                }
            ],
            "pendingRequest": False,
        }

    # Générer les clients en utilisant les client_ids fournis
    # clients = [generate_fake_client(client_id, index) for index, client_id in enumerate(client_ids)]
    clients = [
        generate_fake_client(data["clientId"], index, sectionid)
        for index, (sectionid, data) in enumerate(CLIENTS.items())
    ]

    # Assembler le JSON
    area_json = {
        "webSiteClientAreaDtoId": 866459,
        "clients": clients,
        "isClientEligible": False,
        "families": [],
    }

    return area_json


def generate_delivery_point(
    serial_number: str, installation_date: str
) -> dict[str, Any]:
    return {
        "deliveryPointId": "01234567890123456789",
        "reference": "01234567890123456789",
        "regionCode": "99",
        "commissioningDate": "2000-01-01T00:00:00",
        "removalDate": "1900-01-01T00:00:00",
        "deliveryPointStatusCode": "ENSERV",
        "meterDomainCode": "PRVACCESSOBS",
        "meterLocationCode": "NonDéfini",
        "meterLocationLabel": "Non Défini",
        "productCode": "EPOTA",
        "sectionSubscriptionId": "01234567890123456789",
        "sectionSubscription": {
            "id": 1234567890123456789,
            "sourceId": 1,
            "regionCode": "5",
            "connectionCategory": "PrivateClients",
            "fixedConsumption": 0,
            "applicationModeCode": "MAX",
            "meterOwnerTypeCode": "1",
            "meterOwnerTypeLabel": "Société",
            "sendOverConsumptionAlertToClient": 1,
            "averageConsumption": 123,
            "estimateConsumption": 0,
            "entryDate": "1900-01-01T00:00:00",
            "exitDate": "1900-01-01T00:00:00",
            "billableCode": "0",
            "isInsured": "0",
            "referenceDeliveryPointId": None,
            "deliveryPointId": 1234567890123456789,
            "contractId": 1234567890123456789,
            "partnerContractId": None,
            "clientId": "01234567890123456789",
            "supplyDeliveryPoint": None,
        },
        "geographicAddress": {
            "geographicAddressId": "01234567890123456789",
            "number": "0",
            "lane": "SOMEWHERE",
            "streetAddress": "0 SOMEWHERE",
            "addressComplement": None,
            "inseeCode": "12345",
            "zipCode": "12345",
            "commune": "FAKE TOWN",
            "city": "FAKE TOWN",
            "country": "France",
            "countryCode": "France",
            "building": None,
            "floor": None,
            "stairs": None,
            "door": None,
        },
        "meter": {
            "meterId": "01234567890123456789",
            "deliveryPointId": "01234567890123456789",
            "supplyAreaId": None,
            "manufacturingYear": datetime.now().year - 1,
            "meterState": "0",
            "registrationNumber": "12345",
            "meterDiameterCode": "15mm",
            "meterBrandCode": "MADDALENA (MID)",
            "meterModelCode": "tModele169",
            "serialNumber": serial_number,
            "meterStatusCode": "POSE",
            "meterPropertyCode": None,
            "installationDate": installation_date,
            "removalDate": None,
            "calibrationDate": "1900-01-01T00:00:00",
            "measureUnitCode": None,
            "pairingStatusCode": "APP",
            "pairingTechnologyCode": "TeleCoronis",
            "lastMeterIndex": None,
            "trueRegistrationNumber": "A12345Z",
        },
    }


def main() -> None:
    """Set up the server."""
    uvicorn.run(app, host="127.0.0.1", port=8080)


if __name__ == "__main__":
    main()
