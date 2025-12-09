"""
Application web Flask pour l'interface vocale interactive.
Permet de parler via le micro du navigateur et d'écouter la réponse.
"""

import os
import io
import tempfile
import requests
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
from elevenlabs.client import ElevenLabs
import speech_recognition as sr
from pydub import AudioSegment

# Charger les variables d'environnement
load_dotenv("src/.env")

# Initialiser Flask
app = Flask(__name__)
CORS(app)

# Initialiser les clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
recognizer = sr.Recognizer()

# Configuration
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

# Voix ElevenLabs pour les agents (basé sur src/agents/prompts.py)
AGENT_VOICES = {
    'facilitateur': '21m00Tcm4TlvDq8ikWAM',  # Rachel - Professional female
    'strategie': 'pNInz6obpgDQGcFmaJgB',     # Adam - Articulate male
    'tech': 'TxGEqnHWrfWFTfGW9XjX',          # Josh - Clear male
    'creatif': 'EXAVITQu4vr4xnSDxMaL',      # Bella - Enthusiastic female
}


@app.route('/')
def index():
    """Page principale."""
    return render_template('index.html')


@app.route('/api/transcribe', methods=['POST'])
def transcribe_audio():
    """
    Transcrit l'audio envoyé depuis le navigateur.
    Whisper accepte directement WebM, pas besoin de conversion.
    """
    temp_path = None

    try:
        # Vérifier qu'un fichier audio a été envoyé
        if 'audio' not in request.files:
            return jsonify({'error': 'Aucun fichier audio fourni'}), 400

        audio_file = request.files['audio']

        # Sauvegarder le fichier temporairement
        # Whisper API accepte plusieurs formats dont webm, mp3, mp4, mpeg, mpga, m4a, wav
        # Utiliser .wav car c'est ce que le frontend envoie après conversion
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
            audio_file.save(temp_audio.name)
            temp_path = temp_audio.name

        print(f"📦 Fichier reçu: {os.path.getsize(temp_path)} bytes")

        # Transcrire avec Whisper (OpenAI)
        # Whisper accepte directement le format WebM
        print("🎤 Envoi à Whisper...")
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


