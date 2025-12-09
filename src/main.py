"""
Point d'entrée CLI pour lancer une réunion multi-agents.
"""

import sys
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator import Orchestrator


def print_banner():
    """Affiche la bannière de bienvenue."""
    banner = """
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║           🤖 SYSTÈME MULTI-AGENTS - RÉUNION IA 🤖              ║
║                                                                ║
║  Orchestration intelligente d'agents spécialisés :            ║
║    • Facilitateur (anime et synthétise)                       ║
║    • Stratège Business (analyse marché & risques)             ║
║    • Tech Lead (faisabilité & architecture)                   ║
║    • Creative Thinker (innovation & différenciation)          ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def get_meeting_objective() -> str:
    """
    Demande à l'utilisateur de définir l'objectif de la réunion.

    Returns:
        Objectif de la réunion
    """
    print("\n📌 DÉFINITION DE L'OBJECTIF\n")
    print("Quel est l'objectif de cette réunion ?")
    print("(Exemple : 'Définir la stratégie de lancement d'une app mobile de fitness')\n")

    objective = input("Objectif : ").strip()

    while not objective:
        print("\n⚠️  L'objectif ne peut pas être vide. Veuillez réessayer.\n")
        objective = input("Objectif : ").strip()

    return objective


def configure_model() -> str:
    """
    Permet à l'utilisateur de choisir le modèle LLM.

    Returns:
        Nom du modèle sélectionné
    """
    print("\n⚙️  CONFIGURATION DU MODÈLE LLM\n")
    print("Modèles disponibles :")
    print("  1. gpt-4o-mini (rapide, économique) [PAR DÉFAUT]")
    print("  2. gpt-4o (plus intelligent, plus cher)")
    print("  3. gpt-4-turbo (équilibré)")

    choice = input("\nChoix (1-3, Entrée pour défaut) : ").strip()

    models = {
        "1": "gpt-4o-mini",
        "2": "gpt-4o",
        "3": "gpt-4-turbo",
        "": "gpt-4o-mini"
    }

    return models.get(choice, "gpt-4o-mini")


def check_api_key() -> bool:
    """
    Vérifie que la clé API OpenAI est configurée.

    Returns:
        True si la clé est présente
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n❌ ERREUR : Variable d'environnement OPENAI_API_KEY non définie.\n")
        print("Veuillez configurer votre clé API OpenAI :")
        print("  1. Obtenez une clé avec $5 de crédits gratuits : https://platform.openai.com/api-keys")
        print("  2. Configurez-la :")
        print("     Windows : set OPENAI_API_KEY=your-api-key")
        print("     Linux/Mac : export OPENAI_API_KEY=your-api-key")
        print("  Ou créez un fichier .env avec : OPENAI_API_KEY=your-api-key\n")
        return False
    return True


def main():
    """Fonction principale."""
    print_banner()

    # Vérifier la clé API
    if not check_api_key():
        sys.exit(1)

    # Configuration
    objective = get_meeting_objective()
    model = configure_model()

    print(f"\n✅ Configuration terminée")
    print(f"   • Objectif : {objective}")
    print(f"   • Modèle : {model}")
    print("\n" + "=" * 80)

    # Lancer l'orchestrateur
    try:
        orchestrator = Orchestrator(objective=objective, model=model)
        summary = orchestrator.run_meeting()

        # Afficher le résumé final
        print(summary)

    except KeyboardInterrupt:
        print("\n\n⚠️  Réunion interrompue par l'utilisateur.")
        sys.exit(0)

    except Exception as e:
        print(f"\n\n❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
