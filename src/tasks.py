"""
Tâches Celery pour BrainStormIA.
Gestion asynchrone des réunions multi-agents avec streaming WebSocket.
"""

import os
import sys
from celery import Celery
from typing import Dict, Any, Optional
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Ajouter le répertoire src au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuration Celery
celery_app = Celery(
    "brainstormia",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0")
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 heure max par tâche
    worker_prefetch_multiplier=1,
)

# Import des services (après initialisation Celery)
try:
    from src.orchestrator.orchestrator import Orchestrator
    from src.services.tts_service import get_tts_service
except ImportError:
    # Fallback pour imports locaux
    from orchestrator.orchestrator import Orchestrator
    from services.tts_service import get_tts_service


class WebSocketOrchestrator(Orchestrator):
    """
    Orchestrateur adapté pour le streaming WebSocket.
    """

    def __init__(
        self,
        objective: str,
        job_id: str,
        model: str = "gpt-4o-mini",
        websocket_callback=None
    ):
        """
        Initialise l'orchestrateur avec callback WebSocket.

        Args:
            objective: Objectif de la réunion
            job_id: ID du job Celery
            model: Modèle LLM
            websocket_callback: Fonction async pour envoyer des messages WebSocket
        """
        super().__init__(objective, model)
        self.job_id = job_id
        self.websocket_callback = websocket_callback
        self.tts_service = None

        # Initialiser TTS si clé disponible
        if os.getenv("ELEVENLABS_API_KEY"):
            try:
                self.tts_service = get_tts_service(use_firebase=False)
            except Exception as e:
                print(f"⚠️  TTS non disponible : {e}")

    def speak(self, agent_id: str, message: str) -> None:
        """
        Envoie un message via WebSocket avec audio.

        Args:
            agent_id: ID de l'agent
            message: Message texte
        """
        # Ajouter à l'historique (hérité)
        super().speak(agent_id, message)

        # Générer l'audio si TTS disponible
        audio_url = None
        if self.tts_service:
            try:
                audio_url = self.tts_service.generate_audio(message, agent_id)
            except Exception as e:
                print(f"⚠️  Erreur TTS pour {agent_id}: {e}")

        # Envoyer via WebSocket (callback synchrone via Redis)
        if self.websocket_callback:
            try:
                # Créer le message WebSocket
                ws_message = {
                    "type": "turn",
                    "agent": agent_id,
                    "text": message,
                    "audio_url": audio_url,
                    "job_id": self.job_id
                }

                # Appeler le callback synchrone
                self.websocket_callback(self.job_id, ws_message)

            except Exception as e:
                print(f"⚠️  Erreur WebSocket : {e}")


@celery_app.task(bind=True, name="brainstormia.start_meeting")
def start_meeting_task(
    self,
    meeting_params: Dict[str, Any],
    job_id: str
) -> Dict[str, Any]:
    """
    Tâche Celery pour démarrer une réunion multi-agents.

    Args:
        meeting_params: Paramètres de la réunion
            - objective: Objectif de la réunion
            - agents: Liste des agents à inclure
            - context_static: Contexte statique (injection directe)
            - use_rag: Utiliser le RAG ou non
            - max_turns: Nombre max de tours
        job_id: ID unique du job

    Returns:
        Résultat de la réunion avec synthèse
    """
    print(f"🚀 Démarrage meeting task : {job_id}")

    # Extraire les paramètres
    objective = meeting_params.get("objective", "Discussion générale")
    max_turns = meeting_params.get("max_turns", 20)
    model = meeting_params.get("model", "gpt-4o-mini")

    # Fonction callback pour WebSocket (via Redis PubSub)
    def websocket_callback(job_id: str, message: dict):
        """
        Callback synchrone pour envoyer des messages WebSocket via Redis.
        """
        import redis
        import json
        r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        r.publish(f"ws:{job_id}", json.dumps(message))

    try:
        # Créer l'orchestrateur
        orchestrator = WebSocketOrchestrator(
            objective=objective,
            job_id=job_id,
            model=model,
            websocket_callback=websocket_callback
        )

        # Message de début
        orchestrator.speak(
            "facilitateur",
            f"🎯 Réunion lancée : {objective}\n\nDémarrage de la discussion..."
        )

        # Boucle de débat
        turn_count = 0

        while turn_count < max_turns and orchestrator.meeting_active:
            turn_count += 1

            # Mettre à jour le statut Celery
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': turn_count,
                    'total': max_turns,
                    'status': f'Tour {turn_count}/{max_turns}'
                }
            )

            # Construire le contexte
            context = orchestrator._build_context(include_rag=True)

            # Vérifier si clôture nécessaire
            if orchestrator._check_facilitator_should_close():
                closing = orchestrator._get_agent_response(
                    "facilitateur",
                    context + "\n\nFormalisez la SYNTHÈSE FINALE et clôturez la réunion."
                )
                orchestrator.speak("facilitateur", closing)
                orchestrator.meeting_active = False
                break

            # Sélectionner le prochain agent
            next_speaker = orchestrator._select_next_speaker(context)

            if next_speaker:
                response = orchestrator._get_agent_response(next_speaker, context)
                orchestrator.speak(next_speaker, response)
            elif turn_count % 5 == 0:
                # Synthèse tous les 5 tours
                synthesis = orchestrator._get_agent_response(
                    "facilitateur",
                    context + "\n\nFaites une synthèse rapide des points clés."
                )
                orchestrator.speak("facilitateur", synthesis)

        # Synthèse finale
        if turn_count >= max_turns:
            final_context = orchestrator._build_context()
            final_summary = orchestrator._get_agent_response(
                "facilitateur",
                final_context + "\n\nFormalisez la SYNTHÈSE FINALE."
            )
            orchestrator.speak("facilitateur", final_summary)

        # Message de fin via WebSocket
        websocket_callback(job_id, {
            "type": "end",
            "job_id": job_id,
            "summary": orchestrator._generate_summary(),
            "turns": len(orchestrator.conversation_history)
        })

        return {
            "status": "completed",
            "job_id": job_id,
            "turns": len(orchestrator.conversation_history),
            "summary": orchestrator._generate_summary()
        }

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Erreur meeting task : {e}")
        print(f"📋 Traceback complet:\n{error_trace}")

        # Envoyer erreur via WebSocket
        try:
            websocket_callback(job_id, {
                "type": "error",
                "job_id": job_id,
                "error": str(e)
            })
        except:
            pass

        return {
            "status": "failed",
            "job_id": job_id,
            "error": str(e)
        }


@celery_app.task(name="brainstormia.index_document")
def index_document_task(file_path: str, doc_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tâche Celery pour indexer un document dans le RAG.

    Args:
        file_path: Chemin du fichier
        doc_id: ID unique du document
        metadata: Métadonnées du document

    Returns:
        Résultat de l'indexation
    """
    from context.qdrant_service import get_qdrant_service

    try:
        print(f"📄 Indexation document : {file_path}")

        rag_service = get_qdrant_service()

        # Charger et indexer
        content = rag_service.load_document(file_path)
        chunk_ids = rag_service.index_document(
            doc_id=doc_id,
            content=content,
            metadata=metadata
        )

        print(f"✅ Document indexé : {len(chunk_ids)} chunks")

        return {
            "status": "completed",
            "doc_id": doc_id,
            "chunks_count": len(chunk_ids)
        }

    except Exception as e:
        print(f"❌ Erreur indexation : {e}")
        return {
            "status": "failed",
            "doc_id": doc_id,
            "error": str(e)
        }
