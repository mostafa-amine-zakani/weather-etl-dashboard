"""Tests Transform : typage, valeurs manquantes/aberrantes, agrégation."""
import pandas as pd

from src.etl.transform import hourly_to_daily, raw_to_hourly_df, transform


def payload(city="Casablanca", times=None, temps=None, hums=None, winds=None):
    times = times or ["2026-07-01T00:00", "2026-07-01T12:00", "2026-07-02T00:00"]
    n = len(times)
    return {
        "city": city,
        "hourly": {
            "time": times,
            "temperature_2m": temps if temps is not None else [20.0] * n,
            "relative_humidity_2m": hums if hums is not None else [50.0] * n,
            "wind_speed_10m": winds if winds is not None else [10.0] * n,
        },
    }


def test_raw_to_hourly_types_and_city():
    df = raw_to_hourly_df(payload())
    assert pd.api.types.is_datetime64_any_dtype(df["time"])
    assert df["temperature"].dtype == float
    assert (df["city"] == "Casablanca").all()


def test_out_of_bounds_values_become_nan_then_interpolated():
    # 999 °C est aberrant -> NaN -> interpolé entre 10 et 20
    df = raw_to_hourly_df(payload(
        times=["2026-07-01T00:00", "2026-07-01T01:00", "2026-07-01T02:00"],
        temps=[10.0, 999.0, 20.0],
    ))
    assert df["temperature"].tolist() == [10.0, 15.0, 20.0]


def test_missing_values_handled():
    df = raw_to_hourly_df(payload(
        times=["2026-07-01T00:00", "2026-07-01T01:00", "2026-07-01T02:00"],
        temps=[10.0, None, 30.0],
    ))
    assert not df["temperature"].isna().any()


def test_daily_aggregation():
    df = raw_to_hourly_df(payload(
        times=["2026-07-01T00:00", "2026-07-01T12:00", "2026-07-02T00:00"],
        temps=[10.0, 20.0, 30.0],
    ))
    daily = hourly_to_daily(df)
    assert len(daily) == 2
    d1 = daily[daily["date"] == "2026-07-01"].iloc[0]
    assert d1["temp_avg"] == 15.0
    assert d1["temp_min"] == 10.0
    assert d1["temp_max"] == 20.0


def test_transform_multiple_cities_and_empty_payload():
    out = transform([payload("Casablanca"), payload("Tokyo"), {"city": "X", "hourly": {}}])
    assert set(out["city"]) == {"Casablanca", "Tokyo"}
    assert {"temp_avg", "humidity_avg", "wind_avg"} <= set(out.columns)


def test_transform_empty_input_returns_empty_df():
    out = transform([])
    assert out.empty
