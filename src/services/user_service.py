"""
Service de gestion des utilisateurs avec Firebase Firestore.
"""

import os
from typing import Optional, List
from datetime import datetime
import firebase_admin
from firebase_admin import firestore
from src.models.user import UserProfile, UserCreate, UserUpdate, MeetingHistory, UserStats


class UserService:
    """Service de gestion des utilisateurs."""

    def __init__(self):
        """Initialise le service utilisateur."""
        # Utiliser Firestore si Firebase est initialisé
        try:
            self.db = firestore.client()
            self.enabled = True
        except Exception as e:
            print(f"⚠️  Firestore non disponible : {e}")
            self.db = None
            self.enabled = False

    def get_user(self, uid: str) -> Optional[UserProfile]:
        """
        Récupère un utilisateur par son UID.

        Args:
            uid: UID Firebase de l'utilisateur

        Returns:
            Profil utilisateur ou None
        """
        if not self.enabled:
            return None

        try:
            user_ref = self.db.collection('users').document(uid)
            user_doc = user_ref.get()

            if user_doc.exists:
                data = user_doc.to_dict()
                return UserProfile(**data)

            return None

        except Exception as e:
            print(f"❌ Erreur récupération utilisateur {uid}: {e}")
            return None

    def create_user(self, user_data: UserCreate) -> Optional[UserProfile]:
        """
        Crée un nouvel utilisateur.

        Args:
            user_data: Données de l'utilisateur

        Returns:
            Profil utilisateur créé ou None
        """
        if not self.enabled:
            return None

        try:
            now = datetime.utcnow()

            user_profile = UserProfile(
                uid=user_data.uid,
                email=user_data.email,
                name=user_data.name,
                photo_url=user_data.photo_url,
                created_at=now,
                last_login=now,
                meetings_count=0,
                total_tokens_used=0
            )

            # Sauvegarder dans Firestore
            user_ref = self.db.collection('users').document(user_data.uid)
            user_ref.set(user_profile.model_dump())

            print(f"✅ Utilisateur créé : {user_data.email}")
            return user_profile

        except Exception as e:
            print(f"❌ Erreur création utilisateur : {e}")
            return None

    def update_user(self, uid: str, user_data: UserUpdate) -> Optional[UserProfile]:
        """
        Met à jour un utilisateur.

        Args:
            uid: UID de l'utilisateur
            user_data: Données à mettre à jour

        Returns:
            Profil utilisateur mis à jour ou None
        """
        if not self.enabled:
            return None

        try:
            user_ref = self.db.collection('users').document(uid)

            # Récupérer l'utilisateur existant
            user_doc = user_ref.get()
            if not user_doc.exists:
                return None

            # Préparer les données de mise à jour
            update_data = user_data.model_dump(exclude_none=True)

            # Mettre à jour
            user_ref.update(update_data)

            # Récupérer et retourner l'utilisateur mis à jour
            return self.get_user(uid)

        except Exception as e:
            print(f"❌ Erreur mise à jour utilisateur {uid}: {e}")
            return None

    def update_last_login(self, uid: str):
        """
        Met à jour la date de dernière connexion.

        Args:
            uid: UID de l'utilisateur
        """
        if not self.enabled:
            return

        try:
            user_ref = self.db.collection('users').document(uid)
            user_ref.update({'last_login': datetime.utcnow()})

        except Exception as e:
            print(f"❌ Erreur update last_login {uid}: {e}")

    def add_meeting_history(self, meeting: MeetingHistory):
        """
        Ajoute une réunion à l'historique utilisateur.

        Args:
            meeting: Données de la réunion
        """
        if not self.enabled:
            return

        try:
            # Sauvegarder la réunion
            meeting_ref = self.db.collection('meetings').document(meeting.meeting_id)
            meeting_ref.set(meeting.model_dump())

            # Mettre à jour les statistiques utilisateur
            user_ref = self.db.collection('users').document(meeting.user_uid)
            user_ref.update({
                'meetings_count': firestore.Increment(1),
                'total_tokens_used': firestore.Increment(meeting.tokens_used)
            })

            print(f"✅ Réunion {meeting.meeting_id} ajoutée à l'historique")

        except Exception as e:
            print(f"❌ Erreur ajout historique : {e}")

    def get_user_meetings(self, uid: str, limit: int = 10) -> List[MeetingHistory]:
        """
        Récupère l'historique des réunions d'un utilisateur.

        Args:
            uid: UID de l'utilisateur
            limit: Nombre maximum de réunions à récupérer

        Returns:
            Liste des réunions
        """
        if not self.enabled:
            return []

        try:
            meetings_ref = self.db.collection('meetings') \
                .where('user_uid', '==', uid) \
                .order_by('created_at', direction=firestore.Query.DESCENDING) \
                .limit(limit)

            meetings = []
            for doc in meetings_ref.stream():
                meetings.append(MeetingHistory(**doc.to_dict()))

            return meetings

        except Exception as e:
            print(f"❌ Erreur récupération historique {uid}: {e}")
            return []

    def get_user_stats(self, uid: str) -> Optional[UserStats]:
        """
        Récupère les statistiques d'un utilisateur.

        Args:
            uid: UID de l'utilisateur

        Returns:
            Statistiques utilisateur
        """
        if not self.enabled:
            return None

        try:
            # Récupérer toutes les réunions de l'utilisateur
            meetings_ref = self.db.collection('meetings').where('user_uid', '==', uid)

            total_meetings = 0
            total_duration = 0
            total_tokens = 0
            agents_count = {}
            meetings_this_week = 0
            meetings_this_month = 0

            now = datetime.utcnow()
            week_ago = now.replace(day=now.day - 7)
            month_ago = now.replace(day=1)

            for doc in meetings_ref.stream():
                meeting = doc.to_dict()
                total_meetings += 1
                total_duration += meeting.get('duration_seconds', 0)
                total_tokens += meeting.get('tokens_used', 0)

                # Compter les agents
                for agent in meeting.get('agents_used', []):
                    agents_count[agent] = agents_count.get(agent, 0) + 1

                # Compter par période
                created_at = meeting.get('created_at')
                if created_at:
                    if created_at >= week_ago:
                        meetings_this_week += 1
                    if created_at >= month_ago:
                        meetings_this_month += 1

            # Agents favoris (top 3)
            favorite_agents = sorted(agents_count.items(), key=lambda x: x[1], reverse=True)[:3]
            favorite_agents = [agent for agent, _ in favorite_agents]

            return UserStats(
                total_meetings=total_meetings,
                total_duration_minutes=total_duration // 60,
                total_tokens=total_tokens,
                favorite_agents=favorite_agents,
                meetings_this_week=meetings_this_week,
                meetings_this_month=meetings_this_month
            )

        except Exception as e:
            print(f"❌ Erreur calcul stats {uid}: {e}")
            return None


# Instance globale du service
_user_service: Optional[UserService] = None


def get_user_service() -> UserService:
    """Récupère l'instance du service utilisateur."""
    global _user_service
    if _user_service is None:
        _user_service = UserService()
    return _user_service
