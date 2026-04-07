"""Scraping + matching pipeline service (no Qt imports)."""
from __future__ import annotations

import logging
from datetime import datetime

import httpx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import (
    ADZUNA_APP_ID,
    ADZUNA_API_KEY,
    CLAUDE_THRESHOLD,
    DEDUP_COSINE_THRESHOLD,
    MAX_OFFERS_PER_RUN,
    SOURCES,
    TFIDF_THRESHOLD,
)

logger = logging.getLogger(__name__)


def _profile_query() -> tuple[str, str]:
    try:
        from services.profile_service import get_profils

        profils = get_profils()
        if profils:
            p = profils[0]
            return str(getattr(p, "titre", "stage") or "stage"), str(getattr(p, "localisation", "Maroc") or "Maroc")
    except Exception:
        pass
    return "stage", "Maroc"


def _offer_dict(source: str, titre: str, entreprise: str, localisation: str, description: str, url: str) -> dict:
    return {
        "source": source,
        "titre": (titre or "").strip()[:300],
        "entreprise": (entreprise or "").strip()[:200],
        "localisation": (localisation or "").strip()[:150],
        "description": (description or "").strip(),
        "url": (url or "").strip()[:500],
        "date_detection": datetime.utcnow(),
    }


def scrape_rss_indeed(titre: str, ville: str) -> list[dict]:
    import feedparser

    feed_url = f"https://fr.indeed.com/rss?q={titre}&l={ville}"
    feed = feedparser.parse(feed_url)
    offers: list[dict] = []
    for entry in feed.entries[:MAX_OFFERS_PER_RUN]:
        if getattr(entry, "title", "") and getattr(entry, "link", ""):
            offers.append(
                _offer_dict(
                    "indeed_rss",
                    getattr(entry, "title", ""),
                    getattr(entry, "author", ""),
                    ville,
                    getattr(entry, "summary", ""),
                    getattr(entry, "link", ""),
                )
            )
    return offers


def scrape_rss_url(source: str, url: str) -> list[dict]:
    import feedparser

    feed = feedparser.parse(url)
    offers: list[dict] = []
    for entry in feed.entries[:MAX_OFFERS_PER_RUN]:
        if getattr(entry, "title", "") and getattr(entry, "link", ""):
            offers.append(
                _offer_dict(
                    source,
                    getattr(entry, "title", ""),
                    getattr(entry, "author", ""),
                    "",
                    getattr(entry, "summary", ""),
                    getattr(entry, "link", ""),
                )
            )
    return offers


def scrape_playwright(source_key: str) -> list[dict]:
    cfg = SOURCES.get(source_key, {})
    url = cfg.get("url", "")
    selectors = cfg.get("selectors", {})
    if not url:
        return []

    from playwright.sync_api import sync_playwright

    offers: list[dict] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=20000)
        page.wait_for_load_state("networkidle", timeout=20000)

        items = page.query_selector_all(selectors.get("listing", ""))
        for item in items[:MAX_OFFERS_PER_RUN]:
            try:
                title_el = item.query_selector(selectors.get("title", "a"))
                link_el = item.query_selector(selectors.get("link", "a"))
                company_el = item.query_selector(selectors.get("company", ""))
                location_el = item.query_selector(selectors.get("location", ""))

                title = title_el.inner_text().strip() if title_el else ""
                href = link_el.get_attribute("href") if link_el else ""
                company = company_el.inner_text().strip() if company_el else ""
                location = location_el.inner_text().strip() if location_el else ""
                if not title or not href:
                    continue
                if not href.startswith("http"):
                    href = url.rstrip("/") + "/" + href.lstrip("/")

                offers.append(_offer_dict(source_key, title, company, location, "", href))
            except Exception:
                continue
        browser.close()
    return offers


