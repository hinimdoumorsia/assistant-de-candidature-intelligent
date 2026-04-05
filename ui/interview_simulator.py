"""
ui/interview_simulator.py - Coach IA + Simulateur d'entretien en mode chat
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QComboBox, QScrollArea, QSizePolicy,
    QTabWidget, QListWidget, QListWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont
from config import COLORS


class AIThread(QThread):
    response = pyqtSignal(str)
    error    = pyqtSignal(str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn     = fn
        self.args   = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.response.emit(result or "")
        except Exception as e:
            self.error.emit(str(e))


class ChatBubble(QFrame):
    """Bulle de message pour le simulateur."""
    def __init__(self, text: str, is_user: bool):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setMaximumWidth(480)
        lbl.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        if is_user:
            lbl.setStyleSheet(f"""
                background: {COLORS['primary']};
                color: white;
                border-radius: 14px 14px 4px 14px;
                padding: 12px 16px;
                font-size: 13px;
            """)
            layout.addStretch()
            layout.addWidget(lbl)
        else:
            lbl.setStyleSheet(f"""
                background: white;
                color: {COLORS['text']};
                border: 1.5px solid {COLORS['card_border']};
                border-radius: 14px 14px 14px 4px;
                padding: 12px 16px;
                font-size: 13px;
            """)
            layout.addWidget(lbl)
            layout.addStretch()

        self.setStyleSheet("background: transparent; border: none;")


class InterviewSimulatorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._history    = []
        self._current_offre  = None
        self._current_profil = None
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(32, 28, 32, 28)
        main.setSpacing(20)

        title = QLabel("Coach IA & Simulateur d'Entretien")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {COLORS['primary_dark']};")
        main.addWidget(title)

        # Tabs : Coach | Simulateur
        tabs = QTabWidget()
        tabs.addTab(self._build_coach_tab(),     "🤖 Coach de Candidature")
        tabs.addTab(self._build_simulator_tab(), "🎤 Simulateur d'Entretien")
        main.addWidget(tabs)

    # ── Onglet Coach ────────────────────────────────────────────────────────────

    def _build_coach_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Sélecteurs
        sel_row = QHBoxLayout()
        sel_row.addWidget(QLabel("Profil :"))
        self.coach_profil_combo = QComboBox()
        self.coach_profil_combo.setMinimumWidth(200)
        sel_row.addWidget(self.coach_profil_combo)

        sel_row.addWidget(QLabel("Offre :"))
        self.coach_offre_combo = QComboBox()
        self.coach_offre_combo.setMinimumWidth(250)
        sel_row.addWidget(self.coach_offre_combo)
        sel_row.addStretch()

        btn_analyse = QPushButton("🔍 Analyser ma candidature")
        btn_analyse.clicked.connect(self._run_coach)
        sel_row.addWidget(btn_analyse)
        layout.addLayout(sel_row)

        # Résultats coach
        self.coach_result_area = QScrollArea()
        self.coach_result_area.setWidgetResizable(True)
        self.coach_result_area.setFrameShape(QFrame.Shape.NoFrame)
        self.coach_result_area.setStyleSheet("background: transparent;")

        self.coach_content = QWidget()
        self.coach_content_layout = QVBoxLayout(self.coach_content)
        self.coach_content_layout.setSpacing(14)
        self.coach_content_layout.addWidget(
            self._info_box("💡 Sélectionnez un profil et une offre puis cliquez sur Analyser."))
        self.coach_content_layout.addStretch()
        self.coach_result_area.setWidget(self.coach_content)
        layout.addWidget(self.coach_result_area)

        # Bouton génération LM
        btn_row = QHBoxLayout()
        for i, label in enumerate(["📝 Variante Technique", "💚 Variante Humaine", "🚀 Variante Projet"], 1):
            btn = QPushButton(label)
            btn.setProperty("class", "secondary" if i > 1 else "")
            _i = i
            btn.clicked.connect(lambda _, v=_i: self._generate_lettre(v))
            btn_row.addWidget(btn)
        layout.addLayout(btn_row)

        return w

    def _info_box(self, text: str, color: str = None) -> QFrame:
        card = QFrame()
        c = color or COLORS["veryLightBlue"] if hasattr(COLORS, "veryLightBlue") else "#DEEAF1"
        card.setStyleSheet(f"background: {COLORS['bg_dark']}; border-radius: 10px; border: 1px solid {COLORS['card_border']};")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(16, 14, 16, 14)
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(f"color: {COLORS['text']};")
        cl.addWidget(lbl)
        return card

    def _build_section_card(self, title: str, items: list, color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: white;
                border-left: 4px solid {color};
                border-radius: 0 10px 10px 0;
                border-top: 1px solid {COLORS['card_border']};
                border-right: 1px solid {COLORS['card_border']};
                border-bottom: 1px solid {COLORS['card_border']};
            }}
        """)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(16, 14, 16, 14)
        cl.setSpacing(8)

        t = QLabel(f"<b>{title}</b>")
        t.setStyleSheet(f"color: {color}; font-size: 14px;")
        cl.addWidget(t)

        for item in items:
            row = QHBoxLayout()
            dot = QLabel("•")
            dot.setStyleSheet(f"color: {color}; font-weight: 700;")
            dot.setFixedWidth(12)
            txt = QLabel(item)
            txt.setWordWrap(True)
            txt.setStyleSheet("color: #333;")
            row.addWidget(dot)
            row.addWidget(txt)
            row.addStretch()
            cl.addLayout(row)
        return card

    # ── Onglet Simulateur ───────────────────────────────────────────────────────

    def _build_simulator_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Sélecteurs
        sel_row = QHBoxLayout()
        sel_row.addWidget(QLabel("Profil :"))
        self.sim_profil_combo = QComboBox()
        self.sim_profil_combo.setMinimumWidth(200)
        sel_row.addWidget(self.sim_profil_combo)

        sel_row.addWidget(QLabel("Offre :"))
        self.sim_offre_combo = QComboBox()
        self.sim_offre_combo.setMinimumWidth(250)
        sel_row.addWidget(self.sim_offre_combo)
        sel_row.addStretch()

        btn_start = QPushButton("▶ Démarrer l'entretien")
        btn_start.clicked.connect(self._start_interview)
        sel_row.addWidget(btn_start)

        btn_reset = QPushButton("🔄 Réinitialiser")
        btn_reset.setProperty("class", "secondary")
        btn_reset.clicked.connect(self._reset_interview)
        sel_row.addWidget(btn_reset)
        layout.addLayout(sel_row)

        # Zone de chat
        chat_frame = QFrame()
        chat_frame.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_dark']};
                border: 1.5px solid {COLORS['card_border']};
                border-radius: 12px;
            }}
        """)
        cf_layout = QVBoxLayout(chat_frame)
        cf_layout.setContentsMargins(0, 0, 0, 0)

        # Header chat
        chat_header = QFrame()
        chat_header.setStyleSheet(f"background: {COLORS['primary_dark']}; border-radius: 10px 10px 0 0;")
        ch_layout = QHBoxLayout(chat_header)
        ch_layout.setContentsMargins(16, 12, 16, 12)
        avatar = QLabel("🤵")
        avatar.setStyleSheet("font-size: 22px; background: transparent;")
        name = QLabel("Recruteur IA — Simulateur d'entretien")
        name.setStyleSheet("color: white; font-weight: 600; background: transparent;")
        self.interview_status = QLabel("⚪ En attente")
        self.interview_status.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 12px; background: transparent;")
        ch_layout.addWidget(avatar)
        ch_layout.addWidget(name)
        ch_layout.addStretch()
        ch_layout.addWidget(self.interview_status)
        cf_layout.addWidget(chat_header)

        # Messages scroll
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.chat_scroll.setStyleSheet("background: transparent;")
        self.chat_scroll.setMinimumHeight(320)

        self.chat_messages = QWidget()
        self.chat_messages.setStyleSheet("background: transparent;")
        self.messages_layout = QVBoxLayout(self.chat_messages)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.messages_layout.setSpacing(10)
        self.messages_layout.setContentsMargins(12, 12, 12, 12)

        self.chat_scroll.setWidget(self.chat_messages)
        cf_layout.addWidget(self.chat_scroll)

        # Saisie
        input_frame = QFrame()
        input_frame.setStyleSheet(f"background: white; border-radius: 0 0 10px 10px; border-top: 1px solid {COLORS['card_border']};")
        il = QHBoxLayout(input_frame)
        il.setContentsMargins(12, 10, 12, 10)
        il.setSpacing(10)

        self.chat_input = QTextEdit()
        self.chat_input.setPlaceholderText("Tapez votre réponse ici… (Ctrl+Entrée pour envoyer)")
        self.chat_input.setMaximumHeight(70)
        self.chat_input.setStyleSheet(f"""
            QTextEdit {{
                border: 1.5px solid {COLORS['card_border']};
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
            }}
            QTextEdit:focus {{ border-color: {COLORS['primary']}; }}
        """)

        btn_send = QPushButton("Envoyer ▶")
        btn_send.setFixedWidth(110)
        btn_send.setFixedHeight(60)
        btn_send.clicked.connect(self._send_message)
        il.addWidget(self.chat_input)
        il.addWidget(btn_send)
        cf_layout.addWidget(input_frame)

        layout.addWidget(chat_frame)
        return w

    # ── Données ─────────────────────────────────────────────────────────────────

    def _load_data(self):
        from services.profile_service import get_profils
        from database.db_manager import get_session
        from database.models import Offre

        profils = get_profils()
        self._profils = profils
        for combo in (self.coach_profil_combo, self.sim_profil_combo):
            combo.clear()
            for p in profils:
                combo.addItem(p.titre, p.id)

        with get_session() as db:
            offres = db.query(Offre).order_by(Offre.score_tfidf.desc()).limit(50).all()
        self._offres = offres
        for combo in (self.coach_offre_combo, self.sim_offre_combo):
            combo.clear()
            for o in offres:
                combo.addItem(f"{o.titre[:45]} — {o.entreprise[:25]}", o.id)

    def _get_profil(self, combo: QComboBox):
        idx = combo.currentIndex()
        if 0 <= idx < len(self._profils):
            return self._profils[idx]
        return None

    def _get_offre(self, combo: QComboBox):
        idx = combo.currentIndex()
        if 0 <= idx < len(self._offres):
            return self._offres[idx]
        return None

    # ── Actions Coach ───────────────────────────────────────────────────────────

    def _run_coach(self):
        profil = self._get_profil(self.coach_profil_combo)
        offre  = self._get_offre(self.coach_offre_combo)
        if not profil or not offre:
            QMessageBox.warning(self, "Sélection", "Choisissez un profil et une offre.")
            return

        # Vider
        while self.coach_content_layout.count() > 0:
            item = self.coach_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        loading = self._info_box("⏳ Analyse en cours avec Claude IA…")
        self.coach_content_layout.addWidget(loading)

        from services.generator_service import coach_candidature
        self._coach_thread = AIThread(coach_candidature, profil, offre)
        self._coach_thread.response.connect(lambda _: None)  # non utilisé directement
        self._coach_thread.finished.connect(lambda: self._display_coach(profil, offre))
        # Stocker résultat
        self._coach_result = None

        def _run():
            from services.generator_service import coach_candidature
            self._coach_result = coach_candidature(profil, offre)

        import threading
        t = threading.Thread(target=_run, daemon=True)
        t.start()

        # Poll result
        self._coach_timer = QTimer()
        self._coach_timer.timeout.connect(lambda: self._check_coach_done())
        self._coach_timer.start(500)

    def _check_coach_done(self):
        if not hasattr(self, "_coach_result"):
            return
        if self._coach_result is not None or True:
            self._coach_timer.stop()
            self._display_coach_result(self._coach_result)

    def _display_coach_result(self, data: dict | None):
        # Vider
        while self.coach_content_layout.count() > 0:
            item = self.coach_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not data:
            self.coach_content_layout.addWidget(
                self._info_box("❌ Impossible d'analyser. Vérifiez votre clé API Claude dans .env"))
            self.coach_content_layout.addStretch()
            return

        # Score global
        score = data.get("score_global", 0)
        sc_card = QFrame()
        sc_card.setStyleSheet(f"background: white; border-radius: 12px; border: 1.5px solid {COLORS['card_border']};")
        scl = QHBoxLayout(sc_card)
        scl.setContentsMargins(20, 16, 20, 16)
        sc_icon = QLabel("📊")
        sc_icon.setStyleSheet("font-size: 28px;")
        sc_txt = QLabel(f"Score de compatibilité globale : <b style='color:{COLORS['primary']};font-size:20px'>{score}/100</b>")
        sc_txt.setStyleSheet("font-size: 14px;")
        scl.addWidget(sc_icon)
        scl.addWidget(sc_txt)
        scl.addStretch()
        self.coach_content_layout.addWidget(sc_card)

        # Points forts
        if data.get("points_forts"):
            self.coach_content_layout.addWidget(
                self._build_section_card("✅ Points forts", data["points_forts"], COLORS["success"]))

        # Points faibles
        if data.get("points_faibles"):
            self.coach_content_layout.addWidget(
                self._build_section_card("⚠️ Points à renforcer", data["points_faibles"], COLORS["warning"]))

        # Mots-clés manquants
        if data.get("mots_cles_manquants"):
            self.coach_content_layout.addWidget(
                self._build_section_card("🔑 Mots-clés à ajouter au profil",
                                         data["mots_cles_manquants"], COLORS["accent"]))

        # Conseils
        if data.get("conseils"):
            self.coach_content_layout.addWidget(
                self._build_section_card("💡 Conseils personnalisés", data["conseils"], COLORS["primary"]))

        self.coach_content_layout.addStretch()

    def _generate_lettre(self, variante: int):
        profil = self._get_profil(self.coach_profil_combo)
        offre  = self._get_offre(self.coach_offre_combo)
        if not profil or not offre:
            QMessageBox.warning(self, "Sélection", "Choisissez un profil et une offre.")
            return

        from services.generator_service import generate_lettre_motivation
        from services.pdf_service import generate_lettre_pdf
        from config import EXPORTS_DIR
        from datetime import datetime

        loading = QMessageBox(self)
        loading.setWindowTitle("Génération en cours")
        loading.setText("⏳ Claude génère votre lettre de motivation…")
        loading.setStandardButtons(QMessageBox.StandardButton.NoButton)
        loading.show()

        def _gen():
            lettre = generate_lettre_motivation(profil, offre, variante)
            if lettre:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                path = str(EXPORTS_DIR / f"lettre_v{variante}_{ts}.pdf")
                out = generate_lettre_pdf(lettre, profil, offre, path)
                return out, lettre
            return None, None

        import threading
        self._lettre_result = None

        def _run():
            self._lettre_result = _gen()

        t = threading.Thread(target=_run, daemon=True)
        t.start()

        def _check():
            if self._lettre_result is None:
                return
            self._lettre_timer.stop()
            loading.close()
            path, content = self._lettre_result
            if path:
                QMessageBox.information(self, "Lettre générée",
                    f"✅ Lettre de motivation (variante {variante}) exportée :\n{path}")
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de générer la lettre. Vérifiez la clé API.")

        self._lettre_timer = QTimer()
        self._lettre_timer.timeout.connect(_check)
        self._lettre_timer.start(500)

    # ── Actions Simulateur ──────────────────────────────────────────────────────

    def _start_interview(self):
        profil = self._get_profil(self.sim_profil_combo)
        offre  = self._get_offre(self.sim_offre_combo)
        if not profil or not offre:
            QMessageBox.warning(self, "Sélection", "Choisissez un profil et une offre.")
            return

        self._current_profil = profil
        self._current_offre  = offre
        self._history = []
        self.interview_status.setText("🟢 Entretien en cours")

        # Vider les messages
        while self.messages_layout.count() > 0:
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Message d'introduction
        intro = f"Bonjour ! Je suis votre recruteur pour le poste de **{offre.titre}** chez **{offre.entreprise}**. Commençons l'entretien. Pouvez-vous vous présenter brièvement ?"
        self._add_message(intro, is_user=False)

    def _reset_interview(self):
        self._history = []
        self._current_profil = None
        self._current_offre  = None
        self.interview_status.setText("⚪ En attente")
        while self.messages_layout.count() > 0:
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.chat_input.clear()

    def _send_message(self):
        text = self.chat_input.toPlainText().strip()
        if not text:
            return
        if not self._current_profil or not self._current_offre:
            QMessageBox.information(self, "Info", "Démarrez d'abord un entretien.")
            return

        self.chat_input.clear()
        self._add_message(text, is_user=True)

        # Réponse IA
        self._history.append({"role": "user", "content": text})
        self.interview_status.setText("🟡 Le recruteur répond…")

        from services.generator_service import simulate_entretien
        self._sim_thread = AIThread(
            simulate_entretien,
            self._current_profil,
            self._current_offre,
            list(self._history),
            text
        )
        self._sim_thread.response.connect(self._on_sim_response)
        self._sim_thread.error.connect(lambda e: (
            self._add_message(f"❌ Erreur: {e}", is_user=False),
            self.interview_status.setText("🔴 Erreur")))
        self._sim_thread.start()

    def _on_sim_response(self, text: str):
        self._history.append({"role": "assistant", "content": text})
        self._add_message(text, is_user=False)
        self.interview_status.setText("🟢 Entretien en cours")

    def _add_message(self, text: str, is_user: bool):
        bubble = ChatBubble(text, is_user)
        self.messages_layout.addWidget(bubble)
        # Scroll to bottom
        QTimer.singleShot(100, lambda: self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()))

    def _display_coach(self, profil, offre):
        pass  # Géré via timer
