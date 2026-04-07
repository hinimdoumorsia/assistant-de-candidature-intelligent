"""
ui/fluent_dashboard.py - Fenetre principale Fluent avec navigation native.
"""
from __future__ import annotations

from importlib import import_module

from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QTableWidgetItem, QVBoxLayout, QWidget

from qfluentwidgets import (
    Action,
    BodyLabel,
    CardWidget,
    FluentIcon,
    FluentWindow,
    IndeterminateProgressRing,
    NavigationItemPosition,
    PrimaryPushButton,
    PushButton,
    ScrollArea,
    SearchLineEdit,
    SubtitleLabel,
    TableWidget,
    TitleLabel,
    setTheme,
    Theme,
    RoundMenu,
)

from config import APP_NAME, APP_VERSION
from services.auth_service import get_current_user, logout
from services.user_settings_service import load_user_settings
from workers.scraper_worker import start_worker, stop_worker, run_now
from ui.lottie_banner import LottieBannerWidget
from ui.lottie_widget import LottieWidget
from ui.settings_page import SettingsPageWidget


def _icon(name: str, fallback: str):
    return getattr(FluentIcon, name, fallback)


class StatCard(CardWidget):
    def __init__(self, label: str, value: str = "—", hint: str = "", parent=None):
        super().__init__(parent)
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("font-size: 30px; font-weight: 700;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

        title = SubtitleLabel()
        title.setText(label)
        title.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(self.value_label)

        if hint:
            hint_label = BodyLabel()
            hint_label.setText(hint)
            hint_label.setWordWrap(True)
            hint_label.setStyleSheet("color: #6b7280;")
            layout.addWidget(hint_label)

    def set_value(self, value: str):
        self.value_label.setText(value)

    def animate_to(self, new_value: int) -> None:
        self.value_label.setText(str(new_value))


class HomePageWidget(QWidget):
    openSettingsRequested = pyqtSignal()
    runScanRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.user = get_current_user()

        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        hero = CardWidget()
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(18, 18, 18, 18)
        hero_layout.setSpacing(18)

        self.banner = LottieBannerWidget(
            "welcome",
            "StageAuto",
            "Veille d'offres, matching et candidatures automatisees.",
        )
        hero_layout.addWidget(self.banner, 1)

        side = QVBoxLayout()
        side.setSpacing(8)
        title = TitleLabel()
        title.setText("Tableau de bord")
        subtitle = BodyLabel()
        subtitle.setText("Navigation Fluent, cartes natives et réglages en temps réel.")
        subtitle.setWordWrap(True)
        side.addWidget(title)
        side.addWidget(subtitle)
        side.addSpacing(10)

        self.user_label = SubtitleLabel()
        self.user_label.setText("Utilisateur")
        side.addWidget(self.user_label)

        self.cta_scan = PrimaryPushButton()
        self.cta_scan.setText("Scanner maintenant")
        self.cta_scan.clicked.connect(self.runScanRequested.emit)
        side.addWidget(self.cta_scan)

        self.cta_settings = PushButton()
        self.cta_settings.setText("Ouvrir les parametres")
        self.cta_settings.clicked.connect(self.openSettingsRequested.emit)
        side.addWidget(self.cta_settings)
        side.addStretch()

        hero_layout.addLayout(side, 1)
        root.addWidget(hero)

        status_row = QHBoxLayout()
        self.scraper_ring = IndeterminateProgressRing()
        self.scraper_ring.setFixedSize(28, 28)
        self.radar = LottieWidget("assets/lottie/radar_scan.json")
        self.radar.setFixedSize(42, 42)
        self.scraper_label = BodyLabel("Scraper actif")
        status_row.addStretch(1)
        status_row.addWidget(self.scraper_ring)
        status_row.addWidget(self.radar)
        status_row.addWidget(self.scraper_label)
        root.addLayout(status_row)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        self.stat_deposees = StatCard("Candidatures deposees", "0", "Statut finalise")
        self.stat_attente = StatCard("En attente", "0", "A traiter")
        self.stat_offres = StatCard("Offres detectees", "0", "Dernieres 24h")
        self.stat_score = StatCard("Score moyen", "—", "TF-IDF / IA")
        for card in [self.stat_deposees, self.stat_attente, self.stat_offres, self.stat_score]:
            stats_row.addWidget(card)
        root.addLayout(stats_row)

        recent = CardWidget()
        recent_layout = QVBoxLayout(recent)
        recent_layout.setContentsMargins(18, 18, 18, 18)
        recent_layout.setSpacing(10)

        title = SubtitleLabel()
        title.setText("Dernieres offres")
        recent_layout.addWidget(title)

        self.recent_table = TableWidget(0, 4)
        self.recent_table.setHorizontalHeaderLabels(["Entreprise", "Poste", "Source", "Score"])
        self.recent_table.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.recent_table.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        vertical_header = self.recent_table.verticalHeader()
        assert vertical_header is not None
        vertical_header.setVisible(False)
        self.recent_table.setShowGrid(False)
        self.empty_state = QWidget()
        empty_layout = QVBoxLayout(self.empty_state)
        empty_layout.setContentsMargins(0, 0, 0, 0)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_lottie = LottieWidget("assets/lottie/empty_state.json")
        self.empty_lottie.setFixedSize(200, 200)
        empty_layout.addWidget(self.empty_lottie)
        empty_layout.addWidget(BodyLabel("Aucune offre pour l'instant"))

        recent_layout.addWidget(self.recent_table)
        recent_layout.addWidget(self.empty_state)
        root.addWidget(recent, 1)

    def refresh_data(self):
        self.user = get_current_user()
        if self.user:
            self.user_label.setText(f"Connecté: {self.user.prenom} {self.user.nom}")
        else:
            self.user_label.setText("Utilisateur")

        try:
            from database.db_manager import get_session
            from database.models import Candidature, Offre, StatutCandidature
            from sqlalchemy import func
            from datetime import date

            with get_session() as db:
                deposees = db.query(Candidature).filter_by(statut=StatutCandidature.deposee).count()
                attente = db.query(Candidature).filter_by(statut=StatutCandidature.en_attente).count()
                offres_today = db.query(Offre).filter(func.date(Offre.date_detection) == date.today()).count()
                avg_score = db.query(func.avg(Offre.score_claude)).scalar()
                avg_tfidf = db.query(func.avg(Offre.score_tfidf)).scalar()

                self.stat_deposees.animate_to(int(deposees))
                self.stat_attente.animate_to(int(attente))
                self.stat_offres.animate_to(int(offres_today))
                if avg_score is not None:
                    self.stat_score.set_value(f"{avg_score:.0f}%")
                elif avg_tfidf is not None:
                    self.stat_score.set_value(f"{avg_tfidf * 100:.0f}%")
                else:
                    self.stat_score.set_value("—")

                offers = db.query(Offre).order_by(Offre.date_detection.desc()).limit(8).all()
                has_offers = bool(offers)
                self.recent_table.setVisible(has_offers)
                self.empty_state.setVisible(not has_offers)
                self.recent_table.setRowCount(len(offers))
                for row, offer in enumerate(offers):
                    self.recent_table.setItem(row, 0, QTableWidgetItem(offer.entreprise or "—"))
                    self.recent_table.setItem(row, 1, QTableWidgetItem(offer.titre[:60]))
                    self.recent_table.setItem(row, 2, QTableWidgetItem(offer.source))
                    score = offer.score_claude if offer.score_claude is not None else (offer.score_tfidf * 100)
                    self.recent_table.setItem(row, 3, QTableWidgetItem(f"{score:.0f}%"))
        except Exception:
            self.recent_table.setRowCount(0)
            self.recent_table.setVisible(False)
            self.empty_state.setVisible(True)


class OffersPageWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(10)

        root.addWidget(TitleLabel("Offres"))
        self.search = SearchLineEdit()
        self.search.setPlaceholderText("Filtrer en temps réel (titre, entreprise, ville, source)")
        self.search.textChanged.connect(self.refresh)
        root.addWidget(self.search)

        self.table = TableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Source", "Titre", "Entreprise", "Ville", "Score TF-IDF", "Score Claude", "Statut"]
        )
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._open_row_menu)
        self.table.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        vh = self.table.verticalHeader()
        assert vh is not None
        vh.setVisible(False)

        self.empty = QWidget()
        empty_l = QVBoxLayout(self.empty)
        empty_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_lottie = LottieWidget("assets/lottie/empty_state.json")
        self.empty_lottie.setFixedSize(200, 200)
        empty_l.addWidget(self.empty_lottie)
        empty_l.addWidget(BodyLabel("Aucune offre détectée pour l'instant..."))

        root.addWidget(self.table, 1)
        root.addWidget(self.empty)
        self.refresh()

    def refresh(self):
        try:
            from database.db_manager import get_session
            from database.models import Offre

            term = self.search.text().strip().lower()
            with get_session() as db:
                offers = db.query(Offre).order_by(Offre.date_detection.desc()).limit(300).all()

            rows = []
            for o in offers:
                hay = f"{o.source} {o.titre} {o.entreprise} {o.localisation}".lower()
                if term and term not in hay:
                    continue
                rows.append(o)

            self.table.setRowCount(len(rows))
            self.table.setVisible(bool(rows))
            self.empty.setVisible(not rows)
            for idx, o in enumerate(rows):
                self.table.setItem(idx, 0, QTableWidgetItem(o.source))
                self.table.setItem(idx, 1, QTableWidgetItem(o.titre))
                self.table.setItem(idx, 2, QTableWidgetItem(o.entreprise or ""))
                self.table.setItem(idx, 3, QTableWidgetItem(o.localisation or ""))
                self.table.setItem(idx, 4, QTableWidgetItem(f"{(o.score_tfidf or 0.0)*100:.0f}%"))
                self.table.setItem(idx, 5, QTableWidgetItem("—" if o.score_claude is None else f"{o.score_claude:.0f}"))
                self.table.setItem(idx, 6, QTableWidgetItem(getattr(o.statut, "value", str(o.statut))))
                self.table.item(idx, 0).setData(Qt.ItemDataRole.UserRole, int(o.id))
        except Exception:
            self.table.setRowCount(0)
            self.table.setVisible(False)
            self.empty.setVisible(True)

    def _open_row_menu(self, pos):
        row = self.table.currentRow()
        if row < 0:
            return
        item = self.table.item(row, 0)
        if item is None:
            return
        offer_id = item.data(Qt.ItemDataRole.UserRole)
        if offer_id is None:
            return

        menu = RoundMenu(parent=self)
        postuler = Action("Postuler", menu)
        snooze_1 = Action("Snooze 1j", menu)
        snooze_3 = Action("Snooze 3j", menu)
        snooze_7 = Action("Snooze 7j", menu)
        ignorer = Action("Ignorer", menu)
        postuler.triggered.connect(lambda: self._set_offer_status(int(offer_id), "traitee"))
        snooze_1.triggered.connect(lambda: self._snooze_offer(int(offer_id), 1))
        snooze_3.triggered.connect(lambda: self._snooze_offer(int(offer_id), 3))
        snooze_7.triggered.connect(lambda: self._snooze_offer(int(offer_id), 7))
        ignorer.triggered.connect(lambda: self._set_offer_status(int(offer_id), "traitee"))
        menu.addAction(postuler)
        menu.addAction(snooze_1)
        menu.addAction(snooze_3)
        menu.addAction(snooze_7)
        menu.addAction(ignorer)
        menu.exec(self.table.mapToGlobal(pos))

    def _set_offer_status(self, offer_id: int, status: str):
        from database.db_manager import get_session
        from database.models import Offre, StatutOffre

        with get_session() as db:
            offer = db.get(Offre, offer_id)
            if offer is not None:
                offer.statut = StatutOffre(status)
        self.refresh()

    def _snooze_offer(self, offer_id: int, days: int):
        from datetime import datetime, timedelta
        from database.db_manager import get_session
        from database.models import Snooze
        from services.auth_service import get_current_user

        user = get_current_user()
        if user is None:
            return
        with get_session() as db:
            db.add(
                Snooze(
                    offre_id=offer_id,
                    user_id=int(user.id),
                    snooze_until=datetime.utcnow() + timedelta(days=days),
                )
            )


class FluentDashboardWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.user = get_current_user()
        self.is_dark_theme = True
        self._apply_saved_theme()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1360, 860)

        self._build_navigation()
        self._wire_services()
        try:
            self.navigationInterface.setExpandWidth(200)
        except Exception:
            pass

        start_worker(on_new_offers_callback=lambda _n: self.refresh_all())

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_all)
        self.refresh_timer.start(120_000)

        self.refresh_all()

    def _apply_saved_theme(self):
        try:
            settings = load_user_settings(getattr(self.user, "email", None))
            theme_mode = str(settings.get("theme_mode", "dark")).lower()
            self.is_dark_theme = theme_mode != "light"
            setTheme(Theme.DARK if self.is_dark_theme else Theme.LIGHT)
        except Exception:
            pass

    def _build_navigation(self):
        self.home_page = HomePageWidget()
        self.settings_page = SettingsPageWidget()

        self.offers_page = OffersPageWidget()
        self.history_page = self._load_legacy_widget("ui.candidature_history", "CandidatureHistoryWidget", "Historique")
        self.profile_page = self._load_legacy_widget("ui.profile_editor", "ProfileEditorWidget", "Profil")
        self.coach_page = self._load_legacy_widget("ui.interview_simulator", "InterviewSimulatorWidget", "Coach IA")

        self.addSubInterface(self.home_page, _icon("HOME", "🏠"), "Tableau de bord")
        self.addSubInterface(self.offers_page, _icon("SEARCH", "🔍"), "Offres")
        self.addSubInterface(self.history_page, _icon("DOCUMENT", "📋"), "Candidatures")
        self.addSubInterface(self.profile_page, _icon("PEOPLE", "👤"), "Profil")
        self.addSubInterface(self.coach_page, _icon("CHAT", "🤖"), "Coach IA")
        self.addSubInterface(self.settings_page, _icon("SETTING", "⚙️"), "Parametres", NavigationItemPosition.BOTTOM)

    def _load_legacy_widget(self, module_path: str, class_name: str, fallback_text: str) -> QWidget:
        try:
            module = import_module(module_path)
            widget_class = getattr(module, class_name)
            return widget_class()
        except Exception:
            widget = CardWidget()
            layout = QVBoxLayout(widget)
            layout.setContentsMargins(24, 24, 24, 24)
            label = TitleLabel()
            label.setText(fallback_text)
            body = BodyLabel()
            body.setText("Ce module n'a pas pu etre charge. Utilisez la page principale pour le reste du flux.")
            body.setWordWrap(True)
            layout.addWidget(label)
            layout.addWidget(body)
            return widget

    def _wire_services(self):
        self.home_page.openSettingsRequested.connect(lambda: self.switchTo(self.settings_page))
        self.home_page.runScanRequested.connect(self._run_scan)
        self.settings_page.restartRequested.connect(self._restart_worker)
        self.settings_page.themeToggled.connect(self._apply_theme)

    def _apply_theme(self, dark: bool):
        self.is_dark_theme = dark
        try:
            setTheme(Theme.DARK if dark else Theme.LIGHT)
        except Exception:
            pass

    def _run_scan(self):
        try:
            run_now()
        finally:
            self.refresh_all()

    def _restart_worker(self):
        try:
            stop_worker()
            start_worker()
        finally:
            self.refresh_all()

    def refresh_all(self):
        self.home_page.refresh_data()
        self.settings_page.set_user_from_session()

    def closeEvent(self, e):
        try:
            stop_worker()
        except Exception:
            pass
        e.accept()


DashboardWindow = FluentDashboardWindow
