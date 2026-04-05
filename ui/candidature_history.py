"""
ui/candidature_history.py - Historique des candidatures filtrable
Thème : blanc / vert / bleu — professionnel et moderne
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QFrame, QMessageBox, QLineEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont
import subprocess
import os

# ── Palette blanc / vert / bleu (identique à profile_editor) ─────────────────
BG_PAGE    = "#f0f4f8"
BG_CARD    = "#ffffff"
BG_INPUT   = "#f8fafc"
BORDER     = "#e2e8f0"

GREEN      = "#16a34a"
GREEN_LT   = "#dcfce7"
GREEN_MID  = "#22c55e"
BLUE       = "#3b82f6"
BLUE_LT    = "#dbeafe"
BLUE_DARK  = "#1d4ed8"

RED        = "#ef4444"
RED_LT     = "#fee2e2"

TEXT_PRI   = "#0f172a"
TEXT_SEC   = "#64748b"
TEXT_MUT   = "#94a3b8"


class ReportThread(QThread):
    done  = pyqtSignal(str)
    error = pyqtSignal(str)

    def run(self):
        try:
            from database.db_manager import get_session
            from database.models import Candidature
            from config import EXPORTS_DIR
            from datetime import datetime
            import os

            # Créer le dossier exports s'il n'existe pas
            EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

            path = str(EXPORTS_DIR / f"rapport_candidatures_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")

            with get_session() as db:
                cands = db.query(Candidature).all()

            try:
                from reportlab.lib.pagesizes import A4
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib import colors as rl_colors
                from reportlab.lib.enums import TA_CENTER

                doc = SimpleDocTemplate(path, pagesize=A4)
                styles = getSampleStyleSheet()
                
                # Style personnalisé pour le titre
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Title'],
                    fontSize=24,
                    textColor=rl_colors.HexColor(GREEN),
                    alignment=TA_CENTER,
                    spaceAfter=30
                )
                
                story = []
                story.append(Paragraph("Rapport des Candidatures", title_style))
                story.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", styles["Normal"]))
                story.append(Spacer(1, 20))
                story.append(Paragraph(f"<b>Total candidatures : {len(cands)}</b>", styles["Normal"]))
                story.append(Spacer(1, 12))

                if cands:
                    data = [["ID", "Statut", "Date", "Variante"]]
                    for c in cands:
                        data.append([
                            str(c.id), 
                            c.statut.value,
                            c.created_at.strftime("%d/%m/%Y") if c.created_at else "—",
                            str(c.variante_choisie)
                        ])
                    
                    t = Table(data, colWidths=[60, 100, 100, 80])
                    t.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), rl_colors.HexColor(GREEN)),
                        ("TEXTCOLOR",  (0, 0), (-1, 0), rl_colors.white),
                        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE",   (0, 0), (-1, 0), 12),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), rl_colors.white),
                                ("GRID",       (0, 0), (-1, -1), 0.5, rl_colors.grey),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [rl_colors.white, rl_colors.HexColor(GREEN_LT)]),
                    ]))
                    story.append(t)

                doc.build(story)
                self.done.emit(path)
            except ImportError:
                self.error.emit("reportlab non installé. Installez-le avec: pip install reportlab")
        except Exception as e:
            self.error.emit(str(e))


class CandidatureHistoryWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._load()

    def _setup_ui(self):
        self.setStyleSheet(f"background-color: {BG_PAGE};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 32)
        layout.setSpacing(20)

        # ── Header avec dégradé vert→bleu ────────────────────────────────────
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
        header_card.setFixedHeight(80)
        hl = QHBoxLayout(header_card)
        hl.setContentsMargins(24, 0, 24, 0)

        title = QLabel("Historique des Candidatures")
        title.setStyleSheet("color: white; font-size: 22px; font-weight: 700; background: transparent;")
        
        subtitle = QLabel("Suivez et gérez vos candidatures")
        subtitle.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 13px; background: transparent;")
        
        title_col = QVBoxLayout()
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        
        hl.addLayout(title_col)
        hl.addStretch()

        btn_report = QPushButton("📄 Rapport PDF")
        btn_report.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255,255,255,0.2);
                border: 1px solid rgba(255,255,255,0.4);
                border-radius: 8px;
                color: white;
                font-size: 13px;
                font-weight: 600;
                padding: 8px 18px;
            }}
            QPushButton:hover {{
                background-color: rgba(255,255,255,0.3);
            }}
        """)
        btn_report.clicked.connect(self._generate_report)
        
        btn_refresh = QPushButton("🔄 Actualiser")
        btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255,255,255,0.2);
                border: 1px solid rgba(255,255,255,0.4);
                border-radius: 8px;
                color: white;
                font-size: 13px;
                font-weight: 600;
                padding: 8px 18px;
            }}
            QPushButton:hover {{
                background-color: rgba(255,255,255,0.3);
            }}
        """)
        btn_refresh.clicked.connect(self._load)
        
        hl.addWidget(btn_report)
        hl.addWidget(btn_refresh)
        layout.addWidget(header_card)

        # ── Filtres ──────────────────────────────────────────────────────────
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)
        fl = QHBoxLayout(filter_frame)
        fl.setContentsMargins(20, 16, 20, 16)
        fl.setSpacing(15)

        filter_label = QLabel("Filtrer :")
        filter_label.setStyleSheet(f"color: {TEXT_SEC}; font-size: 13px; font-weight: 600;")
        fl.addWidget(filter_label)

        self.filter_statut = QComboBox()
        self.filter_statut.addItems(["Tous les statuts", "en_attente", "confirmee", "deposee", "rejetee"])
        self.filter_statut.setStyleSheet(self._combo_style())
        self.filter_statut.currentIndexChanged.connect(self._load)
        fl.addWidget(self.filter_statut)

        self.filter_source = QComboBox()
        self.filter_source.addItems(["Toutes les sources", "indeed_rss", "rekrute", "emploi_ma", "bayt", "adzuna"])
        self.filter_source.setStyleSheet(self._combo_style())
        self.filter_source.currentIndexChanged.connect(self._load)
        fl.addWidget(self.filter_source)

        self.filter_search = QLineEdit()
        self.filter_search.setPlaceholderText("🔍 Rechercher (poste, entreprise…)")
        self.filter_search.setMinimumWidth(220)
        self.filter_search.setStyleSheet(self._input_style())
        self.filter_search.textChanged.connect(self._load)
        fl.addWidget(self.filter_search)
        fl.addStretch()
        layout.addWidget(filter_frame)

        # ── Tableau ──────────────────────────────────────────────────────────
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Poste", "Entreprise", "Source", "Score", "Statut", "Variante", "Date"])
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 12px;
                gridline-color: {BORDER};
                outline: none;
            }}
            QTableWidget::item {{
                padding: 10px;
                color: {TEXT_PRI};
                font-size: 13px;
            }}
            QTableWidget::item:selected {{
                background-color: {BLUE_LT};
                color: {TEXT_PRI};
            }}
            QHeaderView::section {{
                background-color: {BG_INPUT};
                color: {TEXT_SEC};
                font-weight: 600;
                font-size: 12px;
                padding: 10px;
                border: none;
                border-bottom: 2px solid {BORDER};
            }}
        """)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

        # ── Barre d'actions ──────────────────────────────────────────────────
        action_card = QFrame()
        action_card.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)
        action_row = QHBoxLayout(action_card)
        action_row.setContentsMargins(20, 14, 20, 14)
        action_row.setSpacing(12)

        self.count_lbl = QLabel("0 candidature(s)")
        self.count_lbl.setStyleSheet(f"color: {TEXT_SEC}; font-size: 13px; font-weight: 500;")

        btn_deposee = QPushButton("✅ Marquer Déposée")
        btn_deposee.setStyleSheet(self._success_btn_style())
        btn_deposee.clicked.connect(lambda: self._change_status("deposee"))

        btn_rejetee = QPushButton("❌ Marquer Rejetée")
        btn_rejetee.setStyleSheet(self._danger_btn_style())
        btn_rejetee.clicked.connect(lambda: self._change_status("rejetee"))

        btn_delete = QPushButton("🗑 Supprimer")
        btn_delete.setStyleSheet(self._secondary_btn_style())
        btn_delete.clicked.connect(self._delete_selected)

        action_row.addWidget(self.count_lbl)
        action_row.addStretch()
        action_row.addWidget(btn_deposee)
        action_row.addWidget(btn_rejetee)
        action_row.addWidget(btn_delete)
        layout.addWidget(action_card)

    # ── Styles helpers ──────────────────────────────────────────────────────
    def _combo_style(self) -> str:
        return f"""
            QComboBox {{
                background-color: {BG_INPUT};
                border: 1.5px solid {BORDER};
                border-radius: 8px;
                color: {TEXT_PRI};
                font-size: 13px;
                padding: 6px 12px;
                min-width: 140px;
            }}
            QComboBox:focus {{ border-color: {BLUE}; }}
            QComboBox::drop-down {{ border: none; width: 28px; }}
            QComboBox QAbstractItemView {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                color: {TEXT_PRI};
                selection-background-color: {BLUE_LT};
                selection-color: {BLUE_DARK};
            }}
        """

    def _input_style(self) -> str:
        return f"""
            QLineEdit {{
                background-color: {BG_INPUT};
                border: 1.5px solid {BORDER};
                border-radius: 8px;
                color: {TEXT_PRI};
                font-size: 13px;
                padding: 6px 14px;
            }}
            QLineEdit:focus {{
                border-color: {BLUE};
                background-color: white;
            }}
        """

    def _success_btn_style(self) -> str:
        return f"""
            QPushButton {{
                background-color: {GREEN_LT};
                border: 1.5px solid {GREEN};
                border-radius: 8px;
                color: {GREEN};
                font-size: 13px;
                font-weight: 600;
                padding: 8px 18px;
            }}
            QPushButton:hover {{
                background-color: {GREEN};
                color: white;
            }}
        """

    def _danger_btn_style(self) -> str:
        return f"""
            QPushButton {{
                background-color: {RED_LT};
                border: 1.5px solid {RED};
                border-radius: 8px;
                color: {RED};
                font-size: 13px;
                font-weight: 600;
                padding: 8px 18px;
            }}
            QPushButton:hover {{
                background-color: {RED};
                color: white;
            }}
        """

    def _secondary_btn_style(self) -> str:
        return f"""
            QPushButton {{
                background-color: {BG_INPUT};
                border: 1.5px solid {BORDER};
                border-radius: 8px;
                color: {TEXT_SEC};
                font-size: 13px;
                font-weight: 600;
                padding: 8px 18px;
            }}
            QPushButton:hover {{
                background-color: {BORDER};
                color: {TEXT_PRI};
            }}
        """

    def _bold_font(self):
        f = QFont()
        f.setBold(True)
        return f

    # ── Load data ───────────────────────────────────────────────────────────
    def _load(self):
        try:
            from database.db_manager import get_session
            from database.models import Candidature, Offre

            statut_filter = self.filter_statut.currentText()
            source_filter = self.filter_source.currentText()
            search_text   = self.filter_search.text().strip().lower()

            with get_session() as db:
                query = db.query(Candidature).join(Offre, Candidature.offre_id == Offre.id, isouter=True)

                if statut_filter != "Tous les statuts":
                    query = query.filter(Candidature.statut == statut_filter)
                if source_filter != "Toutes les sources":
                    query = query.filter(Offre.source == source_filter)

                cands = query.order_by(Candidature.created_at.desc()).all()

            self.table.setRowCount(0)
            self._row_ids = []

            for c in cands:
                offre = c.offre
                titre      = offre.titre if offre else "—"
                entreprise = offre.entreprise if offre else "—"
                source     = offre.source if offre else "—"
                score      = f"{offre.score_claude:.0f}" if (offre and offre.score_claude) else "—"

                if search_text and search_text not in titre.lower() and search_text not in entreprise.lower():
                    continue

                row = self.table.rowCount()
                self.table.insertRow(row)
                self._row_ids.append(c.id)

                item_titre = QTableWidgetItem(titre[:55])
                item_titre.setForeground(QColor(TEXT_PRI))
                self.table.setItem(row, 0, item_titre)
                
                item_entreprise = QTableWidgetItem(entreprise[:35])
                item_entreprise.setForeground(QColor(TEXT_SEC))
                self.table.setItem(row, 1, item_entreprise)
                
                item_source = QTableWidgetItem(source)
                item_source.setForeground(QColor(TEXT_MUT))
                self.table.setItem(row, 2, item_source)
                
                item_score = QTableWidgetItem(score)
                if score != "—" and int(score) >= 80:
                    item_score.setForeground(QColor(GREEN))
                elif score != "—" and int(score) >= 60:
                    item_score.setForeground(QColor(BLUE))
                else:
                    item_score.setForeground(QColor(TEXT_MUT))
                self.table.setItem(row, 3, item_score)

                statut_item = QTableWidgetItem(c.statut.value)
                color_map = {
                    "deposee":    GREEN,
                    "en_attente": "#eab308",
                    "rejetee":    RED,
                    "confirmee":  BLUE,
                }
                statut_item.setForeground(QColor(color_map.get(c.statut.value, TEXT_SEC)))
                statut_item.setFont(self._bold_font())
                self.table.setItem(row, 4, statut_item)

                item_var = QTableWidgetItem(str(c.variante_choisie))
                item_var.setForeground(QColor(TEXT_SEC))
                self.table.setItem(row, 5, item_var)
                
                date_str = c.created_at.strftime("%d/%m/%Y") if c.created_at else "—"
                item_date = QTableWidgetItem(date_str)
                item_date.setForeground(QColor(TEXT_MUT))
                self.table.setItem(row, 6, item_date)

            self.count_lbl.setText(f"{self.table.rowCount()} candidature(s)")

        except Exception as e:
            self.count_lbl.setText(f"Erreur: {e}")

    def _get_selected_cand_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._row_ids):
            return None
        return self._row_ids[row]

    def _change_status(self, new_status: str):
        cand_id = self._get_selected_cand_id()
        if not cand_id:
            self._show_message("Sélection", "Veuillez sélectionner une candidature.", "warning")
            return
        try:
            from database.db_manager import get_session
            from database.models import Candidature, StatutCandidature
            from datetime import datetime
            with get_session() as db:
                c = db.query(Candidature).get(cand_id)
                if c:
                    c.statut = StatutCandidature(new_status)
                    if new_status == "deposee":
                        c.deposee_at = datetime.utcnow()
            self._load()
            self._show_message("Succès", f"Statut mis à jour : {new_status}", "info")
        except Exception as e:
            self._show_message("Erreur", str(e), "error")

    def _delete_selected(self):
        cand_id = self._get_selected_cand_id()
        if not cand_id:
            self._show_message("Sélection", "Veuillez sélectionner une candidature.", "warning")
            return
        
        # Utiliser QMessageBox standard mais forcer le style
        msg = QMessageBox(self)
        msg.setWindowTitle("Supprimer")
        msg.setText("Êtes-vous sûr de vouloir supprimer cette candidature ?")
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {BG_CARD};
            }}
            QMessageBox QLabel {{
                color: {TEXT_PRI};
                font-size: 13px;
            }}
            QPushButton {{
                padding: 6px 16px;
                border-radius: 6px;
                font-weight: 600;
            }}
        """)
        
        reply = msg.exec()
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from database.db_manager import get_session
                from database.models import Candidature
                with get_session() as db:
                    c = db.query(Candidature).get(cand_id)
                    if c:
                        db.delete(c)
                self._load()
                self._show_message("Succès", "Candidature supprimée avec succès.", "info")
            except Exception as e:
                self._show_message("Erreur", str(e), "error")

    def _generate_report(self):
        """Génère le rapport PDF et l'ouvre automatiquement"""
        # Message de chargement
        self._show_message("Génération", "Génération du rapport PDF en cours...", "info", auto_close=2000)
        
        self._report_thread = ReportThread()
        self._report_thread.done.connect(self._on_report_generated)
        self._report_thread.error.connect(lambda e: self._show_message("Erreur", f"Échec de génération : {e}", "error"))
        self._report_thread.start()

    def _on_report_generated(self, path: str):
        """Appelé quand le PDF est généré"""
        # Ouvrir le dossier contenant le fichier
        folder = os.path.dirname(path)
        
        # Boîte de dialogue personnalisée pour éviter le flou
        msg = QMessageBox(self)
        msg.setWindowTitle("Rapport généré")
        msg.setText(f"✅ Rapport PDF généré avec succès !\n\n📁 Emplacement : {path}")
        msg.setInformativeText("Voulez-vous ouvrir le fichier ?")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Open)
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {BG_CARD};
                min-width: 500px;
            }}
            QMessageBox QLabel {{
                color: {TEXT_PRI};
                font-size: 13px;
            }}
            QPushButton {{
                padding: 8px 20px;
                border-radius: 8px;
                font-weight: 600;
                min-width: 100px;
            }}
            QPushButton[text="&Yes"] {{
                background-color: {GREEN};
                color: white;
                border: none;
            }}
            QPushButton[text="&Yes"]:hover {{
                background-color: #15803d;
            }}
            QPushButton[text="&No"] {{
                background-color: {BG_INPUT};
                border: 1px solid {BORDER};
                color: {TEXT_SEC};
            }}
            QPushButton[text="&Open"] {{
                background-color: {BLUE};
                color: white;
                border: none;
            }}
            QPushButton[text="&Open"]:hover {{
                background-color: {BLUE_DARK};
            }}
        """)
        
        # Personnaliser les boutons
        yes_button = msg.button(QMessageBox.StandardButton.Yes)
        if yes_button:
            yes_button.setText("📂 Ouvrir le dossier")
        
        no_button = msg.button(QMessageBox.StandardButton.No)
        if no_button:
            no_button.setText("❌ Fermer")
            
        open_button = msg.button(QMessageBox.StandardButton.Open)
        if open_button:
            open_button.setText("📄 Ouvrir le PDF")
        
        reply = msg.exec()
        
        if reply == QMessageBox.StandardButton.Yes:
            # Ouvrir le dossier contenant le fichier
            try:
                os.startfile(folder)  # Windows
            except:
                subprocess.Popen(f'explorer "{folder}"')
        elif reply == QMessageBox.StandardButton.Open:
            # Ouvrir directement le PDF
            self._open_pdf(path)

    def _open_pdf(self, path: str):
        """Ouvre le PDF avec l'application par défaut"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(path)
            else:  # Mac/Linux
                subprocess.Popen(['open', path] if sys.platform == 'darwin' else ['xdg-open', path])
        except Exception as e:
            self._show_message("Erreur", f"Impossible d'ouvrir le PDF : {e}", "error")

    def _show_message(self, title: str, text: str, icon_type: str = "info", auto_close: int = 0):
        """Affiche une boîte de dialogue avec style personnalisé"""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {BG_CARD};
            }}
            QMessageBox QLabel {{
                color: {TEXT_PRI};
                font-size: 13px;
                min-width: 300px;
            }}
            QPushButton {{
                padding: 6px 16px;
                border-radius: 6px;
                font-weight: 600;
                background-color: {BLUE};
                color: white;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {BLUE_DARK};
            }}
        """)
        
        if icon_type == "warning":
            msg.setIcon(QMessageBox.Icon.Warning)
        elif icon_type == "error":
            msg.setIcon(QMessageBox.Icon.Critical)
        else:
            msg.setIcon(QMessageBox.Icon.Information)
        
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        if auto_close > 0:
            QTimer.singleShot(auto_close, msg.accept)
        
        msg.exec()