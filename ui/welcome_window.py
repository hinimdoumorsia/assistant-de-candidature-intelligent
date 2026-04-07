"""Welcome page for StageAuto using Fluent widgets and local demo animations."""
from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QSequentialAnimationGroup, Qt, QTimer, QVariantAnimation
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QDialog, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    ElevatedCardWidget,
    FluentIcon as FIF,
    FluentWindow,
    HyperlinkButton,
    PillPushButton,
    PrimaryPushButton,
    PushButton,
    SimpleCardWidget,
    SmoothScrollArea,
    SubtitleLabel,
    TitleLabel,
    TransparentPushButton,
)


@dataclass(slots=True)
class DemoOffer:
    title: str
    company: str
    city: str
    score: int


class AnimatedNumberLabel(QLabel):
    """Label exposing an animatable integer property."""

    def __init__(self, suffix: str = "", parent=None):
        super().__init__("0", parent)
        self._value = 0
        self._suffix = suffix
        self.setStyleSheet("font-size: 26px; font-weight: 700;")

    def set_value(self, value: int) -> None:
        self._value = value
        self.setText(f"{int(value)}{self._suffix}")


class WelcomeWindow(FluentWindow):
    """Fluent landing screen with a read-only animated demo."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("StageAuto")

        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            self.setFixedSize(screen.size())

        self._offers = [
            DemoOffer("Stage Data Analyst", "Atlas Analytics", "Casablanca", 92),
            DemoOffer("Stage Backend Python", "BlueOps", "Rabat", 88),
            DemoOffer("Stage BI Reporting", "North Insights", "Marrakech", 84),
            DemoOffer("Stage QA Automation", "Delta Systems", "Tanger", 81),
            DemoOffer("Stage Product Ops", "Nova Labs", "Agadir", 79),
        ]

        self._build_ui()
        self._start_demo_animations()

    def _build_ui(self) -> None:
        content = QWidget(self)
        content.setObjectName("welcomeInterface")
        root = QVBoxLayout(content)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        top = QHBoxLayout()
        top.setSpacing(18)
        root.addLayout(top, 1)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(18, 12, 18, 12)
        left_layout.setSpacing(10)
        left_layout.addStretch(1)

        left_layout.addWidget(TitleLabel("StageAuto"))
        left_layout.addWidget(SubtitleLabel("Trouvez votre stage. Postulez automatiquement."))
        left_layout.addWidget(BodyLabel("Un assistant desktop pour détecter les offres,\nmatcher votre profil et préparer vos candidatures\navec validation humaine à chaque étape."))

        self.btn_register = PrimaryPushButton("Créer un compte")
        self.btn_register.clicked.connect(self._open_register)
        left_layout.addWidget(self.btn_register)

        self.btn_login = PushButton("Se connecter")
        self.btn_login.clicked.connect(self._open_login)
        left_layout.addWidget(self.btn_login)

        help_btn = TransparentPushButton("❓ Comment ça marche ?")
        help_btn.clicked.connect(self._show_how_dialog)
        left_layout.addWidget(help_btn)
        left_layout.addStretch(2)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setSpacing(12)

        stats_row = QHBoxLayout()
        self._counter_labels: list[AnimatedNumberLabel] = []
        stats_config = [
            ("offres détectées cette semaine", 127, ""),
            ("candidatures envoyées", 43, ""),
            ("taux de matching moyen", 89, "%"),
        ]
        self._counter_targets: list[int] = []
        for text, target, suffix in stats_config:
            card = SimpleCardWidget()
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 12, 12, 12)
            number = AnimatedNumberLabel(suffix=suffix)
            self._counter_labels.append(number)
            self._counter_targets.append(target)
            card_layout.addWidget(number)
            card_layout.addWidget(BodyLabel(text))
            stats_row.addWidget(card)
        right_layout.addLayout(stats_row)

        feed_card = ElevatedCardWidget()
        feed_layout = QVBoxLayout(feed_card)
        feed_layout.setContentsMargins(12, 12, 12, 12)
        feed_layout.setSpacing(8)
        feed_layout.addWidget(SubtitleLabel("Mini feed des offres"))

        self.feed_scroll = SmoothScrollArea()
        self.feed_scroll.setWidgetResizable(True)
        self.feed_widget = QWidget()
        self.feed_list_layout = QVBoxLayout(self.feed_widget)
        self.feed_list_layout.setSpacing(8)

        for index, offer in enumerate(self._offers):
            self.feed_list_layout.addWidget(self._build_offer_item(offer, index == 0))

        self.feed_scroll.setWidget(self.feed_widget)
        feed_layout.addWidget(self.feed_scroll)
        right_layout.addWidget(feed_card, 1)

        sources_row = QHBoxLayout()
        self._source_pills: list[PillPushButton] = []
        for source in ["Indeed", "Rekrute", "Emploi.ma", "Bayt", "Adzuna"]:
            pill = PillPushButton(source)
            self._source_pills.append(pill)
            sources_row.addWidget(pill)
        sources_row.addStretch(1)
        right_layout.addLayout(sources_row)

        top.addWidget(left, 4)
        top.addWidget(right, 6)

        footer = CardWidget()
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(14, 10, 14, 10)
        footer_layout.addWidget(BodyLabel("Ces clés sont gratuites. Elles seront demandées à l'inscription."))
        footer_layout.addStretch(1)
        footer_layout.addWidget(HyperlinkButton("https://console.anthropic.com", "Clé Anthropic Claude API"))
        footer_layout.addWidget(HyperlinkButton("https://developer.adzuna.com/signup", "Clé Adzuna API"))
        root.addWidget(footer)

        self.addSubInterface(content, FIF.HOME, "Accueil")

    def _build_offer_item(self, offer: DemoOffer, with_badge: bool) -> QWidget:
        card = ElevatedCardWidget()
        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)

        info = QVBoxLayout()
        info.addWidget(BodyLabel(f"{offer.title}"))
        info.addWidget(BodyLabel(f"{offer.company} · {offer.city}"))
        layout.addLayout(info, 1)

        score_badge = PillPushButton(f"{offer.score}/100")
        layout.addWidget(score_badge)

        if with_badge:
            self._new_badge = PillPushButton("Nouvelle")
            self._new_badge.setStyleSheet("background-color:#b91c1c;color:white;")
            layout.addWidget(self._new_badge)

        return card

    def _start_demo_animations(self) -> None:
        for index, label in enumerate(self._counter_labels):
            anim = QVariantAnimation(self)
            anim.setDuration(1500)
            anim.setStartValue(0)
            anim.setEndValue(self._counter_targets[index])
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            anim.valueChanged.connect(lambda value, lbl=label: lbl.set_value(int(value)))
            anim.start()

        self._feed_timer = QTimer(self)
        self._feed_timer.timeout.connect(self._auto_scroll_feed)
        self._feed_timer.start(3000)

        for index, pill in enumerate(self._source_pills):
            effect = QGraphicsOpacityEffect(pill)
            pill.setGraphicsEffect(effect)
            group = QSequentialAnimationGroup(self)
            fade_out = QPropertyAnimation(effect, b"opacity", self)
            fade_out.setDuration(450)
            fade_out.setStartValue(1.0)
            fade_out.setEndValue(0.3)
            fade_in = QPropertyAnimation(effect, b"opacity", self)
            fade_in.setDuration(450)
            fade_in.setStartValue(0.3)
            fade_in.setEndValue(1.0)
            group.addAnimation(fade_out)
            group.addAnimation(fade_in)
            group.setLoopCount(-1)
            QTimer.singleShot(index * 200, group.start)

        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(lambda: self._new_badge.setVisible(not self._new_badge.isVisible()))
        self._blink_timer.start(800)

    def _auto_scroll_feed(self) -> None:
        bar = self.feed_scroll.verticalScrollBar()
        if bar is None:
            return
        if bar.maximum() == 0:
            return
        step = max(36, bar.pageStep() // 3)
        nxt = bar.value() + step
        if nxt >= bar.maximum():
            bar.setValue(0)
        else:
            bar.setValue(nxt)

    def _open_register(self) -> None:
        from ui.register_wizard import RegisterWizard

        wizard = RegisterWizard(self)
        wizard.exec()

    def _open_login(self) -> None:
        from ui.login_window import LoginWindow

        self._login_window = LoginWindow(on_login_success=lambda: None)
        self._login_window.show()

    def _show_how_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Comment ça marche ?")
        dialog.setMinimumWidth(560)
        layout = QVBoxLayout(dialog)
        layout.addWidget(TitleLabel("Flux StageAuto"))
        layout.addWidget(BodyLabel("1) Détection multi-sources des offres."))
        layout.addWidget(BodyLabel("2) Pré-filtrage TF-IDF hors ligne puis scoring IA."))
        layout.addWidget(BodyLabel("3) Préparation assistée des candidatures avec validation humaine."))
        dialog.exec()
