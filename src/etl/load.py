"""Load : insertion idempotente en SQLite (upsert sur (city, date))."""
import logging
import sqlite3
from pathlib import Path

import pandas as pd

from src.config import DB_PATH
from src.db import get_connection

logger = logging.getLogger(__name__)

UPSERT_SQL = """
INSERT INTO daily_weather (city, date, temp_avg, temp_min, temp_max, humidity_avg, wind_avg)
VALUES (:city, :date, :temp_avg, :temp_min, :temp_max, :humidity_avg, :wind_avg)
ON CONFLICT(city, date) DO UPDATE SET
    temp_avg     = excluded.temp_avg,
    temp_min     = excluded.temp_min,
    temp_max     = excluded.temp_max,
    humidity_avg = excluded.humidity_avg,
    wind_avg     = excluded.wind_avg,
    updated_at   = datetime('now');
"""


def load(daily: pd.DataFrame, db_path: Path | str = DB_PATH) -> int:
    """Insère/actualise les lignes journalières. Retourne le nombre de lignes traitées."""
    if daily.empty:
        logger.info("Rien à charger.")
        return 0

    records = daily.where(pd.notna(daily), None).to_dict(orient="records")
    conn: sqlite3.Connection = get_connection(db_path)
    try:
        with conn:  # transaction atomique
            conn.executemany(UPSERT_SQL, records)
    finally:
        conn.close()
    logger.info("%d lignes chargées (upsert).", len(records))
    return len(records)
