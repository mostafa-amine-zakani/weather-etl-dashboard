"""Accès SQLite : connexion et schéma."""
import sqlite3
from pathlib import Path

from src.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS daily_weather (
    city         TEXT NOT NULL,
    date         TEXT NOT NULL,          -- YYYY-MM-DD (UTC)
    temp_avg     REAL,
    temp_min     REAL,
    temp_max     REAL,
    humidity_avg REAL,
    wind_avg     REAL,
    updated_at   TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (city, date)
);
CREATE INDEX IF NOT EXISTS idx_daily_weather_date ON daily_weather(date);
"""


def get_connection(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn
