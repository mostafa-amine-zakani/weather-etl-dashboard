"""Orchestration ETL : python -m src.etl.pipeline pour un run unique."""
import logging

from src.etl.extract import extract_all
from src.etl.load import load
from src.etl.transform import transform

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def run() -> int:
    """Exécute Extract -> Transform -> Load. Retourne le nombre de lignes chargées."""
    logger.info("Démarrage du pipeline ETL")
    raw = extract_all()
    if not raw:
        logger.error("Aucune donnée extraite, arrêt.")
        return 0
    daily = transform(raw)
    n = load(daily)
    logger.info("Pipeline terminé : %d lignes.", n)
    return n


if __name__ == "__main__":
    run()
