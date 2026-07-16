"""Extract : appel de l'API Open-Meteo avec gestion des erreurs réseau."""
import logging
import time

import requests

from src.config import CITIES, HOURLY_VARS, OPEN_METEO_URL, PAST_DAYS

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Levée quand la récupération échoue après tous les retries."""


def fetch_city_weather(
    city: str,
    latitude: float,
    longitude: float,
    *,
    session: requests.Session | None = None,
    retries: int = 3,
    backoff: float = 1.5,
    timeout: int = 10,
) -> dict:
    """Récupère les données horaires d'une ville. Retry avec backoff exponentiel."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ",".join(HOURLY_VARS),
        "past_days": PAST_DAYS,
        "forecast_days": 1,
        "timezone": "UTC",
    }
    http = session or requests
    last_err: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            resp = http.get(OPEN_METEO_URL, params=params, timeout=timeout)
            resp.raise_for_status()
            payload = resp.json()
            if "hourly" not in payload:
                raise ExtractionError(f"Réponse inattendue pour {city}: clé 'hourly' absente")
            payload["city"] = city
            return payload
        except (requests.RequestException, ValueError) as err:
            last_err = err
            logger.warning("Tentative %d/%d échouée pour %s: %s", attempt, retries, city, err)
            if attempt < retries:
                time.sleep(backoff ** attempt)

    raise ExtractionError(f"Échec de l'extraction pour {city}") from last_err


def extract_all(cities: dict | None = None) -> list[dict]:
    """Extrait les données de toutes les villes. Une ville en échec n'arrête pas les autres."""
    cities = cities or CITIES
    results: list[dict] = []
    with requests.Session() as session:
        for name, coords in cities.items():
            try:
                results.append(
                    fetch_city_weather(name, coords["latitude"], coords["longitude"], session=session)
                )
            except ExtractionError:
                logger.error("Ville ignorée après échecs répétés : %s", name)
    return results
