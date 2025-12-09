"""
Test rapide d'ElevenLabs pour debug
"""
import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv("src/.env")

try:
    client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

    print("🔊 Test de génération audio...")

    # Nouvelle API ElevenLabs
    audio = client.text_to_speech.convert(
        voice_id="21m00Tcm4TlvDq8ikWAM",
        text="Hello, this is a test.",
        model_id="eleven_multilingual_v2"
    )

    audio_bytes = b"".join(audio)

    print(f"✅ Succès ! Audio généré: {len(audio_bytes)} bytes")

except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
