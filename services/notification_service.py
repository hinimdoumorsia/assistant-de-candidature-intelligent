"""Notification-domain service helpers (no Qt imports)."""
from __future__ import annotations

from dataclasses import dataclass


_trigger_callback = None


@dataclass(slots=True)
class OfferNotificationPayload:
    """Normalized payload used by UI flyouts and notification workers."""

    title: str
    entreprise: str
    localisation: str
    score_tfidf: float
    score_claude: float | None


def build_offer_payload(offre) -> OfferNotificationPayload:
    """Builds a serializable payload from an ORM offer entity."""
    return OfferNotificationPayload(
        title=str(getattr(offre, "titre", "Offre")),
        entreprise=str(getattr(offre, "entreprise", "")),
        localisation=str(getattr(offre, "localisation", "")),
        score_tfidf=float(getattr(offre, "score_tfidf", 0.0) or 0.0),
        score_claude=(
            float(getattr(offre, "score_claude", 0.0))
            if getattr(offre, "score_claude", None) is not None
            else None
        ),
    )


def register_trigger_callback(callback) -> None:
    """Registers an in-process callback used by UI layer to receive notifications."""
    global _trigger_callback
    _trigger_callback = callback


def trigger(offre_id: int) -> None:
    """Triggers a notification event for a specific offer id."""
    if callable(_trigger_callback):
        _trigger_callback(int(offre_id))
