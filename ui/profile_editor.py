"""
ui/profile_editor.py - Éditeur de profil
Thème : blanc / vert / bleu — professionnel et moderne
FlowLayout custom (QFlowLayout n'existe PAS dans PyQt6)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QFrame, QFileDialog, QMessageBox,
    QScrollArea, QComboBox, QSizePolicy, QInputDialog, QLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QRect, QPoint
from PyQt6.QtGui import QColor, QPainter, QLinearGradient, QBrush, QFont
from config import COLORS

# ── Palette harmonisée Fluent ─────────────────────────────────────────────────
BG_PAGE    = COLORS["bg"]
BG_CARD    = COLORS["bg_card"]
BG_INPUT   = COLORS["bg_input"]
BORDER     = COLORS["border"]
BORDER_FOC = COLORS["primary"]

GREEN      = COLORS["success"]
GREEN_LT   = f"{COLORS['success']}22"
GREEN_MID  = COLORS["success"]
BLUE       = COLORS["primary"]
BLUE_LT    = COLORS["primary_light"]
BLUE_DARK  = COLORS["primary_dark"]
PURPLE     = COLORS["purple"]

RED        = COLORS["danger"]
RED_LT     = f"{COLORS['danger']}18"

TEXT_PRI   = COLORS["text"]
TEXT_SEC   = COLORS["text_light"]
TEXT_MUT   = "#94a3b8"

TAG_BG     = COLORS["primary_light"]
TAG_BORDER = COLORS["primary"]
TAG_TEXT   = COLORS["primary_dark"]


# ── FlowLayout custom ─────────────────────────────────────────────────────────
class FlowLayout(QLayout):
    def __init__(self, parent=None, h_spacing=8, v_spacing=8):
        super().__init__(parent)
        self._items     = []
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index):
        return self._items.pop(index) if 0 <= index < len(self._items) else None

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), test=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        return size + QSize(m.left() + m.right(), m.top() + m.bottom())

    def _do_layout(self, rect, test):
        m = self.contentsMargins()
        x, y = rect.x() + m.left(), rect.y() + m.top()
        line_h = 0
        right_edge = rect.right() - m.right()
        for item in self._items:
            w = item.sizeHint()
            next_x = x + w.width()
            if next_x > right_edge and line_h > 0:
                x = rect.x() + m.left()
                y += line_h + self._v_spacing
                next_x = x + w.width()
                line_h = 0
            if not test:
                item.setGeometry(QRect(QPoint(x, y), w))
            x = next_x + self._h_spacing
            line_h = max(line_h, w.height())
        return y + line_h - rect.y() + m.bottom()


# ── Barre de progression dégradée vert→bleu ───────────────────────────────────
class GradientProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0
        self.setFixedHeight(10)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def setValue(self, v: int):
        self._value = max(0, min(100, v))
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        # Track
        p.setBrush(QBrush(QColor(BORDER)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, w, h, 5, 5)
        # Fill
        fw = int(w * self._value / 100)
        if fw > 0:
            grad = QLinearGradient(0, 0, fw, 0)
            grad.setColorAt(0, QColor(GREEN_MID))
            grad.setColorAt(1, QColor(BLUE))
            p.setBrush(QBrush(grad))
            p.drawRoundedRect(0, 0, fw, h, 5, 5)


# ── Tag compétence ────────────────────────────────────────────────────────────
class CompTag(QPushButton):
    removed = pyqtSignal(object)

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self._text = text
        self.setText(f"  {text}  ✕")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(30)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {TAG_BG};
                border: 1.5px solid {TAG_BORDER};
                border-radius: 15px;
                color: {TAG_TEXT};
                font-size: 12px;
                font-weight: 600;
                padding: 0 14px;
            }}
            QPushButton:hover {{
                background-color: {RED_LT};
                border-color: {RED};
                color: {RED};
            }}
        """)
        self.clicked.connect(lambda: self.removed.emit(self))


