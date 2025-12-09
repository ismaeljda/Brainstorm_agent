"""
Module pour gérer l'interface vocale avec ElevenLabs.
Gère le speech-to-text (reconnaissance vocale) et text-to-speech (synthèse vocale).
"""

import os
import io
import tempfile
from typing import Optional
from elevenlabs.client import ElevenLabs
from elevenlabs import play, save
import speech_recognition as sr


class VoiceInterface:
    """
    Interface vocale pour le système multi-agents.
    Permet de parler avec les agents et d'écouter leurs réponses.
    """

    def __init__(self, api_key: Optional[str] = None, voice_id: Optional[str] = None):
        """
        Initialise l'interface vocale.

        Args:
            api_key: Clé API ElevenLabs (par défaut depuis env)
            voice_id: ID de la voix à utiliser (par défaut depuis env ou voix standard)
        """
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ELEVENLABS_API_KEY non définie. "
                "Ajoutez-la dans .env ou passez-la en paramètre."
            )

        # Initialiser le client ElevenLabs
        self.client = ElevenLabs(api_key=self.api_key)

        # Voice ID (Rachel par défaut - voix féminine anglaise)
        self.voice_id = voice_id or os.getenv(
            "ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM"
        )

        # Initialiser le recognizer pour speech-to-text
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        # Calibrer le micro pour le bruit ambiant
        with self.microphone as source:
            print("🎤 Calibration du microphone...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

    def listen(self, timeout: int = 10, phrase_time_limit: int = 30) -> Optional[str]:
        """
        Écoute l'utilisateur et convertit la parole en texte.

        Args:
            timeout: Temps d'attente maximal avant de commencer à écouter (secondes)
            phrase_time_limit: Durée maximale d'enregistrement (secondes)

        Returns:
            Le texte transcrit ou None en cas d'erreur
        """
        print("\n🎤 Parlez maintenant...")

        try:
            with self.microphone as source:
                # Écouter l'utilisateur
                audio = self.recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_time_limit
                )

            print("🔄 Transcription en cours...")

            # Convertir en texte avec Google Speech Recognition (gratuit)
            # Alternatives: Whisper API, Azure Speech, etc.
            text = self.recognizer.recognize_google(audio, language="fr-FR")

            print(f"✅ Vous avez dit: '{text}'")
            return text

        except sr.WaitTimeoutError:
            print("⏱️  Temps d'attente dépassé. Aucune parole détectée.")
            return None

        except sr.UnknownValueError:
            print("❌ Impossible de comprendre l'audio.")
            return None

        except sr.RequestError as e:
            print(f"❌ Erreur du service de reconnaissance vocale: {e}")
            return None

        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            return None

    def speak(
        self, text: str, play_audio: bool = True, save_path: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Convertit du texte en parole et le joue/sauvegarde.

        Args:
            text: Le texte à synthétiser
            play_audio: Si True, joue l'audio directement
            save_path: Si fourni, sauvegarde l'audio dans ce fichier

        Returns:
            Les données audio en bytes ou None en cas d'erreur
        """
        try:
            print(f"\n🔊 Génération de la réponse vocale...")

            # Générer l'audio avec ElevenLabs
            audio_generator = self.client.generate(
                text=text, voice=self.voice_id, model="eleven_multilingual_v2"
            )

            # Convertir le générateur en bytes
            audio_bytes = b"".join(audio_generator)

            # Jouer l'audio si demandé
            if play_audio:
                print("▶️  Lecture de la réponse...")
                # Créer un fichier temporaire pour jouer l'audio
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                    f.write(audio_bytes)
                    temp_path = f.name

                # Jouer l'audio
                play(audio_bytes)

                # Nettoyer le fichier temporaire
                try:
                    os.unlink(temp_path)
                except:
                    pass

            # Sauvegarder si un chemin est fourni
            if save_path:
                with open(save_path, "wb") as f:
                    f.write(audio_bytes)
                print(f"💾 Audio sauvegardé dans: {save_path}")

            return audio_bytes

        except Exception as e:
            print(f"❌ Erreur lors de la synthèse vocale: {e}")
            return None

    def conversation_loop(self, agent_callback):
        """
        Lance une boucle de conversation: écoute → agent → parle.

        Args:
            agent_callback: Fonction qui prend le texte en entrée et retourne la réponse de l'agent
        """
        print("\n" + "=" * 80)
        print("🎙️  MODE CONVERSATION VOCALE ACTIVÉ")
        print("Dites 'stop' ou 'quitter' pour terminer la conversation.")
        print("=" * 80)

        while True:
            # Écouter l'utilisateur
            user_text = self.listen()

            if not user_text:
                continue

            # Vérifier si l'utilisateur veut quitter
            if user_text.lower() in ["stop", "quitter", "arrêter", "exit", "quit"]:
                print("\n👋 Fin de la conversation vocale.")
                self.speak("Au revoir !", play_audio=True)
                break

            # Obtenir la réponse de l'agent
            print(f"\n💭 Traitement par les agents...")
            agent_response = agent_callback(user_text)

            # Synthétiser et jouer la réponse
            if agent_response:
                print(f"\n🤖 Réponse: {agent_response}")
                self.speak(agent_response, play_audio=True)


# Exemple d'utilisation
if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    try:
        # Créer l'interface vocale
        voice = VoiceInterface()

        # Test simple: écouter et répéter
        print("\n📢 Test de l'interface vocale")
        print("Parlez pour tester la reconnaissance vocale...")

        text = voice.listen()

        if text:
            print(f"\n✅ Transcription réussie: '{text}'")
            print("\nTest de la synthèse vocale...")
            voice.speak(f"Vous avez dit: {text}", play_audio=True)

    except ValueError as e:
        print(f"\n❌ Erreur de configuration: {e}")
        print("\nAssurez-vous d'avoir configuré ELEVENLABS_API_KEY dans votre .env")

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback

        traceback.print_exc()
