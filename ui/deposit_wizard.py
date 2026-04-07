"""Fluent assisted deposit wizard (3-step consent flow)."""
from __future__ import annotations

import webbrowser
from datetime import datetime

import pyperclip
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from qfluentwidgets import BodyLabel, InfoBar, InfoBarPosition, PrimaryPushButton, PushButton, TitleLabel

from ui.lottie_widget import LottieWidget


class DepositWizard(QWidget):
    def __init__(self, candidature, profil, lettre_text: str, parent=None):
        super().__init__(parent)
        self.candidature = candidature
        self.profil = profil
        self.lettre_text = lettre_text

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(10)

        root.addWidget(TitleLabel("Dépôt assisté"))

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_step_open_form())
        self.stack.addWidget(self._build_step_copy())
        self.stack.addWidget(self._build_step_confirm())
        root.addWidget(self.stack, 1)

    def _build_step_open_form(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(BodyLabel("Étape 1 — Ouvrir le formulaire de candidature"))
        btn = PrimaryPushButton("Ouvrir le formulaire de candidature")
        btn.clicked.connect(self._open_form)
        l.addWidget(btn)
        l.addWidget(BodyLabel("Le formulaire s'ouvre dans votre navigateur. Puis passez à l'étape suivante."))
        next_btn = PushButton("Étape suivante")
        next_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        l.addWidget(next_btn)
        l.addStretch(1)
        return w

    def _build_step_copy(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(BodyLabel("Étape 2 — Copier les données"))
        copy_identity = PushButton("Copier mon nom + email")
        copy_identity.clicked.connect(self._copy_identity)
        copy_letter = PushButton("Copier ma lettre de motivation")
        copy_letter.clicked.connect(self._copy_letter)
        l.addWidget(copy_identity)
        l.addWidget(copy_letter)
        l.addWidget(BodyLabel("Collez dans le formulaire avec Ctrl+V."))
        next_btn = PushButton("Étape suivante")
        next_btn.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        l.addWidget(next_btn)
        l.addStretch(1)
        return w

    def _build_step_confirm(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(BodyLabel("Étape 3 — Avez-vous bien soumis votre candidature ?"))

        yes_btn = PrimaryPushButton("✅ Oui, j'ai soumis ma candidature")
        yes_btn.clicked.connect(self._confirm_deposit)
        cancel_btn = PushButton("Non, annuler")
        cancel_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))

        self.confetti = LottieWidget("assets/lottie/confetti.json", loop=False)
        self.confetti.setFixedSize(220, 220)
        self.confetti.hide()

        l.addWidget(yes_btn)
        l.addWidget(cancel_btn)
        l.addWidget(self.confetti, alignment=Qt.AlignmentFlag.AlignCenter)
        l.addStretch(1)
        return w

    def _open_form(self) -> None:
        url = getattr(getattr(self.candidature, "offre", None), "url", "")
        if url:
            webbrowser.open(url)

    def _copy_identity(self) -> None:
        user = getattr(self.profil, "user", None)
        if user is None:
            return
        pyperclip.copy(f"{user.prenom} {user.nom}\n{user.email}")

    def _copy_letter(self) -> None:
        pyperclip.copy(self.lettre_text or "")

    def _confirm_deposit(self) -> None:
        from database.db_manager import get_session
        from database.models import Candidature, StatutCandidature

        with get_session() as db:
            current = db.get(Candidature, int(getattr(self.candidature, "id", 0) or 0))
            if current is None:
                return
            current.statut = StatutCandidature.deposee
            current.deposee_at = datetime.utcnow()

        self.confetti.show()
        InfoBar.success(
            title="Candidature enregistrée",
            content="Le dépôt manuel a été confirmé.",
            parent=self,
            position=InfoBarPosition.TOP_RIGHT,
        )
        QTimer.singleShot(3000, self.close)
