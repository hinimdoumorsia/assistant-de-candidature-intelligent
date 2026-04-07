"""Fluent login page with centered card and in-memory session flow."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    FluentIcon as FIF,
    FluentWindow,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    PasswordLineEdit,
    PrimaryPushButton,
    PushButton,
    SubtitleLabel,
    TitleLabel,
)

from config import APP_NAME


class LoginWindow(FluentWindow):
    """Authentication screen using Fluent components only."""

    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self.setWindowTitle(f"{APP_NAME} - Connexion")
        self.resize(940, 640)
        self._build_ui()

    def _build_ui(self) -> None:
        content = QWidget(self)
        content.setObjectName("loginInterface")
        root = QVBoxLayout(content)
        root.setContentsMargins(20, 20, 20, 20)

        row = QHBoxLayout()
        row.addStretch(1)

        card = CardWidget()
        card.setMaximumWidth(520)
        form = QVBoxLayout(card)
        form.setContentsMargins(24, 20, 24, 20)
        form.setSpacing(10)

        form.addWidget(TitleLabel("Connexion"))
        form.addWidget(SubtitleLabel("Accédez à votre tableau de bord StageAuto"))

        form.addWidget(BodyLabel("Email"))
        self.email_input = LineEdit()
        self.email_input.setPlaceholderText("vous@exemple.com")
        form.addWidget(self.email_input)

        form.addWidget(BodyLabel("Mot de passe"))
        self.password_input = PasswordLineEdit()
        self.password_input.setPlaceholderText("Votre mot de passe")
        self.password_input.returnPressed.connect(self._do_login)
        form.addWidget(self.password_input)

        login_btn = PrimaryPushButton("Se connecter")
        login_btn.clicked.connect(self._do_login)
        form.addWidget(login_btn)

        create_account = PushButton("Créer un compte")
        create_account.clicked.connect(self._open_register)
        form.addWidget(create_account, alignment=Qt.AlignmentFlag.AlignRight)

        row.addWidget(card)
        row.addStretch(1)
        root.addLayout(row, 1)

        self.addSubInterface(content, FIF.PEOPLE, "Connexion")

    def _do_login(self) -> None:
        from services.auth_service import login

        user = login(self.email_input.text().strip(), self.password_input.text())
        if user is None:
            InfoBar.error(
                title="Identifiants incorrects",
                content="Email ou mot de passe incorrect.",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
            )
            self.password_input.clear()
            return

        InfoBar.success(
            title="Connexion",
            content=f"Bienvenue {getattr(user, 'prenom', '')}.",
            parent=self,
            position=InfoBarPosition.TOP_RIGHT,
        )
        self.on_login_success()

    def _open_register(self) -> None:
        from ui.register_wizard import RegisterWizard

        wizard = RegisterWizard(self)
        if wizard.exec() == wizard.DialogCode.Accepted:
            email = wizard.registration_data.get("email", "")
            if email:
                self.email_input.setText(email)
