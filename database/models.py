"""SQLAlchemy ORM models for StageAuto."""
from __future__ import annotations

import enum
import json
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum as SAEnum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class StatutOffre(str, enum.Enum):
    nouvelle = "nouvelle"
    traitee = "traitee"
    expiree = "expiree"


class StatutCandidature(str, enum.Enum):
    en_attente = "en_attente"
    confirmee = "confirmee"
    deposee = "deposee"
    rejetee = "rejetee"
    en_entretien = "en_entretien"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    mot_de_passe = Column(String(255), nullable=False)  # bcrypt hash

    anthropic_key = Column(Text, default="")
    adzuna_app_id = Column(String(255), default="")
    adzuna_app_key = Column(Text, default="")
    claude_model = Column(String(100), default="claude-sonnet-4-6")

    notifications_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    profils = relationship("Profil", back_populates="user", cascade="all, delete-orphan")
    snoozes = relationship("Snooze", back_populates="user", cascade="all, delete-orphan")


class Profil(Base):
    __tablename__ = "profils"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    titre = Column(String(200), nullable=False, default="Mon Profil")
    competences = Column(Text, default="[]")
    formation = Column(Text, default="")
    experience = Column(Text, default="")
    langues = Column(String(255), default="")
    cv_path = Column(String(500), default="")
    disponibilite = Column(String(100), default="")
    localisation = Column(String(150), default="")
    secteurs = Column(Text, default="[]")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profils")
    candidatures = relationship("Candidature", back_populates="profil", cascade="all, delete-orphan")

    @property
    def competences_list(self) -> list[str]:
        try:
            return json.loads(str(self.competences or "[]"))
        except Exception:
            return []

    @competences_list.setter
    def competences_list(self, value: list[str]) -> None:
        self.competences = json.dumps(value, ensure_ascii=False)


class Offre(Base):
    __tablename__ = "offres"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False)
    titre = Column(String(300), nullable=False)
    entreprise = Column(String(200), default="")
    localisation = Column(String(150), default="")
    description = Column(Text, default="")
    url = Column(String(500), unique=True, nullable=False)
    date_detection = Column(DateTime, default=datetime.utcnow)
    statut = Column(SAEnum(StatutOffre), default=StatutOffre.nouvelle)
    score_tfidf = Column(Float, default=0.0)
    score_claude = Column(Float, nullable=True)

    candidatures = relationship("Candidature", back_populates="offre")
    snoozes = relationship("Snooze", back_populates="offre", cascade="all, delete-orphan")


class Candidature(Base):
    __tablename__ = "candidatures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profil_id = Column(Integer, ForeignKey("profils.id"), nullable=False)
    offre_id = Column(Integer, ForeignKey("offres.id"), nullable=False)
    lettre_path = Column(String(500), default="")
    cv_genere_path = Column(String(500), default="")
    variante = Column(Integer, default=1)
    statut = Column(SAEnum(StatutCandidature), default=StatutCandidature.en_attente)
    user_consent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    deposee_at = Column(DateTime, nullable=True)

    profil = relationship("Profil", back_populates="candidatures")
    offre = relationship("Offre", back_populates="candidatures")

    @property
    def variante_choisie(self) -> int:
        return int(getattr(self, "variante", 1) or 1)

    @variante_choisie.setter
    def variante_choisie(self, value: int) -> None:
        self.variante = int(value)


class Snooze(Base):
    __tablename__ = "snoozes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    offre_id = Column(Integer, ForeignKey("offres.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    snooze_until = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    offre = relationship("Offre", back_populates="snoozes")
    user = relationship("User", back_populates="snoozes")
