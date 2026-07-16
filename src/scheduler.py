"""Scheduler : python -m src.scheduler lance le pipeline toutes les N minutes."""
import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from src.config import ETL_INTERVAL_MINUTES
from src.etl.pipeline import run

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def main() -> None:
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(run, "interval", minutes=ETL_INTERVAL_MINUTES, next_run_time=None)
    run()  # premier run immédiat
    logging.info("Scheduler démarré (toutes les %d min). Ctrl+C pour arrêter.", ETL_INTERVAL_MINUTES)
    scheduler.start()


if __name__ == "__main__":
    main()
