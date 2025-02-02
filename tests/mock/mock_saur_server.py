"""Serveur de test pour l'API SAUR avec FastAPI et Uvicorn."""

# pylint: disable=E0401

import json
import logging
from typing import Any

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


async def _handle_json_endpoint(
    method: str,
    file_path: str,
    detail: str | None = None,
) -> dict[str, Any]:
    """Fonction générique pour gérer les endpoints JSON."""
    _LOGGER.info("Received %s request, processing %s", method, file_path)
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
    return await _handle_json_endpoint(
        method="GET",
        file_path="./delivery.json",
        detail=(
            "Erreur lors du traitement du endpoint /deli/section_"
            f"subscriptions/{default_section_id}/delivery_points"
        ),
    )


@app.get(
    "/deli/section_subscriptions/{default_section_id}/meter_indexes/last",
    response_class=JSONResponse,
)
async def handle_last(default_section_id: str) -> dict[str, Any]:
    """Handles the last meter index endpoint."""
    return await _handle_json_endpoint(
        method="GET",
        file_path="./last.json",
        detail=(
            "Erreur lors du traitement du endpoint /deli/"
            f"section_subscriptions/{default_section_id}/meter_indexes/last"
        ),
    )


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
    return await _handle_json_endpoint(
        method="GET",
        file_path="./weekly.json",
        detail=(
            "Erreur lors du traitement du endpoint /deli/section_subscription/"
            f"{default_section_id}/consumptions/weekly"
        ),
    )


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
    return await _handle_json_endpoint(
        method="GET",
        file_path="./monthly.json",
        detail=(
            "Erreur lors du traitement du endpoint /deli/section_subscription/"
            f"{default_section_id}/consumptions/monthly"
        ),
    )


def main():
    """Set up the server."""
    uvicorn.run(app, host="127.0.0.1", port=8080)


if __name__ == "__main__":
    main()
