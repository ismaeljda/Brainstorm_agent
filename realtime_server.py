"""
Backend server for OpenAI Realtime API
Generates ephemeral tokens for secure client connections
"""

import os
import io
from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
from dotenv import load_dotenv
import requests
from elevenlabs.client import ElevenLabs

# Load environment variables
load_dotenv("src/.env")

app = Flask(__name__)
CORS(app)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# ElevenLabs voice IDs for each agent
AGENT_VOICES = {
    'ceo': '21m00Tcm4TlvDq8ikWAM',      # Rachel - Professional female
    'marketing': 'EXAVITQu4vr4xnSDxMaL',  # Bella - Enthusiastic female
    'tech': 'TxGEqnHWrfWFTfGW9XjX',      # Josh - Clear male
    'finance': 'pNInz6obpgDQGcFmaJgB',    # Adam - Articulate male
}

@app.route('/')
def index():
    """Serve the meeting room page - Multi-agent system"""
    return send_file('meeting_room.html')

@app.route('/simple')
def simple():
    """Serve the simple single-agent version"""
    return send_file('realtime_simple.html')

@app.route('/api/token', methods=['GET'])
def get_token():
    """
    Generate an ephemeral token for OpenAI Realtime API
    This token is short-lived and can be used from the browser
    """
    try:
        print("🔑 Generating ephemeral token...")

        response = requests.post(
            'https://api.openai.com/v1/realtime/sessions',
            headers={
                'Authorization': f'Bearer {OPENAI_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'gpt-4o-realtime-preview-2024-12-17',
                'voice': 'alloy'
            }
        )

        if response.status_code != 200:
            print(f"❌ Error from OpenAI: {response.status_code}")
            print(f"Response: {response.text}")
            return jsonify({
                'error': f'Failed to create session: {response.text}'
            }), response.status_code

        data = response.json()
        print(f"✅ Token generated: {data.get('client_secret', {}).get('value', '')[:20]}...")

        return jsonify({
            'token': data['client_secret']['value'],
            'expires_at': data['client_secret']['expires_at']
        })

    except Exception as e:
        print(f"❌ Error generating token: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/speak', methods=['POST'])
def generate_speech():
    """
    Generate speech using ElevenLabs with specific agent voice
    """
    try:
        data = request.json
        text = data.get('text', '')
        agent_id = data.get('agent', 'ceo')

        if not text:
            return jsonify({'error': 'No text provided'}), 400

        voice_id = AGENT_VOICES.get(agent_id, AGENT_VOICES['ceo'])

        print(f"🎵 Generating speech for {agent_id} ({voice_id}): '{text[:50]}...'")

        # Generate audio with ElevenLabs
        audio_generator = elevenlabs_client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id="eleven_multilingual_v2"
        )

        audio_bytes = b"".join(audio_generator)

        print(f"✅ Audio generated: {len(audio_bytes)} bytes")

        # Return audio as MP3
        return send_file(
            io.BytesIO(audio_bytes),
            mimetype='audio/mpeg',
            as_attachment=False
        )

    except Exception as e:
        print(f"❌ Error generating speech: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("\n╔════════════════════════════════════════════════════════════════╗")
    print("║                                                                ║")
    print("║           🎙️  OPENAI REALTIME API SERVER 🎙️                   ║")
    print("║                                                                ║")
    print("║  Serveur démarré sur http://localhost:5000                     ║")
    print("║                                                                ║")
    print("╚════════════════════════════════════════════════════════════════╝\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
