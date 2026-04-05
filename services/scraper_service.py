"""
services/scraper_service.py - RSS + Playwright + Adzuna API
Aucun import Qt.
"""
import logging
import hashlib
from datetime import datetime
from typing import Iterator
from config import SOURCES, ADZUNA_APP_ID, ADZUNA_API_KEY, MAX_OFFERS_PER_RUN

logger = logging.getLogger(__name__)


def _make_offre_dict(source: str, titre: str, entreprise: str,
                     localisation: str, description: str, url: str) -> dict:
    return {
        "source": source,
        "titre": titre[:300],
        "entreprise": entreprise[:200],
        "localisation": localisation[:150],
        "description": description,
        "url": url[:500],
        "date_detection": datetime.utcnow(),
    }


# ── RSS (feedparser) ─────────────────────────────────────────────────────────

def scrape_rss(source_key: str) -> list[dict]:
    cfg = SOURCES.get(source_key, {})
    if not cfg.get("enabled"):
        return []
    url = cfg.get("rss_url") or cfg.get("url", "")
    if not url:
        return []

    try:
        import feedparser
        feed = feedparser.parse(url)
        offers = []
        for entry in feed.entries[:MAX_OFFERS_PER_RUN]:
            title    = getattr(entry, "title", "")
            link     = getattr(entry, "link", "")
            summary  = getattr(entry, "summary", "")
            company  = getattr(entry, "author", "")
            location = ""
            if not title or not link:
                continue
            offers.append(_make_offre_dict(
                source=source_key,
                titre=title,
                entreprise=company,
                localisation=location,
                description=summary,
                url=link,
            ))
        logger.info(f"RSS {source_key}: {len(offers)} offres récupérées")
        return offers
    except ImportError:
        logger.error("feedparser non installé.")
        return []
    except Exception as e:
        logger.error(f"RSS {source_key} error: {e}")
        return []


# ── Playwright (Rekrute, Emploi.ma) ──────────────────────────────────────────

def scrape_playwright(source_key: str) -> list[dict]:
    cfg = SOURCES.get(source_key, {})
    if not cfg.get("enabled"):
        return []
    url = cfg.get("url", "")
    selectors = cfg.get("selectors", {})

    try:
        from playwright.sync_api import sync_playwright
        from config import PLAYWRIGHT_HEADLESS, PLAYWRIGHT_TIMEOUT_MS

        offers = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=PLAYWRIGHT_HEADLESS)
            page = browser.new_page()
            page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (compatible)"})
            page.goto(url, timeout=PLAYWRIGHT_TIMEOUT_MS)
            page.wait_for_load_state("networkidle", timeout=PLAYWRIGHT_TIMEOUT_MS)

            items = page.query_selector_all(selectors.get("listing", ".job"))
            for item in items[:MAX_OFFERS_PER_RUN]:
                try:
                    title_el    = item.query_selector(selectors.get("title", "a"))
                    company_el  = item.query_selector(selectors.get("company", ""))
                    location_el = item.query_selector(selectors.get("location", ""))
                    link_el     = item.query_selector(selectors.get("link", "a"))

                    title    = title_el.inner_text()    if title_el    else ""
                    company  = company_el.inner_text()  if company_el  else ""
                    location = location_el.inner_text() if location_el else ""
                    href     = link_el.get_attribute("href") if link_el else ""

                    if not title or not href:
                        continue

                    if not href.startswith("http"):
                        base = url.rstrip("/")
                        href = base + "/" + href.lstrip("/")

                    offers.append(_make_offre_dict(
                        source=source_key,
                        titre=title.strip(),
                        entreprise=company.strip(),
                        localisation=location.strip(),
                        description="",
                        url=href,
                    ))
                except Exception as inner_e:
                    logger.debug(f"Item error {source_key}: {inner_e}")
                    continue

            browser.close()

        logger.info(f"Playwright {source_key}: {len(offers)} offres récupérées")
        return offers

    except ImportError:
        logger.error("playwright non installé. Lancez: pip install playwright && playwright install chromium")
        return []
    except Exception as e:
        logger.error(f"Playwright {source_key} error: {e}")
        return []


# ── Adzuna API ────────────────────────────────────────────────────────────────

def scrape_adzuna() -> list[dict]:
    cfg = SOURCES.get("adzuna", {})
    if not cfg.get("enabled"):
        return []
    if not ADZUNA_APP_ID or not ADZUNA_API_KEY:
        logger.warning("Adzuna API keys manquantes.")
        return []

    try:
        import httpx
        url = cfg["base_url"] + "/1"
        params = {
            "app_id":   ADZUNA_APP_ID,
            "app_key":  ADZUNA_API_KEY,
            "results_per_page": min(MAX_OFFERS_PER_RUN, 50),
            "what": "stage",
            "where": "Maroc",
            "content-type": "application/json",
        }
        resp = httpx.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        offers = []
        for job in data.get("results", []):
            offers.append(_make_offre_dict(
                source="adzuna",
                titre=job.get("title", ""),
                entreprise=job.get("company", {}).get("display_name", ""),
                localisation=job.get("location", {}).get("display_name", ""),
                description=job.get("description", ""),
                url=job.get("redirect_url", ""),
            ))
        logger.info(f"Adzuna: {len(offers)} offres récupérées")
        return offers
    except Exception as e:
        logger.error(f"Adzuna error: {e}")
        return []


# ── Pipeline principal ────────────────────────────────────────────────────────

def scrape_all() -> list[dict]:
    """Lance tous les scrapers activés et retourne la liste brute d'offres."""
    all_offers = []

    # RSS sources
    for key, cfg in SOURCES.items():
        if cfg.get("enabled") and cfg.get("method") in ("rss", "rss+playwright"):
            all_offers.extend(scrape_rss(key))

    # Playwright sources
    for key, cfg in SOURCES.items():
        if cfg.get("enabled") and cfg.get("method") in ("playwright", "rss+playwright"):
            all_offers.extend(scrape_playwright(key))

    # Adzuna API
    if SOURCES.get("adzuna", {}).get("enabled"):
        all_offers.extend(scrape_adzuna())

    # Déduplication par URL
    seen_urls = set()
    unique = []
    for o in all_offers:
        url = o.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique.append(o)

    logger.info(f"Total offres uniques: {len(unique)}")
    return unique


def save_offers_to_db(offers: list[dict]) -> int:
    """Sauvegarde les offres en base, ignore les doublons (URL UNIQUE)."""
    from database.db_manager import get_session
    from database.models import Offre

    saved = 0
    for o in offers:
        try:
            with get_session() as db:
                exists = db.query(Offre).filter_by(url=o["url"]).first()
                if not exists:
                    offre = Offre(**o)
                    db.add(offre)
                    saved += 1
        except Exception as e:
            logger.debug(f"Offre déjà en base ou erreur: {e}")
    logger.info(f"{saved} nouvelles offres sauvegardées.")
    return saved
