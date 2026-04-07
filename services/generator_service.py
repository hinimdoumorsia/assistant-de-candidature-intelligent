"""Claude-based generation service (no Qt imports)."""
from __future__ import annotations

import json
import logging
from typing import Any

from anthropic import Anthropic

from config import CLAUDE_MODEL

logger = logging.getLogger(__name__)


def _extract_text(response) -> str:
    text = ""
    for block in getattr(response, "content", []) or []:
        if getattr(block, "type", "") == "text":
            text += getattr(block, "text", "")
    return text.strip()


def _call_claude(api_key: str, prompt: str, max_tokens: int = 1200, temperature: float = 0.2) -> str | None:
    key = (api_key or "").strip()
    if not key:
        return None
    try:
        client = Anthropic(api_key=key)
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return _extract_text(response)
    except Exception as exc:
        logger.error("Claude call error: %s", exc)
        return None


def generate_letter_variant(offre: Any, profil: Any, api_key: str, angle: str) -> str | None:
    prompt = (
        "Redige une lettre de motivation en francais pour candidature de stage. "
        f"Angle obligatoire: {angle}. "
        "Ton professionnel, 3 a 4 paragraphes, sans puces.\n"
        f"CANDIDAT: {getattr(profil, 'titre', '')}, competences={', '.join(getattr(profil, 'competences_list', []) or [])}, "
        f"formation={getattr(profil, 'formation', '')}, experience={getattr(profil, 'experience', '')}.\n"
        f"OFFRE: poste={getattr(offre, 'titre', '')}, entreprise={getattr(offre, 'entreprise', '')}, "
        f"ville={getattr(offre, 'localisation', '')}, description={str(getattr(offre, 'description', '') or '')[:1800]}"
    )
    return _call_claude(api_key, prompt, max_tokens=900)


def generate_letter_variants(offre: Any, profil: Any, api_key: str) -> dict[str, str | None]:
    return {
        "technique": generate_letter_variant(offre, profil, api_key, "TECHNIQUE (competences, stack, chiffres)"),
        "humain": generate_letter_variant(offre, profil, api_key, "HUMAIN (motivation, valeurs, culture)"),
        "projet": generate_letter_variant(offre, profil, api_key, "PROJET (vision, contribution, ambition)"),
    }


def merge_variants(variants: dict[str, str], api_key: str) -> str | None:
    joined = "\n\n".join([f"[{k}]\n{v}" for k, v in variants.items() if v])
    prompt = (
        "Fusionne les variantes suivantes en une seule lettre finale concise et coherente.\n"
        f"{joined}"
    )
    return _call_claude(api_key, prompt, max_tokens=900)


def generate_cv(profil: Any, api_key: str) -> dict[str, Any] | None:
    prompt = (
        "Retourne UNIQUEMENT un JSON valide de CV structure avec les champs: "
        "nom, contact, formation, experience, competences.\n"
        f"Nom: {getattr(getattr(profil, 'user', None), 'prenom', '')} {getattr(getattr(profil, 'user', None), 'nom', '')}\n"
        f"Titre: {getattr(profil, 'titre', '')}\n"
        f"Formation: {getattr(profil, 'formation', '')}\n"
        f"Experience: {getattr(profil, 'experience', '')}\n"
        f"Competences: {', '.join(getattr(profil, 'competences_list', []) or [])}"
    )
    text = _call_claude(api_key, prompt, max_tokens=1000)
    if not text:
        return None
    try:
        if "```" in text:
            parts = text.split("```")
            text = parts[1].replace("json", "").strip() if len(parts) > 1 else text
        return json.loads(text)
    except Exception as exc:
        logger.error("generate_cv parse error: %s", exc)
        return None


def coach_analyse(offre: Any, profil: Any, api_key: str) -> dict[str, Any] | None:
    prompt = (
        "Analyse cette candidature et retourne UNIQUEMENT un JSON avec: "
        "points_forts (liste), mots_cles_manquants (liste), reformulations (liste).\n"
        f"PROFIL: {getattr(profil, 'titre', '')}; competences={', '.join(getattr(profil, 'competences_list', []) or [])}.\n"
        f"OFFRE: {getattr(offre, 'titre', '')}; description={str(getattr(offre, 'description', '') or '')[:1800]}"
    )
    text = _call_claude(api_key, prompt, max_tokens=700)
    if not text:
        return None
    try:
        if "```" in text:
            parts = text.split("```")
            text = parts[1].replace("json", "").strip() if len(parts) > 1 else text
        payload = json.loads(text)
        return {
            "points_forts": list(payload.get("points_forts", [])),
            "mots_cles_manquants": list(payload.get("mots_cles_manquants", [])),
            "reformulations": list(payload.get("reformulations", [])),
        }
    except Exception as exc:
        logger.error("coach_analyse parse error: %s", exc)
        return None


def interview_message(historique: list[dict[str, str]], offre: Any, profil: Any, api_key: str) -> str | None:
    hist = historique[-12:]
    content = [
        {
            "role": "user",
            "content": (
                "Tu joues le role d'un recruteur pour un entretien de stage. "
                f"Contexte offre: {getattr(offre, 'titre', '')} chez {getattr(offre, 'entreprise', '')}. "
                f"Contexte candidat: {getattr(profil, 'titre', '')}, competences={', '.join(getattr(profil, 'competences_list', []) or [])}."
            ),
        }
    ]
    for msg in hist:
        role = str(msg.get("role", "user"))
        txt = str(msg.get("content", ""))
        if txt:
            content.append({"role": role if role in {"user", "assistant"} else "user", "content": txt})

    key = (api_key or "").strip()
    if not key:
        return None
    try:
        client = Anthropic(api_key=key)
        resp = client.messages.create(model=CLAUDE_MODEL, max_tokens=350, temperature=0.4, messages=content)
        return _extract_text(resp)
    except Exception as exc:
        logger.error("interview_message error: %s", exc)
        return None


# Backward-compatible wrappers used by legacy UI

def generate_lettre_motivation(profil: Any, offre: Any, variante: int = 1) -> str | None:
    angle = {1: "TECHNIQUE", 2: "HUMAIN", 3: "PROJET"}.get(variante, "TECHNIQUE")
    from services.auth_service import get_runtime_claude_key

    api_key = get_runtime_claude_key()
    return generate_letter_variant(offre, profil, api_key, angle)


def coach_candidature(profil: Any, offre: Any) -> dict[str, Any] | None:
    from services.auth_service import get_runtime_claude_key

    api_key = get_runtime_claude_key()
    return coach_analyse(offre, profil, api_key)


def simulate_entretien(profil: Any, offre: Any, historique: list[dict], message_user: str) -> str | None:
    history = list(historique) + [{"role": "user", "content": message_user}]
    from services.auth_service import get_runtime_claude_key

    api_key = get_runtime_claude_key()
    return interview_message(history, offre, profil, api_key)
