"""
Script de test simple pour l'interface vocale ElevenLabs.
Teste le mécanisme: Parole → Texte → Agent simple → Texte → Parole
"""

import sys
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Ajouter src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from voice_interface import VoiceInterface


def simple_agent(user_input: str) -> str:
    """
    Agent simple de test qui répond à l'utilisateur.
    Dans ton système final, ce sera remplacé par tes agents CrewAI.

    Args:
        user_input: Ce que l'utilisateur a dit

    Returns:
        La réponse de l'agent
    """
    # Simuler une réponse d'agent
    responses = {
        "bonjour": "Bonjour ! Je suis votre assistant de brainstorming. Comment puis-je vous aider aujourd'hui ?",
        "marketing": "En tant que spécialiste marketing, je peux vous aider à définir votre stratégie de communication, votre positionnement et votre plan de lancement.",
        "développement": "Côté technique, je peux vous conseiller sur l'architecture, les technologies à utiliser et la roadmap de développement.",
        "idée": "Excellente question ! Pour une startup réussie, il faut identifier un problème réel, avoir une solution innovante et un marché cible clair. Quelle industrie vous intéresse ?",
    }

    # Rechercher une réponse appropriée
    user_lower = user_input.lower()
    for keyword, response in responses.items():
        if keyword in user_lower:
            return response

    # Réponse par défaut
    return f"J'ai bien entendu : '{user_input}'. En tant qu'équipe de consultants, nous analysons votre demande. Pouvez-vous préciser dans quel domaine vous souhaitez innover ?"


def test_simple():
    """Test simple: un seul échange."""
    print("\n" + "=" * 80)
    print("🧪 TEST SIMPLE: UN ÉCHANGE VOCAL")
    print("=" * 80)

    try:
        voice = VoiceInterface()

        # Écouter l'utilisateur
        user_text = voice.listen()

        if user_text:
            # Obtenir la réponse de l'agent
            response = simple_agent(user_text)
            print(f"\n🤖 Agent: {response}")

            # Synthétiser et jouer la réponse
            voice.speak(response, play_audio=True)

            print("\n✅ Test terminé avec succès!")

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback

        traceback.print_exc()


def test_conversation():
    """Test complet: conversation en boucle."""
    print("\n" + "=" * 80)
    print("🧪 TEST COMPLET: CONVERSATION VOCALE")
    print("=" * 80)

    try:
        voice = VoiceInterface()

        # Message de bienvenue
        welcome_msg = "Bonjour ! Je suis votre assistant de brainstorming. Posez-moi vos questions ou décrivez votre projet."
        print(f"\n🤖 {welcome_msg}")
        voice.speak(welcome_msg, play_audio=True)

        # Lancer la boucle de conversation
        voice.conversation_loop(simple_agent)

        print("\n✅ Test terminé avec succès!")

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback

        traceback.print_exc()


def main():
    """Menu principal."""
    print("\n╔════════════════════════════════════════════════════════════════╗")
    print("║                                                                ║")
    print("║           🎙️  TEST INTERFACE VOCALE ELEVENLABS 🎙️              ║")
    print("║                                                                ║")
    print("╚════════════════════════════════════════════════════════════════╝")

    # Vérifier les clés API
    if not os.getenv("ELEVENLABS_API_KEY"):
        print("\n❌ ERREUR: ELEVENLABS_API_KEY non définie dans .env")
        print("\nÉtapes pour configurer:")
        print("1. Créez un compte sur https://elevenlabs.io")
        print("2. Récupérez votre clé API")
        print("3. Ajoutez-la dans le fichier .env:")
        print("   ELEVENLABS_API_KEY=votre-cle-api-ici")
        return

    print("\n📋 Choisissez un test:")
    print("  1. Test simple (un seul échange)")
    print("  2. Test complet (conversation continue)")
    print("  3. Test rapide (text-to-speech uniquement)")

    choice = input("\nChoix (1-3) : ").strip()

    if choice == "1":
        test_simple()
    elif choice == "2":
        test_conversation()
    elif choice == "3":
        # Test rapide sans micro
        try:
            voice = VoiceInterface()
            test_text = "Ceci est un test de synthèse vocale avec ElevenLabs."
            print(f"\n🔊 Test: '{test_text}'")
            voice.speak(test_text, play_audio=True)
            print("\n✅ Test terminé!")
        except Exception as e:
            print(f"\n❌ Erreur: {e}")
    else:
        print("\n❌ Choix invalide")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrompu par l'utilisateur.")
        sys.exit(0)