def scrape_adzuna(titre: str, ville: str) -> list[dict]:
    if not ADZUNA_APP_ID or not ADZUNA_API_KEY:
        return []
    url = "https://api.adzuna.com/v1/api/jobs/ma/search/1"
    response = httpx.get(
        url,
        params={
            "app_id": ADZUNA_APP_ID,
            "app_key": ADZUNA_API_KEY,
            "what": titre,
            "where": ville,
            "results_per_page": min(50, MAX_OFFERS_PER_RUN),
        },
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    offers: list[dict] = []
    for row in data.get("results", []):
        offers.append(
            _offer_dict(
                "adzuna",
                row.get("title", ""),
                row.get("company", {}).get("display_name", ""),
                row.get("location", {}).get("display_name", ""),
                row.get("description", ""),
                row.get("redirect_url", ""),
            )
        )
    return offers


def scrape_all() -> list[dict]:
    titre, ville = _profile_query()
    offers: list[dict] = []

    tasks = [
        ("indeed_rss", lambda: scrape_rss_indeed(titre, ville)),
        ("bayt", lambda: scrape_rss_url("bayt", "https://www.bayt.com/rss/maroc/stage-jobs/")),
        ("remotive", lambda: scrape_rss_url("remotive", "https://remotive.com/remote-jobs/feed")),
        ("rekrute", lambda: scrape_playwright("rekrute")),
        ("emploi_ma", lambda: scrape_playwright("emploi_ma")),
        ("adzuna", lambda: scrape_adzuna(titre, ville)),
    ]

    for source, fn in tasks:
        try:
            if not SOURCES.get(source, {}).get("enabled", source in {"indeed_rss", "bayt", "rekrute", "emploi_ma", "adzuna"}):
                continue
            batch = fn()
            offers.extend(batch)
            logger.info("Source %s: %s offres", source, len(batch))
        except Exception as exc:
            logger.error("Scraper source error [%s]: %s", source, exc)

    unique: list[dict] = []
    seen = set()
    for offer in offers:
        url = offer.get("url", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(offer)

    return unique


def _semantic_duplicate(db, candidate_title: str, candidate_company: str) -> bool:
    from database.models import Offre

    recent = db.query(Offre).order_by(Offre.date_detection.desc()).limit(350).all()
    if not recent:
        return False

    candidate = f"{candidate_title} {candidate_company}".strip().lower()
    corpus = [candidate] + [f"{o.titre} {o.entreprise}".strip().lower() for o in recent]
    vect = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
    matrix = vect.fit_transform(corpus)
    sims = cosine_similarity(matrix[0:1], matrix[1:]).ravel()
    return bool(len(sims) and float(max(sims)) >= float(DEDUP_COSINE_THRESHOLD))


def process_and_save_offers(offers: list[dict]) -> int:
    """Applies dedup + TF-IDF + Claude gate and persists offers."""
    from database.db_manager import get_session
    from database.models import Offre, StatutOffre
    from services.auth_service import get_current_user, get_runtime_claude_key
    from services.matching_service import claude_score, tfidf_score
    from services.notification_service import trigger
    from services.profile_service import get_profils

    user = get_current_user()
    profils = get_profils()
    profil = profils[0] if profils else None

    if profil is None:
        return 0

    tfidf_limit = float(getattr(user, "tfidf_threshold", TFIDF_THRESHOLD) if user else TFIDF_THRESHOLD)
    claude_limit = float(getattr(user, "claude_threshold", CLAUDE_THRESHOLD) if user else CLAUDE_THRESHOLD)
    claude_key = get_runtime_claude_key()

    saved = 0
    with get_session() as db:
        for payload in offers:
            try:
                if db.query(Offre).filter_by(url=payload["url"]).first() is not None:
                    continue
                if _semantic_duplicate(db, payload.get("titre", ""), payload.get("entreprise", "")):
                    continue

                offre = Offre(**payload)
                score_tfidf_value = float(tfidf_score(offre, profil))
                setattr(offre, "score_tfidf", score_tfidf_value)
                if score_tfidf_value < tfidf_limit:
                    setattr(offre, "statut", StatutOffre.traitee)
                    db.add(offre)
                    saved += 1
                    continue

                fine = claude_score(offre, profil, claude_key)
                fine_score = fine.get("score")
                if fine_score is not None:
                    setattr(offre, "score_claude", float(fine_score))
                db.add(offre)
                db.flush()
                saved += 1

                stored_score = getattr(offre, "score_claude", None)
                if stored_score is not None and float(stored_score) >= claude_limit:
                    trigger(int(getattr(offre, "id", 0) or 0))
            except Exception as exc:
                logger.error("Offer process error: %s", exc)
                continue

    logger.info("Nouvelles offres sauvegardees: %s", saved)
    return saved


# Backward compatibility
save_offers_to_db = process_and_save_offers
