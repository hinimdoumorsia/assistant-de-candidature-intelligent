"""Authentication and secure user onboarding service (no Qt imports)."""
# pyright: reportMissingImports=false
from __future__ import annotations

import base64
import logging
import os
from typing import Any

import bcrypt
import httpx
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from config import BCRYPT_ROUNDS
from database.db_manager import get_session
from database.models import Profil, User

logger = logging.getLogger(__name__)

_current_user: User | None = None
_session_password: str = ""


def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=390000)
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def _encrypt_api_value(value: str, password: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    salt = os.urandom(16)
    token = Fernet(_derive_key(password, salt)).encrypt(raw.encode("utf-8"))
    return base64.urlsafe_b64encode(salt).decode("utf-8") + ":" + token.decode("utf-8")


def _decrypt_api_value(value: str, password: str) -> str:
    if not value or ":" not in value:
        return ""
    salt_b64, token = value.split(":", 1)
    salt = base64.urlsafe_b64decode(salt_b64.encode("utf-8"))
    return Fernet(_derive_key(password, salt)).decrypt(token.encode("utf-8")).decode("utf-8")


def mask_api_key(value: str) -> str:
    """Masks API keys in UI-safe format like sk-ant-****...****."""
    raw = (value or "").strip()
    if len(raw) <= 8:
        return "****"
    return f"{raw[:7]}****...{raw[-4:]}"


def get_current_user() -> User | None:
    return _current_user


def is_logged_in() -> bool:
    return _current_user is not None


def test_claude_key(api_key: str) -> tuple[bool, str]:
    """Validate Anthropic API key by requesting the models endpoint."""
    key = (api_key or "").strip()
    if not key:
        return False, "Clé Claude vide."

    try:
        response = httpx.get(
            "https://api.anthropic.com/v1/models",
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
            },
            timeout=12,
        )
        if response.status_code == 200:
            return True, "ok"
        if response.status_code in (401, 403):
            return False, "Clé invalide ou non autorisée"
        return False, f"Erreur API ({response.status_code})"
    except Exception as exc:
        return False, str(exc)


def create_user(payload: dict[str, Any]) -> tuple[bool, str, int | None]:
    """Create user + default profile with encrypted API keys."""
    nom = str(payload.get("nom", "")).strip()
    prenom = str(payload.get("prenom", "")).strip()
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))

    if not nom or not prenom or not email or not password:
        return False, "Tous les champs sont obligatoires.", None
    if "@" not in email or "." not in email:
        return False, "Email invalide.", None
    if len(password) < 8 or not any(c.isupper() for c in password) or not any(c.isdigit() for c in password):
        return False, "Mot de passe insuffisant (8+, 1 majuscule, 1 chiffre).", None

    profile_data = payload.get("profile", {}) if isinstance(payload.get("profile", {}), dict) else {}

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=BCRYPT_ROUNDS))
    enc_anthropic = _encrypt_api_value(str(payload.get("claude_key", "")), password)
    enc_adzuna = _encrypt_api_value(str(payload.get("adzuna_api_key", "")), password)

    try:
        with get_session() as db:
            existing = db.query(User).filter_by(email=email).first()
            if existing:
                return False, "Un compte existe déjà avec cet email.", None

            user = User(
                nom=nom,
                prenom=prenom,
                email=email,
                mot_de_passe=hashed.decode("utf-8"),
                anthropic_key=enc_anthropic,
                adzuna_app_id=str(payload.get("adzuna_app_id", "")).strip(),
                adzuna_app_key=enc_adzuna,
                claude_model=str(payload.get("claude_model", "claude-sonnet-4-6")).strip() or "claude-sonnet-4-6",
                notifications_active=True,
            )
            db.add(user)
            db.flush()

            profil = Profil(
                user_id=user.id,
                titre=str(profile_data.get("titre", "Mon Profil")).strip() or "Mon Profil",
                competences=(
                    json_dumps_list(profile_data.get("competences", []))
                    if isinstance(profile_data.get("competences", []), list)
                    else "[]"
                ),
                formation=str(profile_data.get("formation", "")),
                experience=str(profile_data.get("experience", "")),
                langues=str(profile_data.get("langues", "")),
                localisation=str(profile_data.get("localisation", "")),
                disponibilite=str(profile_data.get("disponibilite", "")),
                cv_path=str(profile_data.get("cv_path", "")),
                secteurs=(
                    json_dumps_list(payload.get("settings", {}).get("sectors", []))
                    if isinstance(payload.get("settings", {}), dict)
                    else "[]"
                ),
            )
            db.add(profil)
            db.flush()
            user_id = int(getattr(user, "id", 0) or 0)
            return True, "Compte créé avec succès.", user_id
    except Exception as exc:
        logger.error("Erreur create_user: %s", exc)
        return False, "Erreur lors de la création du compte.", None


