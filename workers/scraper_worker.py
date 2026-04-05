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


def _run_scrape_cycle():
    """Un cycle complet de scraping + matching + sauvegarde."""
    from services.scraper_service import scrape_all, save_offers_to_db
    from services.matching_service import match_offre_profil, build_profil_corpus
    from services.auth_service import get_current_user
    from services.profile_service import get_profils
    from database.db_manager import get_session
    from database.models import Offre

    logger.info(f"[{datetime.now()}] Cycle de scraping démarré")
    try:
        raw_offers = scrape_all()
        saved = save_offers_to_db(raw_offers)

        # Scoring TF-IDF sur les nouvelles offres
        user = get_current_user()
        if user:
            profils = get_profils()
            if profils:
                profil = profils[0]  # Profil principal
                with get_session() as db:
                    new_offers = db.query(Offre).filter(
                        Offre.score_tfidf == 0.0
                    ).limit(50).all()
                    for offre in new_offers:
                        from services.matching_service import score_tfidf, build_profil_corpus
                        pt = build_profil_corpus(profil)
                        ot = f"{offre.titre} {offre.description}".lower()
                        offre.score_tfidf = score_tfidf(ot, pt)

        logger.info(f"Cycle terminé. {saved} nouvelles offres.")
    except Exception as e:
        logger.error(f"Erreur cycle scraping: {e}")


def start_worker(on_new_offers_callback=None):
    """Démarre le scheduler APScheduler dans un thread daemon."""
    global _scheduler, _running
    if _running:
        logger.warning("Worker déjà actif.")
        return

    try:
        from apscheduler.schedulers.background import BackgroundScheduler

        _scheduler = BackgroundScheduler()
        _scheduler.add_job(
            _run_scrape_cycle,
            trigger="interval",
            minutes=SCRAPE_INTERVAL_MINUTES,
            id="scrape_job",
            next_run_time=datetime.now(),  # Lance immédiatement au démarrage
        )
        _scheduler.start()
        _running = True
        logger.info(f"Worker démarré (intervalle: {SCRAPE_INTERVAL_MINUTES} min)")
    except ImportError:
        logger.error("APScheduler non installé.")
    except Exception as e:
        logger.error(f"Erreur démarrage worker: {e}")


def stop_worker():
    global _scheduler, _running
    if _scheduler and _running:
        _scheduler.shutdown(wait=False)
        _running = False
        logger.info("Worker arrêté.")


def is_running() -> bool:
    return _running


def run_now():
    """Force un cycle immédiat (depuis le dashboard)."""
    t = threading.Thread(target=_run_scrape_cycle, daemon=True)
    t.start()
    return t
