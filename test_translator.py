"""
Test simple: Parle en français → Transcription → Agent traducteur → Réponse en anglais vocale
"""

import sys
import os
from dotenv import load_dotenv
from openai import OpenAI

# Charger les variables d'environnement
load_dotenv("src/.env")

# Ajouter src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from voice_interface import VoiceInterface


def translator_agent(french_text: str) -> str:
    """
    Agent traducteur simple qui traduit du français vers l'anglais avec OpenAI.

    Args:
        french_text: Le texte en français à traduire

    Returns:
        Le texte traduit en anglais
    """
    print(f"\n📝 Texte à traduire: '{french_text}'")

    try:
        # Initialiser le client OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Appeler GPT pour traduire
        response = client.chat.completions.create(
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

        return translation

    except Exception as e:
        print(f"❌ Erreur lors de la traduction: {e}")
        return f"Translation error: {e}"


def main():
    """Programme principal."""
    print("\n╔════════════════════════════════════════════════════════════════╗")
    print("║                                                                ║")
    print("║           🌍 AGENT TRADUCTEUR VOCAL FR → EN 🌍                 ║")
    print("║                                                                ║")
    print("║  1. Parlez en français                                         ║")
    print("║  2. Votre parole est transcrite                                ║")
    print("║  3. L'agent traduit en anglais                                 ║")
    print("║  4. ElevenLabs lit la traduction en anglais                    ║")
    print("║                                                                ║")
    print("╚════════════════════════════════════════════════════════════════╝")

    # Vérifier les clés API
    if not os.getenv("ELEVENLABS_API_KEY"):
        print("\n❌ ERREUR: ELEVENLABS_API_KEY non définie dans src/.env")
        return

    if not os.getenv("OPENAI_API_KEY"):
        print("\n❌ ERREUR: OPENAI_API_KEY non définie dans src/.env")
        return

    print("\n📋 Modes disponibles:")
    print("  1. Un seul échange (parlez une fois)")
    print("  2. Conversation continue (dites 'stop' pour arrêter)")

    choice = input("\nChoix (1-2) : ").strip()

    try:
        # Créer l'interface vocale
        voice = VoiceInterface()

        if choice == "1":
            # Mode simple: un seul échange
            print("\n" + "=" * 80)
            print("🎤 MODE SIMPLE: UN ÉCHANGE")
            print("=" * 80)

            # Message de bienvenue
            welcome = "Hello! I'm your translation agent. Please speak in French and I will translate to English."
            print(f"\n🤖 {welcome}")
            voice.speak(welcome, play_audio=True)

            # Écouter l'utilisateur
            print("\n🎤 Parlez maintenant en français...")
            french_text = voice.listen()

            if french_text:
                # Traduire
                english_text = translator_agent(french_text)

                # Lire la traduction
                print(f"\n🔊 Lecture de la traduction...")
                voice.speak(english_text, play_audio=True)

                print("\n✅ Test terminé avec succès!")
            else:
                print("\n❌ Aucun texte détecté.")

        elif choice == "2":
            # Mode conversation
            print("\n" + "=" * 80)
            print("🎤 MODE CONVERSATION: TRADUCTION EN CONTINU")
            print("Dites 'stop' ou 'quitter' pour terminer")
            print("=" * 80)

            # Message de bienvenue
            welcome = "Hello! I'm your French to English translation agent. Speak in French and I'll translate for you."
            print(f"\n🤖 {welcome}")
            voice.speak(welcome, play_audio=True)

            # Boucle de conversation
            voice.conversation_loop(translator_agent)

            print("\n✅ Session terminée!")

        else:
            print("\n❌ Choix invalide")

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Programme interrompu par l'utilisateur.")
        sys.exit(0)
