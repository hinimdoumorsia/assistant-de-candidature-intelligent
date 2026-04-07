"""
services/pdf_service.py - Génération PDF (CV + Lettre de motivation)
Aucun import Qt.
"""
import logging
from pathlib import Path
from datetime import datetime
from config import EXPORTS_DIR, COLORS

logger = logging.getLogger(__name__)


def generate_lettre_pdf(content: str, profil, offre, output_path: str = None) -> str | None:
    """
    Génère un PDF de lettre de motivation.
    Retourne le chemin du fichier créé.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_RIGHT

        if not output_path:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(EXPORTS_DIR / f"lettre_{ts}.pdf")

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=2.5*cm, rightMargin=2.5*cm,
            topMargin=2.5*cm, bottomMargin=2.5*cm,
        )

        styles = getSampleStyleSheet()
        green = colors.HexColor(COLORS["primary_dark"])
        orange = colors.HexColor(COLORS["accent"])

        style_header = ParagraphStyle("header",
            parent=styles["Normal"], fontSize=11, textColor=green, fontName="Helvetica-Bold")
        style_body = ParagraphStyle("body",
            parent=styles["Normal"], fontSize=10.5, alignment=TA_JUSTIFY,
            leading=16, spaceAfter=10)
        style_date = ParagraphStyle("date",
            parent=styles["Normal"], fontSize=10, alignment=TA_RIGHT)

        story = []

        # En-tête candidat
        story.append(Paragraph(
            f"<b>{profil.user.prenom} {profil.user.nom}</b>", style_header))
        story.append(Paragraph(profil.titre, styles["Normal"]))
        story.append(Paragraph(profil.localisation or "", styles["Normal"]))
        story.append(Paragraph(profil.user.email, styles["Normal"]))
        story.append(Spacer(1, 20))

        # Date + destinataire
        story.append(Paragraph(datetime.now().strftime("%d %B %Y"), style_date))
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"<b>{offre.entreprise}</b>", style_header))
        story.append(Paragraph(offre.localisation or "", styles["Normal"]))
        story.append(Spacer(1, 20))

        # Objet
        story.append(Paragraph(
            f"<b>Objet : Candidature au poste de {offre.titre}</b>",
            ParagraphStyle("objet", parent=styles["Normal"], fontSize=11,
                           textColor=orange, fontName="Helvetica-Bold")))
        story.append(Spacer(1, 15))

        # Corps de la lettre
        for para in content.split("\n\n"):
            para = para.strip()
            if para:
                story.append(Paragraph(para, style_body))
                story.append(Spacer(1, 6))

        doc.build(story)
        logger.info(f"Lettre PDF générée: {output_path}")
        return output_path

    except ImportError:
        logger.error("reportlab non installé.")
        return None
    except Exception as e:
        logger.error(f"Erreur génération lettre PDF: {e}")
        return None


def generate_cv_pdf(cv_data: dict, output_path: str = None) -> str | None:
    """
    Génère un CV PDF moderne depuis un dict structuré.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_LEFT, TA_CENTER

        if not output_path:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(EXPORTS_DIR / f"cv_{ts}.pdf")

        doc = SimpleDocTemplate(output_path, pagesize=A4,
            leftMargin=1.8*cm, rightMargin=1.8*cm,
            topMargin=1.8*cm, bottomMargin=1.8*cm)

        green = colors.HexColor(COLORS["primary_dark"])
        orange = colors.HexColor(COLORS["accent"])
        light_green = colors.HexColor(COLORS["primary_light"])

        styles = getSampleStyleSheet()
        s_name   = ParagraphStyle("name",   fontSize=22, fontName="Helvetica-Bold", textColor=green, alignment=TA_LEFT)
        s_titre  = ParagraphStyle("titre",  fontSize=13, fontName="Helvetica",      textColor=orange)
        s_section= ParagraphStyle("section",fontSize=11, fontName="Helvetica-Bold", textColor=green, spaceBefore=12)
        s_body   = ParagraphStyle("body",   fontSize=10, leading=14)
        s_tag    = ParagraphStyle("tag",    fontSize=9,  fontName="Helvetica-Bold", textColor=colors.white)

        story = []

        # Nom + titre
        story.append(Paragraph(cv_data.get("nom_complet", ""), s_name))
        story.append(Paragraph(cv_data.get("titre", ""), s_titre))
        story.append(Spacer(1, 6))
        story.append(HRFlowable(width="100%", thickness=2, color=green))
        story.append(Spacer(1, 8))

        # Résumé
        if cv_data.get("resume"):
            story.append(Paragraph("Résumé", s_section))
            story.append(Paragraph(cv_data["resume"], s_body))
            story.append(Spacer(1, 8))

        # Compétences (badges)
        if cv_data.get("competences"):
            story.append(Paragraph("Compétences Techniques", s_section))
            comps = " | ".join(cv_data["competences"])
            story.append(Paragraph(comps, ParagraphStyle("comps",
                fontSize=10, fontName="Helvetica-Bold", textColor=green)))
            story.append(Spacer(1, 8))

        # Formation
        if cv_data.get("formation"):
            story.append(Paragraph("Formation", s_section))
            for f in cv_data["formation"]:
                story.append(Paragraph(
                    f"<b>{f.get('diplome','')}</b> — {f.get('ecole','')} ({f.get('annee','')})",
                    s_body))
            story.append(Spacer(1, 8))

        # Expérience
        if cv_data.get("experience"):
            story.append(Paragraph("Expérience", s_section))
            for e in cv_data["experience"]:
                story.append(Paragraph(
                    f"<b>{e.get('poste','')}</b> @ {e.get('entreprise','')} — {e.get('duree','')}",
                    s_body))
                if e.get("description"):
                    story.append(Paragraph(f"• {e['description']}", s_body))
            story.append(Spacer(1, 8))

        # Langues
        if cv_data.get("langues"):
            story.append(Paragraph("Langues", s_section))
            langues_str = " | ".join(
                f"{l.get('langue','')} ({l.get('niveau','')})"
                for l in cv_data["langues"]
            )
            story.append(Paragraph(langues_str, s_body))

        doc.build(story)
        logger.info(f"CV PDF généré: {output_path}")
        return output_path

    except ImportError:
        logger.error("reportlab non installé.")
        return None
    except Exception as e:
        logger.error(f"Erreur génération CV PDF: {e}")
        return None


