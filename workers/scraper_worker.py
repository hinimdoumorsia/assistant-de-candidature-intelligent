"""
workers/scraper_worker.py - Daemon APScheduler pour le scraping périodique
Lancé dans un thread séparé depuis le dashboard.
"""
import logging
import threading
from datetime import datetime
from config import SCRAPE_INTERVAL_MINUTES

logger = logging.getLogger(__name__)

_scheduler = None
_running    = False
_on_new_offers_callback = None


def _run_scrape_cycle():
    """Un cycle complet de scraping + matching + sauvegarde."""
    from services.scraper_service import process_and_save_offers, scrape_all

    global _on_new_offers_callback
    logger.info(f"[{datetime.now()}] Cycle de scraping démarré")
    try:
        raw_offers = scrape_all()
        saved = process_and_save_offers(raw_offers)

        logger.info(f"Cycle terminé. {saved} nouvelles offres.")
        if saved > 0 and callable(_on_new_offers_callback):
            try:
                _on_new_offers_callback(saved)
            except Exception as callback_error:
                logger.debug(f"Callback offres error: {callback_error}")
    except Exception as e:
        logger.error(f"Erreur cycle scraping: {e}")


def start_worker(on_new_offers_callback=None):
    """Démarre le scheduler APScheduler dans un thread daemon."""
    global _scheduler, _running, _on_new_offers_callback
    if _running:
        logger.warning("Worker déjà actif.")
        return

    _on_new_offers_callback = on_new_offers_callback

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from services.auth_service import get_current_user
        from services.user_settings_service import load_user_settings

        interval = SCRAPE_INTERVAL_MINUTES
        user = get_current_user()
        if user:
            settings = load_user_settings(user.email)
            interval = int(settings.get("scrape_interval_minutes", SCRAPE_INTERVAL_MINUTES))
            interval = max(15, min(120, interval))

        _scheduler = BackgroundScheduler()
        _scheduler.add_job(
            _run_scrape_cycle,
            trigger="interval",
            minutes=interval,
            id="scrape_job",
            next_run_time=datetime.now(),  # Lance immédiatement au démarrage
        )
        _scheduler.start()
        _running = True
        logger.info(f"Worker démarré (intervalle: {interval} min)")
    except ImportError:
        logger.error("APScheduler non installé.")
    except Exception as e:
        logger.error(f"Erreur démarrage worker: {e}")


def stop_worker():
    global _scheduler, _running
    if _scheduler and _running:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        _running = False
        logger.info("Worker arrêté.")


def is_running() -> bool:
    return _running


def run_now():
    """Force un cycle immédiat (depuis le dashboard)."""
    t = threading.Thread(target=_run_scrape_cycle, daemon=True)
    t.start()
    return t
