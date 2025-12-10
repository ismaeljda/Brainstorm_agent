"""
Application Flask pour l'interface Meeting Room multi-agents.
Système de brainstorming avec agents IA vocaux.
"""

import os
import io
import requests
from flask import Flask, render_template, request, jsonify, send_file, session
from flask_cors import CORS
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
import sys

# Charger les variables d'environnement (override=True pour écraser les variables système)
load_dotenv(".env", override=True)

# Ajouter le dossier src au path pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Initialiser Flask
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app)

# Initialiser ElevenLabs
elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

# Configuration
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

# Voix ElevenLabs pour les agents (basé sur src/agents/prompts.py)
AGENT_VOICES = {
    'facilitateur': '21m00Tcm4TlvDq8ikWAM',  # Rachel - Professional female
    'strategie': 'pNInz6obpgDQGcFmaJgB',     # Adam - Articulate male
    'tech': 'TxGEqnHWrfWFTfGW9XjX',          # Josh - Clear male
    'creatif': 'EXAVITQu4vr4xnSDxMaL',      # Bella - Enthusiastic female
}

# Stocker les orchestrateurs par session
orchestrators = {}


def get_orchestrator(session_id: str, meeting_context: dict = None):
    """Récupère ou crée un orchestrateur pour une session."""
    if session_id not in orchestrators:
        from agents.prompts import AGENTS_PROMPTS
        from orchestrator import IntelligentOrchestrator

        agents_config = {
            'facilitateur': {'name': 'Facilitateur', 'prompt': AGENTS_PROMPTS['facilitateur'], 'voice': 'facilitateur'},
            'strategie': {'name': 'Stratège Business', 'prompt': AGENTS_PROMPTS['strategie'], 'voice': 'strategie'},
            'tech': {'name': 'Tech Lead', 'prompt': AGENTS_PROMPTS['tech'], 'voice': 'tech'},
            'creatif': {'name': 'Creative Thinker', 'prompt': AGENTS_PROMPTS['creatif'], 'voice': 'creatif'}
        }

        orchestrators[session_id] = IntelligentOrchestrator(agents_config, meeting_context)

    return orchestrators[session_id]


@app.route('/')
def index():
    """Page d'accueil avec assistant IA pour créer le brief."""
    return render_template('index.html')


@app.route('/meeting')
def meeting_room():
    """Interface de meeting room - Style Teams/Zoom professionnel."""
    return render_template('meeting.html')


@app.route('/static/anam-sdk.js')
def anam_sdk():
    """Serve Anam SDK locally."""
    sdk_path = os.path.join(os.path.dirname(__file__), 'node_modules/@anam-ai/js-sdk/dist/umd/anam.js')
    return send_file(sdk_path, mimetype='application/javascript')


