"""Preview and second-consent UI before assisted deposit."""
from __future__ import annotations

from PyQt6.QtWidgets import QHBoxLayout, QTextEdit, QVBoxLayout, QWidget
from qfluentwidgets import BodyLabel, CheckBox, PrimaryPushButton, PushButton, TitleLabel


class ConsentPreviewWidget(QWidget):
    def __init__(self, lettre_text: str, cv_data: dict, profil, offre, on_confirm, parent=None):
        super().__init__(parent)
        self.lettre_text = lettre_text
        self.cv_data = cv_data
        self.profil = profil
        self.offre = offre
        self.on_confirm = on_confirm

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(10)

        root.addWidget(TitleLabel("Prévisualisation & confirmation"))

        root.addWidget(BodyLabel("Lettre choisie"))
        self.letter_editor = QTextEdit()
        self.letter_editor.setReadOnly(True)
        self.letter_editor.setPlainText(lettre_text or "")
        root.addWidget(self.letter_editor, 1)

        actions = QHBoxLayout()
        export_letter = PushButton("Télécharger la lettre PDF")
        export_cv = PushButton("Télécharger le CV PDF")
        export_letter.clicked.connect(self._export_letter)
        export_cv.clicked.connect(self._export_cv)
        actions.addWidget(export_letter)
        actions.addWidget(export_cv)
        actions.addStretch(1)
        root.addLayout(actions)

        self.cb_letter = CheckBox("J'ai vérifié et approuvé ma lettre de motivation")
        self.cb_cv = CheckBox("J'ai vérifié et approuvé mon CV")
        self.cb_letter.stateChanged.connect(self._sync_button)
        self.cb_cv.stateChanged.connect(self._sync_button)
        root.addWidget(self.cb_letter)
        root.addWidget(self.cb_cv)

        self.confirm_btn = PrimaryPushButton("Confirmer et préparer le dépôt")
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.clicked.connect(self.on_confirm)
        root.addWidget(self.confirm_btn)

    def _sync_button(self):
        self.confirm_btn.setEnabled(self.cb_letter.isChecked() and self.cb_cv.isChecked())

    def _export_letter(self):
        from services.pdf_service import export_letter

        export_letter(self.letter_editor.toPlainText(), self.profil, self.offre)

    def _export_cv(self):
        from services.pdf_service import export_cv

        export_cv(self.cv_data)
