"""
services/profile_service.py - Gestion des profils utilisateur
Aucun import Qt.
"""
import json
import logging
from database.db_manager import get_session
from database.models import Profil
from services.auth_service import get_current_user

logger = logging.getLogger(__name__)


def get_profils() -> list[Profil]:
    """Retourne tous les profils de l'utilisateur connecté."""
    user = get_current_user()
    if not user:
        return []
    with get_session() as db:
        return db.query(Profil).filter_by(user_id=user.id).all()


def get_profil(profil_id: int) -> Profil | None:
    with get_session() as db:
        return db.get(Profil, profil_id)


def create_profil(titre: str) -> Profil | None:
    user = get_current_user()
    if not user:
        return None
    with get_session() as db:
        p = Profil(user_id=user.id, titre=titre)
        db.add(p)
        db.flush()
        return p


def update_profil(profil_id: int, data: dict) -> tuple[bool, str]:
    """
    Met à jour un profil.
    data = {titre, competences (list), formation, experience, langues,
            disponibilite, localisation, cv_path}
    """
    try:
        with get_session() as db:
            p = db.get(Profil, profil_id)
            if not p:
                return False, "Profil introuvable."

            if "titre" in data:
                p.titre = data["titre"]
            if "competences" in data:
                competences = data["competences"]
                if isinstance(competences, list):
                    p.competences = json.dumps(competences, ensure_ascii=False)
                else:
                    p.competences = competences
            if "formation" in data:
                p.formation = data["formation"]
            if "experience" in data:
                p.experience = data["experience"]
            if "langues" in data:
                p.langues = data["langues"]
            if "disponibilite" in data:
                p.disponibilite = data["disponibilite"]
            if "localisation" in data:
                p.localisation = data["localisation"]
            if "cv_path" in data:
                p.cv_path = data["cv_path"]

        return True, "Profil sauvegardé."
    except Exception as e:
        logger.error(f"Erreur update_profil: {e}")
        return False, f"Erreur: {e}"


def delete_profil(profil_id: int) -> tuple[bool, str]:
    try:
        with get_session() as db:
            p = db.get(Profil, profil_id)
            if not p:
                return False, "Profil introuvable."
            db.delete(p)
        return True, "Profil supprimé."
    except Exception as e:
        return False, str(e)


def parse_cv_text(cv_path: str) -> dict:
    """
    Extrait le texte d'un PDF CV et retourne un dict de champs pré-remplis.
    Utilise pdfplumber.
    """
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(cv_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return {"raw_text": text, "cv_path": cv_path}
    except ImportError:
        logger.warning("pdfplumber non installé, parsing CV ignoré.")
        return {"raw_text": "", "cv_path": cv_path}
    except Exception as e:
        logger.error(f"Erreur parsing CV: {e}")
        return {"raw_text": "", "cv_path": cv_path}


def parse_cv_with_claude(cv_path: str, api_key: str = "") -> dict[str, object]:
    """Extracts structured profile hints from a CV file.

    The function keeps a safe offline fallback path based on `pdfplumber` and
    only enriches with API data when an Anthropic client is available.
    """
    parsed = parse_cv_text(cv_path)
    raw_text = str(parsed.get("raw_text") or "")

    keywords = {
        "python": "Python",
        "sql": "SQL",
        "excel": "Excel",
        "power bi": "Power BI",
        "machine learning": "Machine Learning",
        "django": "Django",
        "flask": "Flask",
        "react": "React",
    }
    lower_text = raw_text.lower()
    competences = [value for key, value in keywords.items() if key in lower_text]

    profile: dict[str, object] = {
        "titre": "Profil extrait du CV",
        "competences": competences,
        "formation": "",
        "langues": "",
        "localisation": "",
        "cv_path": cv_path,
        "raw_text": raw_text,
    }

    # Optional Claude enrichment when user key is provided.
    if api_key.strip() and raw_text.strip():
        try:
            from services.generator_service import _call_claude  # type: ignore

            prompt = (
                "Extrait un JSON valide avec les champs titre, competences (liste), formation, langues, localisation "
                "depuis ce CV:\n" + raw_text[:3500]
            )
            response = _call_claude(api_key, prompt, max_tokens=600, temperature=0.1)
            if response:
                if "```" in response:
                    parts = response.split("```")
                    response = parts[1].replace("json", "").strip() if len(parts) > 1 else response
                parsed = json.loads(response)
                profile.update({
                    "titre": str(parsed.get("titre", profile["titre"])),
                    "competences": list(parsed.get("competences", profile["competences"])),
                    "formation": str(parsed.get("formation", "")),
                    "langues": str(parsed.get("langues", "")),
                    "localisation": str(parsed.get("localisation", "")),
                })
        except Exception as exc:
            logger.debug("Claude CV enrichment unavailable: %s", exc)
    return profile
