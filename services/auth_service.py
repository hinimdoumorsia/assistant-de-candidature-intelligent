"""
services/auth_service.py - Authentification & gestion des sessions
Aucun import Qt — logique métier pure.
"""
import bcrypt
import logging
from database.db_manager import get_session
from database.models import User, Profil
from config import BCRYPT_ROUNDS

logger = logging.getLogger(__name__)

# Session utilisateur en mémoire (pas de fichier sur disque)
_current_user: User | None = None


def get_current_user() -> User | None:
    return _current_user


def is_logged_in() -> bool:
    return _current_user is not None


def register(nom: str, prenom: str, email: str, password: str) -> tuple[bool, str]:
    """
    Inscrit un nouvel utilisateur.
    Retourne (succès, message).
    """
    if not nom or not prenom or not email or not password:
        return False, "Tous les champs sont obligatoires."
    if "@" not in email or "." not in email:
        return False, "Email invalide."
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères."

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=BCRYPT_ROUNDS))

    try:
        with get_session() as db:
            existing = db.query(User).filter_by(email=email.lower()).first()
            if existing:
                return False, "Un compte existe déjà avec cet email."

            user = User(
                nom=nom.strip(),
                prenom=prenom.strip(),
                email=email.lower().strip(),
                mot_de_passe=hashed.decode("utf-8"),
            )
            db.add(user)
            db.flush()

            # Profil par défaut
            profil = Profil(user_id=user.id, titre="Mon Profil Principal")
            db.add(profil)

        logger.info(f"Nouvel utilisateur inscrit : {email}")
        return True, "Compte créé avec succès."
    except Exception as e:
        logger.error(f"Erreur register: {e}")
        return False, "Erreur lors de la création du compte."


def login(email: str, password: str) -> tuple[bool, str]:
    """
    Connecte un utilisateur. Retourne (succès, message).
    """
    global _current_user
    if not email or not password:
        return False, "Email et mot de passe requis."

    try:
        with get_session() as db:
            user = db.query(User).filter_by(email=email.lower().strip()).first()
            if not user:
                return False, "Email ou mot de passe incorrect."

            if not bcrypt.checkpw(password.encode("utf-8"), user.mot_de_passe.encode("utf-8")):
                return False, "Email ou mot de passe incorrect."

            _current_user = user
            logger.info(f"Connexion réussie : {email}")
            return True, f"Bienvenue, {user.prenom} !"
    except Exception as e:
        logger.error(f"Erreur login: {e}")
        return False, "Erreur lors de la connexion."


def logout():
    global _current_user
    _current_user = None
    logger.info("Déconnexion.")


def change_password(old_password: str, new_password: str) -> tuple[bool, str]:
    global _current_user
    if not _current_user:
        return False, "Non connecté."
    if len(new_password) < 8:
        return False, "Nouveau mot de passe trop court (min 8 chars)."

    if not bcrypt.checkpw(old_password.encode("utf-8"), _current_user.mot_de_passe.encode("utf-8")):
        return False, "Ancien mot de passe incorrect."

    hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt(rounds=BCRYPT_ROUNDS))
    try:
        with get_session() as db:
            user = db.query(User).get(_current_user.id)
            user.mot_de_passe = hashed.decode("utf-8")
        _current_user.mot_de_passe = hashed.decode("utf-8")
        return True, "Mot de passe modifié."
    except Exception as e:
        logger.error(f"Erreur changement mdp: {e}")
        return False, "Erreur lors du changement."
