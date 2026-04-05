"""
database/models.py - Modèles SQLAlchemy ORM
Compatible SQLite (v1) et PostgreSQL (v2 web via DATABASE_URL)
"""
import json
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean,
    DateTime, ForeignKey, Enum as SAEnum, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()


class StatutOffre(str, enum.Enum):
    nouvelle  = "nouvelle"
    traitee   = "traitee"
    expiree   = "expiree"


class StatutCandidature(str, enum.Enum):
    en_attente = "en_attente"
    confirmee  = "confirmee"
    deposee    = "deposee"
    rejetee    = "rejetee"


class User(Base):
    __tablename__ = "users"

    id                    = Column(Integer, primary_key=True, autoincrement=True)
    nom                   = Column(String(100), nullable=False)
    prenom                = Column(String(100), nullable=False)
    email                 = Column(String(150), unique=True, nullable=False)
    mot_de_passe          = Column(String(255), nullable=False)  # bcrypt hash
    notifications_actives = Column(Boolean, default=True)
    created_at            = Column(DateTime, default=datetime.utcnow)

    profils      = relationship("Profil", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"


class Profil(Base):
    __tablename__ = "profils"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    titre        = Column(String(200), nullable=False, default="Mon Profil")
    competences  = Column(Text, default="[]")   # JSON list
    formation    = Column(Text, default="")
    experience   = Column(Text, default="")
    langues      = Column(String(255), default="Français")
    cv_path      = Column(String(500), default="")
    disponibilite = Column(String(100), default="Immédiat")
    localisation  = Column(String(150), default="")
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user          = relationship("User", back_populates="profils")
    candidatures  = relationship("Candidature", back_populates="profil", cascade="all, delete-orphan")

    @property
    def competences_list(self):
        try:
            return json.loads(self.competences)
        except Exception:
            return []

    @competences_list.setter
    def competences_list(self, value):
        self.competences = json.dumps(value, ensure_ascii=False)

    def __repr__(self):
        return f"<Profil {self.titre} (user={self.user_id})>"


class Offre(Base):
    __tablename__ = "offres"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    source         = Column(String(50), nullable=False)
    titre          = Column(String(300), nullable=False)
    entreprise     = Column(String(200), default="")
    localisation   = Column(String(150), default="")
    description    = Column(Text, default="")
    url            = Column(String(500), unique=True, nullable=False)
    date_detection = Column(DateTime, default=datetime.utcnow)
    statut         = Column(SAEnum(StatutOffre), default=StatutOffre.nouvelle)
    score_tfidf    = Column(Float, default=0.0)
    score_claude   = Column(Float, nullable=True)

    candidatures   = relationship("Candidature", back_populates="offre")

    def __repr__(self):
        return f"<Offre {self.titre[:40]} ({self.source})>"


class Candidature(Base):
    __tablename__ = "candidatures"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    profil_id        = Column(Integer, ForeignKey("profils.id"), nullable=False)
    offre_id         = Column(Integer, ForeignKey("offres.id"), nullable=False)
    lettre_path      = Column(String(500), default="")
    cv_genere_path   = Column(String(500), default="")
    variante_choisie = Column(Integer, default=1)  # 1, 2 ou 3
    statut           = Column(SAEnum(StatutCandidature), default=StatutCandidature.en_attente)
    user_consent     = Column(Boolean, default=False)
    created_at       = Column(DateTime, default=datetime.utcnow)
    deposee_at       = Column(DateTime, nullable=True)

    profil = relationship("Profil", back_populates="candidatures")
    offre  = relationship("Offre",  back_populates="candidatures")

    def __repr__(self):
        return f"<Candidature profil={self.profil_id} offre={self.offre_id}>"
