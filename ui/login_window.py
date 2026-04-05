"""
ui/login_window.py - Fenêtre de connexion / inscription
Aucune logique métier ici — appels services uniquement.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QStackedWidget, QMessageBox, QApplication, QScrollArea
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QIcon, QPixmap
from config import COLORS, APP_NAME, APP_VERSION


class LoginWindow(QWidget):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle(f"{APP_NAME} — Connexion")
        self.setFixedSize(900, 700)
        self.setObjectName("loginWindow")

        # Layout principal : gauche (visuel) + droite (formulaire)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Panel gauche (branding) ──────────────────────────────────────
        left = QFrame()
        left.setFixedWidth(380)
        left.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['sidebar']},
                    stop:0.6 {COLORS['primary_dark']},
                    stop:1 {COLORS['primary']});
            }}
        """)
        left_layout = QVBoxLayout(left)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.setContentsMargins(40, 60, 40, 60)

        # Logo emoji + titre
        logo_lbl = QLabel("🎯")
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_lbl.setStyleSheet("font-size: 64px; background: transparent;")

        app_name = QLabel(APP_NAME)
        app_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_name.setStyleSheet("color: white; font-size: 28px; font-weight: 700; background: transparent;")

        tagline = QLabel("Votre candidature automatisée\nen stage, sans effort.")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline.setWordWrap(True)
        tagline.setStyleSheet("color: rgba(255,255,255,0.85); font-size: 14px; background: transparent; line-height: 1.6;")

        version_lbl = QLabel(f"v{APP_VERSION}")
        version_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_lbl.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 11px; background: transparent;")

        # Features
        features_frame = QFrame()
        features_frame.setStyleSheet("background: rgba(255,255,255,0.12); border-radius: 12px;")
        feat_layout = QVBoxLayout(features_frame)
        feat_layout.setContentsMargins(16, 12, 16, 12)
        feat_layout.setSpacing(8)
        for icon, text in [("🔍", "6 sources gratuites"), ("🤖", "IA Claude intégrée"),
                            ("📝", "LM multi-variante"), ("🎤", "Coach entretien")]:
            row = QHBoxLayout()
            il = QLabel(icon)
            il.setStyleSheet("font-size: 16px; background: transparent;")
            tl = QLabel(text)
            tl.setStyleSheet("color: rgba(255,255,255,0.9); font-size: 13px; background: transparent;")
            row.addWidget(il)
            row.addWidget(tl)
            row.addStretch()
            feat_layout.addLayout(row)

        left_layout.addWidget(logo_lbl)
        left_layout.addSpacing(12)
        left_layout.addWidget(app_name)
        left_layout.addSpacing(8)
        left_layout.addWidget(tagline)
        left_layout.addSpacing(24)
        left_layout.addWidget(features_frame)
        left_layout.addStretch()
        left_layout.addWidget(version_lbl)

        # ── Panel droit (formulaires) ───────────────────────────────────
        right = QFrame()
        right.setStyleSheet(f"background: {COLORS['bg']};")
        right_layout = QVBoxLayout(right)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.setContentsMargins(48, 40, 48, 40)

        # Stacked : page login / page register
        self.stack = QStackedWidget()

        # Page Connexion
        login_page = self._build_login_page()
        # Page Inscription
        register_page = self._build_register_page()

        self.stack.addWidget(login_page)   # index 0
        self.stack.addWidget(register_page)  # index 1

        right_layout.addWidget(self.stack)

        main_layout.addWidget(left)
        main_layout.addWidget(right)

    def _field(self, placeholder: str, echo: bool = False) -> QLineEdit:
        f = QLineEdit()
        f.setPlaceholderText(placeholder)
        if echo:
            f.setEchoMode(QLineEdit.EchoMode.Password)
        f.setMinimumHeight(44)
        return f

    def _label(self, text: str, big=False, color=None) -> QLabel:
        lbl = QLabel(text)
        size = "22px" if big else "13px"
        weight = "700" if big else "400"
        c = color or COLORS["text"]
        lbl.setStyleSheet(f"font-size: {size}; font-weight: {weight}; color: {c};")
        return lbl

    def _build_login_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 20, 0, 20)

        layout.addWidget(self._label("Connexion", big=True, color=COLORS["primary_dark"]))
        layout.addWidget(self._label("Entrez vos identifiants pour continuer.", color=COLORS["text_light"]))
        layout.addSpacing(12)

        layout.addWidget(self._label("Email"))
        self.login_email = self._field("vous@exemple.com")
        layout.addWidget(self.login_email)

        layout.addWidget(self._label("Mot de passe"))
        self.login_pwd = self._field("••••••••", echo=True)
        layout.addWidget(self.login_pwd)

        # Message erreur
        self.login_error = QLabel("")
        self.login_error.setStyleSheet(f"color: {COLORS['danger']}; font-size: 12px;")
        layout.addWidget(self.login_error)

        btn_login = QPushButton("Se connecter →")
        btn_login.setMinimumHeight(46)
        btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_login.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 8px;
                padding: 10px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dark']};
            }}
        """)
        btn_login.clicked.connect(self._do_login)
        self.login_pwd.returnPressed.connect(self._do_login)
        layout.addWidget(btn_login)

        layout.addSpacing(12)
        sep = QLabel("— Pas encore de compte ? —")
        sep.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sep.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 12px;")
        layout.addWidget(sep)

        btn_register = QPushButton("Créer un compte")
        btn_register.setProperty("class", "secondary")
        btn_register.setMinimumHeight(42)
        btn_register.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_register.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666666;
                font-weight: normal;
                border: 1px solid #cccccc;
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                color: #333333;
            }
        """)
        btn_register.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        layout.addWidget(btn_register)

        layout.addStretch()
        return page

    def _build_register_page(self) -> QWidget:
        # Utilisation d'un scroll area pour que tout soit visible
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 20, 0, 20)

        layout.addWidget(self._label("Créer un compte", big=True, color=COLORS["primary_dark"]))
        layout.addWidget(self._label("Rejoignez SCA Desktop gratuitement.", color=COLORS["text_light"]))
        layout.addSpacing(8)

        row = QHBoxLayout()
        self.reg_prenom = self._field("Prénom")
        self.reg_nom = self._field("Nom")
        row.addWidget(self.reg_prenom)
        row.addWidget(self.reg_nom)
        layout.addLayout(row)

        layout.addWidget(self._label("Email"))
        self.reg_email = self._field("vous@exemple.com")
        layout.addWidget(self.reg_email)

        layout.addWidget(self._label("Mot de passe (min. 8 caractères)"))
        self.reg_pwd = self._field("••••••••", echo=True)
        layout.addWidget(self.reg_pwd)

        layout.addWidget(self._label("Confirmer le mot de passe"))
        self.reg_pwd2 = self._field("••••••••", echo=True)
        layout.addWidget(self.reg_pwd2)

        self.reg_error = QLabel("")
        self.reg_error.setStyleSheet(f"color: {COLORS['danger']}; font-size: 12px;")
        self.reg_error.setWordWrap(True)
        layout.addWidget(self.reg_error)

        # Bouton "Créer mon compte"
        btn_reg = QPushButton("Créer mon compte →")
        btn_reg.setMinimumHeight(46)
        btn_reg.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reg.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 8px;
                padding: 10px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dark']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['sidebar']};
            }}
        """)
        btn_reg.clicked.connect(self._do_register)
        layout.addWidget(btn_reg)

        # Bouton retour
        btn_back = QPushButton("← Retour à la connexion")
        btn_back.setProperty("class", "secondary")
        btn_back.setMinimumHeight(42)
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_back.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666666;
                font-weight: normal;
                border: 1px solid #cccccc;
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                color: #333333;
            }
        """)
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        layout.addWidget(btn_back)

        layout.addStretch()
        
        scroll.setWidget(content)
        return scroll

    # ── Actions ────────────────────────────────────────────────────────────────

    def _do_login(self):
        from services.auth_service import login
        email = self.login_email.text().strip()
        pwd   = self.login_pwd.text()
        ok, msg = login(email, pwd)
        if ok:
            self.login_error.setText("")
            self.on_login_success()
        else:
            self.login_error.setText(f"⚠ {msg}")
            self.login_pwd.clear()

    def _do_register(self):
        from services.auth_service import register
        prenom = self.reg_prenom.text().strip()
        nom    = self.reg_nom.text().strip()
        email  = self.reg_email.text().strip()
        pwd    = self.reg_pwd.text()
        pwd2   = self.reg_pwd2.text()

        if pwd != pwd2:
            self.reg_error.setText("⚠ Les mots de passe ne correspondent pas.")
            return

        ok, msg = register(nom, prenom, email, pwd)
        if ok:
            self.reg_error.setText("")
            QMessageBox.information(self, "Compte créé", msg + "\nVous pouvez maintenant vous connecter.")
            self.reg_email.setText(email)
            self.stack.setCurrentIndex(0)
            self.login_email.setText(email)
        else:
            self.reg_error.setText(f"⚠ {msg}")