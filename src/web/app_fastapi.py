"""
Backend FastAPI avec intégration Inngest pour monitoring du RAG.
FastAPI supporte nativement async, parfait pour Inngest.
Avec WebSocket pour streaming temps réel et Celery pour async.
"""

import sys
import os
import io
import requests
from fastapi import FastAPI, File, UploadFile, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from threading import Thread, Lock
from queue import Queue
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import uuid
import json
import redis
import asyncio
from openai import OpenAI
from elevenlabs.client import ElevenLabs

# Charger les variables d'environnement
load_dotenv()

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator import Orchestrator
from context import OrganizationalContext, ContextStorage
from context.qdrant_service import get_qdrant_service
from middleware.firebase_auth import FirebaseAuthMiddleware, get_current_user
from models.user import UserCreate, UserUpdate, UserProfile
from services.user_service import get_user_service

# Import Celery tasks (import lazy pour éviter les dépendances circulaires)
# Les tasks seront importés seulement quand on en a besoin

# ==================== FASTAPI APP ====================

app = FastAPI(
    title="DebateHub API",
    description="Multi-agent debate system with RAG",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
UPLOAD_FOLDER = 'data/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'doc', 'docx', 'xls', 'xlsx'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
MAX_UPLOAD_SIZE = 16 * 1024 * 1024  # 16MB

# Créer les répertoires nécessaires
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# Templates et static files
templates = Jinja2Templates(directory=TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Initialiser le gestionnaire de contexte
context_storage = ContextStorage()

# Initialiser les clients pour le système vocal
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

# ElevenLabs voice IDs pour le système multi-agents vocal
AGENT_VOICES = {
    'ceo': '21m00Tcm4TlvDq8ikWAM',      # Rachel - Professional female
    'marketing': 'EXAVITQu4vr4xnSDxMaL',  # Bella - Enthusiastic female
    'tech': 'TxGEqnHWrfWFTfGW9XjX',      # Josh - Clear male
    'finance': 'pNInz6obpgDQGcFmaJgB',    # Adam - Articulate male
}
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

# État global de la réunion
meeting_state = {
    'orchestrator': None,
    'objective': '',
    'messages': [],
    'new_messages': Queue(),
    'meeting_active': False,
    'lock': Lock()
}



# ==================== PYDANTIC MODELS ====================

class MeetingStart(BaseModel):
    objective: str = "Discussion générale"


class MessageSend(BaseModel):
    message: str


class ContextSave(BaseModel):
    context: Dict[str, Any]


class ContextPreview(BaseModel):
    context: Dict[str, Any]


class SearchQuery(BaseModel):
    query: str
    top_k: int = 5


class RAGQuery(BaseModel):
    question: str
    top_k: int = 5


# ==================== WEB ORCHESTRATOR ====================

class WebOrchestrator(Orchestrator):
    """Version modifiée de l'orchestrateur pour l'interface web."""

    def speak(self, agent_id: str, message: str) -> None:
        self.conversation_history.append({
            "agent": agent_id,
            "message": message
        })

        meeting_state['new_messages'].put({
            'agent': agent_id,
            'message': message
        })

        with meeting_state['lock']:
            meeting_state['messages'].append({
                'agent': agent_id,
                'message': message
            })

    def _get_human_input_async(self):
        return None

    def run_meeting_web(self):
        meeting_state['meeting_active'] = True
        self.speak("facilitateur", f"Bonjour ! Je suis le facilitateur de cette réunion. Notre objectif aujourd'hui : {self.objective}\n\nN'hésitez pas à lancer la discussion quand vous êtes prêt. Les agents réagiront selon leur expertise.")

        import time
        while meeting_state['meeting_active']:
            time.sleep(1)


# ==================== ROUTES MEETING ====================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Page d'accueil - Interface vocale unifiée avec RAG."""
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/text", response_class=HTMLResponse)
async def text_meeting(request: Request):
    """Interface texte originale (ancienne version pour référence)."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/context", response_class=HTMLResponse)
async def context_page(request: Request):
    """Page de gestion du contexte."""
    return templates.TemplateResponse("context.html", {"request": request})


@app.post("/start_meeting")
async def start_meeting(data: MeetingStart):
    """Démarre une nouvelle réunion."""
    with meeting_state['lock']:
        meeting_state['objective'] = data.objective
        meeting_state['messages'] = []
        meeting_state['orchestrator'] = WebOrchestrator(
            objective=data.objective,
            model="gpt-4o-mini"
        )

    thread = Thread(target=meeting_state['orchestrator'].run_meeting_web)
    thread.daemon = True
    thread.start()

    return {
        'status': 'ok',
        'message': 'Réunion démarrée'
    }


@app.post("/send_message")
async def send_message(data: MessageSend):
    """Envoie un message humain à la réunion."""
    if not data.message:
        raise HTTPException(status_code=400, detail="Message vide")

    orchestrator = meeting_state['orchestrator']
    if not orchestrator:
        raise HTTPException(status_code=400, detail="Réunion non démarrée")

    print(f"\n📨 Message humain reçu : {data.message}")

    orchestrator.speak('human', data.message)

    context_with_rag = orchestrator._build_context(include_rag=True)

    print(f"📊 Contexte construit : {len(context_with_rag)} caractères")
    print(f"\n🔍 CONTEXTE COMPLET ENVOYÉ AUX AGENTS:")
    print("=" * 80)
    print(context_with_rag)
    print("=" * 80)
    print()

    agents_spoken = []
    max_responses = 2

    for i in range(max_responses):
        print(f"\n🤖 Tour {i+1}/{max_responses}")

        # CHAQUE agent interroge le RAG systématiquement
        print(f"🔄 Reconstruction du contexte avec RAG pour agent {i+1}...")
        context = orchestrator._build_context(include_rag=True)

        next_speaker = orchestrator._select_next_speaker(context)
        print(f"🎯 Agent sélectionné : {next_speaker}")

        if not next_speaker or next_speaker in agents_spoken:
            print(f"⏹️ Arrêt : {'Aucun agent' if not next_speaker else 'Agent déjà parlé'}")
            break

        print(f"⏳ Génération réponse de {next_speaker}...")
        response = orchestrator._get_agent_response(next_speaker, context)
        print(f"✅ Réponse générée : {len(response)} caractères")

        orchestrator.speak(next_speaker, response)
        agents_spoken.append(next_speaker)

    return {'status': 'ok', 'agents_responded': len(agents_spoken)}


@app.get("/get_messages")
async def get_messages():
    """Récupère les nouveaux messages."""
    new_messages = []

    while not meeting_state['new_messages'].empty():
        new_messages.append(meeting_state['new_messages'].get())

    return {
        'messages': new_messages,
        'objective': meeting_state['objective'],
        'meeting_active': meeting_state['meeting_active'],
        'status': 'Réunion en cours' if meeting_state['meeting_active'] else 'Réunion terminée'
    }


@app.post("/stop_meeting")
async def stop_meeting():
    """Arrête la réunion en cours."""
    meeting_state['meeting_active'] = False
    return {'status': 'ok', 'message': 'Réunion arrêtée'}


# ==================== ROUTES CONTEXTE ====================

def allowed_file(filename: str) -> bool:
    """Vérifie si le fichier est autorisé."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.get("/api/context")
async def get_context():
    """Récupère le contexte actuel."""
    context = context_storage.load()

    if context:
        return {
            'status': 'ok',
            'context': context.to_dict()
        }
    else:
        return {
            'status': 'ok',
            'context': None
        }


@app.post("/api/context")
async def save_context(data: ContextSave):
    """Sauvegarde le contexte."""
    try:
        if not data.context:
            raise HTTPException(status_code=400, detail="Données manquantes")

        context = OrganizationalContext(**data.context)
        context_storage.save(context)

        return {
            'status': 'ok',
            'message': 'Contexte sauvegardé',
            'context': context.to_dict()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/context")
async def delete_context():
    """Supprime le contexte."""
    try:
        context_storage.delete()

        if os.path.exists(UPLOAD_FOLDER):
            for filename in os.listdir(UPLOAD_FOLDER):
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)

        return {'status': 'ok', 'message': 'Contexte supprimé'}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/context/preview")
async def preview_context(data: ContextPreview):
    """Prévisualise le contexte formaté."""
    try:
        if not data.context:
            raise HTTPException(status_code=400, detail="Données manquantes")

        context = OrganizationalContext(**data.context)
        formatted = context.format_for_agents()

        return {
            'status': 'ok',
            'formatted': formatted
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/context/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload un document pour le RAG via Celery (asynchrone).
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Fichier vide")

        if not allowed_file(file.filename):
            raise HTTPException(status_code=400, detail="Type de fichier non autorisé")

        # Lire le contenu
        contents = await file.read()

        if len(contents) > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=400, detail=f"Fichier trop volumineux (max {MAX_UPLOAD_SIZE/1024/1024}MB)")

        # Générer un nom de fichier unique
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

        # Sauvegarder le fichier
        with open(file_path, "wb") as f:
            f.write(contents)

        # Déclencher l'ingestion via Celery
        print(f"📤 Déclenchement indexation Celery pour : {file_path}")

        from src.tasks import index_document_task
        task = index_document_task.apply_async(
            args=[file_path, filename, "default"]
        )

        return {
            'status': 'ok',
            'message': 'Fichier uploadé, indexation en cours',
            'file_path': file_path,
            'task_id': task.id
        }

    except HTTPException:
        raise
    except Exception as e:
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/context/document/{filename}")
async def delete_document(filename: str):
    """Supprime un document."""
    try:
        file_path = None

        for f in os.listdir(UPLOAD_FOLDER):
            if filename in f:
                file_path = os.path.join(UPLOAD_FOLDER, f)
                break

        if file_path and os.path.exists(file_path):
            # Supprimer de Qdrant
            rag_service = get_qdrant_service()
            rag_service.delete_document(filename)

            # Supprimer le fichier
            os.remove(file_path)

        return {'status': 'ok', 'message': 'Document supprimé'}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/context/search")
async def search_context(data: SearchQuery):
    """
    Recherche dans le contexte RAG via Qdrant (synchrone).
    """
    try:
        if not data.query:
            raise HTTPException(status_code=400, detail="Requête vide")

        rag_service = get_qdrant_service()
        results = rag_service.search(data.query, top_k=data.top_k)

        return {
            'status': 'ok',
            'results': results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/context/stats")
async def context_stats():
    """Statistiques Qdrant."""
    try:
        rag_service = get_qdrant_service()
        stats = rag_service.get_collection_stats()

        return {
            'status': 'ok',
            'stats': stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy",
        "qdrant": "connected" if get_qdrant_service() else "disconnected",
        "inngest_dashboard": "http://localhost:8288",
        "celery": "connected",
        "redis": "connected"
    }


# ==================== WEBSOCKET & CELERY ====================

# Gestionnaire de connexions WebSocket
class ConnectionManager:
    """Gère les connexions WebSocket actives."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, job_id: str, websocket: WebSocket):
        """Accepte une nouvelle connexion."""
        await websocket.accept()
        self.active_connections[job_id] = websocket
        print(f"🔌 WebSocket connecté : {job_id}")

    def disconnect(self, job_id: str):
        """Déconnecte un client."""
        if job_id in self.active_connections:
            del self.active_connections[job_id]
            print(f"🔌 WebSocket déconnecté : {job_id}")

    async def send_message(self, job_id: str, message: dict):
        """Envoie un message à un client."""
        if job_id in self.active_connections:
            try:
                await self.active_connections[job_id].send_json(message)
            except Exception as e:
                print(f"❌ Erreur envoi WebSocket : {e}")
                self.disconnect(job_id)

    async def broadcast(self, message: dict):
        """Envoie un message à tous les clients."""
        for job_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"❌ Erreur broadcast WebSocket : {e}")


manager = ConnectionManager()


@app.post("/api/v1/start_meeting")
async def api_start_meeting(data: MeetingStart):
    """
    Démarre une nouvelle réunion via Celery (asynchrone).

    Args:
        data: Paramètres de la réunion

    Returns:
        Job ID pour suivre via WebSocket
    """
    try:
        # Import lazy pour éviter les dépendances au démarrage
        from src.tasks import start_meeting_task

        # Générer un job ID unique
        job_id = str(uuid.uuid4())

        # Préparer les paramètres
        meeting_params = {
            "objective": data.objective,
            "max_turns": 20,
            "model": "gpt-4o-mini"
        }

        # Déclencher la tâche Celery
        task = start_meeting_task.apply_async(
            args=[meeting_params, job_id],
            task_id=job_id
        )

        return {
            "status": "ok",
            "job_id": job_id,
            "task_id": task.id,
            "message": "Réunion démarrée en arrière-plan",
            "websocket_url": f"/ws/meeting/{job_id}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/meeting/{job_id}")
async def websocket_meeting(websocket: WebSocket, job_id: str):
    """
    Endpoint WebSocket pour le streaming en temps réel d'une réunion.

    Args:
        job_id: ID du job Celery

    Streame les messages :
    - {"type": "turn", "agent": "...", "text": "...", "audio_url": "..."}
    - {"type": "end", "summary": "..."}
    - {"type": "error", "error": "..."}
    """
    await manager.connect(job_id, websocket)

    # Connexion Redis pour écouter les messages
    r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

    try:
        # Message de bienvenue
        await websocket.send_json({
            "type": "connected",
            "job_id": job_id,
            "message": "Connecté au streaming de la réunion"
        })

        # S'abonner au canal Redis PubSub
        pubsub = r.pubsub()
        pubsub.subscribe(f"ws:{job_id}")

        # Timeout pour get_message (non-bloquant)
        import time

        # Boucle d'écoute Redis PubSub (non-bloquante)
        try:
            meeting_ended = False
            while not meeting_ended:
                # Récupérer message avec timeout court (non-bloquant)
                message = pubsub.get_message(timeout=0.1)

                if message and message['type'] == 'message':
                    try:
                        # Parser et envoyer le message
                        import json
                        msg_dict = json.loads(message['data'])
                        print(f"📤 Envoi WebSocket: {msg_dict.get('type')}")
                        await websocket.send_json(msg_dict)

                        # Si message de fin ou erreur, arrêter
                        if msg_dict.get("type") in ["end", "completed"]:
                            meeting_ended = True

                    except Exception as e:
                        print(f"❌ Erreur parsing message : {e}")

                # Petit délai pour ne pas surcharger le CPU
                await asyncio.sleep(0.1)

                # Vérifier périodiquement si le job est terminé
                from src.tasks import celery_app
                task_result = celery_app.AsyncResult(job_id)
                if task_result.ready() and not meeting_ended:
                    # Envoyer le résultat final si pas déjà envoyé
                    await websocket.send_json({
                        "type": "completed",
                        "job_id": job_id,
                        "result": task_result.result
                    })
                    meeting_ended = True

        finally:
            pubsub.unsubscribe(f"ws:{job_id}")
            pubsub.close()

    except WebSocketDisconnect:
        print(f"🔌 Client déconnecté : {job_id}")
        manager.disconnect(job_id)

    except Exception as e:
        print(f"❌ Erreur WebSocket : {e}")
        await websocket.send_json({
            "type": "error",
            "error": str(e)
        })

    finally:
        manager.disconnect(job_id)


@app.get("/api/v1/meeting_status/{job_id}")
async def get_meeting_status(job_id: str):
    """
    Récupère le statut d'une réunion en cours.

    Args:
        job_id: ID du job Celery

    Returns:
        Statut de la tâche
    """
    try:
        from src.tasks import celery_app
        task = celery_app.AsyncResult(job_id)

        return {
            "status": "ok",
            "job_id": job_id,
            "task_status": task.status,
            "task_result": task.result if task.ready() else None,
            "task_info": task.info
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/upload_document")
async def api_upload_document(file: UploadFile = File(...)):
    """
    Upload et indexe un document via Celery (asynchrone).

    Args:
        file: Fichier à uploader

    Returns:
        Job ID de l'indexation
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Fichier vide")

        if not allowed_file(file.filename):
            raise HTTPException(status_code=400, detail="Type de fichier non autorisé")

        # Lire et sauvegarder le fichier
        contents = await file.read()

        if len(contents) > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=400, detail=f"Fichier trop volumineux")

        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

        with open(file_path, "wb") as f:
            f.write(contents)

        # Déclencher l'indexation Celery
        from src.tasks import index_document_task
        doc_id = str(uuid.uuid4())
        task = index_document_task.apply_async(
            args=[file_path, doc_id, {"filename": filename}]
        )

        return {
            "status": "ok",
            "job_id": task.id,
            "doc_id": doc_id,
            "message": "Indexation en cours",
            "file_path": file_path
        }

    except HTTPException:
        raise
    except Exception as e:
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ROUTES VOCAL SYSTEM ====================

@app.get("/meeting", response_class=HTMLResponse)
async def meeting_room(request: Request):
    """Interface de meeting room avec multi-agents vocaux."""
    return templates.TemplateResponse("meeting_room.html", {"request": request})


class RAGQueryRequest(BaseModel):
    query: str
    top_k: int = 3


@app.post("/api/rag")
async def rag_query_for_vocal(request: RAGQueryRequest):
    """
    Interroge le RAG et retourne le contexte formaté pour le meeting vocal.
    Utilisé pour enrichir les prompts de l'orchestrateur en temps réel.
    """
    try:
        if not request.query:
            return {'context': '', 'results': []}

        # Chercher dans Qdrant
        rag_service = get_qdrant_service()
        results = rag_service.search(request.query, top_k=request.top_k)

        if not results:
            return {'context': '', 'results': []}

        # Formater le contexte pour l'injection dans le prompt
        context_parts = ["=== CONTEXTE DOCUMENTAIRE PERTINENT ===\n"]
        for i, result in enumerate(results, 1):
            text = result.get('text', '')
            score = result.get('score', 0)
            if score > 0.7:  # Seuil de pertinence
                context_parts.append(f"[Document {i} - Score: {score:.2f}]")
                context_parts.append(text[:500])  # Limiter à 500 caractères
                context_parts.append("")

        formatted_context = "\n".join(context_parts)

        print(f"🔍 RAG Query: '{request.query}' → {len(results)} résultats")

        return {
            'context': formatted_context,
            'results': results,
            'count': len(results)
        }

    except Exception as e:
        print(f"❌ Erreur RAG query: {e}")
        return {'context': '', 'results': [], 'error': str(e)}


class SpeakRequest(BaseModel):
    text: str
    agent: Optional[str] = None


@app.get("/api/token")
async def get_realtime_token():
    """
    Génère un token éphémère pour l'API OpenAI Realtime.
    Ce token permet au frontend de se connecter directement au WebSocket OpenAI
    sans exposer la clé API principale.
    """
    try:
        print("🔑 Génération d'un token éphémère pour OpenAI Realtime API...")

        response = requests.post(
            'https://api.openai.com/v1/realtime/sessions',
            headers={
                'Authorization': f'Bearer {os.getenv("OPENAI_API_KEY")}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'gpt-4o-realtime-preview-2024-12-17',
                'voice': 'alloy'
            }
        )

        if response.status_code != 200:
            print(f"❌ Erreur API OpenAI: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail="Failed to generate token")

        data = response.json()
        token = data['client_secret']['value']
        expires_at = data['client_secret']['expires_at']

        print(f"✅ Token généré (expire: {expires_at})")

        return {
            'token': token,
            'expires_at': expires_at
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur lors de la génération du token: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/speak")
async def text_to_speech(request: SpeakRequest):
    """
    Convertit le texte en audio avec ElevenLabs et renvoie le fichier audio.
    Supporte les multi-voix pour le système d'agents.
    """
    try:
        text = request.text
        agent_id = request.agent

        if not text:
            raise HTTPException(status_code=400, detail="Aucun texte fourni")

        # Choisir la voix: agent spécifique ou voix par défaut
        if agent_id and agent_id in AGENT_VOICES:
            voice_id = AGENT_VOICES[agent_id]
            print(f"🎵 Génération audio pour agent '{agent_id}' ({voice_id}): '{text[:50]}...'")
        else:
            voice_id = ELEVENLABS_VOICE_ID
            print(f"🔊 Génération audio pour: '{text[:50]}...'")

        # Générer l'audio avec ElevenLabs
        audio_generator = elevenlabs_client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id="eleven_multilingual_v2"
        )

        # Convertir en bytes
        audio_bytes = b"".join(audio_generator)

        # Retourner l'audio en streaming
        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=speech.mp3"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur lors de la génération audio: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== USER MANAGEMENT ====================

@app.post("/api/users/me", response_model=UserProfile)
async def create_or_get_user(user_data: UserCreate, request: Request):
    """
    Crée ou récupère le profil utilisateur.
    Appelé lors de la première connexion Firebase.
    """
    try:
        user_service = get_user_service()

        # Vérifier si l'utilisateur existe
        existing_user = user_service.get_user(user_data.uid)

        if existing_user:
            # Mettre à jour last_login
            user_service.update_last_login(user_data.uid)
            return existing_user

        # Créer nouvel utilisateur
        new_user = user_service.create_user(user_data)
        if not new_user:
            raise HTTPException(status_code=500, detail="Erreur création utilisateur")

        return new_user

    except Exception as e:
        print(f"❌ Erreur create_or_get_user : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/users/me", response_model=UserProfile)
async def get_my_profile(request: Request):
    """Récupère le profil de l'utilisateur connecté."""
    try:
        # Récupérer l'utilisateur depuis le middleware Firebase
        user = get_current_user(request)
        user_service = get_user_service()

        profile = user_service.get_user(user["uid"])
        if not profile:
            raise HTTPException(status_code=404, detail="Profil non trouvé")

        return profile

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur get_my_profile : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/users/me", response_model=UserProfile)
async def update_my_profile(user_data: UserUpdate, request: Request):
    """Met à jour le profil de l'utilisateur connecté."""
    try:
        user = get_current_user(request)
        user_service = get_user_service()

        updated_profile = user_service.update_user(user["uid"], user_data)
        if not updated_profile:
            raise HTTPException(status_code=404, detail="Profil non trouvé")

        return updated_profile

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur update_my_profile : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/users/me/meetings")
async def get_my_meetings(request: Request, limit: int = 10):
    """Récupère l'historique des réunions de l'utilisateur."""
    try:
        user = get_current_user(request)
        user_service = get_user_service()

        meetings = user_service.get_user_meetings(user["uid"], limit)

        return {
            "status": "ok",
            "meetings": [meeting.model_dump() for meeting in meetings]
        }

    except Exception as e:
        print(f"❌ Erreur get_my_meetings : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/users/me/stats")
async def get_my_stats(request: Request):
    """Récupère les statistiques de l'utilisateur."""
    try:
        user = get_current_user(request)
        user_service = get_user_service()

        stats = user_service.get_user_stats(user["uid"])
        if not stats:
            raise HTTPException(status_code=404, detail="Statistiques non disponibles")

        return {
            "status": "ok",
            "stats": stats.model_dump()
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur get_my_stats : {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== MAIN ====================

if __name__ == '__main__':
    import uvicorn

    print("🌐 Démarrage du serveur FastAPI BrainStormIA...")
    print("📍 Application : http://localhost:8000")
    print("🎤 Meeting Room Vocal : http://localhost:8000/meeting")
    print("📖 Documentation API : http://localhost:8000/docs")
    print("\n⚠️  Assurez-vous que Redis et Qdrant sont lancés")
    print("   docker-compose up -d redis qdrant")

    uvicorn.run(
        "app_fastapi:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