@app.route('/api/chat', methods=['POST'])
def chat_with_agent():
    """
    Agent conversationnel simple - répond en une seule fois (pas de streaming).
    """
    try:
        data = request.json
        user_message = data.get('text', '')
        conversation_history = data.get('history', [])

        if not user_message:
            return jsonify({'error': 'Aucun message fourni'}), 400

        print(f"💬 Message utilisateur: '{user_message}'")

        # Construire l'historique de conversation
        messages = [
            {
                "role": "system",
                "content": """Tu es un assistant de brainstorming intelligent et créatif.
Tu aides les consultants indépendants à développer leurs idées de business.
Tu poses des questions pertinentes, proposes des idées innovantes et donnes des conseils stratégiques.
Réponds toujours en français de manière claire, concise et professionnelle.
Sois enthousiaste et encourageant.
Fais des phrases courtes et claires."""
            }
        ]

        # Ajouter l'historique de conversation
        messages.extend(conversation_history)

        # Ajouter le nouveau message de l'utilisateur
        messages.append({
            "role": "user",
            "content": user_message
        })

        # Générer la réponse avec GPT (sans streaming)
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=200
        )

        agent_response = response.choices[0].message.content.strip()
        print(f"✅ Réponse agent: '{agent_response}'")

        return jsonify({
            'success': True,
            'response': agent_response
        })

    except Exception as e:
        print(f"❌ Erreur agent: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/chat_stream', methods=['POST'])
def chat_with_agent_stream():
    """
    Agent conversationnel avec streaming - génère et envoie le texte progressivement.
    """
    try:
        data = request.json
        user_message = data.get('text', '')
        conversation_history = data.get('history', [])

        if not user_message:
            return jsonify({'error': 'Aucun message fourni'}), 400

        print(f"💬 Message utilisateur: '{user_message}'")

        # Construire l'historique de conversation
        messages = [
            {
                "role": "system",
                "content": """Tu es un assistant de brainstorming intelligent et créatif.
Tu aides les consultants indépendants à développer leurs idées de business.
Tu poses des questions pertinentes, proposes des idées innovantes et donnes des conseils stratégiques.
Réponds toujours en français de manière claire, concise et professionnelle.
Sois enthousiaste et encourageant.
Fais des phrases courtes et claires."""
            }
        ]

        # Ajouter l'historique de conversation
        messages.extend(conversation_history)

        # Ajouter le nouveau message de l'utilisateur
        messages.append({
            "role": "user",
            "content": user_message
        })

        def generate():
            """Générateur pour le streaming SSE (Server-Sent Events)"""
            try:
                # Générer la réponse avec GPT en streaming
                stream = openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=200,
                    stream=True  # Activer le streaming
                )

                full_response = ""
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        # Envoyer chaque morceau au client
                        yield f"data: {content}\n\n"

                # Envoyer le signal de fin
                yield "data: [DONE]\n\n"

                print(f"✅ Réponse complète: '{full_response}'")

            except Exception as e:
                print(f"❌ Erreur streaming: {e}")
                yield f"data: [ERROR]: {str(e)}\n\n"

        return app.response_class(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )

    except Exception as e:
        print(f"❌ Erreur agent: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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


@app.route('/api/chat_and_speak_stream', methods=['POST'])
def chat_and_speak_stream():
    """
    Streaming intelligent: GPT génère phrase par phrase, chaque phrase est convertie en audio.
    Format de sortie: Server-Sent Events avec texte ET audio encodé en base64.
    """
    try:
        import json
        import base64
        import re

        data = request.json
        user_message = data.get('text', '')
        conversation_history = data.get('history', [])

        if not user_message:
            return jsonify({'error': 'Aucun message fourni'}), 400

        print(f"💬 Message utilisateur: '{user_message}'")

        # Construire l'historique de conversation
        messages = [
            {
                "role": "system",
                "content": """Tu es un assistant de brainstorming intelligent et créatif.
Tu aides les consultants indépendants à développer leurs idées de business.
Tu poses des questions pertinentes, proposes des idées innovantes et donnes des conseils stratégiques.
Réponds toujours en français de manière claire, concise et professionnelle.
Sois enthousiaste et encourageant.
Fais des phrases courtes et claires."""
            }
        ]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})

        def generate():
            """Générateur qui stream texte + audio phrase par phrase"""
            try:
                # Streamer GPT
                stream = openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=200,
                    stream=True
                )

                buffer = ""
                sentence_buffer = []  # Buffer pour accumuler des phrases
                sentence_count = 0
                SENTENCES_PER_CHUNK = 2  # Envoyer par blocs de 2 phrases (plus réactif)

                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        buffer += content

                        # Envoyer le texte immédiatement pour l'affichage
                        yield f"data: {json.dumps({'type': 'text', 'content': content})}\n\n"

                        # Détecter les fins de phrases (plus flexible avec ponctuation)
                        sentences = re.split(r'([.!?]+\s*)', buffer)

                        # Si on a au moins une phrase complète
                        if len(sentences) > 2:
                            # Récupérer toutes les phrases complètes
                            complete_sentences = ''.join(sentences[:-1])
                            buffer = sentences[-1]  # Garder le reste dans le buffer

                            if complete_sentences.strip():
                                sentence_buffer.append(complete_sentences.strip())
                                sentence_count += 1

                                print(f"✅ Phrase #{sentence_count} détectée: '{complete_sentences.strip()[:50]}...'")

                                # Envoyer l'audio par blocs de 2 phrases OU immédiatement si déjà beaucoup de texte
                                if len(sentence_buffer) >= SENTENCES_PER_CHUNK:
                                    text_chunk = ' '.join(sentence_buffer)
                                    sentence_buffer = []  # Vider le buffer

                                    print(f"🎵 Génération audio ({len(sentence_buffer) + SENTENCES_PER_CHUNK} phrases): '{text_chunk[:60]}...'")

                                    # Générer l'audio pour ce bloc SANS ATTENDRE
                                    try:
                                        audio_generator = elevenlabs_client.text_to_speech.convert(
                                            voice_id=ELEVENLABS_VOICE_ID,
                                            text=text_chunk,
                                            model_id="eleven_multilingual_v2"
                                        )
                                        audio_bytes = b"".join(audio_generator)
                                        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

                                        # Envoyer l'audio encodé
                                        audio_data = {'type': 'audio', 'content': audio_base64}
                                        yield f"data: {json.dumps(audio_data)}\n\n"
                                        print(f"✓ Audio envoyé - base64: {len(audio_base64)} chars, audio brut: {len(audio_bytes)} bytes")
                                    except Exception as audio_error:
                                        print(f"⚠️ Erreur audio bloc: {audio_error}")
                                        import traceback
                                        traceback.print_exc()

                # Traiter les phrases restantes (buffer de phrases + texte en cours)
                remaining_text = []
                if sentence_buffer:
                    remaining_text.extend(sentence_buffer)
                if buffer.strip():
                    remaining_text.append(buffer.strip())

                if remaining_text:
                    final_text = ' '.join(remaining_text)
                    print(f"🎵 Génération audio phrases finales: '{final_text[:60]}...'")
                    try:
                        audio_generator = elevenlabs_client.text_to_speech.convert(
                            voice_id=ELEVENLABS_VOICE_ID,
                            text=final_text,
                            model_id="eleven_multilingual_v2"
                        )
                        audio_bytes = b"".join(audio_generator)
                        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                        yield f"data: {json.dumps({'type': 'audio', 'content': audio_base64})}\n\n"
                    except Exception as audio_error:
                        print(f"⚠️ Erreur audio final: {audio_error}")

                # Signal de fin
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                print(f"✅ Streaming terminé - {sentence_count} phrases générées")

            except Exception as e:
                print(f"❌ Erreur streaming: {e}")
                import traceback
                traceback.print_exc()
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        return app.response_class(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )

    except Exception as e:
        print(f"❌ Erreur: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/speak_stream', methods=['POST'])
def text_to_speech_stream():
    """
    Streaming audio avec ElevenLabs - génère l'audio au fur et à mesure.
    """
    try:
        data = request.json
        text = data.get('text', '')

        if not text:
            return jsonify({'error': 'Aucun texte fourni'}), 400

        print(f"🔊 Streaming audio pour: '{text[:50]}...'")

        # Générer l'audio avec ElevenLabs en streaming
        audio_stream = elevenlabs_client.text_to_speech.convert(
            voice_id=ELEVENLABS_VOICE_ID,
            text=text,
            model_id="eleven_multilingual_v2",
            stream=True  # Activer le streaming
        )

        def generate_audio():
            """Générateur pour streamer l'audio"""
            try:
                for chunk in audio_stream:
                    yield chunk
            except Exception as e:
                print(f"❌ Erreur streaming audio: {e}")

        return app.response_class(
            generate_audio(),
            mimetype='audio/mpeg',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )

    except Exception as e:
        print(f"❌ Erreur de synthèse vocale: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/process', methods=['POST'])
def process_voice():
    """
    Endpoint tout-en-un: transcrit l'audio, traduit et génère la réponse vocale.
    """
    try:
        # Vérifier qu'un fichier audio a été envoyé
        if 'audio' not in request.files:
            return jsonify({'error': 'Aucun fichier audio fourni'}), 400

        audio_file = request.files['audio']

        # 1. Transcrire l'audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
            audio_file.save(temp_audio.name)
            temp_path = temp_audio.name

        with open(temp_path, 'rb') as audio:
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio,
                language="fr"
            )

        os.unlink(temp_path)
        french_text = transcript.text
        print(f"📝 Transcription: {french_text}")

        # 2. Traduire le texte
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional translator. Translate the following French text to English. Only respond with the translation, nothing else."
                },
                {
                    "role": "user",
                    "content": french_text
                }
            ],
            temperature=0.3
        )

        translation = response.choices[0].message.content.strip()
        print(f"✅ Traduction: '{translation}'")

        # 3. Générer l'audio de la traduction
        audio_generator = elevenlabs_client.generate(
            text=translation,
            voice=ELEVENLABS_VOICE_ID,
            model="eleven_multilingual_v2"
        )

        audio_bytes = b"".join(audio_generator)

        return jsonify({
            'success': True,
            'transcription': french_text,
            'translation': translation,
            'audio_url': '/api/speak'  # Le frontend devra faire un second appel
        })

    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
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
            print(f"❌ Erreur API OpenAI: {response.status_code}")
            return jsonify({'error': 'Failed to generate token'}), 500

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


