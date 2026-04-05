"""
ui/notification_popup.py - Popup offre + QWizard dépôt assisté
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QWizard, QWizardPage, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt
from config import COLORS


class OfferDetailDialog(QDialog):
    """Popup de détail d'une offre avec score + actions."""

    def __init__(self, offer_title: str, parent=None, offre=None):
        super().__init__(parent)
        self.offre = offre
        self.setWindowTitle("Détail de l'offre")
        self.setMinimumSize(560, 400)
        self._setup_ui(offer_title)

    def _setup_ui(self, title: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Header coloré
        header = QFrame()
        header.setStyleSheet(f"background: {COLORS['primary_dark']}; border-radius: 10px;")
        hl = QVBoxLayout(header)
        hl.setContentsMargins(20, 16, 20, 16)
        t = QLabel(title)
        t.setStyleSheet("color: white; font-size: 16px; font-weight: 700;")
        t.setWordWrap(True)
        hl.addWidget(t)
        layout.addWidget(header)

        # Scores
        if self.offre:
            sc_row = QHBoxLayout()
            tfidf = QLabel(f"TF-IDF: {self.offre.score_tfidf*100:.0f}%")
            tfidf.setStyleSheet(f"background: {COLORS['primary_light']}; color: {COLORS['primary_dark']}; padding: 6px 14px; border-radius: 16px; font-weight: 600;")
            cl = f"{self.offre.score_claude:.0f}/100" if self.offre.score_claude else "—"
            claude_lbl = QLabel(f"Score IA: {cl}")
            claude_lbl.setStyleSheet(f"background: {COLORS['accent_light']}; color: #7B341E; padding: 6px 14px; border-radius: 16px; font-weight: 600;")
            sc_row.addWidget(tfidf)
            sc_row.addWidget(claude_lbl)
            sc_row.addStretch()
            layout.addLayout(sc_row)

            desc = QTextEdit()
            desc.setPlainText(self.offre.description or "Aucune description disponible.")
            desc.setReadOnly(True)
            desc.setMaximumHeight(160)
            layout.addWidget(desc)

        # Boutons
        btn_row = QHBoxLayout()
        btn_postuler = QPushButton("📤 Préparer le dépôt")
        btn_postuler.clicked.connect(lambda: (self.close(), DepotWizard(self.parent()).exec()))
        btn_close = QPushButton("Fermer")
        btn_close.setProperty("class", "secondary")
        btn_close.clicked.connect(self.close)
        btn_row.addWidget(btn_postuler)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)


class DepotWizard(QWizard):
    """QWizard 3 étapes pour le dépôt assisté."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Préparer le dépôt")
        self.setMinimumSize(620, 480)
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setStyleSheet(f"""
            QWizard {{ background: {COLORS['bg']}; }}
            QWizard QPushButton {{
                background: {COLORS['primary']};
                color: white; border: none; border-radius: 8px;
                padding: 10px 22px; font-weight: 600;
            }}
            QWizard QPushButton:hover {{ background: {COLORS['primary_dark']}; }}
        """)

        self.addPage(self._page_lettre())
        self.addPage(self._page_depot())
        self.addPage(self._page_confirmation())

    def _page_lettre(self) -> QWizardPage:
        page = QWizardPage()
        page.setTitle("Étape 1 — Lettre de motivation")
        page.setSubTitle("Choisissez la variante de lettre à utiliser.")
        layout = QVBoxLayout(page)
        layout.setSpacing(16)

        for i, (label, desc) in enumerate([
            ("Variante Technique", "Met en avant vos compétences et réalisations concrètes."),
            ("Variante Humaine",   "Met en avant votre motivation et vos valeurs."),
            ("Variante Projet",    "Met en avant votre vision et votre apport stratégique."),
        ], 1):
            card = QFrame()
            card.setStyleSheet(f"background: white; border: 2px solid {COLORS['card_border']}; border-radius: 10px;")
            cl = QHBoxLayout(card)
            cl.setContentsMargins(16, 14, 16, 14)
            lbl_num = QLabel(str(i))
            lbl_num.setStyleSheet(f"background: {COLORS['primary']}; color: white; border-radius: 14px; padding: 6px 12px; font-weight: 700; font-size: 14px;")
            lbl_num.setFixedSize(32, 32)
            lbl_num.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col = QVBoxLayout()
            col.addWidget(QLabel(f"<b>{label}</b>"))
            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet(f"color: {COLORS['text_light']};")
            col.addWidget(desc_lbl)
            cl.addWidget(lbl_num)
            cl.addLayout(col)
            layout.addWidget(card)
        return page

    def _page_depot(self) -> QWizardPage:
        page = QWizardPage()
        page.setTitle("Étape 2 — Ouverture du site")
        page.setSubTitle("Suivez ces instructions pour déposer votre candidature.")
        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        steps = [
            ("🌐", "Le lien de l'offre va s'ouvrir dans votre navigateur."),
            ("📋", "Vos données (nom, email, lettre) sont copiées dans le presse-papier."),
            ("📝", "Collez et complétez le formulaire sur le site de l'entreprise."),
            ("✅", "Confirmez le dépôt ici une fois terminé."),
        ]
        for icon, text in steps:
            row = QHBoxLayout()
            il = QLabel(icon)
            il.setStyleSheet("font-size: 22px;")
            il.setFixedWidth(36)
            tl = QLabel(text)
            tl.setWordWrap(True)
            tl.setStyleSheet("font-size: 13px;")
            row.addWidget(il)
            row.addWidget(tl)
            layout.addLayout(row)

        layout.addSpacing(12)
        btn_open = QPushButton("🔗 Ouvrir le lien dans le navigateur")
        btn_open.clicked.connect(self._open_link)
        layout.addWidget(btn_open)

        btn_copy = QPushButton("📋 Copier mes données")
        btn_copy.setProperty("class", "secondary")
        btn_copy.clicked.connect(self._copy_data)
        layout.addWidget(btn_copy)
        return page

    def _page_confirmation(self) -> QWizardPage:
        page = QWizardPage()
        page.setTitle("Étape 3 — Confirmation")
        page.setSubTitle("Confirmez que vous avez bien déposé votre candidature.")
        layout = QVBoxLayout(page)
        layout.setSpacing(16)

        success_icon = QLabel("🎉")
        success_icon.setStyleSheet("font-size: 48px;")
        success_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(success_icon)

        msg = QLabel("Si vous avez soumis votre candidature, cliquez sur Terminer.\n"
                     "Le statut sera mis à jour automatiquement dans votre historique.")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setWordWrap(True)
        msg.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 13px;")
        layout.addWidget(msg)
        return page

    def _open_link(self):
        import webbrowser
        webbrowser.open("https://www.rekrute.com/offres.html")

    def _copy_data(self):
        try:
            import pyperclip
            pyperclip.copy("Nom: [Votre Nom]\nEmail: [Votre Email]\nPoste: [Titre]\nLettre: [Voir fichier lettre.pdf]")
            QMessageBox.information(self, "Copié", "Données copiées dans le presse-papier !")
        except ImportError:
            QMessageBox.warning(self, "Erreur", "pyperclip non installé.")
