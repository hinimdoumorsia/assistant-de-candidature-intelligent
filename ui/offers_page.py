"""
ui/offers_page.py - Page des offres de stage
Thème : blanc / vert / bleu — professionnel et moderne
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QFrame, QLineEdit, QMessageBox, QSplitter, QTextEdit, QProgressDialog,
    QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QDesktopServices, QFont
from PyQt6.QtCore import QUrl

# ── Palette ───────────────────────────────────────────────────────────────────
BG_PAGE    = "#f0f4f8"
BG_CARD    = "#ffffff"
BG_INPUT   = "#f8fafc"
BORDER     = "#e2e8f0"

GREEN      = "#16a34a"
GREEN_LT   = "#dcfce7"
BLUE       = "#3b82f6"
BLUE_LT    = "#dbeafe"
BLUE_DARK  = "#1d4ed8"
YELLOW     = "#eab308"

TEXT_PRI   = "#0f172a"
TEXT_SEC   = "#334155"
TEXT_MUT   = "#64748b"

SOURCE_COLORS = {
    "indeed_rss": "#ff6600",
    "rekrute": "#e31e24",
    "emploi_ma": "#2e8b57",
    "bayt": "#0084d1",
    "adzuna": "#00a86b",
}


class GenerateCandidatureThread(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, offre_id: int, profil_id: int, variante: int = 1):
        super().__init__()
        self.offre_id = offre_id
        self.profil_id = profil_id
        self.variante = variante
    
    def run(self):
        try:
            from services.generator_service import generate_lettre_motivation
            from services.profile_service import get_profil_by_id
            from database.db_manager import get_session
            from database.models import Offre, Candidature, StatutCandidature
            from config import EXPORTS_DIR
            from datetime import datetime
            import os
            
            with get_session() as db:
                offre = db.query(Offre).filter(Offre.id == self.offre_id).first()
                profil = get_profil_by_id(self.profil_id)
                
                if not offre or not profil:
                    self.error.emit("Offre ou profil non trouvé")
                    return
                
                lettre = generate_lettre_motivation(profil, offre, self.variante)
                
                if not lettre:
                    self.error.emit("Échec de génération de la lettre")
                    return
                
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                lettre_filename = f"lettre_{offre.id}_{self.variante}_{ts}.txt"
                lettre_path = str(EXPORTS_DIR / lettre_filename)
                
                os.makedirs(EXPORTS_DIR, exist_ok=True)
                with open(lettre_path, 'w', encoding='utf-8') as f:
                    f.write(lettre)
                
                candidature = Candidature(
                    profil_id=self.profil_id,
                    offre_id=self.offre_id,
                    lettre_path=lettre_path,
                    variante_choisie=self.variante,
                    statut=StatutCandidature.EN_ATTENTE,
                    created_at=datetime.now()
                )
                db.add(candidature)
                db.commit()
                
                self.finished.emit({
                    "candidature_id": candidature.id,
                    "lettre_path": lettre_path,
                    "offre_titre": offre.titre
                })
                
        except Exception as e:
            self.error.emit(str(e))


class OffersPageWidget(QWidget):
    
    def __init__(self):
        super().__init__()
        self._current_profil_id = None
        self._profils = []
        self._current_offre = None
        self._offres_data = []
        self._setup_ui()
        self._load_profils()
        self._load_offres()
    
    def _setup_ui(self):
        self.setStyleSheet(f"background-color: {BG_PAGE};")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 32)
        main_layout.setSpacing(20)
        
        # HEADER
        header_card = QFrame()
        header_card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {GREEN},stop:1 {BLUE});
                border-radius: 14px;
                border: none;
            }}
        """)
        header_card.setFixedHeight(80)
        hl = QHBoxLayout(header_card)
        hl.setContentsMargins(24, 0, 24, 0)
        
        title_col = QVBoxLayout()
        t1 = QLabel("Offres de Stage")
        t1.setStyleSheet("color: white; font-size: 22px; font-weight: 700;")
        t2 = QLabel("Découvrez les offres correspondant à votre profil")
        t2.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 13px;")
        title_col.addWidget(t1)
        title_col.addWidget(t2)
        hl.addLayout(title_col)
        hl.addStretch()
        
        self.count_label = QLabel("0 offre(s)")
        self.count_label.setStyleSheet("color: white; font-size: 18px; font-weight: 700; background: rgba(255,255,255,0.2); padding: 6px 16px; border-radius: 20px;")
        hl.addWidget(self.count_label)
        main_layout.addWidget(header_card)
        
        # PROFIL
        profil_card = QFrame()
        profil_card.setStyleSheet(f"background-color: {BG_CARD}; border: 1px solid {BORDER}; border-radius: 12px;")
        profil_layout = QHBoxLayout(profil_card)
        profil_layout.setContentsMargins(20, 12, 20, 12)
        
        profil_label = QLabel("Profil actif :")
        profil_label.setStyleSheet(f"color: {TEXT_SEC}; font-weight: 600;")
        profil_layout.addWidget(profil_label)
        
        self.profil_combo = QComboBox()
        self.profil_combo.setMinimumWidth(250)
        self.profil_combo.setStyleSheet(self._combo_style())
        self.profil_combo.currentIndexChanged.connect(self._on_profil_changed)
        profil_layout.addWidget(self.profil_combo)
        profil_layout.addStretch()
        
        refresh_btn = QPushButton("Actualiser")
        refresh_btn.setStyleSheet(self._secondary_btn_style())
        refresh_btn.clicked.connect(self._load_offres)
        profil_layout.addWidget(refresh_btn)
        main_layout.addWidget(profil_card)
        
        # FILTRES
        filters_card = QFrame()
        filters_card.setStyleSheet(f"background-color: {BG_CARD}; border: 1px solid {BORDER}; border-radius: 12px;")
        filters_layout = QHBoxLayout(filters_card)
        filters_layout.setContentsMargins(20, 12, 20, 12)
        filters_layout.setSpacing(15)
        
        filter_label = QLabel("Filtrer :")
        filter_label.setStyleSheet(f"color: {TEXT_SEC}; font-weight: 600;")
        filters_layout.addWidget(filter_label)
        
        self.source_filter = QComboBox()
        self.source_filter.addItems(["Toutes les sources", "indeed_rss", "rekrute", "emploi_ma", "bayt", "adzuna"])
        self.source_filter.setStyleSheet(self._combo_style())
        self.source_filter.currentIndexChanged.connect(self._load_offres)
        filters_layout.addWidget(self.source_filter)
        
        self.score_filter = QComboBox()
        self.score_filter.addItems(["Tous scores", "≥ 80%", "≥ 60%", "≥ 40%"])
        self.score_filter.setStyleSheet(self._combo_style())
        self.score_filter.currentIndexChanged.connect(self._load_offres)
        filters_layout.addWidget(self.score_filter)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher par titre, entreprise...")
        self.search_input.setMinimumWidth(250)
        self.search_input.setStyleSheet(self._input_style())
        self.search_input.textChanged.connect(self._load_offres)
        filters_layout.addWidget(self.search_input)
        filters_layout.addStretch()
        main_layout.addWidget(filters_card)
        
        # SPLITTER
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet(f"QSplitter::handle {{ background-color: {BORDER}; }}")
        
        # TABLEAU
        table_frame = QFrame()
        table_frame.setStyleSheet(f"background-color: {BG_CARD}; border: 1px solid {BORDER}; border-radius: 12px;")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        self.offres_table = QTableWidget(0, 6)
        self.offres_table.setHorizontalHeaderLabels(["Entreprise", "Poste", "Source", "Score", "Date", ""])
        self.offres_table.setStyleSheet(self._table_style())
        self.offres_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.offres_table.verticalHeader().setVisible(False)
        self.offres_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.offres_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.offres_table.itemSelectionChanged.connect(self._on_offre_selected)
        table_layout.addWidget(self.offres_table)
        splitter.addWidget(table_frame)
        
        # PANNAU DETAILS
        details_frame = QFrame()
        details_frame.setMinimumWidth(450)
        details_frame.setMaximumWidth(550)
        details_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 2px solid {BLUE};
                border-radius: 12px;
            }}
        """)
        
        details_scroll = QScrollArea()
        details_scroll.setWidgetResizable(True)
        details_scroll.setFrameShape(QFrame.Shape.NoFrame)
        details_scroll.setStyleSheet("background: transparent; border: none;")
        
        details_content = QWidget()
        details_layout = QVBoxLayout(details_content)
        details_layout.setContentsMargins(20, 20, 20, 20)
        details_layout.setSpacing(15)
        
        # Titre "DETAILS DE L'OFFRE" avec fond vert
        header_detail = QFrame()
        header_detail.setStyleSheet(f"""
            QFrame {{
                background-color: {GREEN};
                border-radius: 8px;
                border: none;
            }}
        """)
        header_detail.setFixedHeight(45)
        header_detail_layout = QHBoxLayout(header_detail)
        header_detail_layout.setContentsMargins(15, 0, 15, 0)
        header_text = QLabel("DETAILS DE L'OFFRE")
        header_text.setStyleSheet("color: white; font-size: 14px; font-weight: 800;")
        header_detail_layout.addWidget(header_text)
        header_detail_layout.addStretch()
        details_layout.addWidget(header_detail)
        
        # Titre de l'offre
        self.details_title = QLabel("Aucune offre sélectionnée")
        self.details_title.setWordWrap(True)
        self.details_title.setMinimumHeight(50)
        self.details_title.setStyleSheet(f"color: {TEXT_PRI}; font-size: 16px; font-weight: 800;")
        details_layout.addWidget(self.details_title)
        
        # Entreprise
        company_frame = QFrame()
        company_frame.setStyleSheet(f"background-color: {BG_INPUT}; border-radius: 8px; border: 1px solid {BORDER};")
        company_frame.setMinimumHeight(45)
        company_layout = QHBoxLayout(company_frame)
        company_layout.setContentsMargins(12, 10, 12, 10)
        company_label = QLabel("Entreprise :")
        company_label.setStyleSheet(f"color: {TEXT_SEC}; font-weight: 700; font-size: 12px;")
        self.details_company = QLabel("")
        self.details_company.setStyleSheet(f"color: {TEXT_PRI}; font-size: 13px; font-weight: 500;")
        company_layout.addWidget(company_label)
        company_layout.addWidget(self.details_company)
        company_layout.addStretch()
        details_layout.addWidget(company_frame)
        
        # Localisation
        loc_frame = QFrame()
        loc_frame.setStyleSheet(f"background-color: {BG_INPUT}; border-radius: 8px; border: 1px solid {BORDER};")
        loc_frame.setMinimumHeight(45)
        loc_layout = QHBoxLayout(loc_frame)
        loc_layout.setContentsMargins(12, 10, 12, 10)
        loc_label = QLabel("Localisation :")
        loc_label.setStyleSheet(f"color: {TEXT_SEC}; font-weight: 700; font-size: 12px;")
        self.details_location = QLabel("")
        self.details_location.setStyleSheet(f"color: {TEXT_PRI}; font-size: 13px; font-weight: 500;")
        loc_layout.addWidget(loc_label)
        loc_layout.addWidget(self.details_location)
        loc_layout.addStretch()
        details_layout.addWidget(loc_frame)
        
        # Score
        score_frame = QFrame()
        score_frame.setStyleSheet(f"background-color: {BG_INPUT}; border-radius: 8px; border: 1px solid {BORDER};")
        score_frame.setMinimumHeight(45)
        score_layout = QHBoxLayout(score_frame)
        score_layout.setContentsMargins(12, 10, 12, 10)
        score_label = QLabel("Score :")
        score_label.setStyleSheet(f"color: {TEXT_SEC}; font-weight: 700; font-size: 12px;")
        self.details_score = QLabel("")
        self.details_score.setStyleSheet(f"color: {GREEN}; font-size: 13px; font-weight: 800;")
        score_layout.addWidget(score_label)
        score_layout.addWidget(self.details_score)
        score_layout.addStretch()
        details_layout.addWidget(score_frame)
        
        # DESCRIPTION
        desc_label = QLabel("DESCRIPTION")
        desc_label.setStyleSheet(f"color: {GREEN}; font-size: 12px; font-weight: 800; margin-top: 5px;")
        details_layout.addWidget(desc_label)
        
        self.details_desc = QTextEdit()
        self.details_desc.setReadOnly(True)
        self.details_desc.setMinimumHeight(180)
        self.details_desc.setMaximumHeight(250)
        self.details_desc.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BG_INPUT};
                border: 2px solid {GREEN};
                border-radius: 8px;
                padding: 12px;
                color: {TEXT_PRI};
                font-size: 12px;
                font-weight: 500;
            }}
        """)
        details_layout.addWidget(self.details_desc)
        
        details_layout.addStretch()
        
        # BOUTONS
        btn_container = QFrame()
        btn_container.setStyleSheet(f"background-color: {BG_INPUT}; border-radius: 10px; border: 1px solid {BORDER};")
        btn_layout = QVBoxLayout(btn_container)
        btn_layout.setContentsMargins(15, 15, 15, 15)
        btn_layout.setSpacing(12)
        
        self.apply_btn = QPushButton("Postuler a cette offre")
        self.apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.apply_btn.setEnabled(False)
        self.apply_btn.setMinimumHeight(48)
        self.apply_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {GREEN};
                border-radius: 8px;
                color: white;
                font-size: 13px;
                font-weight: 800;
            }}
            QPushButton:hover {{ background-color: #15803d; }}
            QPushButton:disabled {{ background-color: {TEXT_MUT}; }}
        """)
        self.apply_btn.clicked.connect(self._postuler)
        btn_layout.addWidget(self.apply_btn)
        
        self.interview_btn = QPushButton("Simuler un entretien")
        self.interview_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.interview_btn.setEnabled(False)
        self.interview_btn.setMinimumHeight(48)
        self.interview_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BLUE};
                border-radius: 8px;
                color: white;
                font-size: 13px;
                font-weight: 800;
            }}
            QPushButton:hover {{ background-color: {BLUE_DARK}; }}
            QPushButton:disabled {{ background-color: {TEXT_MUT}; }}
        """)
        self.interview_btn.clicked.connect(self._simulate_interview)
        btn_layout.addWidget(self.interview_btn)
        
        self.url_btn = QPushButton("Voir l'offre originale")
        self.url_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.url_btn.setEnabled(False)
        self.url_btn.setMinimumHeight(42)
        self.url_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 2px solid {BLUE};
                border-radius: 8px;
                color: {BLUE};
                font-size: 12px;
                font-weight: 700;
            }}
            QPushButton:hover {{ background-color: {BLUE_LT}; color: {BLUE_DARK}; }}
            QPushButton:disabled {{ border-color: {TEXT_MUT}; color: {TEXT_MUT}; }}
        """)
        self.url_btn.clicked.connect(self._open_url)
        btn_layout.addWidget(self.url_btn)
        
        details_layout.addWidget(btn_container)
        details_scroll.setWidget(details_content)
        
        details_frame_layout = QVBoxLayout(details_frame)
        details_frame_layout.setContentsMargins(0, 0, 0, 0)
        details_frame_layout.addWidget(details_scroll)
        
        splitter.addWidget(details_frame)
        splitter.setSizes([600, 500])
        
        main_layout.addWidget(splitter)
    
    def _combo_style(self) -> str:
        return f"""
            QComboBox {{
                background-color: {BG_INPUT};
                border: 1.5px solid {BORDER};
                border-radius: 8px;
                padding: 8px 12px;
                min-width: 140px;
                color: {TEXT_PRI};
                font-weight: 500;
            }}
            QComboBox QAbstractItemView {{
                background-color: {BG_CARD};
                color: {TEXT_PRI};
                selection-background-color: {BLUE_LT};
                selection-color: {BLUE_DARK};
            }}
            QComboBox:focus {{ border-color: {BLUE}; }}
        """
    
    def _input_style(self) -> str:
        return f"""
            QLineEdit {{
                background-color: {BG_INPUT};
                border: 1.5px solid {BORDER};
                border-radius: 8px;
                padding: 8px 14px;
                color: {TEXT_PRI};
            }}
            QLineEdit:focus {{ border-color: {BLUE}; }}
        """
    
    def _table_style(self) -> str:
        return f"""
            QTableWidget::item {{ padding: 12px 8px; border-bottom: 1px solid {BORDER}; color: {TEXT_PRI}; }}
            QTableWidget::item:selected {{ background-color: {BLUE_LT}; }}
            QHeaderView::section {{
                background-color: {BG_INPUT};
                color: {TEXT_SEC};
                font-weight: 700;
                padding: 12px;
                border-bottom: 2px solid {BLUE};
            }}
        """
    
    def _secondary_btn_style(self) -> str:
        return f"""
            QPushButton {{
                background-color: {BG_INPUT};
                border: 1.5px solid {BORDER};
                border-radius: 8px;
                padding: 8px 16px;
                color: {TEXT_SEC};
                font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {BLUE_LT}; border-color: {BLUE}; color: {BLUE}; }}
        """
    
    def _source_badge(self, source: str) -> QLabel:
        color = SOURCE_COLORS.get(source, TEXT_MUT)
        lbl = QLabel(source.replace("_", " ").upper())
        lbl.setFixedHeight(26)
        lbl.setMinimumWidth(80)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"""
            background-color: {color}22;
            color: {TEXT_PRI};
            font-weight: 700;
            font-size: 10px;
            border: 1px solid {color}66;
            border-radius: 13px;
        """)
        return lbl
    
    def _score_pill(self, score: float) -> QLabel:
        if not score:
            return QLabel("—")
        val = int(score)
        if val >= 80:
            color = GREEN
        elif val >= 60:
            color = BLUE
        else:
            color = YELLOW
        lbl = QLabel(f"{val}%")
        lbl.setFixedHeight(26)
        lbl.setMinimumWidth(50)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"""
            background-color: {color}22;
            color: {TEXT_PRI};
            font-weight: 800;
            font-size: 12px;
            border: 1px solid {color}66;
            border-radius: 13px;
        """)
        return lbl
    
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
                self._current_profil_id = self._profils[0].id
        except Exception as e:
            print(f"Erreur profils: {e}")
    
    def _on_profil_changed(self, idx):
        if 0 <= idx < len(self._profils):
            self._current_profil_id = self._profils[idx].id
            self._load_offres()
    
    def _load_offres(self):
        try:
            from database.db_manager import get_session
            from database.models import Offre
            from sqlalchemy import desc
            from datetime import datetime, timedelta
            
            source_filter = self.source_filter.currentText()
            score_filter = self.score_filter.currentText()
            search_text = self.search_input.text().strip().lower()
            
            with get_session() as db:
                # D'abord, essayer de récupérer les offres récentes (aujourd'hui)
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                query = db.query(Offre).filter(Offre.date_detection >= today)
                
                if source_filter != "Toutes les sources":
                    query = query.filter(Offre.source == source_filter)
                
                offres = query.order_by(desc(Offre.date_detection)).all()
                
                # SI PAS D'OFFRES RECENTES, prendre celles des 3 derniers jours
                if len(offres) == 0:
                    date_limite = datetime.now() - timedelta(days=3)
                    query = db.query(Offre).filter(Offre.date_detection >= date_limite)
                    
                    if source_filter != "Toutes les sources":
                        query = query.filter(Offre.source == source_filter)
                    
                    offres = query.order_by(desc(Offre.date_detection)).all()
                
                filtered = []
                for o in offres:
                    score = o.score_claude or (o.score_tfidf * 100 if o.score_tfidf else 0)
                    if score_filter == "≥ 80%" and score < 80:
                        continue
                    elif score_filter == "≥ 60%" and score < 60:
                        continue
                    elif score_filter == "≥ 40%" and score < 40:
                        continue
                    if search_text:
                        if search_text not in (o.titre or "").lower() and search_text not in (o.entreprise or "").lower():
                            continue
                    filtered.append((o, score))
            
            self.offres_table.setRowCount(0)
            self._offres_data = []
            
            for o, score in filtered:
                row = self.offres_table.rowCount()
                self.offres_table.insertRow(row)
                self._offres_data.append(o)
                
                # Entreprise
                company_widget = QWidget()
                company_layout = QHBoxLayout(company_widget)
                company_layout.setContentsMargins(4, 2, 4, 2)
                avatar = QLabel((o.entreprise or "?")[0].upper())
                avatar.setFixedSize(36, 36)
                avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
                avatar.setStyleSheet(f"background-color: {GREEN_LT}; color: {GREEN}; border-radius: 10px; font-size: 16px; font-weight: 800;")
                company_name = QLabel(o.entreprise or "—")
                company_name.setStyleSheet(f"color: {TEXT_PRI}; font-weight: 600;")
                company_layout.addWidget(avatar)
                company_layout.addWidget(company_name)
                company_layout.addStretch()
                self.offres_table.setCellWidget(row, 0, company_widget)
                
                # Poste
                poste_item = QTableWidgetItem(o.titre or "—")
                poste_item.setForeground(QColor(TEXT_PRI))
                font = QFont()
                font.setWeight(500)
                poste_item.setFont(font)
                self.offres_table.setItem(row, 1, poste_item)
                
                # Source
                self.offres_table.setCellWidget(row, 2, self._source_badge(o.source))
                
                # Score
                if score > 0:
                    self.offres_table.setCellWidget(row, 3, self._score_pill(score))
                else:
                    score_item = QTableWidgetItem("—")
                    score_item.setForeground(QColor(TEXT_MUT))
                    self.offres_table.setItem(row, 3, score_item)
                
                # Date
                date_str = o.date_detection.strftime("%d/%m/%Y") if o.date_detection else "—"
                date_item = QTableWidgetItem(date_str)
                date_item.setForeground(QColor(TEXT_MUT))
                self.offres_table.setItem(row, 4, date_item)
                
                # Bouton
                quick_btn = QPushButton("Postuler")
                quick_btn.setFixedHeight(30)
                quick_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {GREEN};
                        border-radius: 6px;
                        color: white;
                        font-weight: 700;
                        font-size: 11px;
                    }}
                    QPushButton:hover {{ background-color: #15803d; }}
                """)
                quick_btn.clicked.connect(lambda checked, o_id=o.id: self._quick_apply(o_id))
                self.offres_table.setCellWidget(row, 5, quick_btn)
            
            self.count_label.setText(f"{self.offres_table.rowCount()} offre(s)")
        except Exception as e:
            self.count_label.setText(f"Erreur: {e}")
    
    def _on_offre_selected(self):
        selected = self.offres_table.currentRow()
        if selected >= 0 and selected < len(self._offres_data):
            self._current_offre = self._offres_data[selected]
            self.apply_btn.setEnabled(True)
            self.interview_btn.setEnabled(True)
            self.url_btn.setEnabled(True)
            
            o = self._current_offre
            self.details_title.setText(o.titre or "Sans titre")
            self.details_company.setText(o.entreprise or "Non specifiee")
            self.details_location.setText(o.localisation or "Non specifiee")
            self.details_desc.setPlainText(o.description or "Aucune description disponible.")
            
            score = o.score_claude or (o.score_tfidf * 100 if o.score_tfidf else 0)
            self.details_score.setText(f"{score:.0f}%" if score > 0 else "Non disponible")
    
    def _quick_apply(self, offre_id: int):
        if not self._current_profil_id:
            QMessageBox.warning(self, "Erreur", "Selectionnez un profil")
            return
        for o in self._offres_data:
            if o.id == offre_id:
                self._current_offre = o
                break
        self._postuler()
    
    def _postuler(self):
        if not self._current_profil_id or not self._current_offre:
            QMessageBox.warning(self, "Erreur", "Selectionnez un profil et une offre")
            return
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Postuler")
        msg.setText(f"Postuler a :\n{self._current_offre.titre}")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.button(QMessageBox.StandardButton.Yes).setText("Technique")
        msg.button(QMessageBox.StandardButton.No).setText("Humaine")
        msg.addButton("Projet", QMessageBox.ButtonRole.ActionRole)
        
        reply = msg.exec()
        variante = 1 if reply == QMessageBox.StandardButton.Yes else (2 if reply == QMessageBox.StandardButton.No else 3)
        
        progress = QProgressDialog("Generation...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()
        
        self._gen_thread = GenerateCandidatureThread(self._current_offre.id, self._current_profil_id, variante)
        self._gen_thread.finished.connect(lambda r: self._on_candidature_generated(r, progress))
        self._gen_thread.error.connect(lambda e: self._on_gen_error(e, progress))
        self._gen_thread.start()
    
    def _on_candidature_generated(self, result, progress):
        progress.close()
        QMessageBox.information(self, "Succes", "Candidature creee avec succes !")
    
    def _on_gen_error(self, error, progress):
        progress.close()
        QMessageBox.critical(self, "Erreur", f"Echec : {error}")
    
    def _simulate_interview(self):
        if self._current_offre:
            QMessageBox.information(self, "Simulateur", f"Offre : {self._current_offre.titre}\n\nRendez-vous dans l'onglet 'Coach IA'")
    
    def _open_url(self):
        if self._current_offre and self._current_offre.url:
            QDesktopServices.openUrl(QUrl(self._current_offre.url))