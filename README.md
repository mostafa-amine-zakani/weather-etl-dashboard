# Weather ETL + Dashboard

Pipeline ETL météo (Open-Meteo → SQLite) exposé via une API REST FastAPI et un dashboard Chart.js.
Villes suivies : **Casablanca, Paris, Tokyo** (modifiables dans `src/config.py`).

## Architecture (5 lignes)

1. **Extract** (`src/etl/extract.py`) : appel HTTP de l'API Open-Meteo (données horaires, 14 derniers jours), retries avec backoff exponentiel, une ville en échec ne bloque pas les autres.
2. **Transform** (`src/etl/transform.py`) : typage pandas, valeurs aberrantes hors bornes physiques → NaN, interpolation temporelle courte (≤ 3 h), agrégation en moyennes journalières (+ min/max température).
3. **Load** (`src/etl/load.py`) : upsert SQLite sur clé primaire `(city, date)` → idempotent, zéro doublon même en relançant le pipeline.
4. **API** (`src/api.py`) : FastAPI expose `/api/weather` (filtres ville/période), `/api/summary`, `/api/cities` et sert le dashboard statique.
5. **Dashboard** (`static/index.html`) : page unique HTML/JS + Chart.js — cartes de synthèse, courbes température/humidité/vent, comparaison des villes, filtres ville + période.

## Installation

```bash
python -m venv .venv && source .venv/bin/activate   # Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

## Lancement

```bash
# 1. Remplir la base (run ETL unique)
python -m src.etl.pipeline

# 2. Démarrer l'API + dashboard
uvicorn src.api:app --reload

# 3. Ouvrir http://127.0.0.1:8000  (doc API : http://127.0.0.1:8000/docs)
```

### Scheduler (optionnel)

Rafraîchissement automatique toutes les 60 min (configurable via `ETL_INTERVAL_MINUTES`) :

```bash
python -m src.scheduler
```

Alternative cron :

```cron
0 * * * * cd /chemin/vers/weather-etl && .venv/bin/python -m src.etl.pipeline
```

## Tests

```bash
python -m pytest tests/ -v
```

14 tests unitaires : extraction (mocks réseau, retries, erreurs), transformation (typage, NaN, valeurs aberrantes, agrégations), chargement (idempotence, mise à jour, base temporaire).

## Endpoints

| Méthode | Route | Description |
|---|---|---|
| GET | `/api/weather?city=&start=&end=` | Moyennes journalières filtrables (ville, période `YYYY-MM-DD`) |
| GET | `/api/summary` | Dernière journée disponible par ville |
| GET | `/api/cities` | Liste des villes configurées |
| GET | `/api/health` | Healthcheck |
| GET | `/` | Dashboard |

## Structure

```
weather-etl/
├── src/
│   ├── config.py          # villes, chemins, constantes
│   ├── db.py              # connexion SQLite + schéma
│   ├── api.py             # application FastAPI
│   ├── scheduler.py       # APScheduler (run périodique)
│   └── etl/
│       ├── extract.py     # E — appel API + gestion erreurs réseau
│       ├── transform.py   # T — nettoyage + agrégation journalière
│       ├── load.py        # L — upsert SQLite idempotent
│       └── pipeline.py    # orchestration (run unique)
├── static/index.html      # dashboard Chart.js (page unique)
├── tests/                 # pytest (extract / transform / load)
├── data/                  # weather.db (gitignoré)
└── requirements.txt
```

## Choix techniques (résumé)

- **Granularité stockée : journalière.** Le brief demande des moyennes journalières ; stocker l'agrégat directement simplifie l'API et le dashboard. La table `daily_weather` a une PK `(city, date)` avec `ON CONFLICT DO UPDATE` — relancer l'ETL met à jour les jours existants au lieu de dupliquer.
- **`past_days=14`** : chaque run recouvre les 14 derniers jours, ce qui répare automatiquement les trous si le scheduler a été arrêté quelques jours.
- **Valeurs manquantes** : bornes physiques (`-60..60 °C`, `0..100 %`, `0..120 km/h`) pour neutraliser les aberrations, puis interpolation temporelle limitée à 3 h ; les jours sans aucune température valide sont exclus.
- **Timezone UTC partout** (extraction et dates agrégées) pour comparer les villes sur des journées identiques.
- **Pas de framework front** : un seul fichier HTML, Chart.js via CDN, fetch natif.

## Captures d'écran

Le dashboard affiche 3 cartes de synthèse (dernière journée par ville) puis 3 graphiques
(température comparée, humidité, vent) avec filtres ville et période.
Ajoutez vos captures dans `docs/` après un premier lancement :

```markdown
![Dashboard](docs/screenshot-dashboard.png)
```
