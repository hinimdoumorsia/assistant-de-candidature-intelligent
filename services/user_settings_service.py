"""
services/user_settings_service.py - Parametres utilisateur persistes localement.
"""
import json
from pathlib import Path
from typing import Any

from services.api_keys_service import get_user_config_dir


SETTINGS_FILE = "user_settings.json"


DEFAULT_SETTINGS = {
    "theme_mode": "dark",
    "scrape_interval_minutes": 30,
    "tfidf_threshold": 0.40,
    "semantic_threshold": 60,
    "sources_enabled": {
        "indeed_rss": True,
        "rekrute": True,
        "emploi_ma": True,
        "bayt": True,
        "adzuna": True,
        "remotive": False,
    },
    "sectors": [],
}


def _settings_path() -> Path:
    return get_user_config_dir() / SETTINGS_FILE


def _read_all() -> dict[str, Any]:
    path = _settings_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_user_settings(user_email: str | None) -> dict[str, Any]:
    if not user_email:
        return dict(DEFAULT_SETTINGS)

    data = _read_all()
    user_data = data.get(user_email.lower().strip(), {})
    merged = dict(DEFAULT_SETTINGS)
    merged.update(user_data)
    merged["sources_enabled"] = {
        **DEFAULT_SETTINGS["sources_enabled"],
        **user_data.get("sources_enabled", {}),
    }
    return merged


def save_user_settings(user_email: str, settings: dict[str, Any]) -> tuple[bool, str]:
    if not user_email:
        return False, "Email utilisateur requis pour sauvegarder les parametres."

    try:
        all_data = _read_all()
        merged = dict(load_user_settings(user_email))
        merged.update(settings)

        if "sources_enabled" in settings:
            merged["sources_enabled"] = {
                **DEFAULT_SETTINGS["sources_enabled"],
                **settings.get("sources_enabled", {}),
            }

        all_data[user_email.lower().strip()] = merged
        path = _settings_path()
        path.write_text(json.dumps(all_data, ensure_ascii=False, indent=2), encoding="utf-8")
        return True, "Parametres enregistres."
    except Exception as e:
        return False, f"Erreur sauvegarde parametres: {e}"
