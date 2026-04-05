"""
ui/dashboard.py - Dashboard SCA
Thème : Blanc / Vert / Bleu / Gris — Icônes grandes et visibles
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QStackedWidget, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QSizePolicy, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QPointF
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen, QBrush, QLinearGradient, QFont
from config import APP_NAME, APP_VERSION

# ── Palette Blanc / Vert / Bleu / Gris ────────────────────────────────────────
BG_MAIN    = "#f0f4f8"       # Fond gris très clair
BG_CARD    = "#ffffff"       # Cartes blanches
BG_SIDEBAR = "#ffffff"       # Sidebar blanche
BORDER     = "#e2e8f0"       # Bordures gris clair
ACCENT     = "#3b82f6"       # Bleu principal
GREEN      = "#16a34a"       # Vert principal
GREEN_LT   = "#dcfce7"       # Vert clair
BLUE       = "#3b82f6"       # Bleu
BLUE_DARK  = "#1d4ed8"       # Bleu foncé
ORANGE     = "#f97316"       # Orange
PURPLE     = "#8b5cf6"       # Violet
RED        = "#ef4444"       # Rouge
YELLOW     = "#eab308"       # Jaune
TEXT_PRI   = "#0f172a"       # Texte principal (noir/gris foncé)
TEXT_SEC   = "#64748b"       # Texte secondaire (gris)

STATUS_COLORS = {
    "en_attente": ("#eab308", "#fef3c7"),
    "en attente": ("#eab308", "#fef3c7"),
    "confirmee":  ("#16a34a", "#dcfce7"),
    "confirmée":  ("#16a34a", "#dcfce7"),
    "deposee":    ("#3b82f6", "#dbeafe"),
    "déposée":    ("#3b82f6", "#dbeafe"),
    "rejetee":    ("#ef4444", "#fee2e2"),
    "rejetée":    ("#ef4444", "#fee2e2"),
    "nouvelle":   ("#64748b", "#f1f5f9"),
}

COMPANY_COLORS = [
    "#3b82f6", "#16a34a", "#f97316", "#8b5cf6",
    "#ef4444", "#eab308", "#06b6d4", "#ec4899",
]


class ScraperThread(QThread):
    finished = pyqtSignal(int)
    error    = pyqtSignal(str)

    def run(self):
        try:
            from workers.scraper_worker import run_now
            t = run_now()
            t.join(timeout=120)
            self.finished.emit(0)
        except Exception as e:
            self.error.emit(str(e))


class SparkLine(QWidget):
    def __init__(self, data: list, color: str, parent=None):
        super().__init__(parent)
        self.data  = data
        self.color = QColor(color)
        self.setFixedSize(80, 32)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, _):
        if len(self.data) < 2:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        mn, mx = min(self.data), max(self.data)
        rng = mx - mn or 1

        def pt(i):
            x = i / (len(self.data) - 1) * w
            y = h - (self.data[i] - mn) / rng * h * 0.8 - h * 0.1
            return QPointF(x, y)

        path = QPainterPath()
        path.moveTo(pt(0))
        for i in range(1, len(self.data)):
            path.lineTo(pt(i))
        path.lineTo(QPointF(w, h))
        path.lineTo(QPointF(0, h))
        path.closeSubpath()

        grad = QLinearGradient(0, 0, 0, h)
        c1 = QColor(self.color)
        c1.setAlpha(50)
        c2 = QColor(self.color)
        c2.setAlpha(0)
        grad.setColorAt(0, c1)
        grad.setColorAt(1, c2)
        p.fillPath(path, QBrush(grad))

        pen = QPen(self.color, 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        for i in range(len(self.data) - 1):
            p.drawLine(pt(i), pt(i + 1))


class BarChart(QWidget):
    DAYS = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    DATA = [28, 25, 22, 25, 38, 41, 35]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(170)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        pl, pr, pt, pb = 38, 10, 28, 28
        cw = w - pl - pr
        ch = h - pt - pb
        n = len(self.DATA)
        mx = max(self.DATA)

        for level in [0, 20, 40, 60, 80]:
            y = pt + ch - (level / mx) * ch
            p.setPen(QPen(QColor(BORDER), 1))
            p.drawLine(pl, int(y), w - pr, int(y))
            p.setPen(QColor(TEXT_SEC))
            p.setFont(QFont("Segoe UI", 8))
            p.drawText(0, int(y) - 6, pl - 4, 14,
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                       str(level))

        bw = cw / n
        gap = bw * 0.3

        for i, val in enumerate(self.DATA):
            x = pl + i * bw + gap / 2
            bh = (val / mx) * ch
            y = pt + ch - bh
            rw = bw - gap
            c = QColor(BLUE)
            c.setAlpha(230)
            p.setBrush(QBrush(c))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(int(x), int(y), int(rw), int(bh), 4, 4)

            p.setPen(QColor(TEXT_SEC))
            p.setFont(QFont("Segoe UI", 8))
            p.drawText(int(x), h - pb + 4, int(rw), 16,
                       Qt.AlignmentFlag.AlignCenter, self.DAYS[i])


class ToggleSwitch(QWidget):
    def __init__(self, checked=True, parent=None):
        super().__init__(parent)
        self.checked = checked
        self.setFixedSize(44, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(QColor(GREEN if self.checked else "#cbd5e1")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, 44, 24, 12, 12)
        p.setBrush(QBrush(QColor("white")))
        p.drawEllipse(22 if self.checked else 2, 2, 20, 20)

    def mousePressEvent(self, _):
        self.checked = not self.checked
        self.update()


def company_avatar(name: str, idx: int = 0) -> QLabel:
    color = COMPANY_COLORS[idx % len(COMPANY_COLORS)]
    letter = (name or "?")[0].upper()
    lbl = QLabel(letter)
    lbl.setFixedSize(36, 36)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setStyleSheet(f"""
        background-color: {color}22;
        border: 1px solid {color}66;
        border-radius: 10px;
        color: {color};
        font-size: 15px;
        font-weight: 800;
    """)
    return lbl


def badge(text: str) -> QLabel:
    fg, bg = STATUS_COLORS.get(text.lower(), ("#64748b", "#f1f5f9"))
    lbl = QLabel(text.replace("_", " "))
    lbl.setFixedHeight(24)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setStyleSheet(f"""
        background-color: {bg};
        color: {fg};
        border: 1px solid {fg}55;
        border-radius: 12px;
        padding: 0px 12px;
        font-size: 11px;
        font-weight: 700;
    """)
    return lbl


def score_pill(score: float) -> QLabel:
    val = int(score)
    color = GREEN if val >= 70 else (YELLOW if val >= 50 else ORANGE)
    lbl = QLabel(f"{val}%")
    lbl.setFixedHeight(24)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setStyleSheet(f"""
        background-color: {color}22;
        color: {color};
        border-radius: 12px;
        padding: 0px 12px;
        font-size: 12px;
        font-weight: 800;
    """)
    return lbl


def cell_item(text: str, color: str = TEXT_SEC) -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    item.setForeground(QColor(color))
    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    return item


class DashboardWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            from services.auth_service import get_current_user
            self.user = get_current_user()
        except Exception:
            self.user = None

        self.kpi_widgets = {}
        self.toggle = None
        self._setup_ui()
        self._start_worker()

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._refresh_all)
        self.refresh_timer.start(120_000)

    def _setup_ui(self):
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1280, 780)
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {BG_MAIN}; }}
            QWidget {{ background-color: transparent; color: {TEXT_PRI}; font-family: 'Segoe UI', Arial, sans-serif; }}
            QScrollArea {{ border: none; background-color: transparent; }}
            QScrollBar:vertical {{ background-color: {BG_CARD}; width: 8px; border-radius: 4px; }}
            QScrollBar::handle:vertical {{ background-color: {BORDER}; border-radius: 4px; min-height: 30px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QTableWidget {{ background-color: transparent; border: none; outline: none; gridline-color: {BORDER}; }}
            QTableCornerButton::section {{ background-color: {BG_MAIN}; border: none; }}
            QHeaderView::section {{
                background-color: {BG_MAIN};
                color: {TEXT_SEC};
                border: none;
                border-bottom: 2px solid {BLUE};
                padding: 10px 8px;
                font-size: 12px;
                font-weight: 700;
            }}
            QTableWidget::item {{ padding: 8px; border-bottom: 1px solid {BORDER}; color: {TEXT_PRI}; }}
            QTableWidget::item:selected {{ background-color: {BLUE}22; }}
            QPushButton {{
                background-color: {BLUE};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 18px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {BLUE_DARK}; }}
            QMessageBox {{ background-color: {BG_CARD}; }}
        """)

        central = QWidget()
        central.setStyleSheet(f"background-color: {BG_MAIN};")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())

        right_w = QWidget()
        right_w.setStyleSheet(f"background-color: {BG_MAIN};")
        right = QVBoxLayout(right_w)
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)
        right.addWidget(self._build_topbar())

        self.content = QStackedWidget()
        self.content.setStyleSheet(f"background-color: {BG_MAIN};")

        self.page_home = self._build_home_page()
        self.page_offers = self._build_offers_stub()
        self.page_history = self._build_history_stub()
        self.page_profile = self._build_profile_stub()
        self.page_coach = self._build_coach_stub()
        self.page_settings = self._build_settings_stub()

        for pg in [self.page_home, self.page_offers, self.page_history,
                   self.page_profile, self.page_coach, self.page_settings]:
            self.content.addWidget(pg)

        right.addWidget(self.content)
        root.addWidget(right_w)

        self._refresh_all()

    def _build_sidebar(self) -> QWidget:
        sb = QWidget()
        sb.setFixedWidth(80)
        sb.setStyleSheet(f"""
            background-color: {BG_SIDEBAR};
            border-right: 1px solid {BORDER};
        """)

        lay = QVBoxLayout(sb)
        lay.setContentsMargins(12, 20, 12, 20)
        lay.setSpacing(12)

        # Logo
        logo = QLabel("SCA")
        logo.setFixedSize(56, 56)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet(f"""
            background-color: {BLUE};
            border-radius: 14px;
            color: white;
            font-size: 18px;
            font-weight: 800;
        """)
        lay.addWidget(logo)
        lay.addSpacing(20)

        # Boutons nav avec GRANDES icônes
        nav_items = [
            ("🏠", 0, True),
            ("👤", 3, False),
            ("📊", 2, False),
            ("➕", 1, False),
            ("🎤", 4, False),
            ("⚙️", 5, False),
        ]
        for icon, idx, active in nav_items:
            btn = self._nav_btn(icon, active)
            if idx >= 0:
                btn.clicked.connect(lambda _, i=idx: self.content.setCurrentIndex(i))
            lay.addWidget(btn)

        lay.addStretch()

        # Bouton déconnexion
        pw = QPushButton("⏻")
        pw.setFixedSize(56, 56)
        pw.setToolTip("Déconnexion")
        pw.setCursor(Qt.CursorShape.PointingHandCursor)
        pw.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {BORDER};
                border-radius: 14px;
                color: {TEXT_SEC};
                font-size: 24px;
            }}
            QPushButton:hover {{
                background-color: {RED}22;
                color: {RED};
                border-color: {RED};
            }}
        """)
        pw.clicked.connect(self._logout)
        lay.addWidget(pw)

        return sb

    def _nav_btn(self, icon: str, active: bool) -> QPushButton:
        btn = QPushButton(icon)
        btn.setFixedSize(56, 56)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFont(QFont("Segoe UI", 24))
        if active:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {BLUE};
                    border-radius: 14px;
                    color: white;
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: {BLUE_DARK};
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border-radius: 14px;
                    color: {TEXT_SEC};
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: {GREEN_LT};
                    color: {GREEN};
                }}
            """)
        return btn

    def _build_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(64)
        bar.setStyleSheet(f"background-color: {BG_SIDEBAR}; border-bottom: 1px solid {BORDER};")

        lay = QHBoxLayout(bar)
        lay.setContentsMargins(24, 0, 24, 0)

        t = QLabel("SCA Desktop")
        t.setStyleSheet(f"color: {TEXT_PRI}; font-size: 20px; font-weight: 800;")
        s = QLabel("Système de Candidature Automatique aux Stages")
        s.setStyleSheet(f"color: {TEXT_SEC}; font-size: 13px; margin-left: 12px;")
        lay.addWidget(t)
        lay.addWidget(s)
        lay.addStretch()

        user_name = "Utilisateur"
        if self.user:
            try:
                user_name = f"{self.user.prenom} {self.user.nom}"
            except Exception:
                pass

        nm = QLabel(user_name)
        nm.setStyleSheet(f"color: {TEXT_PRI}; font-size: 14px; font-weight: 600;")

        lay.addWidget(nm)
        return bar

    def _make_kpi_card(self, key, title, icon, color, spark_data) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 16px;
            }}
        """)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 16, 18, 14)
        lay.setSpacing(8)

        top = QHBoxLayout()
        ic = QLabel(icon)
        ic.setFixedSize(44, 44)
        ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ic.setFont(QFont("Segoe UI", 22))
        ic.setStyleSheet(f"background-color: {color}22; border-radius: 12px;")
        top.addWidget(ic)
        top.addStretch()
        top.addWidget(SparkLine(spark_data, color))
        lay.addLayout(top)

        val = QLabel("—")
        val.setStyleSheet(f"color: {TEXT_PRI}; font-size: 32px; font-weight: 800;")
        self.kpi_widgets[key] = val
        lay.addWidget(val)

        lbl = QLabel(title)
        lbl.setStyleSheet(f"color: {TEXT_SEC}; font-size: 13px; font-weight: 500;")
        lay.addWidget(lbl)
        return card

    def _build_home_page(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"background-color: {BG_MAIN}; border: none;")

        page = QWidget()
        page.setStyleSheet(f"background-color: {BG_MAIN};")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(20)

        # KPI row
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(16)
        for key, title, icon, color, data in [
            ("deposees", "Candidatures déposées", "📋", BLUE, [10, 18, 14, 25, 22, 30, 35]),
            ("attente", "En attente", "⏳", ORANGE, [3, 5, 4, 7, 6, 9, 10]),
            ("total", "Offres détectées", "🔍", PURPLE, [1, 2, 1, 3, 2, 4, 5]),
            ("score", "Score moyen", "⭐", GREEN, [55, 60, 58, 65, 63, 68, 70]),
        ]:
            kpi_row.addWidget(self._make_kpi_card(key, title, icon, color, data))
        lay.addLayout(kpi_row)

        # Tableau récent
        table_frame = QFrame()
        table_frame.setStyleSheet(f"background-color: {BG_CARD}; border: 1px solid {BORDER}; border-radius: 16px;")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(0, 0, 0, 0)

        self.recent_table = QTableWidget(0, 6)
        self.recent_table.setHorizontalHeaderLabels(["Entreprise", "Poste", "Source", "Score", "Statut", "Date"])
        self.recent_table.setStyleSheet(self._table_style())
        self.recent_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.recent_table.verticalHeader().setVisible(False)
        self.recent_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.recent_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table_layout.addWidget(self.recent_table)

        lay.addWidget(table_frame)

        # Graphique
        chart_frame = QFrame()
        chart_frame.setStyleSheet(f"background-color: {BG_CARD}; border: 1px solid {BORDER}; border-radius: 16px;")
        chart_layout = QVBoxLayout(chart_frame)
        chart_layout.setContentsMargins(20, 16, 20, 16)

        chart_title = QLabel("Activité des 7 derniers jours")
        chart_title.setStyleSheet(f"color: {TEXT_PRI}; font-size: 15px; font-weight: 700;")
        chart_layout.addWidget(chart_title)
        chart_layout.addWidget(BarChart())

        lay.addWidget(chart_frame)

        scroll.setWidget(page)
        return scroll

    def _table_style(self) -> str:
        return f"""
            QTableWidget {{
                background-color: {BG_CARD};
                border: none;
                gridline-color: {BORDER};
            }}
            QTableWidget::item {{
                padding: 12px 10px;
                color: {TEXT_PRI};
                font-size: 13px;
                border-bottom: 1px solid {BORDER};
            }}
            QTableWidget::item:selected {{
                background-color: {BLUE}22;
            }}
            QHeaderView::section {{
                background-color: {BG_MAIN};
                color: {TEXT_SEC};
                font-weight: 700;
                font-size: 12px;
                padding: 12px;
                border: none;
                border-bottom: 2px solid {BLUE};
            }}
        """

    def _build_offers_stub(self) -> QWidget:
        try:
            from ui.offers_page import OffersPageWidget
            return OffersPageWidget()
        except Exception:
            return self._stub("Offres de Stage")

    def _build_history_stub(self) -> QWidget:
        try:
            from ui.candidature_history import CandidatureHistoryWidget
            return CandidatureHistoryWidget()
        except Exception:
            return self._stub("Historique")

    def _build_profile_stub(self) -> QWidget:
        try:
            from ui.profile_editor import ProfileEditorWidget
            return ProfileEditorWidget()
        except Exception:
            return self._stub("Mon Profil")

    def _build_coach_stub(self) -> QWidget:
        try:
            from ui.interview_simulator import InterviewSimulatorWidget
            return InterviewSimulatorWidget()
        except Exception:
            return self._stub("Coach IA")

    def _build_settings_stub(self) -> QWidget:
        return self._stub("Paramètres")

    def _stub(self, title: str) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background-color: {BG_MAIN};")
        l = QVBoxLayout(w)
        l.setContentsMargins(32, 32, 32, 32)
        lb = QLabel(title)
        lb.setStyleSheet(f"color: {TEXT_PRI}; font-size: 24px; font-weight: 700;")
        l.addWidget(lb)
        l.addStretch()
        return w

    def _refresh_all(self):
        self._refresh_kpi()
        self._refresh_recent_table()

    def _refresh_kpi(self):
        try:
            from database.db_manager import get_session
            from database.models import Offre, Candidature, StatutCandidature
            from sqlalchemy import func
            from datetime import date

            with get_session() as db:
                deposees = db.query(Candidature).filter_by(statut=StatutCandidature.deposee).count()
                attente = db.query(Candidature).filter_by(statut=StatutCandidature.en_attente).count()
                offres_today = db.query(Offre).filter(func.date(Offre.date_detection) == date.today()).count()
                avg_claude = db.query(func.avg(Offre.score_claude)).scalar()
                if avg_claude:
                    score_moy = f"{avg_claude:.0f}%"
                else:
                    score_moy = "—"

                self.kpi_widgets["deposees"].setText(str(deposees))
                self.kpi_widgets["attente"].setText(str(attente))
                self.kpi_widgets["total"].setText(str(offres_today))
                self.kpi_widgets["score"].setText(score_moy)
        except Exception:
            for k in self.kpi_widgets:
                self.kpi_widgets[k].setText("—")

    def _refresh_recent_table(self):
        try:
            from database.db_manager import get_session
            from database.models import Offre, Candidature

            with get_session() as db:
                offres = db.query(Offre).order_by(Offre.date_detection.desc()).limit(10).all()
                self.recent_table.setRowCount(len(offres))

                for row, o in enumerate(offres):
                    cand = db.query(Candidature).filter_by(offre_id=o.id).order_by(Candidature.created_at.desc()).first()
                    statut_str = cand.statut.value if cand else "nouvelle"

                    cw = QWidget()
                    cl2 = QHBoxLayout(cw)
                    cl2.setContentsMargins(4, 2, 4, 2)
                    cl2.setSpacing(10)
                    cl2.addWidget(company_avatar(o.entreprise or "?", row))
                    n = QLabel(o.entreprise or "—")
                    n.setStyleSheet(f"color:{TEXT_PRI};font-size:13px;font-weight:600;")
                    cl2.addWidget(n)
                    cl2.addStretch()
                    self.recent_table.setCellWidget(row, 0, cw)

                    self.recent_table.setItem(row, 1, cell_item(o.titre[:60]))

                    sw = QWidget()
                    sl2 = QHBoxLayout(sw)
                    sl2.setContentsMargins(4, 2, 4, 2)
                    sc2 = QLabel(o.source)
                    sc2.setStyleSheet(f"color:{TEXT_SEC};font-size:11px;")
                    sl2.addWidget(sc2)
                    sl2.addStretch()
                    self.recent_table.setCellWidget(row, 2, sw)

                    s = o.score_claude if o.score_claude else (o.score_tfidf * 100 if o.score_tfidf else 0)
                    self.recent_table.setCellWidget(row, 3, score_pill(s))

                    self.recent_table.setCellWidget(row, 4, badge(statut_str))

                    date_str = o.date_detection.strftime("%d/%m/%Y") if o.date_detection else "—"
                    self.recent_table.setItem(row, 5, cell_item(date_str))

        except Exception as e:
            self.recent_table.setRowCount(0)

    def _start_worker(self):
        try:
            from workers.scraper_worker import start_worker
            start_worker()
        except Exception:
            pass

    def _logout(self):
        reply = QMessageBox.question(self, "Déconnexion", "Voulez-vous vraiment vous déconnecter ?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from services.auth_service import logout
                from workers.scraper_worker import stop_worker
                logout()
                stop_worker()
            except Exception:
                pass
            self.close()

    def closeEvent(self, event):
        try:
            from workers.scraper_worker import stop_worker
            stop_worker()
        except Exception:
            pass
        event.accept()