"""
WebSocket Relay Server for OpenAI Realtime API
Relays audio between browser and OpenAI with proper format conversion
"""

import os
import json
import asyncio
import base64
from flask import Flask, render_template, send_file
from flask_cors import CORS
from flask_sock import Sock
import websockets
from dotenv import load_dotenv

load_dotenv("src/.env")

app = Flask(__name__)
CORS(app)
sock = Sock(app)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

@app.route('/')
def index():
    return send_file('realtime_simple.html')

@sock.route('/ws')
def websocket(ws):
    """WebSocket endpoint that relays between browser and OpenAI"""
    print("🔌 Client connected")

    async def relay():
        # Connect to OpenAI Realtime API
        model = 'gpt-4o-realtime-preview-2024-12-17'
        url = f"wss://api.openai.com/v1/realtime?model={model}"

        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1"
        }

        try:
            async with websockets.connect(url, extra_headers=headers) as openai_ws:
                print("✅ Connected to OpenAI")

                # Send session configuration
                config = {
                    "type": "session.update",
                    "session": {
                        "modalities": ["text", "audio"],
                        "instructions": """Tu es un assistant de brainstorming énergique pour entrepreneurs.

Ton rôle:
- Aider à clarifier et affiner les idées de business
- Poser des questions ciblées pour identifier le market fit
- Challenger constructivement
- Suggérer des prochaines étapes pratiques

Style:
- Conversationnel et encourageant
- UNE question à la fois
- Réponses COURTES (2-3 phrases max)
- Utilise "nous" pour être collaboratif

Important:
- Focus sur l'actionnable
- Pousse vers la précision: client cible, pricing, distribution""",
                        "voice": "alloy",
                        "input_audio_format": "pcm16",
                        "output_audio_format": "pcm16",
                        "turn_detection": {
                            "type": "server_vad",
                            "threshold": 0.5,
                            "prefix_padding_ms": 300,
                            "silence_duration_ms": 500
                        },
                        "input_audio_transcription": {
                            "model": "whisper-1"
                        }
                    }
                }
                await openai_ws.send(json.dumps(config))

                # Create tasks to handle bidirectional communication
                async def browser_to_openai():
                    """Forward messages from browser to OpenAI"""
                    try:
                        while True:
                            data = ws.receive()
                            if data:
                                await openai_ws.send(data)
                    except Exception as e:
                        print(f"❌ Browser to OpenAI error: {e}")

                async def openai_to_browser():
                    """Forward messages from OpenAI to browser"""
                    try:
                        async for message in openai_ws:
                            ws.send(message)

                            # Log events
                            try:
                                msg_data = json.loads(message)
                                event_type = msg_data.get('type', '')
                                if event_type in ['conversation.item.created', 'response.audio.delta', 'response.done']:
                                    print(f"📨 {event_type}")
                            except:
                                pass
                    except Exception as e:
                        print(f"❌ OpenAI to browser error: {e}")

                # Run both tasks concurrently
                await asyncio.gather(
                    browser_to_openai(),
                    openai_to_browser()
                )

        except Exception as e:
            print(f"❌ Relay error: {e}")
            ws.send(json.dumps({"type": "error", "error": str(e)}))

    # Run async relay in sync context
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(relay())
    finally:
        loop.close()
        print("🔌 Client disconnected")

if __name__ == '__main__':
    print("\n╔════════════════════════════════════════════════════════════════╗")
    print("║           🎙️  REALTIME WEBSOCKET RELAY SERVER 🎙️              ║")
    print("║  Serveur: http://localhost:5000                                ║")
    print("╚════════════════════════════════════════════════════════════════╝\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