# ── Widget Tags avec FlowLayout ───────────────────────────────────────────────
class TagsWidget(QWidget):
    changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tags = []
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {BG_INPUT};
                border: 1.5px solid {BORDER};
                border-radius: 10px;
            }}
        """)
        self.setMinimumHeight(60)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 8, 10, 8)
        outer.setSpacing(8)

        # Zone flow
        self._flow_widget = QWidget()
        self._flow_widget.setStyleSheet("background: transparent; border: none;")
        self._flow = FlowLayout(self._flow_widget, 6, 6)
        outer.addWidget(self._flow_widget)

        # Bouton ajouter
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        self._plus = QPushButton("＋  Ajouter une compétence")
        self._plus.setFixedHeight(34)
        self._plus.setCursor(Qt.CursorShape.PointingHandCursor)
        self._plus.setStyleSheet(f"""
            QPushButton {{
                background-color: {BLUE_LT};
                border: 1.5px dashed {BLUE};
                border-radius: 8px;
                color: {BLUE};
                font-size: 12px;
                font-weight: 600;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background-color: {BLUE};
                color: white;
                border-style: solid;
            }}
        """)
        self._plus.clicked.connect(self._add_tag)
        btn_row.addWidget(self._plus)
        btn_row.addStretch()
        outer.addLayout(btn_row)

    def add_tag(self, text: str):
        tag = CompTag(text)
        tag.removed.connect(self._remove_tag)
        self._tags.append(tag)
        self._flow.addWidget(tag)
        self._flow_widget.updateGeometry()
        self.updateGeometry()
        self.changed.emit()

    def _remove_tag(self, tag):
        for i in range(self._flow.count()):
            item = self._flow.itemAt(i)
            if item and item.widget() == tag:
                self._flow.takeAt(i)
                break
        tag.hide()
        tag.deleteLater()
        if tag in self._tags:
            self._tags.remove(tag)
        self._flow_widget.updateGeometry()
        self.updateGeometry()
        self.changed.emit()

    def _add_tag(self):
        text, ok = QInputDialog.getText(self, "Ajouter compétence", "Compétence :")
        if ok and text.strip():
            self.add_tag(text.strip())

    def get_tags(self) -> list:
        return [t._text for t in self._tags]

    def set_tags(self, tags: list):
        for t in list(self._tags):
            for i in range(self._flow.count()):
                item = self._flow.itemAt(i)
                if item and item.widget() == t:
                    self._flow.takeAt(i)
                    break
            t.hide()
            t.deleteLater()
        self._tags.clear()
        for text in tags:
            self.add_tag(text)


# ── Thread parsing CV ─────────────────────────────────────────────────────────
class CVParseThread(QThread):
    done  = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, cv_path: str):
        super().__init__()
        self.cv_path = cv_path

    def run(self):
        try:
            from services.profile_service import parse_cv_text
            from services.generator_service import parse_cv_with_claude
            raw    = parse_cv_text(self.cv_path)
            result = parse_cv_with_claude(raw.get("raw_text", "")) or {}
            result["cv_path"] = self.cv_path
            self.done.emit(result)
        except Exception as e:
            self.error.emit(str(e))


# ── Helpers UI ────────────────────────────────────────────────────────────────
def _section_card(title: str) -> tuple:
    """Retourne (card QFrame, layout intérieur QVBoxLayout)"""
    card = QFrame()
    card.setStyleSheet(f"""
        QFrame {{
            background-color: {BG_CARD};
            border: 1px solid {BORDER};
            border-radius: 12px;
        }}
    """)
    inner = QVBoxLayout(card)
    inner.setContentsMargins(20, 16, 20, 20)
    inner.setSpacing(10)

    # Titre de section avec accent vert
    hdr = QHBoxLayout()
    accent = QFrame()
    accent.setFixedSize(4, 18)
    accent.setStyleSheet(f"background-color: {GREEN}; border-radius: 2px; border: none;")
    lbl = QLabel(title)
    lbl.setStyleSheet(f"""
        color: {TEXT_PRI}; font-size: 14px; font-weight: 700;
        background: transparent; border: none;
    """)
    hdr.addWidget(accent)
    hdr.addSpacing(8)
    hdr.addWidget(lbl)
    hdr.addStretch()
    inner.addLayout(hdr)

    sep = QFrame()
    sep.setFrameShape(QFrame.Shape.HLine)
    sep.setStyleSheet(f"background-color: {BORDER}; max-height: 1px; border: none;")
    inner.addWidget(sep)

    return card, inner


def _label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"""
        color: {TEXT_SEC};
        font-size: 12px;
        font-weight: 600;
        background: transparent;
        border: none;
        letter-spacing: 0.3px;
    """)
    return lbl


def _field(placeholder: str = "") -> QLineEdit:
    f = QLineEdit()
    f.setPlaceholderText(placeholder)
    f.setMinimumHeight(40)
    f.setStyleSheet(f"""
        QLineEdit {{
            background-color: {BG_INPUT};
            border: 1.5px solid {BORDER};
            border-radius: 8px;
            color: {TEXT_PRI};
            font-size: 13px;
            padding: 0 14px;
        }}
        QLineEdit:focus {{
            border-color: {BLUE};
            background-color: white;
        }}
        QLineEdit[readOnly="true"] {{
            color: {TEXT_SEC};
            background-color: {BG_INPUT};
        }}
    """)
    return f


def _textarea(placeholder: str = "", rows: int = 4) -> QTextEdit:
    t = QTextEdit()
    t.setPlaceholderText(placeholder)
    h = rows * 24 + 16
    t.setMinimumHeight(h)
    t.setMaximumHeight(h)
    t.setStyleSheet(f"""
        QTextEdit {{
            background-color: {BG_INPUT};
            border: 1.5px solid {BORDER};
            border-radius: 8px;
            color: {TEXT_PRI};
            font-size: 13px;
            padding: 10px 14px;
            line-height: 1.5;
        }}
        QTextEdit:focus {{
            border-color: {BLUE};
            background-color: white;
        }}
    """)
    return t


def _combo(options: list = None) -> QComboBox:
    c = QComboBox()
    if options:
        c.addItems(options)
    c.setMinimumHeight(40)
    c.setStyleSheet(f"""
        QComboBox {{
            background-color: {BG_INPUT};
            border: 1.5px solid {BORDER};
            border-radius: 8px;
            color: {TEXT_PRI};
            font-size: 13px;
            padding: 0 14px;
        }}
        QComboBox:focus {{ border-color: {BLUE}; }}
        QComboBox::drop-down {{ border: none; width: 28px; }}
        QComboBox QAbstractItemView {{
            background-color: white;
            border: 1px solid {BORDER};
            color: {TEXT_PRI};
            selection-background-color: {BLUE_LT};
            selection-color: {BLUE_DARK};
            outline: none;
        }}
    """)
    return c


# ════════════════════════════════════════════════════════════════════════════
# Widget principal
# ════════════════════════════════════════════════════════════════════════════
class ProfileEditorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._current_profil_id = None
        self._profils           = []
        self._setup_ui()
        self._load_profils()

    def _setup_ui(self):
        self.setStyleSheet(f"background-color: {BG_PAGE};")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background-color: {BG_PAGE}; }}
            QScrollBar:vertical {{
                background: {BORDER}; width: 6px; border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: #cbd5e1; border-radius: 3px; min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {BLUE}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        page = QWidget()
        page.setStyleSheet(f"background-color: {BG_PAGE};")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(32, 28, 32, 32)
        lay.setSpacing(20)

        # ── Header ───────────────────────────────────────────────────────────
        header_card = QFrame()
        header_card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {GREEN}, stop:1 {BLUE}
                );
                border-radius: 14px;
                border: none;
            }}
        """)
        header_card.setFixedHeight(90)
        hl = QHBoxLayout(header_card)
        hl.setContentsMargins(24, 0, 24, 0)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        t1 = QLabel("Éditeur de Profil")
        t1.setStyleSheet("color: white; font-size: 22px; font-weight: 700; background: transparent;")
        t2 = QLabel("Complétez votre profil pour maximiser vos chances")
        t2.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 13px; background: transparent;")
        title_col.addWidget(t1)
        title_col.addWidget(t2)
        hl.addLayout(title_col)
        hl.addStretch()

        # Progression dans le header
        prog_col = QVBoxLayout()
        prog_col.setSpacing(6)
        prog_col.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.prog_val = QLabel("0%")
        self.prog_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.prog_val.setStyleSheet(
            "color: white; font-size: 28px; font-weight: 800; background: transparent;"
        )
        prog_lbl = QLabel("Profil complet")
        prog_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        prog_lbl.setStyleSheet(
            "color: rgba(255,255,255,0.8); font-size: 11px; font-weight: 600; background: transparent;"
        )
        self.prog_bar = GradientProgressBar()
        self.prog_bar.setFixedWidth(160)

        # Override la couleur de la barre pour qu'elle soit blanche dans le header
        prog_col.addWidget(self.prog_val)
        prog_col.addWidget(prog_lbl)
        prog_col.addWidget(self.prog_bar, alignment=Qt.AlignmentFlag.AlignCenter)
        hl.addLayout(prog_col)

        lay.addWidget(header_card)

        # ── Sélecteur profil ─────────────────────────────────────────────────
        sel_card = QFrame()
        sel_card.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
        """)
        sel_lay = QHBoxLayout(sel_card)
        sel_lay.setContentsMargins(16, 12, 16, 12)
        sel_lay.setSpacing(12)

        sel_icon = QLabel("👤")
        sel_icon.setStyleSheet("font-size: 18px; background: transparent;")
        sel_lbl = QLabel("Profil actif :")
        sel_lbl.setStyleSheet(f"color: {TEXT_SEC}; font-size: 13px; font-weight: 600; background: transparent;")

        self.profil_combo = _combo()
        self.profil_combo.setMinimumWidth(240)
        self.profil_combo.setMaximumWidth(320)
        self.profil_combo.currentIndexChanged.connect(self._on_profil_changed)

        btn_new = QPushButton("＋ Nouveau profil")
        btn_new.setFixedHeight(36)
        btn_new.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_new.setStyleSheet(f"""
            QPushButton {{
                background-color: {GREEN_LT};
                border: 1.5px solid {GREEN};
                border-radius: 8px;
                color: {GREEN};
                font-size: 12px;
                font-weight: 700;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background-color: {GREEN};
                color: white;
            }}
        """)
        btn_new.clicked.connect(self._new_profil)

        sel_lay.addWidget(sel_icon)
        sel_lay.addWidget(sel_lbl)
        sel_lay.addWidget(self.profil_combo)
        sel_lay.addWidget(btn_new)
        sel_lay.addStretch()
        lay.addWidget(sel_card)

        # ── Grille 2 colonnes ─────────────────────────────────────────────────
        grid = QHBoxLayout()
        grid.setSpacing(20)

        # ── Colonne GAUCHE ────────────────────────────────────────────────────
        left_col = QVBoxLayout()
        left_col.setSpacing(16)

        # Card : Informations personnelles
        card_info, cl_info = _section_card("Informations Personnelles")
        cl_info.addWidget(_label("TITRE DU PROFIL"))
        self.f_titre = _field("Ex: Étudiant Data Science M2")
        self.f_titre.textChanged.connect(self._update_progress)
        cl_info.addWidget(self.f_titre)
        left_col.addWidget(card_info)

        # Card : Compétences
        card_comp, cl_comp = _section_card("Compétences Techniques")
        hint = QLabel("Cliquez sur un tag pour le supprimer")
        hint.setStyleSheet(f"color: {TEXT_MUT}; font-size: 11px; background: transparent;")
        cl_comp.addWidget(hint)
        self.tags_widget = TagsWidget()
        self.tags_widget.changed.connect(self._update_progress)
        cl_comp.addWidget(self.tags_widget)
        left_col.addWidget(card_comp)

        # Card : Expérience
        card_exp, cl_exp = _section_card("Expérience Professionnelle")
        cl_exp.addWidget(_label("DÉTAILS DE VOS EXPÉRIENCES"))
        self.f_experience = _textarea(
            "Ex: Stage Data Analyst, OCP Group, Juin–Août 2023\n"
            "Projet ML : prédiction churn — résultat : 92% accuracy",
            rows=6
        )
        self.f_experience.textChanged.connect(self._update_progress)
        cl_exp.addWidget(self.f_experience)
        left_col.addWidget(card_exp)
        left_col.addStretch()

        # ── Colonne DROITE ────────────────────────────────────────────────────
        right_col = QVBoxLayout()
        right_col.setSpacing(16)

        # Card : Formation
        card_form, cl_form = _section_card("Formation Académique")
        cl_form.addWidget(_label("DIPLÔMES ET FORMATIONS"))
        self.f_formation = _textarea(
            "Ex: Master Data Science, École Centrale Casablanca, 2024\n"
            "Bachelor Informatique, ENSA Rabat, 2022",
            rows=5
        )
        self.f_formation.textChanged.connect(self._update_progress)
        cl_form.addWidget(self.f_formation)
        right_col.addWidget(card_form)

        # Card : Langues + Localisation
        card_lang, cl_lang = _section_card("Langues & Localisation")
        cl_lang.addWidget(_label("LANGUES PARLÉES"))
        self.f_langues = _field("Ex: Français (C1), Anglais (B2), Arabe (natif)")
        self.f_langues.textChanged.connect(self._update_progress)
        cl_lang.addWidget(self.f_langues)
        cl_lang.addSpacing(4)
        cl_lang.addWidget(_label("LOCALISATION PRÉFÉRÉE"))
        self.f_localisation = _field("Ex: Casablanca, Maroc")
        self.f_localisation.textChanged.connect(self._update_progress)
        cl_lang.addWidget(self.f_localisation)
        right_col.addWidget(card_lang)

        # Card : CV + Disponibilité
        card_cv, cl_cv = _section_card("CV & Disponibilité")

        cl_cv.addWidget(_label("TÉLÉCHARGER VOTRE CV (PDF)"))

        # Bouton upload stylé
        upload_row = QHBoxLayout()
        upload_row.setSpacing(10)

        self.f_cv = _field("Aucun fichier sélectionné…")
        self.f_cv.setReadOnly(True)

        btn_browse = QPushButton("📂  Parcourir")
        btn_browse.setFixedHeight(40)
        btn_browse.setMinimumWidth(120)
        btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_browse.setStyleSheet(f"""
            QPushButton {{
                background-color: {BLUE};
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 13px;
                font-weight: 700;
                padding: 0 18px;
            }}
            QPushButton:hover {{
                background-color: {BLUE_DARK};
            }}
            QPushButton:pressed {{
                background-color: #1e40af;
            }}
        """)
        btn_browse.clicked.connect(self._browse_cv)

        btn_parse = QPushButton("🤖  Analyser avec IA")
        btn_parse.setFixedHeight(40)
        btn_parse.setMinimumWidth(150)
        btn_parse.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_parse.setStyleSheet(f"""
            QPushButton {{
                background-color: {GREEN_LT};
                border: 1.5px solid {GREEN};
                border-radius: 8px;
                color: {GREEN};
                font-size: 13px;
                font-weight: 700;
                padding: 0 18px;
            }}
            QPushButton:hover {{
                background-color: {GREEN};
                color: white;
            }}
        """)
        btn_parse.clicked.connect(self._parse_cv)

        upload_row.addWidget(self.f_cv)
        upload_row.addWidget(btn_browse)
        upload_row.addWidget(btn_parse)
        cl_cv.addLayout(upload_row)

        self.parse_status = QLabel("")
        self.parse_status.setStyleSheet(
            f"color: {TEXT_SEC}; font-size: 12px; background: transparent;"
        )
        cl_cv.addWidget(self.parse_status)

        cl_cv.addSpacing(4)
        cl_cv.addWidget(_label("DISPONIBILITÉ"))
        self.f_disponibilite = _combo([
            "Immédiate", "Juillet 2025", "Septembre 2025",
            "Janvier 2026", "Autre"
        ])
        cl_cv.addWidget(self.f_disponibilite)
        right_col.addWidget(card_cv)
        right_col.addStretch()

        grid.addLayout(left_col, 1)
        grid.addLayout(right_col, 1)
        lay.addLayout(grid)

        # ── Barre d'actions ───────────────────────────────────────────────────
        action_card = QFrame()
        action_card.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)
        action_lay = QHBoxLayout(action_card)
        action_lay.setContentsMargins(24, 16, 24, 16)
        action_lay.setSpacing(12)

        self.save_status = QLabel("")
        self.save_status.setStyleSheet(
            f"color: {GREEN}; font-size: 13px; font-weight: 600; background: transparent;"
        )

        btn_del = QPushButton("🗑  Supprimer ce profil")
        btn_del.setFixedHeight(44)
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.setStyleSheet(f"""
            QPushButton {{
                background-color: {RED_LT};
                border: 1.5px solid {RED};
                border-radius: 10px;
                color: {RED};
                font-size: 13px;
                font-weight: 600;
                padding: 0 22px;
            }}
            QPushButton:hover {{
                background-color: {RED};
                color: white;
            }}
        """)
        btn_del.clicked.connect(self._delete_profil)

        self.btn_save = QPushButton("✓  Enregistrer le profil")
        self.btn_save.setFixedHeight(44)
        self.btn_save.setMinimumWidth(220)
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {GREEN_MID}, stop:1 {BLUE}
                );
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 700;
                padding: 0 28px;
            }}
            QPushButton:hover {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #16a34a, stop:1 {BLUE_DARK}
                );
            }}
        """)
        self.btn_save.clicked.connect(self._save)

        action_lay.addWidget(self.save_status)
        action_lay.addStretch()
        action_lay.addWidget(btn_del)
        action_lay.addWidget(self.btn_save)
        lay.addWidget(action_card)

        scroll.setWidget(page)
        root.addWidget(scroll)

    # ── Progress ──────────────────────────────────────────────────────────────
    def _update_progress(self):
        fields = [
            self.f_titre.text(),
            self.f_langues.text(),
            self.f_localisation.text(),
            self.f_formation.toPlainText(),
            self.f_experience.toPlainText(),
        ]
        filled   = sum(1 for f in fields if f.strip())
        has_tags = len(self.tags_widget.get_tags()) > 0
        has_cv   = bool(self.f_cv.text().strip())
        score    = int((filled + has_tags + has_cv) / (len(fields) + 2) * 100)
        self.prog_bar.setValue(score)
        self.prog_val.setText(f"{score}%")

    # ── Profils ───────────────────────────────────────────────────────────────
    def _load_profils(self):
        try:
            from services.profile_service import get_profils
            self.profil_combo.blockSignals(True)
            self.profil_combo.clear()
            self._profils = get_profils()
            for p in self._profils:
                self.profil_combo.addItem(p.titre, p.id)
            self.profil_combo.blockSignals(False)
            if self._profils:
                self._load_profil_data(self._profils[0])
        except Exception:
            pass

    def _on_profil_changed(self, idx):
        if 0 <= idx < len(self._profils):
            self._load_profil_data(self._profils[idx])

    def _load_profil_data(self, profil):
        self._current_profil_id = profil.id
        self.f_titre.setText(profil.titre or "")
        self.f_localisation.setText(profil.localisation or "")
        self.f_langues.setText(profil.langues or "")
        self.f_cv.setText(profil.cv_path or "")
        self.f_formation.setPlainText(profil.formation or "")
        self.f_experience.setPlainText(profil.experience or "")
        idx = self.f_disponibilite.findText(profil.disponibilite or "")
        if idx >= 0:
            self.f_disponibilite.setCurrentIndex(idx)
        self.tags_widget.set_tags(getattr(profil, "competences_list", []))
        self._update_progress()

    # ── CV ────────────────────────────────────────────────────────────────────
    def _browse_cv(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Sélectionner un CV", "", "PDF (*.pdf)")
        if path:
            self.f_cv.setText(path)
            self._update_progress()

    def _parse_cv(self):
        cv_path = self.f_cv.text().strip()
        if not cv_path:
            QMessageBox.warning(self, "CV manquant",
                                "Veuillez d'abord sélectionner un CV PDF.")
            return
        self.parse_status.setText("⏳ Analyse du CV en cours…")
        self._cv_thread = CVParseThread(cv_path)
        self._cv_thread.done.connect(self._on_cv_parsed)
        self._cv_thread.error.connect(
            lambda e: self.parse_status.setText(f"❌ Erreur : {e}"))
        self._cv_thread.start()

    def _on_cv_parsed(self, data: dict):
        if not data:
            self.parse_status.setText("❌ Impossible d'analyser le CV.")
            return
        if data.get("titre"):      self.f_titre.setText(data["titre"])
        if data.get("formation"):  self.f_formation.setPlainText(data["formation"])
        if data.get("experience"): self.f_experience.setPlainText(data["experience"])
        if data.get("langues"):    self.f_langues.setText(data["langues"])
        if data.get("competences"):
            self.tags_widget.set_tags(data["competences"])
        self.parse_status.setText("✅ CV analysé et formulaire pré-rempli !")
        self._update_progress()

    # ── Save ──────────────────────────────────────────────────────────────────
    def _save(self):
        if not self._current_profil_id:
            QMessageBox.warning(self, "Aucun profil", "Créez d'abord un profil.")
            return
        try:
            from services.profile_service import update_profil
            ok, msg = update_profil(self._current_profil_id, {
                "titre":         self.f_titre.text().strip(),
                "competences":   self.tags_widget.get_tags(),
                "formation":     self.f_formation.toPlainText(),
                "experience":    self.f_experience.toPlainText(),
                "langues":       self.f_langues.text().strip(),
                "disponibilite": self.f_disponibilite.currentText(),
                "localisation":  self.f_localisation.text().strip(),
                "cv_path":       self.f_cv.text().strip(),
            })
            self.save_status.setText("✅ " + msg if ok else f"❌ {msg}")
        except Exception as e:
            self.save_status.setText(f"❌ Erreur : {e}")

    def _new_profil(self):
        name, ok = QInputDialog.getText(
            self, "Nouveau profil", "Nom du profil :")
        if ok and name.strip():
            try:
                from services.profile_service import create_profil
                create_profil(name.strip())
                self._load_profils()
            except Exception as e:
                QMessageBox.warning(self, "Erreur", str(e))

    def _delete_profil(self):
        if not self._current_profil_id:
            return
        reply = QMessageBox.question(
            self, "Supprimer", "Supprimer ce profil ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from services.profile_service import delete_profil
                delete_profil(self._current_profil_id)
                self._load_profils()
            except Exception as e:
                QMessageBox.warning(self, "Erreur", str(e))