def export_letter(content: str, profil, offre, output_path: str | None = None) -> str | None:
    return generate_lettre_pdf(content, profil, offre, output_path)


def export_cv(cv_data: dict, output_path: str | None = None) -> str | None:
    return generate_cv_pdf(cv_data, output_path)


def generate_monthly_report(user_id: int, mois: str) -> str | None:
    """Generate a simple monthly PDF report in exports directory."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        from database.db_manager import get_session
        from database.models import Candidature, Offre

        filename = EXPORTS_DIR / f"rapport_mensuel_{user_id}_{mois.replace('-', '')}.pdf"
        doc = SimpleDocTemplate(str(filename), pagesize=A4)
        styles = getSampleStyleSheet()

        with get_session() as db:
            rows = (
                db.query(Candidature, Offre)
                .join(Offre, Candidature.offre_id == Offre.id, isouter=True)
                .filter(Candidature.profil_id.in_(
                    db.query(Candidature.profil_id).subquery()
                ))
                .all()
            )

        story = [Paragraph(f"Rapport mensuel {mois}", styles["Title"]), Spacer(1, 12)]
        table_data = [["Entreprise", "Poste", "Statut", "Date"]]
        for cand, offer in rows:
            table_data.append([
                getattr(offer, "entreprise", ""),
                getattr(offer, "titre", ""),
                getattr(cand.statut, "value", str(cand.statut)),
                cand.created_at.strftime("%Y-%m-%d") if cand.created_at else "",
            ])
        table = Table(table_data)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#5b6af0")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ]
            )
        )
        story.append(table)
        doc.build(story)
        return str(filename)
    except Exception as exc:
        logger.error("Erreur rapport mensuel: %s", exc)
        return None
