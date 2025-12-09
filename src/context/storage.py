"""
Système de stockage du contexte organisationnel.
"""

import os
import json
from typing import Optional
from .models import OrganizationalContext


class ContextStorage:
    """Gestionnaire de stockage du contexte."""

    def __init__(self, storage_path: str = "data/context.json"):
        """
        Initialise le gestionnaire de stockage.

        Args:
            storage_path: Chemin du fichier de stockage
        """
        self.storage_path = storage_path
        self._ensure_storage_dir()

    def _ensure_storage_dir(self) -> None:
        """Crée le répertoire de stockage s'il n'existe pas."""
        storage_dir = os.path.dirname(self.storage_path)
        if storage_dir and not os.path.exists(storage_dir):
            os.makedirs(storage_dir)

    def save(self, context: OrganizationalContext) -> None:
        """
        Sauvegarde le contexte.

        Args:
            context: Contexte à sauvegarder
        """
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            f.write(context.to_json())

    def load(self) -> Optional[OrganizationalContext]:
        """
        Charge le contexte depuis le stockage.

        Returns:
            Contexte chargé ou None si pas de contexte
        """
        if not os.path.exists(self.storage_path):
            return None

        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return OrganizationalContext.from_dict(data)
        except Exception as e:
            print(f"Erreur lors du chargement du contexte : {e}")
            return None

    def delete(self) -> None:
        """Supprime le contexte stocké."""
        if os.path.exists(self.storage_path):
            os.remove(self.storage_path)

    def exists(self) -> bool:
        """Vérifie si un contexte existe."""
        return os.path.exists(self.storage_path)
