"""Transform : nettoyage, typage, valeurs manquantes, agrégation journalière."""
import pandas as pd

# Bornes de plausibilité physique : hors bornes -> NaN
BOUNDS = {
    "temperature": (-60.0, 60.0),      # °C
    "humidity": (0.0, 100.0),          # %
    "wind_speed": (0.0, 120.0),        # km/h (moyenne 10 m)
}


def raw_to_hourly_df(payload: dict) -> pd.DataFrame:
    """Convertit le JSON brut Open-Meteo en DataFrame horaire typé et nettoyé."""
    hourly = payload.get("hourly", {})
    df = pd.DataFrame(
        {
            "time": hourly.get("time", []),
            "temperature": hourly.get("temperature_2m", []),
            "humidity": hourly.get("relative_humidity_2m", []),
            "wind_speed": hourly.get("wind_speed_10m", []),
        }
    )
    if df.empty:
        return df

    df["city"] = payload.get("city", "unknown")
    df["time"] = pd.to_datetime(df["time"], errors="coerce", utc=True)
    df = df.dropna(subset=["time"])

    for col, (lo, hi) in BOUNDS.items():
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df.loc[(df[col] < lo) | (df[col] > hi), col] = pd.NA

    # Valeurs manquantes : interpolation temporelle courte (max 3 h), le reste laissé NaN
    df = df.sort_values("time").set_index("time")
    df[list(BOUNDS)] = df[list(BOUNDS)].astype(float).interpolate(method="time", limit=3)
    return df.reset_index()


def hourly_to_daily(df: pd.DataFrame) -> pd.DataFrame:
    """Agrège en moyennes journalières (+ min/max température).

    On ne conserve pas les jours sans aucune mesure de température.
    """
    if df.empty:
        return pd.DataFrame(
            columns=["city", "date", "temp_avg", "temp_min", "temp_max", "humidity_avg", "wind_avg"]
        )

    df = df.copy()
    df["date"] = df["time"].dt.date.astype(str)

    daily = (
        df.groupby(["city", "date"])
        .agg(
            temp_avg=("temperature", "mean"),
            temp_min=("temperature", "min"),
            temp_max=("temperature", "max"),
            humidity_avg=("humidity", "mean"),
            wind_avg=("wind_speed", "mean"),
        )
        .reset_index()
        .dropna(subset=["temp_avg"])
    )
    for col in ["temp_avg", "temp_min", "temp_max", "humidity_avg", "wind_avg"]:
        daily[col] = daily[col].round(2)
    return daily


def transform(payloads: list[dict]) -> pd.DataFrame:
    """Pipeline complet de transformation pour plusieurs villes."""
    frames = [hourly_to_daily(raw_to_hourly_df(p)) for p in payloads]
    frames = [f for f in frames if not f.empty]
    if not frames:
        return hourly_to_daily(pd.DataFrame())
    return pd.concat(frames, ignore_index=True)
