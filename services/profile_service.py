"""
services/profile_service.py - Gestion des profils utilisateur
Aucun import Qt.
"""
import json
import logging
from database.db_manager import get_session
from database.models import Profil, User
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
        return db.query(Profil).get(profil_id)


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
            p = db.query(Profil).get(profil_id)
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
            p = db.query(Profil).get(profil_id)
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
