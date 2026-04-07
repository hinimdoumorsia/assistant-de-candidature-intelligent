"""Fluent offer notification popup using Flyout/FlyoutView."""
from __future__ import annotations

from datetime import datetime, timedelta

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from qfluentwidgets import (
    Action,
    BodyLabel,
    Flyout,
    FlyoutAnimationType,
    FlyoutView,
    InfoBar,
    InfoBarPosition,
    PillPushButton,
    PrimaryPushButton,
    PushButton,
    RoundMenu,
    SubtitleLabel,
    TitleLabel,
)

from ui.lottie_widget import LottieWidget


class _ConfettiOverlay(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setGeometry(parent.rect())
        self.lottie = LottieWidget("assets/lottie/confetti.json", loop=False, parent=self)
        self.lottie.setGeometry(self.rect())


class OfferFlyoutView(FlyoutView):
    """Composable Fluent view for offer actions and score context."""

    def __init__(self, title: str, entreprise: str, ville: str, score: str, tags_ok: list[str], tags_missing: list[str], parent=None):
        super().__init__(title="Nouvelle offre", content="", parent=parent)

        root = QVBoxLayout()
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        root.addWidget(TitleLabel(title))
        root.addWidget(SubtitleLabel(f"{entreprise} | {ville}"))
        root.addWidget(BodyLabel(f"Score : {score}/100"))

        tags_row = QHBoxLayout()
        for tag in tags_ok[:4]:
            chip = PillPushButton(tag)
            chip.setStyleSheet("background:#16a34a;color:white;")
            tags_row.addWidget(chip)
        for tag in tags_missing[:4]:
            chip = PillPushButton(tag)
            chip.setStyleSheet("background:#f59e0b;color:#1f2937;")
            tags_row.addWidget(chip)
        tags_row.addStretch(1)
        root.addLayout(tags_row)

        action_row = QHBoxLayout()
        self.postuler_btn = PrimaryPushButton("Postuler")
        self.snooze_btn = PushButton("Snooze")
        self.ignore_btn = PushButton("Ignorer")
        self.coach_btn = PushButton("💡 Voir analyse coach IA")
        action_row.addWidget(self.postuler_btn)
        action_row.addWidget(self.snooze_btn)
        action_row.addWidget(self.ignore_btn)
        action_row.addWidget(self.coach_btn)
        root.addLayout(action_row)
        self.setLayout(root)


class OfferDetailDialog:
    """Backward-compatible wrapper that now renders a Fluent flyout instead of QDialog."""

    def __init__(self, offer_title: str, parent=None, offre=None):
        self.offer_title = offer_title
        self.parent = parent
        self.offre = offre

    def exec(self) -> int:
        show_offer_flyout(self.parent, self.offre or self.offer_title)
        return 1


def _show_confetti(parent: QWidget | None) -> None:
    if parent is None:
        return
    overlay = _ConfettiOverlay(parent)
    overlay.show()
    QTimer.singleShot(3000, overlay.deleteLater)


def show_offer_flyout(parent: QWidget | None, offre) -> None:
    """Shows Fluent offer details/actions with optional confetti on first deposit."""
    if parent is None:
        return
    title = getattr(offre, "titre", str(offre))
    entreprise = getattr(offre, "entreprise", "Entreprise")
    ville = getattr(offre, "localisation", "Ville")
    score_num = getattr(offre, "score_claude", None)
    if score_num is None:
        score_num = int(float(getattr(offre, "score_tfidf", 0.0)) * 100)

    view = OfferFlyoutView(
        title=title,
        entreprise=entreprise,
        ville=ville,
        score=str(int(score_num or 0)),
        tags_ok=["Python", "SQL", "Communication"],
        tags_missing=["Docker", "CI/CD"],
    )

    def _postuler() -> None:
        _show_confetti(parent)
        InfoBar.success(
            title="Candidature",
            content="Action Postuler lancee. Finalisez le depot manuellement.",
            parent=parent,
            position=InfoBarPosition.TOP_RIGHT,
        )

    def _mark_ignored() -> None:
        try:
            from database.db_manager import get_session
            from database.models import Offre, StatutOffre

            offer_id = getattr(offre, "id", None)
            if offer_id is not None:
                with get_session() as db:
                    found = db.get(Offre, int(offer_id))
                    if found is not None:
                        found.statut = StatutOffre.traitee
        except Exception:
            pass
        _simple_action("Ignorer")

    def _snooze_for(days: int) -> None:
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from database.db_manager import get_session
            from database.models import Snooze
            from services.auth_service import get_current_user
            from services.notification_service import trigger

            offer_id = getattr(offre, "id", None)
            user = get_current_user()
            if offer_id is not None and user is not None:
                with get_session() as db:
                    run_at = datetime.utcnow() + timedelta(days=days)
                    snooze = Snooze(
                        offre_id=int(offer_id),
                        user_id=int(getattr(user, "id", 0) or 0),
                        snooze_until=run_at,
                    )
                    db.add(snooze)

                sched = BackgroundScheduler()
                sched.start()
                sched.add_job(lambda: trigger(int(offer_id)), "date", run_date=run_at)
        except Exception:
            pass
        _simple_action(f"Snooze {days}j")

    def _open_coach_analysis() -> None:
        try:
            from services.auth_service import get_current_user, get_runtime_claude_key
            from services.generator_service import coach_analyse
            from services.profile_service import get_profils

            user = get_current_user()
            profils = get_profils()
            if user is None or not profils:
                return
            payload = coach_analyse(offre, profils[0], get_runtime_claude_key()) or {}

            lines = []
            forts = payload.get("points_forts", [])
            miss = payload.get("mots_cles_manquants", [])
            reform = payload.get("reformulations", [])
            if forts:
                lines.append("Points forts: " + ", ".join(forts[:5]))
            if miss:
                lines.append("Mots-clés manquants: " + ", ".join(miss[:5]))
            if reform:
                lines.append("Reformulations: " + " | ".join(reform[:3]))
            detail = "\n".join(lines) if lines else "Analyse indisponible"

            coach_view = FlyoutView(title="Analyse coach IA", content=detail, parent=parent)
            Flyout.make(view=coach_view, target=parent, parent=parent, aniType=FlyoutAnimationType.DROP_DOWN)
        except Exception:
            pass

    def _open_snooze_menu() -> None:
        menu = RoundMenu(parent=parent)
        action_1 = Action("Snooze 1 jour", menu)
        action_3 = Action("Snooze 3 jours", menu)
        action_7 = Action("Snooze 7 jours", menu)
        action_1.triggered.connect(lambda: _snooze_for(1))
        action_3.triggered.connect(lambda: _snooze_for(3))
        action_7.triggered.connect(lambda: _snooze_for(7))
        menu.addAction(action_1)
        menu.addAction(action_3)
        menu.addAction(action_7)
        menu.exec(view.snooze_btn.mapToGlobal(view.snooze_btn.rect().bottomLeft()))

    def _simple_action(action: str) -> None:
        InfoBar.info(
            title="Action",
            content=f"{action} appliquee pour cette offre.",
            parent=parent,
            position=InfoBarPosition.TOP_RIGHT,
        )

    view.postuler_btn.clicked.connect(_postuler)
    view.snooze_btn.clicked.connect(_open_snooze_menu)
    view.ignore_btn.clicked.connect(_mark_ignored)
    view.coach_btn.clicked.connect(_open_coach_analysis)

    Flyout.make(
        view=view,
        target=parent,
        parent=parent,
        aniType=FlyoutAnimationType.DROP_DOWN,
    )
