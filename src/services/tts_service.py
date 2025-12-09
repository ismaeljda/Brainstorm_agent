"""
Service Text-to-Speech avec ElevenLabs et Firebase Storage.
"""

import os
from typing import Optional
from elevenlabs import ElevenLabs, Voice, VoiceSettings
import firebase_admin
from firebase_admin import storage
import tempfile
import uuid


class TTSService:
    """
    Service de synthèse vocale avec ElevenLabs et stockage Firebase.
    """

    # Voix par défaut pour chaque agent
    DEFAULT_VOICES = {
        "facilitateur": "Josh",  # Voix professionnelle et claire
        "strategie": "Antoni",   # Voix analytique et posée
        "tech": "Adam",          # Voix énergique et tech
        "creatif": "Bella",      # Voix créative et inspirante
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        firebase_bucket: Optional[str] = None,
        use_firebase: bool = True
    ):
        """
        Initialise le service TTS.

        Args:
            api_key: Clé API ElevenLabs (par défaut depuis env)
            firebase_bucket: Nom du bucket Firebase Storage
            use_firebase: Si True, stocke les fichiers dans Firebase Storage
        """
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        self.use_firebase = use_firebase and firebase_bucket

        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY not found in environment")

        # Initialiser client ElevenLabs
        self.client = ElevenLabs(api_key=self.api_key)

        # Initialiser Firebase Storage si nécessaire
        if self.use_firebase:
            if not firebase_admin._apps:
                firebase_admin.initialize_app()
            self.bucket = storage.bucket(firebase_bucket)
        else:
            self.bucket = None

    def generate_audio(
        self,
        text: str,
        agent_id: str = "facilitateur",
        voice_id: Optional[str] = None,
        model: str = "eleven_multilingual_v2"
    ) -> str:
        """
        Génère un fichier audio et le stocke dans Firebase Storage.

        Args:
            text: Texte à synthétiser
            agent_id: ID de l'agent (pour sélectionner la voix)
            voice_id: ID de voix ElevenLabs spécifique (optionnel)
            model: Modèle ElevenLabs à utiliser

        Returns:
            URL publique du fichier audio
        """
        # Déterminer la voix à utiliser
        if not voice_id:
            voice_id = self.DEFAULT_VOICES.get(agent_id, "Josh")

        try:
            # Générer l'audio avec ElevenLabs
            print(f"🔊 Génération audio pour '{agent_id}' (voix: {voice_id})...")

            audio_data = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id=model,
                voice_settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.75,
                    style=0.0,
                    use_speaker_boost=True
                )
            )

            # Sauvegarder dans un fichier temporaire
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            temp_file.write(b"".join(audio_data))
            temp_file.close()

            print(f"✅ Audio généré : {os.path.getsize(temp_file.name)} bytes")

            # Uploader vers Firebase Storage
            if self.use_firebase and self.bucket:
                return self._upload_to_firebase(temp_file.name, agent_id)
            else:
                # Mode local : retourner le chemin du fichier temporaire
                return f"file://{temp_file.name}"

        except Exception as e:
            print(f"❌ Erreur génération audio : {e}")
            raise

    def _upload_to_firebase(self, local_path: str, agent_id: str) -> str:
        """
        Upload un fichier vers Firebase Storage.

        Args:
            local_path: Chemin local du fichier
            agent_id: ID de l'agent

        Returns:
            URL publique du fichier
        """
        try:
            # Générer un nom unique
            filename = f"audio/{agent_id}/{uuid.uuid4()}.mp3"

            # Upload
            blob = self.bucket.blob(filename)
            blob.upload_from_filename(local_path)

            # Rendre public
            blob.make_public()

            # Supprimer le fichier temporaire
            os.remove(local_path)

            print(f"☁️  Audio uploadé : {blob.public_url}")
            return blob.public_url

        except Exception as e:
            print(f"❌ Erreur upload Firebase : {e}")
            # Fallback : retourner le fichier local
            return f"file://{local_path}"

    def get_available_voices(self) -> list:
        """
        Récupère la liste des voix disponibles.

        Returns:
            Liste des voix ElevenLabs
        """
        try:
            voices = self.client.voices.get_all()
            return [
                {
                    "voice_id": voice.voice_id,
                    "name": voice.name,
                    "category": voice.category if hasattr(voice, "category") else "unknown"
                }
                for voice in voices.voices
            ]
        except Exception as e:
            print(f"❌ Erreur récupération voix : {e}")
            return []


# Instance globale (singleton)
_tts_service: Optional[TTSService] = None


def get_tts_service(
    api_key: Optional[str] = None,
    firebase_bucket: Optional[str] = None,
    use_firebase: bool = True
) -> TTSService:
    """
    Récupère ou crée l'instance TTS (singleton).

    Args:
        api_key: Clé API ElevenLabs
        firebase_bucket: Bucket Firebase Storage
        use_firebase: Utiliser Firebase Storage

    Returns:
        Instance TTSService
    """
    global _tts_service

    if _tts_service is None:
        _tts_service = TTSService(
            api_key=api_key,
            firebase_bucket=firebase_bucket or os.getenv("FIREBASE_STORAGE_BUCKET"),
            use_firebase=use_firebase
        )

    return _tts_service


def generate_audio(
    text: str,
    agent_id: str = "facilitateur",
    voice_id: Optional[str] = None
) -> str:
    """
    Fonction helper pour générer rapidement un audio.

    Args:
        text: Texte à synthétiser
        agent_id: ID de l'agent
        voice_id: ID de voix spécifique (optionnel)

    Returns:
        URL publique du fichier audio
    """
    service = get_tts_service()
    return service.generate_audio(text, agent_id, voice_id)