def register(nom: str, prenom: str, email: str, password: str) -> tuple[bool, str]:
    """Backward-compatible wrapper kept for existing callers."""
    ok, msg, _ = create_user(
        {
            "nom": nom,
            "prenom": prenom,
            "email": email,
            "password": password,
        }
    )
    return ok, msg


def login(email: str, password: str) -> User | None:
    """Authenticate with bcrypt and keep session in memory only."""
    global _current_user, _session_password

    if not email or not password:
        return None

    try:
        with get_session() as db:
            user = db.query(User).filter_by(email=email.strip().lower()).first()
            if not user:
                return None
            if not bcrypt.checkpw(password.encode("utf-8"), user.mot_de_passe.encode("utf-8")):
                return None
            _current_user = user
            _session_password = password
            return user
    except Exception as exc:
        logger.error("Erreur login: %s", exc)
        return None


def login_with_message(email: str, password: str) -> tuple[bool, str]:
    """Compatibility helper for legacy callers expecting (ok, message)."""
    user = login(email, password)
    if user is None:
        return False, "Email ou mot de passe incorrect."
    return True, f"Bienvenue, {user.prenom} !"


def logout() -> None:
    global _current_user, _session_password
    _current_user = None
    _session_password = ""


def change_password(old_password: str, new_password: str) -> tuple[bool, str]:
    if not _current_user:
        return False, "Non connecté."
    if len(new_password) < 8:
        return False, "Nouveau mot de passe trop court (min 8 chars)."

    if not bcrypt.checkpw(old_password.encode("utf-8"), _current_user.mot_de_passe.encode("utf-8")):
        return False, "Ancien mot de passe incorrect."

    hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt(rounds=BCRYPT_ROUNDS))
    try:
        with get_session() as db:
            user = db.get(User, _current_user.id)
            if user is None:
                return False, "Utilisateur introuvable."
            user.mot_de_passe = hashed.decode("utf-8")
        setattr(_current_user, "mot_de_passe", hashed.decode("utf-8"))
        return True, "Mot de passe modifié."
    except Exception as exc:
        logger.error("Erreur changement mdp: %s", exc)
        return False, "Erreur lors du changement."


def get_user_api_keys(password: str) -> dict[str, str]:
    """Decrypt stored API keys for the currently authenticated user."""
    if not _current_user:
        return {}
    try:
        return {
            "claude_key": _decrypt_api_value(str(getattr(_current_user, "anthropic_key", "") or ""), password),
            "adzuna_app_id": str(getattr(_current_user, "adzuna_app_id", "") or ""),
            "adzuna_api_key": _decrypt_api_value(str(getattr(_current_user, "adzuna_app_key", "") or ""), password),
            "claude_model": str(getattr(_current_user, "claude_model", "claude-sonnet-4-6") or "claude-sonnet-4-6"),
        }
    except Exception:
        return {}


def get_runtime_claude_key() -> str:
    """Returns decrypted Claude key for the current in-memory session."""
    if not _current_user or not _session_password:
        return ""
    try:
        return _decrypt_api_value(str(getattr(_current_user, "anthropic_key", "") or ""), _session_password)
    except Exception:
        return ""


def get_runtime_adzuna_key() -> str:
    if not _current_user or not _session_password:
        return ""
    try:
        return _decrypt_api_value(str(getattr(_current_user, "adzuna_app_key", "") or ""), _session_password)
    except Exception:
        return ""


def json_dumps_list(value: Any) -> str:
    import json

    if not isinstance(value, list):
        return "[]"
    return json.dumps(value, ensure_ascii=False)
