"""
services/api_keys_service.py - Validation et stockage local des cles API utilisateur.
"""
import os
from pathlib import Path
from typing import Tuple

import httpx


def get_user_config_dir() -> Path:
    """Retourne le dossier de config utilisateur (Windows/Linux/macOS)."""
    if os.name == "nt":
        base = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
        cfg = base / "StageAuto"
    else:
        cfg = Path.home() / ".config" / "stageauto"
    cfg.mkdir(parents=True, exist_ok=True)
    return cfg


def get_user_env_path() -> Path:
    return get_user_config_dir() / ".env"


def _write_env_value(env_path: Path, key: str, value: str) -> None:
    existing_lines: list[str] = []
    if env_path.exists():
        existing_lines = env_path.read_text(encoding="utf-8").splitlines()

    replacement = f"{key}={value}"
    updated_lines: list[str] = []
    replaced = False

    for line in existing_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            updated_lines.append(line)
            continue

        current_key, _ = line.split("=", 1)
        if current_key.strip() == key:
            updated_lines.append(replacement)
            replaced = True
        else:
            updated_lines.append(line)

    if not replaced:
        updated_lines.append(replacement)

    env_path.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")


def save_api_keys(
    claude_key: str,
    claude_model: str,
    adzuna_app_id: str,
    adzuna_api_key: str,
    adzuna_country: str,
) -> Tuple[bool, str]:
    """Sauvegarde les cles dans le .env utilisateur."""
    try:
        env_path = get_user_env_path()
        env_path.touch(exist_ok=True)

        _write_env_value(env_path, "CLAUDE_API_KEY", claude_key.strip())
        _write_env_value(env_path, "CLAUDE_MODEL", claude_model.strip() or "claude-3-5-sonnet-20241022")
        _write_env_value(env_path, "ADZUNA_APP_ID", adzuna_app_id.strip())
        _write_env_value(env_path, "ADZUNA_API_KEY", adzuna_api_key.strip())
        _write_env_value(env_path, "ADZUNA_COUNTRY", adzuna_country.strip() or "ma")
        return True, f"Cles enregistrees dans {env_path}"
    except Exception as e:
        return False, f"Erreur de sauvegarde des cles: {e}"


def test_claude_key(api_key: str) -> Tuple[bool, str]:
    """Teste la cle Anthropic via endpoint models."""
    key = (api_key or "").strip()
    if not key:
        return False, "Cle Claude vide."

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
            return True, "Connexion Claude valide."
        if response.status_code in (401, 403):
            return False, "Cle Claude invalide ou non autorisee."
        return False, f"Erreur Claude ({response.status_code})."
    except Exception as e:
        return False, f"Echec test Claude: {e}"


def test_adzuna_keys(app_id: str, app_key: str, country: str = "ma") -> Tuple[bool, str]:
    """Teste les cles Adzuna avec une requete simple."""
    aid = (app_id or "").strip()
    akey = (app_key or "").strip()
    c = (country or "ma").strip().lower()

    if not aid and not akey:
        return True, "Adzuna non configure (optionnel)."
    if not aid or not akey:
        return False, "App ID et App Key sont requis ensemble."

    try:
        url = f"https://api.adzuna.com/v1/api/jobs/{c}/search/1"
        response = httpx.get(
            url,
            params={
                "app_id": aid,
                "app_key": akey,
                "results_per_page": 1,
                "what": "stage",
            },
            timeout=12,
        )
        if response.status_code == 200:
            return True, "Connexion Adzuna valide."
        if response.status_code in (401, 403):
            return False, "Cles Adzuna invalides."
        return False, f"Erreur Adzuna ({response.status_code})."
    except Exception as e:
        return False, f"Echec test Adzuna: {e}"
