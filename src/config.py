"""Configuration centrale du projet."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "weather.db"

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# 3 villes suivies (nom -> coordonnées)
CITIES = {
    "Casablanca": {"latitude": 33.5731, "longitude": -7.5898},
    "Paris": {"latitude": 48.8566, "longitude": 2.3522},
    "Tokyo": {"latitude": 35.6762, "longitude": 139.6503},
}

HOURLY_VARS = ["temperature_2m", "relative_humidity_2m", "wind_speed_10m"]
PAST_DAYS = 14  # profondeur d'historique récupérée à chaque run

# Scheduler : fréquence du pipeline (minutes)
ETL_INTERVAL_MINUTES = 60
