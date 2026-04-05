"""
ui/dashboard.py - Dashboard SCA — dark theme exact image de référence
Sidebar visible + données dynamiques depuis la BDD (Offre, Candidature)
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QStackedWidget, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QSizePolicy, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QPointF
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen, QBrush, QLinearGradient, QFont
from config import APP_NAME, APP_VERSION

# ── Palette ──────────────────────────────────────────────────────────────────
BG_MAIN    = "#0f1117"
BG_CARD    = "#1a1f2e"
BG_SIDEBAR = "#12151e"
BORDER     = "#1e2535"
ACCENT     = "#5b6af0"
GREEN      = "#22c55e"
ORANGE     = "#f97316"
PURPLE     = "#a855f7"
RED        = "#ef4444"
YELLOW     = "#eab308"
TEXT_PRI   = "#e2e8f0"
TEXT_SEC   = "#6b7280"

STATUS_COLORS = {
    "en_attente": ("#eab308", "#2d2500"),
    "en attente": ("#eab308", "#2d2500"),
    "confirmee":  ("#22c55e", "#002d1a"),
    "confirmée":  ("#22c55e", "#002d1a"),
    "deposee":    ("#5b6af0", "#0d1033"),
    "déposée":    ("#5b6af0", "#0d1033"),
    "rejetee":    ("#ef4444", "#2d0000"),
    "rejetée":    ("#ef4444", "#2d0000"),
    "nouvelle":   ("#94a3b8", "#1e2535"),
}

COMPANY_COLORS = [
    "#5b6af0", "#22c55e", "#f97316", "#a855f7",
    "#ef4444", "#eab308", "#06b6d4", "#ec4899",
]


# ── Worker scraper ────────────────────────────────────────────────────────────
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


# ── Sparkline ─────────────────────────────────────────────────────────────────
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
        c1 = QColor(self.color); c1.setAlpha(50)
        c2 = QColor(self.color); c2.setAlpha(0)
        grad.setColorAt(0, c1)
        grad.setColorAt(1, c2)
        p.fillPath(path, QBrush(grad))

        pen = QPen(self.color, 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        for i in range(len(self.data) - 1):
            p.drawLine(pt(i), pt(i + 1))


# ── Bar chart ─────────────────────────────────────────────────────────────────
class BarChart(QWidget):
    DAYS      = ["Ma", "Me", "Je", "Je", "Ve", "Sa", "Di", "23", "Sa", "Sa", "Lu", "23"]
    DATA      = [28, 25, 22, 25, 38, 41, 35, 72, 45, 42, 48, 65]
    HIGHLIGHT = 7

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
        n  = len(self.DATA)
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

        bw  = cw / n
        gap = bw * 0.3
        pts = []
        for i, val in enumerate(self.DATA):
            cx = pl + i * bw + bw / 2
            cy = pt + ch - (val / mx) * ch
            pts.append(QPointF(cx, cy))

        for i, val in enumerate(self.DATA):
            x  = pl + i * bw + gap / 2
            bh = (val / mx) * ch
            y  = pt + ch - bh
            rw = bw - gap
            c = QColor(ACCENT)
            c.setAlpha(230 if i == self.HIGHLIGHT else 40)
            p.setBrush(QBrush(c))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(int(x), int(y), int(rw), int(bh), 4, 4)

            if i == self.HIGHLIGHT:
                p.setPen(QColor(TEXT_PRI))
                p.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
                p.drawText(int(x) - 6, int(y) - 16, int(rw) + 12, 14,
                           Qt.AlignmentFlag.AlignCenter, f"{val} ▼")

            p.setPen(QColor(TEXT_SEC))
            p.setFont(QFont("Segoe UI", 8))
            p.drawText(int(x), h - pb + 4, int(rw), 16,
                       Qt.AlignmentFlag.AlignCenter, self.DAYS[i])

        pen = QPen(QColor("#a5b4fc"), 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        for i in range(len(pts) - 1):
            p.drawLine(pts[i], pts[i + 1])
        p.setBrush(QBrush(QColor("#a5b4fc")))
        p.setPen(Qt.PenStyle.NoPen)
        cp = pts[self.HIGHLIGHT]
        p.drawEllipse(int(cp.x()) - 4, int(cp.y()) - 4, 8, 8)


# ── Toggle ────────────────────────────────────────────────────────────────────
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
        p.setBrush(QBrush(QColor(GREEN if self.checked else "#374151")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, 44, 24, 12, 12)
        p.setBrush(QBrush(QColor("white")))
        p.drawEllipse(22 if self.checked else 2, 2, 20, 20)

    def mousePressEvent(self, _):
        self.checked = not self.checked
        self.update()


# ── Helpers ───────────────────────────────────────────────────────────────────
def company_avatar(name: str, idx: int = 0) -> QLabel:
    color  = COMPANY_COLORS[idx % len(COMPANY_COLORS)]
    letter = (name or "?")[0].upper()
    lbl    = QLabel(letter)
    lbl.setFixedSize(32, 32)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setStyleSheet(f"""
        background-color: {color}33;
        border: 1px solid {color}66;
        border-radius: 8px;
        color: {color};
        font-size: 13px;
        font-weight: 700;
    """)
    return lbl


def badge(text: str) -> QLabel:
    fg, bg = STATUS_COLORS.get(text.lower(), ("#94a3b8", "#1e2535"))
    lbl = QLabel(text.replace("_", " "))
    lbl.setFixedHeight(22)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setStyleSheet(f"""
        background-color: {bg};
        color: {fg};
        border: 1px solid {fg}55;
        border-radius: 10px;
        padding: 0px 10px;
        font-size: 11px;
        font-weight: 600;
    """)
    return lbl


def score_pill(score: float) -> QLabel:
    val   = int(score)
    color = GREEN if val >= 70 else (YELLOW if val >= 50 else ORANGE)
    lbl   = QLabel(f"{val}%")
    lbl.setFixedHeight(22)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setStyleSheet(f"""
        background-color: {color}22;
        color: {color};
        border-radius: 10px;
        padding: 0px 10px;
        font-size: 11px;
        font-weight: 700;
    """)
    return lbl


def cell_item(text: str, color: str = TEXT_SEC) -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    item.setForeground(QColor(color))
    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    return item


# ════════════════════════════════════════════════════════════════════════════
# Fenêtre principale
# ════════════════════════════════════════════════════════════════════════════
class DashboardWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            from services.auth_service import get_current_user
            self.user = get_current_user()
        except Exception:
            self.user = None

        self.kpi_widgets = {}
        self.toggle      = None
        self._setup_ui()
        self._start_worker()

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._refresh_all)
        self.refresh_timer.start(120_000)

    # ── Setup ─────────────────────────────────────────────────────────────────
    def _setup_ui(self):
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1280, 780)

        # Override TOTAL du stylesheet vert de config.py
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {BG_MAIN}; }}
            QWidget      {{ background-color: transparent; color: {TEXT_PRI};
                            font-family: 'Segoe UI', Arial, sans-serif; }}
            QScrollArea  {{ border: none; background-color: transparent; }}
            QScrollBar:vertical {{
                background-color: {BG_CARD}; width: 6px; border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {BORDER}; border-radius: 3px; min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QTableWidget  {{ background-color: transparent; border: none; outline: none;
                             gridline-color: {BORDER}; }}
            QTableCornerButton::section {{ background-color: {BG_MAIN}; border: none; }}
            QHeaderView::section {{
                background-color: {BG_MAIN}; color: {TEXT_SEC};
                border: none; border-bottom: 1px solid {BORDER};
                padding: 8px 6px; font-size: 12px; font-weight: 600;
            }}
            QTableWidget::item {{
                padding: 6px; border-bottom: 1px solid {BORDER};
                color: {TEXT_PRI};
            }}
            QTableWidget::item:selected {{
                background-color: {ACCENT}22; color: {TEXT_PRI};
            }}
            QPushButton {{
                background-color: {ACCENT}; color: white;
                border: none; border-radius: 8px;
                padding: 8px 18px; font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background-color: #4a59d0; }}
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

        self.page_home     = self._build_home_page()
        self.page_offers   = self._build_offers_stub()
        self.page_history  = self._build_history_stub()
        self.page_profile  = self._build_profile_stub()
        self.page_coach    = self._build_coach_stub()
        self.page_settings = self._build_settings_stub()

        for pg in [self.page_home, self.page_offers, self.page_history,
                   self.page_profile, self.page_coach, self.page_settings]:
            self.content.addWidget(pg)

        right.addWidget(self.content)
        root.addWidget(right_w)

        self._refresh_all()

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self) -> QWidget:
        sb = QWidget()
        sb.setFixedWidth(64)
        # Couleur explicite sur le widget lui-même
        sb.setStyleSheet(f"background-color: {BG_SIDEBAR}; border-right: 1px solid {BORDER};")

        lay = QVBoxLayout(sb)
        lay.setContentsMargins(12, 16, 12, 16)
        lay.setSpacing(6)

        # Logo
        logo = QLabel("⟳")
        logo.setFixedSize(40, 40)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet(f"""
            background-color: {ACCENT};
            border-radius: 10px;
            color: white;
            font-size: 20px;
            font-weight: 700;
        """)
        lay.addWidget(logo)
        lay.addSpacing(16)

        # Boutons nav
        nav_items = [
            ("🏠", 0, True),
            ("👤", 3, False),
            ("📊", 2, False),
            ("➕", 1, False),
            ("🔔", -1, False),
            ("↺",  -1, False),
        ]
        for icon, idx, active in nav_items:
            btn = self._nav_btn(icon, active)
            if idx >= 0:
                btn.clicked.connect(lambda _, i=idx: self.content.setCurrentIndex(i))
            lay.addWidget(btn)

        lay.addStretch()

        # Power
        pw = QPushButton("⏻")
        pw.setFixedSize(40, 40)
        pw.setToolTip("Déconnexion")
        pw.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {BORDER};
                border-radius: 10px;
                color: {TEXT_SEC};
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: {RED}33;
                color: {RED};
                border-color: {RED};
            }}
        """)
        pw.clicked.connect(self._logout)
        lay.addWidget(pw)

        av = QLabel("😎")
        av.setFixedSize(36, 36)
        av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        av.setStyleSheet(f"background-color: #374151; border-radius: 18px; font-size: 18px;")
        lay.addSpacing(4)
        lay.addWidget(av)

        return sb

    def _nav_btn(self, icon: str, active: bool) -> QPushButton:
        btn = QPushButton(icon)
        btn.setFixedSize(40, 40)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if active:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ACCENT};
                    border-radius: 10px;
                    color: white;
                    font-size: 16px;
                    border: none;
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border-radius: 10px;
                    color: {TEXT_SEC};
                    font-size: 16px;
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: {BORDER};
                    color: {TEXT_PRI};
                }}
            """)
        return btn

    # ── Topbar ────────────────────────────────────────────────────────────────
    def _build_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(56)
        bar.setStyleSheet(f"background-color: {BG_SIDEBAR}; border-bottom: 1px solid {BORDER};")

        lay = QHBoxLayout(bar)
        lay.setContentsMargins(20, 0, 20, 0)

        t = QLabel("SCA")
        t.setStyleSheet(f"color: {TEXT_PRI}; font-size: 18px; font-weight: 700;")
        s = QLabel("  Système de Candidature Automatique aux Stages")
        s.setStyleSheet(f"color: {TEXT_SEC}; font-size: 13px;")
        lay.addWidget(t)
        lay.addWidget(s)
        lay.addStretch()

        user_name = "Utilisateur"
        if self.user:
            try:
                user_name = f"{self.user.prenom} {self.user.nom}"
            except Exception:
                pass

        av = QLabel("😎")
        av.setFixedSize(32, 32)
        av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        av.setStyleSheet("background-color: #374151; border-radius: 16px; font-size: 16px;")

        nm = QLabel(user_name)
        nm.setStyleSheet(f"color: {TEXT_PRI}; font-size: 14px; font-weight: 500;")

        ch = QLabel(" ⌄")
        ch.setStyleSheet(f"color: {TEXT_SEC};")

        lay.addWidget(av)
        lay.addSpacing(8)
        lay.addWidget(nm)
        lay.addWidget(ch)
        return bar

    # ── KPI card ──────────────────────────────────────────────────────────────
    def _make_kpi_card(self, key, title, icon, color, spark_data) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 12)
        lay.setSpacing(6)

        top = QHBoxLayout()
        ic = QLabel(icon)
        ic.setFixedSize(32, 32)
        ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ic.setStyleSheet(f"background-color: {color}33; border-radius: 8px; font-size: 15px;")
        top.addWidget(ic)
        top.addStretch()
        top.addWidget(SparkLine(spark_data, color))
        lay.addLayout(top)

        val = QLabel("—")
        val.setStyleSheet(f"color: {TEXT_PRI}; font-size: 28px; font-weight: 700;")
        self.kpi_widgets[key] = val
        lay.addWidget(val)

        lbl = QLabel(title)
        lbl.setStyleSheet(f"color: {TEXT_SEC}; font-size: 12px;")
        lay.addWidget(lbl)
        return card

    # ── Page Accueil ──────────────────────────────────────────────────────────
    def _build_home_page(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"background-color: {BG_MAIN}; border: none;")

        page = QWidget()
        page.setStyleSheet(f"background-color: {BG_MAIN};")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(16)

        # KPI row
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)
        for key, title, icon, color, data in [
            ("deposees", "Total candidatures déposées", "✈",  ACCENT,  [10,18,14,25,22,30,35,40,38,44,50,55]),
            ("attente",  "Candidatures en attente",     "🕐", ORANGE,  [3,5,4,7,6,9,10,9,11,13,12,15]),
            ("total",    "Offres détectées aujourd'hui","🔍", PURPLE,  [1,2,1,3,2,4,5,4,6,7,5,8]),
            ("score",    "Score moyen de matching (%)", "⭐", GREEN,   [55,60,58,65,63,68,70,69,71,72,72,72]),
        ]:
            kpi_row.addWidget(self._make_kpi_card(key, title, icon, color, data))
        lay.addLayout(kpi_row)

        # Ligne centrale
        mid = QHBoxLayout()
        mid.setSpacing(16)

        # Table
        left = QFrame()
        left.setStyleSheet(f"QFrame {{ background-color: {BG_CARD}; border: 1px solid {BORDER}; border-radius: 12px; }}")
        ll = QVBoxLayout(left)
        ll.setContentsMargins(16, 14, 16, 14)
        ll.setSpacing(10)

        hdr = QHBoxLayout()
        ht = QLabel("Dernières Activité")
        ht.setStyleSheet(f"color: {TEXT_PRI}; font-size: 15px; font-weight: 700;")
        hdr.addWidget(ht)
        hdr.addStretch()
        ll.addLayout(hdr)

        self.recent_table = QTableWidget(0, 6)
        self.recent_table.setHorizontalHeaderLabels(
            ["Entreprise", "Poste", "Source", "Score", "Statut", "Date"])
        for col, mode in [
            (0, QHeaderView.ResizeMode.ResizeToContents),
            (1, QHeaderView.ResizeMode.Stretch),
            (2, QHeaderView.ResizeMode.ResizeToContents),
            (3, QHeaderView.ResizeMode.ResizeToContents),
            (4, QHeaderView.ResizeMode.ResizeToContents),
            (5, QHeaderView.ResizeMode.ResizeToContents),
        ]:
            self.recent_table.horizontalHeader().setSectionResizeMode(col, mode)
        self.recent_table.verticalHeader().setVisible(False)
        self.recent_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.recent_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.recent_table.setShowGrid(False)
        self.recent_table.verticalHeader().setDefaultSectionSize(46)
        ll.addWidget(self.recent_table)

        # Panel droit
        right = QFrame()
        right.setFixedWidth(255)
        right.setStyleSheet(f"QFrame {{ background-color: {BG_CARD}; border: 1px solid {BORDER}; border-radius: 12px; }}")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(16, 14, 16, 14)
        rl.setSpacing(10)

        sh = QHBoxLayout()
        sl = QLabel("Scraper en cours")
        sl.setStyleSheet(f"color: {TEXT_PRI}; font-size: 14px; font-weight: 700;")
        self.toggle = ToggleSwitch(checked=True)
        ec = QLabel("En cours:")
        ec.setStyleSheet(f"color: {TEXT_SEC}; font-size: 11px;")
        sh.addWidget(sl)
        sh.addStretch()
        sh.addWidget(ec)
        sh.addWidget(self.toggle)
        rl.addLayout(sh)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {BORDER}; max-height: 1px;")
        rl.addWidget(sep)

        orl = QLabel("Offres détectées récemment")
        orl.setStyleSheet(f"color: {TEXT_PRI}; font-size: 13px; font-weight: 600;")
        rl.addWidget(orl)

        self.recent_offers_widget = QWidget()
        self.recent_offers_widget.setStyleSheet("background: transparent;")
        self.recent_offers_layout = QVBoxLayout(self.recent_offers_widget)
        self.recent_offers_layout.setContentsMargins(0, 0, 0, 0)
        self.recent_offers_layout.setSpacing(8)

        rscroll = QScrollArea()
        rscroll.setWidget(self.recent_offers_widget)
        rscroll.setWidgetResizable(True)
        rscroll.setStyleSheet("background: transparent; border: none;")
        rl.addWidget(rscroll)

        voir = QPushButton("Voir toutes")
        voir.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {ACCENT};
                border: none; font-size: 12px; font-weight: 600; padding: 0;
            }}
            QPushButton:hover {{ color: #818cf8; }}
        """)
        voir.clicked.connect(lambda: self.content.setCurrentIndex(1))
        rl.addWidget(voir, alignment=Qt.AlignmentFlag.AlignRight)

        mid.addWidget(left)
        mid.addWidget(right)
        lay.addLayout(mid)

        # Graphique
        cf = QFrame()
        cf.setStyleSheet(f"QFrame {{ background-color: {BG_CARD}; border: 1px solid {BORDER}; border-radius: 12px; }}")
        cl = QVBoxLayout(cf)
        cl.setContentsMargins(16, 14, 16, 14)
        cl.setSpacing(8)

        ch_hdr = QHBoxLayout()
        ct = QLabel("Candidatures · Activité des 7 derniers jours")
        ct.setStyleSheet(f"color: {TEXT_PRI}; font-size: 14px; font-weight: 700;")
        dr = QHBoxLayout()
        dr.setSpacing(4)
        for d in ["Ma", "Me", "Je", "Ve", "Sa"]:
            active = (d == "Sa")
            dl = QLabel(d)
            dl.setStyleSheet(f"""
                background-color: {'%s' % ACCENT if active else BG_MAIN};
                color: {'white' if active else TEXT_SEC};
                border-radius: 6px; padding: 3px 8px;
                font-size: 11px; font-weight: {'700' if active else '400'};
            """)
            dr.addWidget(dl)
        ch_hdr.addWidget(ct)
        ch_hdr.addStretch()
        ch_hdr.addLayout(dr)
        cl.addLayout(ch_hdr)
        cl.addWidget(BarChart())
        lay.addWidget(cf)

        scroll.setWidget(page)
        return scroll

    # ── Pages déléguées ───────────────────────────────────────────────────────
    def _build_offers_stub(self) -> QWidget:
        try:
            from ui.offers_page import OffersPageWidget
            return OffersPageWidget()
        except Exception:
            return self._stub("🔍  Offres de Stage")

    def _build_history_stub(self) -> QWidget:
        try:
            from ui.candidature_history import CandidatureHistoryWidget
            return CandidatureHistoryWidget()
        except Exception:
            return self._stub("📋  Historique")

    def _build_profile_stub(self) -> QWidget:
        try:
            from ui.profile_editor import ProfileEditorWidget
            return ProfileEditorWidget()
        except Exception:
            return self._stub("👤  Mon Profil")

    def _build_coach_stub(self) -> QWidget:
        try:
            from ui.interview_simulator import InterviewSimulatorWidget
            return InterviewSimulatorWidget()
        except Exception:
            return self._stub("🤖  Coach IA")

    def _build_settings_stub(self) -> QWidget:
        return self._stub("⚙️  Paramètres")

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

    # ── Refresh DYNAMIQUE ─────────────────────────────────────────────────────
    def _refresh_all(self):
        self._refresh_kpi()
        self._refresh_recent_table()
        self._refresh_recent_offers_panel()

    def _refresh_kpi(self):
        try:
            from database.db_manager import get_session
            from database.models import Offre, Candidature, StatutCandidature
            from sqlalchemy import func
            from datetime import date

            with get_session() as db:
                deposees = db.query(Candidature).filter_by(
                    statut=StatutCandidature.deposee).count()
                attente = db.query(Candidature).filter_by(
                    statut=StatutCandidature.en_attente).count()
                offres_today = db.query(Offre).filter(
                    func.date(Offre.date_detection) == date.today()
                ).count()
                avg_claude = db.query(func.avg(Offre.score_claude)).scalar()
                avg_tfidf  = db.query(func.avg(Offre.score_tfidf)).scalar()
                if avg_claude:
                    score_moy = f"{avg_claude:.0f}%"
                elif avg_tfidf:
                    score_moy = f"{avg_tfidf * 100:.0f}%"
                else:
                    score_moy = "—"

                self.kpi_widgets["deposees"].setText(str(deposees))
                self.kpi_widgets["attente"].setText(str(attente))
                self.kpi_widgets["total"].setText(str(offres_today))
                self.kpi_widgets["score"].setText(score_moy)
        except Exception:
            for k, v in [("deposees","0"),("attente","0"),("total","0"),("score","—")]:
                self.kpi_widgets[k].setText(v)

    def _refresh_recent_table(self):
        try:
            from database.db_manager import get_session
            from database.models import Offre, Candidature

            with get_session() as db:
                offres = (db.query(Offre)
                          .order_by(Offre.date_detection.desc())
                          .limit(8).all())
                self.recent_table.setRowCount(len(offres))

                for row, o in enumerate(offres):
                    cand = (db.query(Candidature)
                            .filter_by(offre_id=o.id)
                            .order_by(Candidature.created_at.desc())
                            .first())
                    statut_str = cand.statut.value if cand else "nouvelle"

                    # Entreprise
                    cw = QWidget(); cw.setStyleSheet("background:transparent;")
                    cl2 = QHBoxLayout(cw); cl2.setContentsMargins(4,2,4,2); cl2.setSpacing(8)
                    cl2.addWidget(company_avatar(o.entreprise or "?", row))
                    n = QLabel(o.entreprise or "—")
                    n.setStyleSheet(f"color:{TEXT_PRI};font-size:12px;font-weight:600;")
                    cl2.addWidget(n); cl2.addStretch()
                    self.recent_table.setCellWidget(row, 0, cw)

                    # Poste
                    self.recent_table.setItem(row, 1, cell_item(o.titre[:55]))

                    # Source
                    sw = QWidget(); sw.setStyleSheet("background:transparent;")
                    sl2 = QHBoxLayout(sw); sl2.setContentsMargins(4,2,4,2); sl2.setSpacing(4)
                    ic2 = QLabel("🔗"); ic2.setStyleSheet("font-size:11px;")
                    sc2 = QLabel(o.source); sc2.setStyleSheet(f"color:{TEXT_SEC};font-size:11px;")
                    sl2.addWidget(ic2); sl2.addWidget(sc2); sl2.addStretch()
                    self.recent_table.setCellWidget(row, 2, sw)

                    # Score
                    s = o.score_claude if o.score_claude else (o.score_tfidf * 100)
                    spw = QWidget(); spw.setStyleSheet("background:transparent;")
                    spl = QHBoxLayout(spw); spl.setContentsMargins(4,2,4,2)
                    spl.addWidget(score_pill(s)); spl.addStretch()
                    self.recent_table.setCellWidget(row, 3, spw)

                    # Statut
                    stw = QWidget(); stw.setStyleSheet("background:transparent;")
                    stl = QHBoxLayout(stw); stl.setContentsMargins(4,2,4,2)
                    stl.addWidget(badge(statut_str)); stl.addStretch()
                    self.recent_table.setCellWidget(row, 4, stw)

                    # Date
                    date_str = o.date_detection.strftime("%d %b %Y") if o.date_detection else "—"
                    self.recent_table.setItem(row, 5, cell_item(date_str))

        except Exception:
            self.recent_table.setRowCount(0)

    def _refresh_recent_offers_panel(self):
        while self.recent_offers_layout.count():
            item = self.recent_offers_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            from database.db_manager import get_session
            from database.models import Offre

            with get_session() as db:
                offres = (db.query(Offre)
                          .order_by(Offre.date_detection.desc())
                          .limit(6).all())

                for i, o in enumerate(offres):
                    rw = QWidget(); rw.setStyleSheet("background:transparent;")
                    rl2 = QHBoxLayout(rw); rl2.setContentsMargins(0,0,0,0); rl2.setSpacing(8)
                    rl2.addWidget(company_avatar(o.entreprise or "?", i))
                    txt = QVBoxLayout(); txt.setSpacing(1)
                    nm = QLabel(o.entreprise or "—")
                    nm.setStyleSheet(f"color:{TEXT_PRI};font-size:12px;font-weight:600;")
                    ps = QLabel(o.titre[:28])
                    ps.setStyleSheet(f"color:{TEXT_SEC};font-size:11px;")
                    sr = QLabel(o.source)
                    sr.setStyleSheet(f"color:{TEXT_SEC};font-size:10px;")
                    txt.addWidget(nm); txt.addWidget(ps); txt.addWidget(sr)
                    rl2.addLayout(txt); rl2.addStretch()
                    dot = QLabel("●"); dot.setStyleSheet(f"color:{GREEN};font-size:10px;")
                    rl2.addWidget(dot)
                    self.recent_offers_layout.addWidget(rw)

                if not offres:
                    e = QLabel("Aucune offre.\nLancez un scan pour commencer.")
                    e.setStyleSheet(f"color:{TEXT_SEC};font-size:12px;")
                    e.setWordWrap(True)
                    self.recent_offers_layout.addWidget(e)

        except Exception:
            e = QLabel("Base de données non disponible.")
            e.setStyleSheet(f"color:{TEXT_SEC};font-size:12px;")
            self.recent_offers_layout.addWidget(e)

        self.recent_offers_layout.addStretch()

    # ── Worker ────────────────────────────────────────────────────────────────
    def _start_worker(self):
        try:
            from workers.scraper_worker import start_worker
            start_worker()
        except Exception:
            pass

    def _logout(self):
        reply = QMessageBox.question(
            self, "Déconnexion", "Voulez-vous vraiment vous déconnecter ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from services.auth_service import logout
                from workers.scraper_worker import stop_worker
                logout(); stop_worker()
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