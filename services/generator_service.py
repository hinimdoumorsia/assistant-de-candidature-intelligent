"""
services/generator_service.py - Génération IA : LM, CV, coach, simulateur
Aucun import Qt.
"""
import json
import logging
from config import GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger(__name__)


def _groq_call(prompt: str, max_tokens: int = 1500) -> str | None:
    """Appel Groq API mutualisé."""
    if not GROQ_API_KEY:
        logger.warning("GROQ_API_KEY non configurée.")
        return None
    try:
        import groq
        client = groq.Client(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return None


def generate_lettre_motivation(profil, offre, variante: int = 1) -> str | None:
    """
    Génère une lettre de motivation.
    variante: 1=technique, 2=humain/motivation, 3=projet/impact
    """
    angles = {
        1: "technique et compétences (mets en avant les technologies, outils et réalisations concrètes)",
        2: "humain et motivation (mets en avant la passion, les valeurs et l'adéquation culturelle)",
        3: "projet et impact (mets en avant la vision, les objectifs à long terme et l'apport à l'entreprise)",
    }
    angle = angles.get(variante, angles[1])

    prompt = f"""Rédige une lettre de motivation professionnelle en français pour ce stage.
Angle: {angle}

CANDIDAT:
- Nom: {profil.user.prenom} {profil.user.nom}
- Profil: {profil.titre}
- Compétences: {', '.join(profil.competences_list)}
- Formation: {profil.formation}
- Expérience: {profil.experience}
- Langues: {profil.langues}
- Disponibilité: {profil.disponibilite}

OFFRE:
- Poste: {offre.titre}
- Entreprise: {offre.entreprise}
- Ville: {offre.localisation}
- Description: {offre.description[:1000]}

Génère une lettre de 3-4 paragraphes, ton professionnel mais chaleureux.
Commence directement par "Madame, Monsieur,"."""

    return _groq_call(prompt, max_tokens=800)


def generate_cv_json(profil) -> dict | None:
    """
    Génère/améliore un CV structuré en JSON depuis le profil.
    Retourne un dict prêt pour export PDF.
    """
    prompt = f"""Génère un CV structuré en JSON pour ce profil de stage.

PROFIL:
- Nom: {profil.user.prenom} {profil.user.nom}
- Titre visé: {profil.titre}
- Compétences: {', '.join(profil.competences_list)}
- Formation: {profil.formation}
- Expérience: {profil.experience}
- Langues: {profil.langues}
- Disponibilité: {profil.disponibilite}

Réponds UNIQUEMENT en JSON valide:
{{
  "nom_complet": "...",
  "titre": "...",
  "resume": "résumé professionnel 2-3 phrases",
  "competences": ["comp1", "comp2"],
  "formation": [{{"diplome": "...", "ecole": "...", "annee": "..."}}],
  "experience": [{{"poste": "...", "entreprise": "...", "duree": "...", "description": "..."}}],
  "langues": [{{"langue": "...", "niveau": "..."}}],
  "competences_soft": ["..."]
}}"""

    result = _groq_call(prompt, max_tokens=800)
    if not result:
        return None
    try:
        if "```" in result:
            result = result.split("```")[1].replace("json", "").strip()
        return json.loads(result)
    except Exception as e:
        logger.error(f"JSON parse error CV: {e}")
        return None


def coach_candidature(profil, offre) -> dict | None:
    """
    Analyse la candidature et fournit des conseils personnalisés.
    Retourne dict: {points_forts, points_faibles, mots_cles, reformulations}
    """
    prompt = f"""Tu es un coach de candidature expert. Analyse cette candidature et donne des conseils précis.

PROFIL:
- Compétences: {', '.join(profil.competences_list)}
- Formation: {profil.formation}
- Expérience: {profil.experience}

OFFRE:
- Poste: {offre.titre}
- Description: {offre.description[:800]}

Réponds en JSON:
{{
  "points_forts": ["point1", "point2", "point3"],
  "points_faibles": ["point1", "point2"],
  "mots_cles_manquants": ["mot1", "mot2", "mot3"],
  "conseils": ["conseil1", "conseil2", "conseil3"],
  "score_global": <0-100>
}}"""

    result = _groq_call(prompt, max_tokens=600)
    if not result:
        return None
    try:
        if "```" in result:
            result = result.split("```")[1].replace("json", "").strip()
        return json.loads(result)
    except Exception as e:
        logger.error(f"JSON parse error coach: {e}")
        return None


def simulate_entretien(profil, offre, historique: list, message_user: str) -> str | None:
    """
    Simule un entretien de recrutement.
    historique: liste de {"role": "user"|"assistant", "content": "..."}
    Retourne la réponse du recruteur simulé.
    """
    system = f"""Tu es un recruteur professionnel qui conduit un entretien de stage pour le poste de {offre.titre} chez {offre.entreprise}.

Contexte du candidat:
- Profil: {profil.titre}
- Compétences: {', '.join(profil.competences_list)}
- Formation: {profil.formation}

Conduis l'entretien de façon naturelle, pose des questions pertinentes, relance si nécessaire.
Commence par une présentation chaleureuse. Limite tes réponses à 150 mots maximum."""

    if not GROQ_API_KEY:
        return "⚠️ Clé API Groq non configurée. Veuillez l'ajouter dans le fichier .env"

    try:
        import groq
        client = groq.Client(api_key=GROQ_API_KEY)
        messages = [{"role": "system", "content": system}] + historique + [{"role": "user", "content": message_user}]
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Simulateur entretien error: {e}")
        return f"Erreur API: {e}"


def parse_cv_with_claude(cv_text: str) -> dict | None:
    """Parse le texte brut d'un CV et extrait les champs structurés."""
    prompt = f"""Extrait les informations de ce CV en JSON structuré.

CV (texte brut):
{cv_text[:2000]}

Réponds UNIQUEMENT en JSON:
{{
  "nom": "...",
  "prenom": "...",
  "email": "...",
  "titre": "...",
  "competences": ["comp1", "comp2"],
  "formation": "description courte",
  "experience": "description courte",
  "langues": "Français, Anglais..."
}}"""

    result = _groq_call(prompt, max_tokens=500)
    if not result:
        return None
    try:
        if "```" in result:
            result = result.split("```")[1].replace("json", "").strip()
        return json.loads(result)
    except Exception as e:
        logger.error(f"JSON parse error CV parsing: {e}")
        return None