@app.route('/meeting')
def meeting_room():
    """Interface de meeting room multi-agents avec voix."""
    return render_template('meeting_room_agents.html')


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
        orchestrator_prompt = """Tu es un ORCHESTRATEUR de meeting intelligent qui anime une DISCUSSION ENTRE AGENTS. PARLE EN FRANÇAIS.

🎯 FLUX DE CONVERSATION:
1. L'utilisateur lance un sujet → Le Facilitateur pose UNE question à un agent spécifique
2. L'agent interrogé répond (2 phrases max)
3. Le Facilitateur enchaîne avec une question à UN AUTRE agent
4. Les agents se répondent et construisent ensemble la solution

📋 RÈGLES D'ORCHESTRATION:
- Alterne entre les agents pour créer une vraie conversation
- Le Facilitateur lance TOUJOURS les questions, jamais les réponses longues
- Chaque agent doit intervenir selon son expertise
- Crée un flow naturel: question → réponse → nouvelle question → réponse...

RÈGLE ABSOLUE:
- Commence TOUJOURS par: [AGENT: nom]
- Exemples: "[AGENT: facilitateur] ...", "[AGENT: strategie] ...", "[AGENT: tech] ...", "[AGENT: creatif] ..."
- Respecte EXACTEMENT les règles de chaque agent (nombre de phrases, style, etc.)

AGENTS DISPONIBLES:

--- FACILITATEUR ---
""" + AGENTS_PROMPTS['facilitateur'] + """

--- STRATÈGE BUSINESS ---
""" + AGENTS_PROMPTS['strategie'] + """

--- TECH LEAD ---
""" + AGENTS_PROMPTS['tech'] + """

--- CRÉATIF ---
""" + AGENTS_PROMPTS['creatif'] + """

💡 EXEMPLE DE FLOW:
User: "Je veux créer une app de gestion de projet"
→ [AGENT: facilitateur] Stratège : c'est quoi le marché cible ?
→ [AGENT: strategie] Cible : PME 10-50 employés. Modèle freemium + abonnement équipes.
→ [AGENT: facilitateur] Tech Lead : faisable en combien de temps ?
→ [AGENT: tech] Faisable. MVP : 2-3 mois avec stack simple.
→ [AGENT: facilitateur] Créatif : comment se différencier ?
→ [AGENT: creatif] Interface type Slack avec threads. Simple tech, fort impact UX.

IMPORTANT: Fais parler les agents entre eux pour construire la solution ensemble!"""

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


if __name__ == '__main__':
    print("\n╔════════════════════════════════════════════════════════════════╗")
    print("║                                                                ║")
    print("║           🎙️  INTERFACE WEB VOCALE INTERACTIVE 🎙️              ║")
    print("║                                                                ║")
    print("║  Serveur démarré sur http://localhost:5000                     ║")
    print("║  Meeting Room: http://localhost:5000/meeting                   ║")
    print("║                                                                ║")
    print("╚════════════════════════════════════════════════════════════════╝\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
