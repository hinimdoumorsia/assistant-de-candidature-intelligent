"""Fluent registration wizard built with QStackedWidget (4 steps)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QObject, Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from qfluentwidgets import (
    BodyLabel,
    CheckBox,
    ComboBox,
    HyperlinkButton,
    IndeterminateProgressRing,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    PasswordLineEdit,
    PillPushButton,
    PrimaryPushButton,
    ProgressBar,
    PushButton,
    Slider,
    StateToolTip,
    SubtitleLabel,
    TitleLabel,
)

from ui.lottie_widget import LottieWidget


class _CvParseWorker(QObject):
    finished = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, cv_path: str, api_key: str):
        super().__init__()
        self.cv_path = cv_path
        self.api_key = api_key

    def run(self) -> None:
        try:
            from services.profile_service import parse_cv_with_claude

            result = parse_cv_with_claude(self.cv_path, self.api_key)
            self.finished.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))


class _ApiTestWorker(QObject):
    finished = pyqtSignal(bool, str)

    def __init__(self, provider: str, key1: str, key2: str = ""):
        super().__init__()
        self.provider = provider
        self.key1 = key1
        self.key2 = key2

    def run(self) -> None:
        if self.provider == "claude":
            from services.auth_service import test_claude_key

            ok, msg = test_claude_key(self.key1)
            self.finished.emit(ok, msg)
            return

        from services.api_keys_service import test_adzuna_keys

        ok, msg = test_adzuna_keys(self.key1, self.key2, "ma")
        self.finished.emit(ok, msg)


class RegisterWizard(QDialog):
    """4-step registration wizard based on Fluent components only."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.registration_data: dict[str, Any] = {}
        self._state_tip: StateToolTip | None = None
        self._cv_thread: QThread | None = None
        self._api_thread: QThread | None = None
        self._step1_valid = False

        self.setWindowTitle("Creation de compte - StageAuto")
        self.setMinimumSize(940, 700)
        self.setModal(True)

        self._build_ui()
        self._update_step_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        title = TitleLabel("Assistant d'inscription")
        subtitle = SubtitleLabel("4 etapes: infos perso, cles API, profil, config scraper")
        root.addWidget(title)
        root.addWidget(subtitle)

        self.progress = ProgressBar()
        self.progress.setRange(0, 100)
        root.addWidget(self.progress)

        self.step_markers = [QLabel(str(i)) for i in range(1, 5)]
        marker_row = QHBoxLayout()
        marker_row.setSpacing(18)
        for marker in self.step_markers:
            marker.setFixedSize(30, 30)
            marker.setAlignment(Qt.AlignmentFlag.AlignCenter)
            marker_row.addWidget(marker)
        marker_row.addStretch(1)
        root.addLayout(marker_row)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_step1())
        self.stack.addWidget(self._build_step2())
        self.stack.addWidget(self._build_step3())
        self.stack.addWidget(self._build_step4())
        root.addWidget(self.stack, 1)

        nav = QHBoxLayout()
        nav.addStretch(1)
        self.back_btn = PushButton("Retour")
        self.back_btn.clicked.connect(self._previous_step)
        self.next_btn = PrimaryPushButton("Suivant")
        self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(self._next_step)
        nav.addWidget(self.back_btn)
        nav.addWidget(self.next_btn)
        root.addLayout(nav)

    def _build_step1(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)

        self.prenom = LineEdit()
        self.nom = LineEdit()
        self.email = LineEdit()
        self.password = PasswordLineEdit()
        self.password_confirm = PasswordLineEdit()
        self.step1_ring = IndeterminateProgressRing()
        self.step1_ring.setFixedSize(26, 26)
        self.step1_ring.hide()
        self.password_strength = ProgressBar()
        self.password_strength.setRange(0, 100)
        self.password_strength.setValue(0)
        self.email_re = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

        self.prenom.textChanged.connect(self._on_step1_live_validation)
        self.nom.textChanged.connect(self._on_step1_live_validation)
        self.email.textChanged.connect(self._on_step1_live_validation)
        self.password.textChanged.connect(self._on_step1_live_validation)
        self.password_confirm.textChanged.connect(self._on_step1_live_validation)

        form.addRow("Prenom", self.prenom)
        form.addRow("Nom", self.nom)
        form.addRow("Email", self.email)
        form.addRow("Mot de passe", self.password)
        form.addRow("Force du mot de passe", self.password_strength)
        form.addRow("Confirmation", self.password_confirm)
        form.addRow("Validation", self.step1_ring)
        return page

    def _build_step2(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        form = QFormLayout()
        self.claude_key = PasswordLineEdit()
        self.adzuna_id = LineEdit()
        self.adzuna_key = PasswordLineEdit()
        self.model_combo = ComboBox()
        self.model_combo.addItems([
            "claude-sonnet-4-6 (recommande)",
            "claude-haiku-4-5 (economique)",
        ])

        form.addRow("Claude API key", self.claude_key)
        form.addRow("Adzuna App ID", self.adzuna_id)
        form.addRow("Adzuna App Key", self.adzuna_key)
        form.addRow("Modele Claude", self.model_combo)
        layout.addLayout(form)

        links = QHBoxLayout()
        links.addWidget(HyperlinkButton("https://console.anthropic.com", "Anthropic Console"))
        links.addWidget(HyperlinkButton("https://developer.adzuna.com/signup", "Adzuna Developer"))
        links.addStretch(1)
        layout.addLayout(links)

        self.api_success_lottie = LottieWidget(str(Path("assets/lottie/success_check.json")), loop=False)
        self.api_success_lottie.setFixedSize(80, 80)
        self.api_success_lottie.hide()
        self.api_loading_lottie = LottieWidget(str(Path("assets/lottie/loading_ai.json")), loop=True)
        self.api_loading_lottie.setFixedSize(80, 80)
        self.api_loading_lottie.hide()

        test_row = QHBoxLayout()
        self.test_claude_btn = PrimaryPushButton("Tester la connexion Claude")
        self.test_claude_btn.clicked.connect(lambda: self._test_api_connections("claude"))
        self.test_adzuna_btn = PrimaryPushButton("Tester Adzuna")
        self.test_adzuna_btn.clicked.connect(lambda: self._test_api_connections("adzuna"))
        test_row.addWidget(self.test_claude_btn)
        test_row.addWidget(self.test_adzuna_btn)
        test_row.addWidget(self.api_loading_lottie)
        test_row.addWidget(self.api_success_lottie)
        test_row.addStretch(1)
        layout.addLayout(test_row)

        return page

    def _build_step3(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        form = QGridLayout()
        self.job_title = LineEdit()
        self.job_title.setPlaceholderText("Ex: Data Analyst Intern")

        self.training = ComboBox()
        self.training.addItems(["Bac+2", "Bac+3", "Bac+4", "Bac+5", "Doctorat"])

        self.level = ComboBox()
        self.level.addItems(["Debutant", "Intermediaire", "Avance"])

        self.localisation = LineEdit()
        self.localisation.setPlaceholderText("Casablanca, Rabat, Marrakech...")

        self.skill_input = LineEdit()
        self.skill_input.setPlaceholderText("Ajouter une competence puis Entree")
        self.skill_input.returnPressed.connect(self._add_skill_tag)
        self.skills_flow = QHBoxLayout()

        form.addWidget(BodyLabel("Titre poste"), 0, 0)
        form.addWidget(self.job_title, 0, 1)
        form.addWidget(BodyLabel("Formation"), 1, 0)
        form.addWidget(self.training, 1, 1)
        form.addWidget(BodyLabel("Niveau"), 2, 0)
        form.addWidget(self.level, 2, 1)
        form.addWidget(BodyLabel("Localisation"), 3, 0)
        form.addWidget(self.localisation, 3, 1)
        layout.addLayout(form)

        layout.addWidget(BodyLabel("Competences"))
        layout.addWidget(self.skill_input)
        layout.addLayout(self.skills_flow)

        langs = QHBoxLayout()
        self.lang_fr = CheckBox("Francais")
        self.lang_en = CheckBox("Anglais")
        self.lang_ar = CheckBox("Arabe")
        self.lang_es = CheckBox("Espagnol")
        for cb in [self.lang_fr, self.lang_en, self.lang_ar, self.lang_es]:
            langs.addWidget(cb)
        langs.addStretch(1)
        layout.addWidget(BodyLabel("Langues"))
        layout.addLayout(langs)

        self.cv_path = LineEdit()
        self.cv_path.setReadOnly(True)
        self.cv_loading_ring = IndeterminateProgressRing()
        self.cv_loading_ring.setFixedSize(26, 26)
        self.cv_loading_ring.hide()
        self.cv_lottie = LottieWidget(str(Path("assets/lottie/loading_ai.json")))
        self.cv_lottie.setFixedSize(120, 120)
        self.cv_lottie.hide()

        cv_row = QHBoxLayout()
        browse_btn = PushButton("Parcourir CV")
        browse_btn.clicked.connect(self._browse_cv)
        parse_btn = PrimaryPushButton("Parser CV")
        parse_btn.clicked.connect(self._parse_cv)

        cv_row.addWidget(self.cv_path)
        cv_row.addWidget(browse_btn)
        cv_row.addWidget(parse_btn)
        cv_row.addWidget(self.cv_loading_ring)
        cv_row.addWidget(self.cv_lottie)
        layout.addLayout(cv_row)
        layout.addStretch(1)

        self._skill_tags: list[str] = []
        return page

    def _build_step4(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        layout.addWidget(BodyLabel("Sources de scraping"))
        self.source_checks = {
            "indeed_rss": CheckBox("Indeed"),
            "rekrute": CheckBox("Rekrute"),
            "emploi_ma": CheckBox("Emploi.ma"),
            "bayt": CheckBox("Bayt"),
            "adzuna": CheckBox("Adzuna"),
            "remotive": CheckBox("Remotive"),
        }
        for cb in self.source_checks.values():
            cb.setChecked(True)
            layout.addWidget(cb)

        self.interval_slider = Slider(Qt.Orientation.Horizontal)
        self.interval_slider.setRange(15, 120)
        self.interval_slider.setValue(30)
        self.interval_label = BodyLabel("Frequence: 30 min")
        self.interval_slider.valueChanged.connect(
            lambda v: self.interval_label.setText(f"Frequence: {v} min")
        )

        self.tfidf_slider = Slider(Qt.Orientation.Horizontal)
        self.tfidf_slider.setRange(0, 100)
        self.tfidf_slider.setValue(40)
        self.tfidf_label = BodyLabel("Seuil TF-IDF: 40%")
        self.tfidf_slider.valueChanged.connect(
            lambda v: self.tfidf_label.setText(f"Seuil TF-IDF: {v}%")
        )

        self.claude_slider = Slider(Qt.Orientation.Horizontal)
        self.claude_slider.setRange(0, 100)
        self.claude_slider.setValue(60)
        self.claude_label = BodyLabel("Seuil Claude: 60/100")
        self.claude_slider.valueChanged.connect(
            lambda v: self.claude_label.setText(f"Seuil Claude: {v}/100")
        )

        self.sector_input = LineEdit()
        self.sector_input.setPlaceholderText("Data, Finance, Industrie...")

        for label, slider in [
            (self.interval_label, self.interval_slider),
            (self.tfidf_label, self.tfidf_slider),
            (self.claude_label, self.claude_slider),
        ]:
            layout.addWidget(label)
            layout.addWidget(slider)

        layout.addWidget(BodyLabel("Secteurs"))
        layout.addWidget(self.sector_input)
        return page

    def _update_step_ui(self) -> None:
        index = self.stack.currentIndex()
        self.progress.setValue(int(((index + 1) / 4) * 100))
        self.back_btn.setEnabled(index > 0)
        self.next_btn.setText("Terminer et demarrer" if index == 3 else "Suivant")

        for i, marker in enumerate(self.step_markers):
            active = i <= index
            marker.setStyleSheet(
                "border-radius: 15px; font-weight: 700;"
                f"background: {'#5b6af0' if active else '#d1d5db'};"
                f"color: {'white' if active else '#374151'};"
            )

    def _previous_step(self) -> None:
        self.stack.setCurrentIndex(max(0, self.stack.currentIndex() - 1))
        self._update_step_ui()

    def _next_step(self) -> None:
        current = self.stack.currentIndex()
        if not self._validate_current_step():
            return

        if current < 3:
            self.stack.setCurrentIndex(current + 1)
            self._update_step_ui()
            return

        self._finish_registration()

    def _validate_current_step(self) -> bool:
        step = self.stack.currentIndex()
        if step == 0:
            return bool(self._step1_valid)
        if step == 1:
            self._save_step2()
            return True
        if step == 2:
            self._save_step3()
            return True
        self._save_step4()
        return True

    def _validate_step1(self) -> bool:
        self._on_step1_live_validation(show_message=True)
        return bool(self._step1_valid)

    def _on_step1_live_validation(self, *_args, show_message: bool = False) -> None:
        prenom = self.prenom.text().strip()
        nom = self.nom.text().strip()
        email = self.email.text().strip()
        pwd = self.password.text()
        pwd2 = self.password_confirm.text()

        score = 0
        if len(pwd) >= 8:
            score += 40
        if any(c.isupper() for c in pwd):
            score += 30
        if any(c.isdigit() for c in pwd):
            score += 30
        self.password_strength.setValue(score)

        if not all([prenom, nom, email, pwd, pwd2]):
            self._step1_valid = False
            self.next_btn.setEnabled(False)
            return
        if not self.email_re.match(email):
            self._step1_valid = False
            self.next_btn.setEnabled(False)
            if show_message:
                self._warning("Etape 1", "Email invalide.")
            return
        if pwd != pwd2:
            self._step1_valid = False
            self.next_btn.setEnabled(False)
            if show_message:
                self._error("Etape 1", "Les mots de passe ne correspondent pas.")
            return
        if score < 100:
            self._step1_valid = False
            self.next_btn.setEnabled(False)
            if show_message:
                self._warning("Etape 1", "Mot de passe: min 8 + 1 majuscule + 1 chiffre.")
            return

        self.registration_data.update(
            {
                "prenom": prenom,
                "nom": nom,
                "email": email,
                "password": pwd,
            }
        )
        self._step1_valid = True
        self.next_btn.setEnabled(True)

    def _save_step2(self) -> None:
        model = self.model_combo.currentText()
        model_id = "claude-sonnet-4-6" if "sonnet" in model else "claude-haiku-4-5"
        self.registration_data.update(
            {
                "claude_key": self.claude_key.text().strip(),
                "claude_model": model_id,
                "adzuna_app_id": self.adzuna_id.text().strip(),
                "adzuna_api_key": self.adzuna_key.text().strip(),
                "adzuna_country": "ma",
            }
        )

    def _save_step3(self) -> None:
        languages = []
        for cb in [self.lang_fr, self.lang_en, self.lang_ar, self.lang_es]:
            if cb.isChecked():
                languages.append(cb.text())

        self.registration_data["profile"] = {
            "titre": self.job_title.text().strip() or "Mon Profil",
            "competences": list(self._skill_tags),
            "formation": self.training.currentText(),
            "experience": self.level.currentText(),
            "langues": ", ".join(languages),
            "localisation": self.localisation.text().strip(),
            "cv_path": self.cv_path.text().strip(),
        }

    def _save_step4(self) -> None:
        sources_enabled = {k: cb.isChecked() for k, cb in self.source_checks.items()}
        sectors = [s.strip() for s in self.sector_input.text().split(",") if s.strip()]
        self.registration_data["settings"] = {
            "scrape_interval_minutes": int(self.interval_slider.value()),
            "tfidf_threshold": float(self.tfidf_slider.value()) / 100.0,
            "semantic_threshold": int(self.claude_slider.value()),
            "sources_enabled": sources_enabled,
            "sectors": sectors,
        }

    def _test_api_connections(self, provider: str) -> None:
        if provider == "claude":
            key1 = self.claude_key.text()
            key2 = ""
            title = "Vérification Claude"
        else:
            key1 = self.adzuna_id.text()
            key2 = self.adzuna_key.text()
            title = "Vérification Adzuna"

        self._state_tip = StateToolTip("Test en cours", title, self)
        self._state_tip.show()
        self.api_success_lottie.hide()
        self.api_loading_lottie.show()

        self._api_thread = QThread(self)
        worker = _ApiTestWorker(provider, key1, key2)
        worker.moveToThread(self._api_thread)
        self._api_thread.started.connect(worker.run)
        worker.finished.connect(lambda ok, msg: self._on_api_test_finished(provider, ok, msg))
        worker.finished.connect(self._api_thread.quit)
        worker.finished.connect(worker.deleteLater)
        self._api_thread.finished.connect(self._api_thread.deleteLater)
        self._api_thread.start()

    def _on_api_test_finished(self, provider: str, ok: bool, msg: str) -> None:
        label = "Claude" if provider == "claude" else "Adzuna"
        self.api_loading_lottie.hide()
        if ok:
            self.api_success_lottie.show()
            self._success("API", f"{label}: {msg}")
            if self._state_tip:
                self._state_tip.setContent("Connexion validée")
                self._state_tip.setState(True)
        else:
            self._error("API", f"{label}: {msg}")
            if self._state_tip:
                self._state_tip.setContent("Validation échouée")
                self._state_tip.setState(False)

    def _browse_cv(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Selectionner CV", "", "CV (*.pdf *.docx)")
        if path:
            self.cv_path.setText(path)

    def _parse_cv(self) -> None:
        cv = self.cv_path.text().strip()
        if not cv:
            self._error("CV", "Selectionnez un CV avant le parsing.")
            return

        self.cv_loading_ring.show()
        self.cv_lottie.show()
        self._state_tip = StateToolTip("Parsing CV", "Parsing CV avec Claude...", self)
        self._state_tip.show()

        self._cv_thread = QThread(self)
        worker = _CvParseWorker(cv, self.claude_key.text().strip())
        worker.moveToThread(self._cv_thread)
        self._cv_thread.started.connect(worker.run)
        worker.finished.connect(self._on_cv_parsed)
        worker.failed.connect(self._on_cv_parse_failed)
        worker.finished.connect(self._cv_thread.quit)
        worker.failed.connect(self._cv_thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        self._cv_thread.finished.connect(self._cv_thread.deleteLater)
        self._cv_thread.start()

    def _on_cv_parsed(self, data: dict) -> None:
        self.cv_loading_ring.hide()
        self.cv_lottie.hide()
        self.job_title.setText(str(data.get("titre") or self.job_title.text()))
        self.localisation.setText(str(data.get("localisation") or self.localisation.text()))
        for skill in data.get("competences", []) or []:
            text = str(skill).strip()
            if text:
                self._add_skill_tag(text)

        if self._state_tip:
            self._state_tip.setContent("CV parse avec succes")
            self._state_tip.setState(True)
        self._success("Profil", "Le profil a ete pre-rempli depuis votre CV.")

    def _on_cv_parse_failed(self, err: str) -> None:
        self.cv_loading_ring.hide()
        self.cv_lottie.hide()
        if self._state_tip:
            self._state_tip.setContent("Parsing echoue")
            self._state_tip.setState(False)
        self._error("Profil", f"Impossible d'analyser le CV: {err}")

    def _add_skill_tag(self, forced: str | None = None) -> None:
        raw = forced if forced is not None else self.skill_input.text()
        value = (raw or "").strip()
        if not value or value in self._skill_tags:
            if forced is None:
                self.skill_input.clear()
            return

        self._skill_tags.append(value)
        tag = PillPushButton(value)
        tag.clicked.connect(lambda: self._remove_skill(tag, value))
        self.skills_flow.addWidget(tag)
        if forced is None:
            self.skill_input.clear()

    def _remove_skill(self, btn: PillPushButton, value: str) -> None:
        if value in self._skill_tags:
            self._skill_tags.remove(value)
        btn.setParent(None)
        btn.deleteLater()

    def _finish_registration(self) -> None:
        from services.auth_service import create_user
        from services.user_settings_service import save_user_settings

        data = self.registration_data
        payload = {
            "nom": data.get("nom", ""),
            "prenom": data.get("prenom", ""),
            "email": data.get("email", ""),
            "password": data.get("password", ""),
            "claude_key": data.get("claude_key", ""),
            "claude_model": data.get("claude_model", "claude-sonnet-4-6"),
            "adzuna_app_id": data.get("adzuna_app_id", ""),
            "adzuna_api_key": data.get("adzuna_api_key", ""),
            "profile": data.get("profile", {}),
            "settings": data.get("settings", {}),
        }
        ok, msg, _user_id = create_user(payload)
        if not ok:
            self._error("Inscription", msg)
            return

        save_user_settings(data.get("email", ""), data.get("settings", {}))

        self._success("Inscription", "Compte cree avec succes.")
        self.accept()

    def _error(self, title: str, content: str) -> None:
        InfoBar.error(
            title=title,
            content=content,
            parent=self,
            position=InfoBarPosition.TOP_RIGHT,
        )

    def _success(self, title: str, content: str) -> None:
        InfoBar.success(
            title=title,
            content=content,
            parent=self,
            position=InfoBarPosition.TOP_RIGHT,
        )

    def _warning(self, title: str, content: str) -> None:
        InfoBar.warning(
            title=title,
            content=content,
            parent=self,
            position=InfoBarPosition.TOP_RIGHT,
        )
