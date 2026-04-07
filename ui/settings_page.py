"""
ui/settings_page.py - Page parametres Fluent avec sauvegarde en temps reel.
"""
from __future__ import annotations

from typing import Callable

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    ComboBox,
    PrimaryPushButton,
    Slider,
    SubtitleLabel,
    SwitchButton,
    TitleLabel,
)

from config import COLORS
from services.auth_service import get_current_user
from services.user_settings_service import load_user_settings, save_user_settings


class SettingsPageWidget(QWidget):
    restartRequested = pyqtSignal()
    themeToggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_email: str | None = None
        self._loading = False
        self._last_interval = 30
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(250)
        self._save_timer.timeout.connect(self._persist)

        self._build_ui()
        self.set_user_from_session()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        header = CardWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(20, 18, 20, 18)

        title = TitleLabel()
        title.setText("Parametres")
        subtitle = SubtitleLabel()
        subtitle.setText("Ajustez vos sources, seuils et le comportement du scraper en temps reel.")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        root.addWidget(header)

        appearance = self._section_card("Apparence")
        appearance_layout = appearance.layout()
        assert appearance_layout is not None

        self.theme_mode_combo = ComboBox()
        self.theme_mode_combo.addItems(["Sombre", "Clair"])
        self.theme_mode_combo.currentTextChanged.connect(self._on_theme_mode_changed)
        appearance_layout.addWidget(self._row("Mode d'affichage", "Choisissez entre le theme sombre et clair.", self.theme_mode_combo))

        root.addWidget(appearance)

        scraping = self._section_card("Scraping")
        scraping_layout = scraping.layout()
        assert scraping_layout is not None

        self.interval_slider = Slider(Qt.Orientation.Horizontal)
        self.interval_slider.setRange(15, 120)
        self.interval_slider.setValue(30)
        self.interval_slider.valueChanged.connect(self._on_interval_change)
        scraping_layout.addWidget(self._row("Frequence de scan", "Intervalle en minutes.", self.interval_slider))

        self.country_combo = ComboBox()
        self.country_combo.addItems(["ma", "fr", "uk", "us"])
        self.country_combo.currentTextChanged.connect(self._schedule_save)
        scraping_layout.addWidget(self._row("Pays cible Adzuna", "Influence l'URL Adzuna et le filtrage local.", self.country_combo))

        self.source_switches: dict[str, SwitchButton] = {}
        source_rows = [
            ("indeed_rss", "Indeed"),
            ("rekrute", "Rekrute"),
            ("emploi_ma", "Emploi.ma"),
            ("bayt", "Bayt"),
            ("adzuna", "Adzuna"),
            ("remotive", "Remotive"),
        ]
        for key, label in source_rows:
            switch = SwitchButton()
            self.source_switches[key] = switch
            self._bind_switch(switch, self._schedule_save)
            scraping_layout.addWidget(self._row(label, "Active ou desactive la source.", switch))

        root.addWidget(scraping)

        matching = self._section_card("Matching")
        matching_layout = matching.layout()
        assert matching_layout is not None

        self.tfidf_slider = Slider(Qt.Orientation.Horizontal)
        self.tfidf_slider.setRange(0, 100)
        self.tfidf_slider.setValue(40)
        self.tfidf_slider.valueChanged.connect(self._schedule_save)
        matching_layout.addWidget(self._row("Seuil TF-IDF", "Plus haut = filtrage plus strict.", self.tfidf_slider))

        self.semantic_slider = Slider(Qt.Orientation.Horizontal)
        self.semantic_slider.setRange(0, 100)
        self.semantic_slider.setValue(60)
        self.semantic_slider.valueChanged.connect(self._schedule_save)
        matching_layout.addWidget(self._row("Seuil semantique", "Utilise le score IA apres le pre-filtrage.", self.semantic_slider))

        root.addWidget(matching)

        actions = CardWidget()
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(20, 18, 20, 18)

        self.key_hint = BodyLabel()
        self.key_hint.setWordWrap(True)
        self.key_hint.setText("Les cles API sont configurees au moment de l'inscription. Vous pouvez rouvrir l'assistant si besoin.")
        actions_layout.addWidget(self.key_hint, 1)

        self.apply_button = PrimaryPushButton()
        self.apply_button.setText("Appliquer")
        self.apply_button.clicked.connect(self._persist)
        actions_layout.addWidget(self.apply_button)

        root.addWidget(actions)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 12px;")
        root.addWidget(self.status_label)
        root.addStretch()

    def _section_card(self, title_text: str) -> CardWidget:
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        title = SubtitleLabel()
        title.setText(title_text)
        layout.addWidget(title)
        return card

    def _row(self, title: str, description: str, control: QWidget) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        left = QVBoxLayout()
        label = BodyLabel()
        label.setText(title)
        help_text = QLabel(description)
        help_text.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 12px;")
        help_text.setWordWrap(True)
        left.addWidget(label)
        left.addWidget(help_text)

        layout.addLayout(left, 1)
        layout.addWidget(control)
        return row

    def _bind_switch(self, switch: SwitchButton, callback: Callable[[], None]):
        for signal_name in ("checkedChanged", "toggled", "stateChanged"):
            signal = getattr(switch, signal_name, None)
            if signal is not None:
                try:
                    signal.connect(lambda *args, cb=callback: cb())
                    return
                except Exception:
                    continue

    def set_user_from_session(self):
        user = get_current_user()
        self.user_email = str(getattr(user, "email", "") or "") or None
        self.refresh_from_storage()

    def refresh_from_storage(self):
        self._loading = True
        try:
            settings = load_user_settings(self.user_email)
            theme_mode = str(settings.get("theme_mode", "dark")).lower()
            self.theme_mode_combo.setCurrentText("Clair" if theme_mode == "light" else "Sombre")
            self._last_interval = int(settings.get("scrape_interval_minutes", 30))
            self.interval_slider.setValue(self._last_interval)
            self.tfidf_slider.setValue(int(float(settings.get("tfidf_threshold", 0.40)) * 100))
            self.semantic_slider.setValue(int(settings.get("semantic_threshold", 60)))
            self.country_combo.setCurrentText(str(settings.get("adzuna_country", "ma")))

            for key, switch in self.source_switches.items():
                enabled = bool(settings.get("sources_enabled", {}).get(key, True))
                switch.setChecked(enabled)

            self.status_label.setText("Parametres charges depuis la config locale.")
        finally:
            self._loading = False

    def _on_theme_mode_changed(self, value: str):
        if self._loading:
            return
        is_dark = value.lower() != "clair"
        self.themeToggled.emit(is_dark)
        self._schedule_save()

    def _on_interval_change(self, *_):
        if self._loading:
            return
        self._schedule_save()

    def _schedule_save(self, *_):
        if self._loading:
            return
        self._save_timer.start()

    def _persist(self):
        if self._loading:
            return
        if not self.user_email:
            self.status_label.setText("Connectez-vous pour enregistrer les parametres.")
            return

        settings = {
            "theme_mode": "dark" if self.theme_mode_combo.currentText().lower() != "clair" else "light",
            "scrape_interval_minutes": int(self.interval_slider.value()),
            "tfidf_threshold": float(self.tfidf_slider.value()) / 100.0,
            "semantic_threshold": int(self.semantic_slider.value()),
            "adzuna_country": self.country_combo.currentText().strip().lower(),
            "sources_enabled": {key: switch.isChecked() for key, switch in self.source_switches.items()},
        }
        ok, message = save_user_settings(self.user_email, settings)
        self.status_label.setText(message)
        if ok and int(self.interval_slider.value()) != self._last_interval:
            self._last_interval = int(self.interval_slider.value())
            self.restartRequested.emit()
