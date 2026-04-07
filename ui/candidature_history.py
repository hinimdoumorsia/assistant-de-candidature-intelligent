"""Fluent candidature history page with real-time filters."""
from __future__ import annotations

from datetime import date, datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QTableWidgetItem, QVBoxLayout, QWidget

from qfluentwidgets import (
    Action,
    BodyLabel,
    CardWidget,
    ComboBox,
    DatePicker,
    PrimaryPushButton,
    RoundMenu,
    SearchLineEdit,
    TableWidget,
    TitleLabel,
)


class CandidatureHistoryWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._row_ids: list[int] = []
        self._setup_ui()
        self._load()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(12)

        root.addWidget(TitleLabel("Historique des candidatures"))

        market = CardWidget()
        market_l = QVBoxLayout(market)
        market_l.setContentsMargins(14, 12, 14, 12)
        self.market_label = BodyLabel("Score marché disponible après 30+ offres vues.")
        market_l.addWidget(self.market_label)
        root.addWidget(market)

        filters = QHBoxLayout()
        self.status_combo = ComboBox()
        self.status_combo.addItems(["Toutes", "en_attente", "deposee", "confirmee", "rejetee", "en_entretien"])
        self.status_combo.currentIndexChanged.connect(self._load)

        self.source_combo = ComboBox()
        self.source_combo.addItems(["Toutes", "indeed_rss", "rekrute", "emploi_ma", "bayt", "adzuna"])
        self.source_combo.currentIndexChanged.connect(self._load)

        self.search = SearchLineEdit()
        self.search.setPlaceholderText("Entreprise ou poste")
        self.search.textChanged.connect(self._load)

        self.start_date = DatePicker()
        self.end_date = DatePicker()
        self.start_date.dateChanged.connect(self._load)
        self.end_date.dateChanged.connect(self._load)

        filters.addWidget(self.status_combo)
        filters.addWidget(self.source_combo)
        filters.addWidget(self.search, 1)
        filters.addWidget(self.start_date)
        filters.addWidget(self.end_date)
        root.addLayout(filters)

        self.table = TableWidget(self)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Date", "Entreprise", "Poste", "Source", "Score", "Statut", "Actions"])
        self.table.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._open_menu)
        vh = self.table.verticalHeader()
        assert vh is not None
        vh.setVisible(False)
        root.addWidget(self.table, 1)

        report_btn = PrimaryPushButton("📄 Générer rapport mensuel")
        report_btn.clicked.connect(self._generate_report)
        root.addWidget(report_btn)

    def _load(self) -> None:
        from database.db_manager import get_session
        from database.models import Candidature, Offre
        from services.auth_service import get_current_user
        from services.matching_service import market_score

        status_filter = self.status_combo.currentText()
        source_filter = self.source_combo.currentText()
        query_text = self.search.text().strip().lower()

        with get_session() as db:
            q = db.query(Candidature).join(Offre, Candidature.offre_id == Offre.id, isouter=True)
            if status_filter != "Toutes":
                q = q.filter(Candidature.statut == status_filter)
            if source_filter != "Toutes":
                q = q.filter(Offre.source == source_filter)
            rows = q.order_by(Candidature.created_at.desc()).all()

        start = self.start_date.getDate().toPyDate()
        end = self.end_date.getDate().toPyDate()

        self.table.setRowCount(0)
        self._row_ids.clear()
        for cand in rows:
            offer = cand.offre
            cdate = cand.created_at.date() if cand.created_at else date.today()
            if cdate < start or cdate > end:
                continue

            entreprise = getattr(offer, "entreprise", "") or ""
            poste = getattr(offer, "titre", "") or ""
            source = getattr(offer, "source", "") or ""
            if query_text and query_text not in f"{entreprise} {poste}".lower():
                continue

            score = "—"
            if offer is not None:
                if offer.score_claude is not None:
                    score = f"{offer.score_claude:.0f}"
                elif offer.score_tfidf is not None:
                    score = f"{offer.score_tfidf * 100:.0f}%"

            r = self.table.rowCount()
            self.table.insertRow(r)
            self._row_ids.append(int(cand.id))
            self.table.setItem(r, 0, QTableWidgetItem(cand.created_at.strftime("%Y-%m-%d") if cand.created_at else "—"))
            self.table.setItem(r, 1, QTableWidgetItem(entreprise))
            self.table.setItem(r, 2, QTableWidgetItem(poste))
            self.table.setItem(r, 3, QTableWidgetItem(source))
            self.table.setItem(r, 4, QTableWidgetItem(score))
            self.table.setItem(r, 5, QTableWidgetItem(getattr(cand.statut, "value", str(cand.statut))))
            self.table.setItem(r, 6, QTableWidgetItem("Clic droit"))

        user = get_current_user()
        if user is not None:
            uid = int(getattr(user, "id", 0) or 0)
            ms = market_score(uid)
            missing = ", ".join(ms.get("competences_manquantes_top5", [])) or "N/A"
            self.market_label.setText(f"Compétences marché manquantes: {missing}")

    def _selected_candidature_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._row_ids):
            return None
        return self._row_ids[row]

    def _open_menu(self, pos) -> None:
        cand_id = self._selected_candidature_id()
        if cand_id is None:
            return

        menu = RoundMenu(parent=self)
        confirmed = Action("Réponse reçue — Confirmée", menu)
        rejected = Action("Réponse reçue — Rejetée", menu)
        interview = Action("En entretien", menu)
        confirmed.triggered.connect(lambda: self._set_status(cand_id, "confirmee"))
        rejected.triggered.connect(lambda: self._set_status(cand_id, "rejetee"))
        interview.triggered.connect(lambda: self._set_status(cand_id, "en_entretien"))
        menu.addAction(confirmed)
        menu.addAction(rejected)
        menu.addAction(interview)
        menu.exec(self.table.mapToGlobal(pos))

    def _set_status(self, cand_id: int, status: str) -> None:
        from database.db_manager import get_session
        from database.models import Candidature, StatutCandidature

        with get_session() as db:
            cand = db.get(Candidature, cand_id)
            if cand is not None:
                cand.statut = StatutCandidature(status)
                if status == "deposee":
                    cand.deposee_at = datetime.utcnow()
        self._load()

    def _generate_report(self) -> None:
        from services.auth_service import get_current_user
        from services.pdf_service import generate_monthly_report

        user = get_current_user()
        if user is None:
            return
        now = datetime.utcnow()
        uid = int(getattr(user, "id", 0) or 0)
        generate_monthly_report(uid, now.strftime("%Y-%m"))
