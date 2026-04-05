"""
services/matching_service.py - TF-IDF local + Claude API scoring sémantique
Aucun import Qt.
"""
import json
import logging
from typing import Optional
from config import GROQ_API_KEY, GROQ_MODEL, TFIDF_THRESHOLD, CLAUDE_THRESHOLD

logger = logging.getLogger(__name__)


# ── TF-IDF (pré-filtrage local, 0 token Claude) ──────────────────────────────

_vectorizer = None
_profil_vector = None


def _get_vectorizer():
    global _vectorizer
    if _vectorizer is None:
        from sklearn.feature_extraction.text import TfidfVectorizer
        _vectorizer = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            min_df=1,
            max_features=10_000,
            sublinear_tf=True,
        )
    return _vectorizer


def build_profil_corpus(profil) -> str:
    """Construit un texte unique à partir du profil pour TF-IDF."""
    parts = []
    parts.append(profil.titre or "")
    parts.extend(profil.competences_list)
    parts.append(profil.formation or "")
    parts.append(profil.experience or "")
    return " ".join(parts).lower()


def score_tfidf(offre_text: str, profil_text: str) -> float:
    """Calcule la similarité cosine TF-IDF entre offre et profil. Retourne 0.0-1.0."""
    try:
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        vect = _get_vectorizer()
        corpus = [profil_text, offre_text]
        tfidf_matrix = vect.fit_transform(corpus)
        sim = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]
        return float(np.clip(sim, 0.0, 1.0))
    except Exception as e:
        logger.error(f"TF-IDF error: {e}")
        return 0.0


# ── Claude API scoring fin ────────────────────────────────────────────────────

def score_groq(offre: dict, profil) -> Optional[dict]:
    """
    Scoring sémantique fin via Groq API.
    Retourne dict: {score, competences_matchees, competences_manquantes, recommandation}
    ou None si API indisponible / offre sous seuil.
    """
    if not GROQ_API_KEY:
        logger.warning("GROQ_API_KEY non configurée, scoring Groq ignoré.")
        return None

    try:
        import groq
        client = groq.Client(api_key=GROQ_API_KEY)

        prompt = f"""Tu es un expert RH. Analyse la compatibilité entre ce profil candidat et cette offre de stage.

PROFIL:
- Titre: {profil.titre}
- Compétences: {', '.join(profil.competences_list)}
- Formation: {profil.formation}
- Expérience: {profil.experience}
- Langues: {profil.langues}
- Localisation: {profil.localisation}
- Disponibilité: {profil.disponibilite}

OFFRE:
- Titre: {offre.get('titre', '')}
- Entreprise: {offre.get('entreprise', '')}
- Localisation: {offre.get('localisation', '')}
- Description: {offre.get('description', '')[:1500]}

Réponds UNIQUEMENT en JSON valide avec cette structure exacte:
{{
  "score": <entier 0-100>,
  "competences_matchees": ["comp1", "comp2"],
  "competences_manquantes": ["comp1", "comp2"],
  "recommandation": "<phrase courte d'évaluation>"
}}"""

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
        )
        raw = response.choices[0].message.content.strip()
        # Extraire le JSON si entouré de backticks
        if "```" in raw:
            raw = raw.split("```")[1].replace("json", "").strip()
        result = json.loads(raw)
        return result
    except Exception as e:
        logger.error(f"Groq scoring error: {e}")
        return None


def match_offre_profil(offre, profil) -> dict:
    """
    Pipeline complet: TF-IDF → Claude si nécessaire.
    Retourne un dict avec tous les scores.
    """
    profil_text = build_profil_corpus(profil)
    offre_text  = f"{offre.titre} {offre.description}".lower()

    tfidf = score_tfidf(offre_text, profil_text)

    claude_result = None
    if tfidf >= TFIDF_THRESHOLD:
        offre_dict = {
            "titre": offre.titre,
            "entreprise": offre.entreprise,
            "localisation": offre.localisation,
            "description": offre.description,
        }
        groq_result = score_groq(offre_dict, profil)

    return {
        "score_tfidf": tfidf,
        "score_claude": groq_result.get("score") if groq_result else None,
        "competences_matchees": claude_result.get("competences_matchees", []) if claude_result else [],
        "competences_manquantes": claude_result.get("competences_manquantes", []) if claude_result else [],
        "recommandation": claude_result.get("recommandation", "") if claude_result else "",
    }
