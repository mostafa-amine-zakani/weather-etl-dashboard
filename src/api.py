"""API REST FastAPI : expose les données transformées + sert le dashboard."""
from datetime import date

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.config import BASE_DIR, CITIES
from src.db import get_connection

app = FastAPI(title="Weather ETL Dashboard", version="1.0.0")

STATIC_DIR = BASE_DIR / "static"


def _query(sql: str, params: tuple = ()) -> list[dict]:
    conn = get_connection()
    try:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/cities")
def cities() -> list[str]:
    """Villes configurées (le dashboard s'en sert pour les filtres)."""
    return list(CITIES)


@app.get("/api/weather")
def weather(
    city: str | None = Query(default=None, description="Filtrer sur une ville"),
    start: date | None = Query(default=None, description="Date de début (YYYY-MM-DD)"),
    end: date | None = Query(default=None, description="Date de fin (YYYY-MM-DD)"),
) -> list[dict]:
    """Moyennes journalières, filtrables par ville et période."""
    if city is not None and city not in CITIES:
        raise HTTPException(status_code=404, detail=f"Ville inconnue : {city}")

    sql = "SELECT city, date, temp_avg, temp_min, temp_max, humidity_avg, wind_avg FROM daily_weather WHERE 1=1"
    params: list = []
    if city:
        sql += " AND city = ?"
        params.append(city)
    if start:
        sql += " AND date >= ?"
        params.append(start.isoformat())
    if end:
        sql += " AND date <= ?"
        params.append(end.isoformat())
    sql += " ORDER BY date ASC, city ASC"
    return _query(sql, tuple(params))


@app.get("/api/summary")
def summary() -> list[dict]:
    """Dernière journée disponible par ville (cartes du dashboard)."""
    return _query(
        """
        SELECT dw.city, dw.date, dw.temp_avg, dw.temp_min, dw.temp_max, dw.humidity_avg, dw.wind_avg
        FROM daily_weather dw
        JOIN (SELECT city, MAX(date) AS max_date FROM daily_weather GROUP BY city) last
          ON dw.city = last.city AND dw.date = last.max_date
        ORDER BY dw.city
        """
    )


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