@app.route('/api/transcribe', methods=['POST'])
def transcribe_audio():
    """
    Transcrit l'audio envoyé depuis le navigateur avec Whisper.
    """
    import tempfile
    from openai import OpenAI

    temp_path = None

    try:
        # Vérifier qu'un fichier audio a été envoyé
        if 'audio' not in request.files:
            return jsonify({'error': 'Aucun fichier audio fourni'}), 400

        audio_file = request.files['audio']

        # Sauvegarder le fichier temporairement
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_audio:
            audio_file.save(temp_audio.name)
            temp_path = temp_audio.name

        print(f"📦 Fichier audio reçu: {os.path.getsize(temp_path)} bytes")

        # Transcrire avec Whisper (OpenAI)
        print("🎤 Transcription avec Whisper...")
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        with open(temp_path, 'rb') as audio_file_obj:
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file_obj,
                language="fr"
            )

        text = transcript.text
        print(f"📝 Transcription: {text}")

        return jsonify({
            'success': True,
            'text': text
        })

    except Exception as e:
        print(f"❌ Erreur de transcription: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

    finally:
        # Nettoyer le fichier temporaire
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


@app.route('/api/speak', methods=['POST'])
def text_to_speech():
    """
    Convertit le texte en audio avec ElevenLabs et renvoie le fichier audio.
    Supporte les multi-voix pour le système d'agents.
    """
    try:
        data = request.json
        text = data.get('text', '')
        agent_id = data.get('agent', None)  # Optionnel: pour multi-agent

        if not text:
            return jsonify({'error': 'Aucun texte fourni'}), 400

        # Choisir la voix: agent spécifique ou voix par défaut
        if agent_id and agent_id in AGENT_VOICES:
            voice_id = AGENT_VOICES[agent_id]
            print(f"🎵 Génération audio pour agent '{agent_id}': '{text[:50]}...'")
        else:
            voice_id = ELEVENLABS_VOICE_ID
            print(f"🔊 Génération audio: '{text[:50]}...'")

        # Générer l'audio avec ElevenLabs (nouvelle API)
        audio_generator = elevenlabs_client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id="eleven_multilingual_v2"
        )

        # Convertir en bytes
        audio_bytes = b"".join(audio_generator)

        # Retourner l'audio
        return send_file(
            io.BytesIO(audio_bytes),
            mimetype='audio/mpeg',
            as_attachment=False
        )

    except Exception as e:
        print(f"❌ Erreur de synthèse vocale: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



@app.route('/api/token', methods=['GET'])
def get_realtime_token():
    """
    Génère un token éphémère pour l'API OpenAI Realtime.
    Permet au frontend de se connecter au WebSocket OpenAI sans exposer la clé API.
    """
    try:
        print("🔑 Génération token OpenAI Realtime API...")

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OPENAI_API_KEY non trouvée dans l'environnement!")
            return jsonify({'error': 'OPENAI_API_KEY not configured'}), 500

        print(f"✓ Clé API chargée (longueur: {len(api_key)} caractères)")

        response = requests.post(
            'https://api.openai.com/v1/realtime/sessions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'gpt-4o-realtime-preview-2024-12-17',
                'voice': 'alloy'
            }
        )

        if response.status_code != 200:
            print(f"❌ Erreur API OpenAI: {response.status_code}")
            print(f"Réponse: {response.text}")
            return jsonify({'error': 'Failed to generate token', 'details': response.text}), 500

        data = response.json()
        print(f"✅ Token généré")

        return jsonify({
            'token': data['client_secret']['value'],
            'expires_at': data['client_secret']['expires_at']
        })

    except Exception as e:
        print(f"❌ Erreur génération token: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/agents_config', methods=['GET'])
def get_agents_config():
    """
    Retourne la configuration des agents depuis src/agents/prompts.py
    pour alimenter l'orchestrateur OpenAI Realtime.
    """
    try:
        # Charger les prompts depuis src/agents/prompts.py
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        from agents.prompts import AGENTS_PROMPTS

        # Construire le prompt d'orchestrateur avec les vraies personnalités
        orchestrator_prompt = """You are an intelligent MEETING ORCHESTRATOR who facilitates a DISCUSSION BETWEEN AGENTS. SPEAK IN ENGLISH.

🎯 CONVERSATION FLOW:
1. User launches a topic → Facilitator asks ONE question to a specific agent
2. The questioned agent responds (2 sentences max)
3. Facilitator follows up with a question to ANOTHER agent
4. Agents respond to each other and build the solution together

📋 ORCHESTRATION RULES:
- Alternate between agents to create a real conversation
- Facilitator ALWAYS launches questions, never long answers
- Each agent must intervene according to their expertise
- Create a natural flow: question → answer → new question → answer...

ABSOLUTE RULE:
- ALWAYS start with: [AGENT: name]
- Examples: "[AGENT: facilitateur] ...", "[AGENT: strategie] ...", "[AGENT: tech] ...", "[AGENT: creatif] ..."
- EXACTLY respect each agent's rules (number of sentences, style, etc.)

AVAILABLE AGENTS:

--- FACILITATOR ---
""" + AGENTS_PROMPTS['facilitateur'] + """

--- BUSINESS STRATEGIST ---
""" + AGENTS_PROMPTS['strategie'] + """

--- TECH LEAD ---
""" + AGENTS_PROMPTS['tech'] + """

--- CREATIVE THINKER ---
""" + AGENTS_PROMPTS['creatif'] + """

💡 EXAMPLE FLOW:
User: "I want to create a project management app"
→ [AGENT: facilitateur] Strategist: what's the target market?
→ [AGENT: strategie] Target: SMBs 10-50 employees. Freemium model + team subscriptions.
→ [AGENT: facilitateur] Tech Lead: how long to build?
→ [AGENT: tech] Doable. MVP: 2-3 months with simple stack.
→ [AGENT: facilitateur] Creative: how to differentiate?
→ [AGENT: creatif] Slack-like interface with threads. Simple tech, strong UX impact.

IMPORTANT: Make agents talk to each other to build the solution together!"""

        return jsonify({
            'orchestrator_prompt': orchestrator_prompt,
            'agents': {
                'facilitateur': {'name': 'Facilitateur', 'voice': 'facilitateur'},
                'strategie': {'name': 'Stratège Business', 'voice': 'strategie'},
                'tech': {'name': 'Tech Lead', 'voice': 'tech'},
                'creatif': {'name': 'Creative Thinker', 'voice': 'creatif'}
            }
        })

    except Exception as e:
        print(f"❌ Erreur chargement config agents: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/orchestrator/init', methods=['POST'])
def init_orchestrator():
    """Initialise une nouvelle session d'orchestration avec le contexte du meeting."""
    try:
        import uuid
        session_id = str(uuid.uuid4())
        session['orchestrator_id'] = session_id

        # Récupérer le contexte du meeting
        data = request.get_json(silent=True) or {}
        meeting_context = data.get('context', {})

        print(f"📋 Contexte du meeting reçu: {meeting_context}")

        # Créer l'orchestrateur avec le contexte
        orchestrator = get_orchestrator(session_id, meeting_context)

        # Message initial optionnel
        initial_message = data.get('initial_message', '')
        if initial_message:
            orchestrator.add_message('user', initial_message)

        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': 'Orchestrateur initialisé avec contexte'
        })

    except Exception as e:
        print(f"❌ Erreur init orchestrateur: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/orchestrator/add_message', methods=['POST'])
def add_user_message():
    """Ajoute un message utilisateur à l'historique."""
    try:
        session_id = session.get('orchestrator_id')
        if not session_id:
            return jsonify({'error': 'Session non initialisée'}), 400

        data = request.json
        message = data.get('message', '')

        if not message:
            return jsonify({'error': 'Message vide'}), 400

        orchestrator = get_orchestrator(session_id)
        orchestrator.add_message('user', message)

        return jsonify({
            'success': True,
            'turn': orchestrator.turn_count
        })

    except Exception as e:
        print(f"❌ Erreur ajout message: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/orchestrator/next_turn', methods=['POST'])
def orchestrate_next_turn():
    """
    Orchestre le prochain tour de conversation.
    Mode RAPIDE activé par défaut pour minimiser la latence.
    """
    try:
        session_id = session.get('orchestrator_id')
        if not session_id:
            return jsonify({'error': 'Session non initialisée'}), 400

        orchestrator = get_orchestrator(session_id)

        # Orchestrer le tour (fast_mode=True par défaut)
        result = orchestrator.orchestrate_turn()

        return jsonify({
            'success': True,
            'agent_id': result['agent_id'],
            'message': result['message'],
            'reasoning': result['reasoning'],
            'debate_mode': result['debate_mode'],
            'turn': result['turn']
        })

    except Exception as e:
        print(f"❌ Erreur orchestration: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/orchestrator/status', methods=['GET'])
def get_orchestrator_status():
    """Récupère le statut de l'orchestrateur."""
    try:
        session_id = session.get('orchestrator_id')
        if not session_id:
            return jsonify({'error': 'Session non initialisée'}), 400

        orchestrator = get_orchestrator(session_id)

        return jsonify({
            'success': True,
            'turn_count': orchestrator.turn_count,
            'debate_mode': orchestrator.debate_mode,
            'last_speaker': orchestrator.last_speaker,
            'history_length': len(orchestrator.conversation_history)
        })

    except Exception as e:
        print(f"❌ Erreur statut: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/orchestrator/reset', methods=['POST'])
def reset_orchestrator():
    """Réinitialise l'orchestrateur."""
    try:
        session_id = session.get('orchestrator_id')
        if session_id and session_id in orchestrators:
            del orchestrators[session_id]

        session.pop('orchestrator_id', None)

        return jsonify({
            'success': True,
            'message': 'Orchestrateur réinitialisé'
        })

    except Exception as e:
        print(f"❌ Erreur reset: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/anam/session', methods=['POST'])
def create_anam_session():
    """
    Crée une session Anam sécurisée pour le client.
    Échange la clé API contre un token de session temporaire.
    """
    try:
        anam_api_key = os.getenv("ANAM_API_KEY")
        if not anam_api_key or anam_api_key == "your_anam_api_key_here":
            return jsonify({
                'error': 'ANAM_API_KEY not configured. Please add your Anam API key to .env file'
            }), 500

        data = request.get_json(silent=True) or {}
        persona_id = data.get('persona_id', None)

        # Define different avatars and voices for each agent
        # You can customize these IDs from your Anam Lab account
        agent_configs = {
            'facilitateur': {
                'name': 'Facilitator',
                'avatarId': '30fa96d0-26c4-4e55-94a0-517025942e18',  # Default Cara avatar
                'voiceId': '6bfbe25a-979d-40f3-a92b-5394170af54b',
                'llmId': 'llm-gpt-4o-mini-2024-07-18',
                'systemPrompt': "[STYLE] Reply in natural speech without formatting. Add pauses using '...' and very occasionally a disfluency. [PERSONALITY] You are a professional facilitator who guides brainstorming sessions."
            },
            'strategie': {
                'name': 'Business Strategist',
                'avatarId': '30fa96d0-26c4-4e55-94a0-517025942e18',
                'voiceId': '6bfbe25a-979d-40f3-a92b-5394170af54b',
                'llmId': 'llm-gpt-4o-mini-2024-07-18',
                'systemPrompt': "[STYLE] Reply in natural speech without formatting. Add pauses using '...' and very occasionally a disfluency. [PERSONALITY] You are a business strategist expert."
            },
            'tech': {
                'name': 'Tech Lead',
                'avatarId': '30fa96d0-26c4-4e55-94a0-517025942e18',
                'voiceId': '6bfbe25a-979d-40f3-a92b-5394170af54b',
                'llmId': 'llm-gpt-4o-mini-2024-07-18',
                'systemPrompt': "[STYLE] Reply in natural speech without formatting. Add pauses using '...' and very occasionally a disfluency. [PERSONALITY] You are a technical architect expert."
            },
            'creatif': {
                'name': 'Creative Thinker',
                'avatarId': '30fa96d0-26c4-4e55-94a0-517025942e18',
                'voiceId': '6bfbe25a-979d-40f3-a92b-5394170af54b',
                'llmId': 'llm-gpt-4o-mini-2024-07-18',
                'systemPrompt': "[STYLE] Reply in natural speech without formatting. Add pauses using '...' and very occasionally a disfluency. [PERSONALITY] You are a creative director expert."
            }
        }

        persona_config = agent_configs.get(persona_id, agent_configs['facilitateur'])

        # Créer une session Anam via leur API avec la config complète
        anam_response = requests.post(
            'https://api.anam.ai/v1/auth/session-token',
            headers={
                'Authorization': f'Bearer {anam_api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'personaConfig': persona_config
            }
        )

        if anam_response.status_code != 200:
            print(f"❌ Erreur API Anam: {anam_response.status_code}")
            print(f"Réponse: {anam_response.text}")
            return jsonify({
                'error': 'Failed to create Anam session',
                'details': anam_response.text
            }), 500

        session_data = anam_response.json()
        print(f"✅ Session Anam créée: {session_data}")

        # The response should contain sessionToken
        return jsonify({
            'success': True,
            'session_token': session_data.get('sessionToken') or session_data.get('session_token'),
            'session_id': session_data.get('sessionId') or session_data.get('session_id')
        })

    except Exception as e:
        print(f"❌ Erreur création session Anam: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("\n╔════════════════════════════════════════════════════════════════╗")
    print("║                                                                ║")
    print("║           🎭  AI MEETING ROOM - MULTI-AGENTS  🎭                ║")
    print("║                                                                ║")
    print("║  Serveur démarré sur http://localhost:5000/meeting             ║")
    print("║                                                                ║")
    print("╚════════════════════════════════════════════════════════════════╝\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
