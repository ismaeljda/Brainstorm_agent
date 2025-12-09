"""
Middleware d'authentification Firebase pour FastAPI.
"""

import os
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import firebase_admin
from firebase_admin import credentials, auth
from typing import Optional


class FirebaseAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour vérifier le Firebase ID Token sur les routes protégées.

    Routes publiques (sans authentification) :
    - /health
    - /docs
    - /openapi.json
    - /static/*
    """

    # Routes publiques qui ne nécessitent pas d'authentification
    PUBLIC_ROUTES = [
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
    ]

    # Préfixes de routes publiques
    PUBLIC_PREFIXES = [
        "/static/",
    ]

    def __init__(self, app, firebase_credentials_path: Optional[str] = None):
        """
        Initialise le middleware Firebase.

        Args:
            app: Application FastAPI
            firebase_credentials_path: Chemin vers le fichier credentials Firebase JSON
        """
        super().__init__(app)

        # Initialiser Firebase Admin SDK si pas déjà fait
        if not firebase_admin._apps:
            if firebase_credentials_path and os.path.exists(firebase_credentials_path):
                cred = credentials.Certificate(firebase_credentials_path)
                firebase_admin.initialize_app(cred)
            else:
                # Mode développement : utiliser les credentials par défaut ou mock
                try:
                    firebase_admin.initialize_app()
                except Exception as e:
                    print(f"⚠️  Firebase non initialisé : {e}")
                    print("ℹ️  L'authentification Firebase est désactivée en mode dev")

    async def dispatch(self, request: Request, call_next):
        """
        Vérifie l'authentification Firebase pour les routes protégées.
        """
        path = request.url.path

        # Vérifier si la route est publique
        if self._is_public_route(path):
            return await call_next(request)

        # Extraire le token du header Authorization
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing or invalid Authorization header"}
            )

        token = auth_header.split("Bearer ")[1]

        # Vérifier le token Firebase
        try:
            decoded_token = auth.verify_id_token(token)

            # Ajouter les infos utilisateur à la requête
            request.state.user = {
                "uid": decoded_token.get("uid"),
                "email": decoded_token.get("email"),
                "name": decoded_token.get("name"),
            }

            return await call_next(request)

        except auth.InvalidIdTokenError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid Firebase ID token"}
            )
        except auth.ExpiredIdTokenError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Expired Firebase ID token"}
            )
        except Exception as e:
            # En mode développement, on peut bypasser l'auth si Firebase n'est pas configuré
            if os.getenv("ENVIRONMENT") == "development":
                request.state.user = {
                    "uid": "dev-user",
                    "email": "dev@brainstormia.local",
                    "name": "Dev User",
                }
                return await call_next(request)

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": f"Authentication error: {str(e)}"}
            )

    def _is_public_route(self, path: str) -> bool:
        """
        Vérifie si une route est publique.

        Args:
            path: Chemin de la route

        Returns:
            True si la route est publique
        """
        # Vérifier les routes exactes
        if path in self.PUBLIC_ROUTES:
            return True

        # Vérifier les préfixes
        for prefix in self.PUBLIC_PREFIXES:
            if path.startswith(prefix):
                return True

        return False


def get_current_user(request: Request) -> dict:
    """
    Récupère l'utilisateur courant depuis la requête.

    Args:
        request: Requête FastAPI

    Returns:
        Informations de l'utilisateur

    Raises:
        HTTPException: Si l'utilisateur n'est pas authentifié
    """
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )

    return request.state.user
