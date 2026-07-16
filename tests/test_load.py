"""Tests Load : insertion, idempotence (pas de doublons), mise à jour."""
import pandas as pd

from src.db import get_connection
from src.etl.load import load


def sample_df(temp=20.0):
    return pd.DataFrame([{
        "city": "Paris", "date": "2026-07-01",
        "temp_avg": temp, "temp_min": temp - 5, "temp_max": temp + 5,
        "humidity_avg": 60.0, "wind_avg": 12.0,
    }])


def count_rows(db_path):
    conn = get_connection(db_path)
    try:
        return conn.execute("SELECT COUNT(*) FROM daily_weather").fetchone()[0]
    finally:
        conn.close()


def test_load_inserts_rows(tmp_path):
    db = tmp_path / "t.db"
    assert load(sample_df(), db_path=db) == 1
    assert count_rows(db) == 1


def test_load_is_idempotent(tmp_path):
    db = tmp_path / "t.db"
    load(sample_df(), db_path=db)
    load(sample_df(), db_path=db)  # même (city, date) rechargé
    assert count_rows(db) == 1


def test_load_updates_existing_row(tmp_path):
    db = tmp_path / "t.db"
    load(sample_df(temp=20.0), db_path=db)
    load(sample_df(temp=25.0), db_path=db)
    conn = get_connection(db)
    try:
        row = conn.execute("SELECT temp_avg FROM daily_weather WHERE city='Paris'").fetchone()
    finally:
        conn.close()
    assert row["temp_avg"] == 25.0
    assert count_rows(db) == 1


def test_load_empty_df_is_noop(tmp_path):
    db = tmp_path / "t.db"
    assert load(pd.DataFrame(), db_path=db) == 0
