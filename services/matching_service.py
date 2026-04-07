"""Matching service: offline TF-IDF + Claude scoring (no Qt imports)."""
from __future__ import annotations

import json
import logging
from collections import Counter
from typing import Any

from anthropic import Anthropic
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import CLAUDE_MODEL, TFIDF_THRESHOLD

logger = logging.getLogger(__name__)


_VECTOR = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=1, max_features=10_000, sublinear_tf=True)


def _effective_tfidf_threshold() -> float:
    try:
        from services.auth_service import get_current_user
        from services.user_settings_service import load_user_settings

        user = get_current_user()
        settings = load_user_settings(getattr(user, "email", None))
        return float(settings.get("tfidf_threshold", TFIDF_THRESHOLD))
    except Exception:
        return float(TFIDF_THRESHOLD)


def _get_profile_skills(profil: Any) -> list[str]:
    raw = getattr(profil, "competences_list", None)
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    try:
        parsed = json.loads(str(getattr(profil, "competences", "[]") or "[]"))
        if isinstance(parsed, list):
            return [str(x).strip() for x in parsed if str(x).strip()]
    except Exception:
        pass
    return []


def _profile_text(profil: Any) -> str:
    parts = [
        str(getattr(profil, "titre", "") or ""),
        " ".join(_get_profile_skills(profil)),
        str(getattr(profil, "formation", "") or ""),
        str(getattr(profil, "experience", "") or ""),
        str(getattr(profil, "langues", "") or ""),
    ]
    return " ".join(parts).strip().lower()


def tfidf_score(offre: Any, profil: Any) -> float:
    """Returns cosine similarity in range [0, 1]."""
    try:
        offer_text = " ".join(
            [
                str(getattr(offre, "titre", "") or ""),
                str(getattr(offre, "description", "") or ""),
                str(getattr(offre, "entreprise", "") or ""),
            ]
        ).lower()
        prof_text = _profile_text(profil)
        if not offer_text.strip() or not prof_text.strip():
            return 0.0

        matrix = _VECTOR.fit_transform([prof_text, offer_text])
        sim = float(cosine_similarity(matrix[0:1], matrix[1:2]).ravel()[0])
        return max(0.0, min(1.0, sim))
    except Exception as exc:
        logger.error("TF-IDF error: %s", exc)
        return 0.0


def claude_score(offre: Any, profil: Any, api_key: str) -> dict[str, Any]:
    """Returns Claude JSON scoring payload expected by the pipeline."""
    key = (api_key or "").strip()
    if not key:
        return {
            "score": None,
            "competences_matchees": [],
            "competences_manquantes": [],
            "recommandation": "Clé Claude absente",
        }

    profile_skills = _get_profile_skills(profil)
    client = Anthropic(api_key=key)
    prompt = (
        "Analyse la compatibilite stage en JSON strict. Reponds uniquement avec un objet JSON ayant "
        "les champs score (0-100), competences_matchees (liste), competences_manquantes (liste), "
        "recommandation (texte court).\n"
        f"PROFIL: titre={getattr(profil, 'titre', '')}; competences={', '.join(profile_skills)}; "
        f"formation={getattr(profil, 'formation', '')}; experience={getattr(profil, 'experience', '')}.\n"
        f"OFFRE: titre={getattr(offre, 'titre', '')}; entreprise={getattr(offre, 'entreprise', '')}; "
        f"localisation={getattr(offre, 'localisation', '')}; description={str(getattr(offre, 'description', '') or '')[:2000]}"
    )

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=500,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}],
        )
        text = ""
        for block in response.content:
            if getattr(block, "type", "") == "text":
                text += getattr(block, "text", "")

        text = text.strip()
        if "```" in text:
            parts = text.split("```")
            text = parts[1].replace("json", "").strip() if len(parts) > 1 else text

        payload = json.loads(text)
        return {
            "score": int(payload.get("score", 0)),
            "competences_matchees": list(payload.get("competences_matchees", [])),
            "competences_manquantes": list(payload.get("competences_manquantes", [])),
            "recommandation": str(payload.get("recommandation", "")),
        }
    except Exception as exc:
        logger.error("Claude scoring error: %s", exc)
        return {
            "score": None,
            "competences_matchees": [],
            "competences_manquantes": [],
            "recommandation": "Erreur Claude",
        }


def match_offre_profil(offre: Any, profil: Any, api_key: str = "") -> dict[str, Any]:
    """Complete pipeline helper used by worker code."""
    score_local = tfidf_score(offre, profil)
    result: dict[str, Any] = {
        "score_tfidf": score_local,
        "score_claude": None,
        "competences_matchees": [],
        "competences_manquantes": [],
        "recommandation": "",
    }
    if score_local >= _effective_tfidf_threshold():
        fine = claude_score(offre, profil, api_key)
        result["score_claude"] = fine.get("score")
        result["competences_matchees"] = fine.get("competences_matchees", [])
        result["competences_manquantes"] = fine.get("competences_manquantes", [])
        result["recommandation"] = fine.get("recommandation", "")
    return result


def market_score(user_id: int) -> dict[str, Any]:
    """Computes top missing market skills from seen offers vs user profile."""
    from database.db_manager import get_session
    from database.models import Offre, Profil

    with get_session() as db:
        profil = db.query(Profil).filter_by(user_id=user_id).first()
        if profil is None:
            return {"competences_manquantes_top5": [], "suggestions": []}

        offers = db.query(Offre).order_by(Offre.date_detection.desc()).limit(200).all()
        if len(offers) < 30:
            return {"competences_manquantes_top5": [], "suggestions": []}

        known = {x.lower() for x in _get_profile_skills(profil)}
        tokens = []
        for offer in offers:
            txt = f"{offer.titre} {offer.description}".lower()
            for token in txt.replace("/", " ").replace(",", " ").split():
                if len(token) >= 4:
                    tokens.append(token)

        counts = Counter(tokens)
        missing = [w for w, _n in counts.most_common(30) if w not in known][:5]
        suggestions = [f"Ajouter une experience concretisant {m}" for m in missing]
        return {
            "competences_manquantes_top5": missing,
            "suggestions": suggestions,
        }


# Backward-compatible aliases
score_tfidf = tfidf_score
