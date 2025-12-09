"""
Modèles de données pour les utilisateurs BrainStormIA.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class UserProfile(BaseModel):
    """Profil utilisateur."""
    uid: str
    email: EmailStr
    name: Optional[str] = None
    photo_url: Optional[str] = None
    created_at: datetime
    last_login: datetime

    # Préférences utilisateur
    preferences: Optional[dict] = {
        "notifications_enabled": True,
        "default_model": "gpt-4o-mini",
        "default_max_turns": 20,
        "language": "fr"
    }

    # Statistiques
    meetings_count: int = 0
    total_tokens_used: int = 0


class UserCreate(BaseModel):
    """Données pour créer un utilisateur."""
    uid: str
    email: EmailStr
    name: Optional[str] = None
    photo_url: Optional[str] = None


class UserUpdate(BaseModel):
    """Données pour mettre à jour un utilisateur."""
    name: Optional[str] = None
    photo_url: Optional[str] = None
    preferences: Optional[dict] = None


class MeetingHistory(BaseModel):
    """Historique d'une réunion."""
    meeting_id: str
    user_uid: str
    objective: str
    created_at: datetime
    duration_seconds: int
    turns_count: int
    agents_used: List[str]
    summary: str
    tokens_used: int


class UserStats(BaseModel):
    """Statistiques utilisateur."""
    total_meetings: int
    total_duration_minutes: int
    total_tokens: int
    favorite_agents: List[str]
    meetings_this_week: int
    meetings_this_month: int
