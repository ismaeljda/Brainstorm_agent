"""
Backend Flask pour l'interface web de DebateHub.
"""

import sys
import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from threading import Thread, Lock
from queue import Queue
from dotenv import load_dotenv

# Désactiver les traces CrewAI AVANT TOUT
os.environ['OTEL_SDK_DISABLED'] = 'true'
os.environ['CREWAI_TELEMETRY_OPT_OUT'] = 'true'

# Charger les variables d'environnement
load_dotenv()

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator import Orchestrator

app = Flask(__name__)
CORS(app)

# État global de la réunion
meeting_state = {
    'orchestrator': None,
    'objective': '',
    'messages': [],
    'new_messages': Queue(),
    'meeting_active': False,
    'lock': Lock()
}


class WebOrchestrator(Orchestrator):
    """
    Version modifiée de l'orchestrateur pour l'interface web.
    Envoie les messages à la queue au lieu de print.
    """

    def speak(self, agent_id: str, message: str) -> None:
        """
        Envoie un message à la queue pour l'interface web.

        Args:
            agent_id: Identifiant de l'agent
            message: Message à afficher
        """
        # Ajouter à l'historique
        self.conversation_history.append({
            "agent": agent_id,
            "message": message
        })

        # Envoyer à la queue web
        meeting_state['new_messages'].put({
            'agent': agent_id,
            'message': message
        })

        # Aussi garder dans la liste globale
        with meeting_state['lock']:
            meeting_state['messages'].append({
                'agent': agent_id,
                'message': message
            })

    def _get_human_input_async(self):
        """
        Version modifiée pour l'interface web.
        Ne demande pas d'input directement, attend les messages de la queue.
        """
        # Pour l'interface web, on ne bloque pas
        # Les messages humains arrivent via l'API REST
        return None

    def run_meeting_web(self):
        """
        Version adaptée pour le web sans input bloquant.
        La réunion attend la première intervention humaine.
        """
        meeting_state['meeting_active'] = True

        # Message de bienvenue simple
        self.speak("facilitateur", f"Bonjour ! Je suis le facilitateur de cette réunion. Notre objectif aujourd'hui : {self.objective}\n\nN'hésitez pas à lancer la discussion quand vous êtes prêt. Les agents réagiront selon leur expertise.")

        # Mode "attente" - la discussion démarre vraiment quand l'humain parle
        # Les agents réagiront via send_message()

        # Pas de boucle automatique, tout se fait via les appels API
        import time
        while meeting_state['meeting_active']:
            time.sleep(1)  # Juste garder le thread actif


@app.route('/')
def index():
    """Page d'accueil."""
    return render_template('index.html')


@app.route('/start_meeting', methods=['POST'])
def start_meeting():
    """Démarre une nouvelle réunion."""
    data = request.json
    objective = data.get('objective', 'Discussion générale')

    with meeting_state['lock']:
        meeting_state['objective'] = objective
        meeting_state['messages'] = []
        meeting_state['orchestrator'] = WebOrchestrator(
            objective=objective,
            model="gpt-4o-mini"
        )

    # Lancer la réunion dans un thread séparé
    thread = Thread(target=meeting_state['orchestrator'].run_meeting_web)
    thread.daemon = True
    thread.start()

    return jsonify({
        'status': 'ok',
        'message': 'Réunion démarrée'
    })


@app.route('/send_message', methods=['POST'])
def send_message():
    """Envoie un message humain à la réunion."""
    data = request.json
    message = data.get('message', '')

    if not message:
        return jsonify({'status': 'error', 'message': 'Message vide'}), 400

    orchestrator = meeting_state['orchestrator']
    if orchestrator:
        # Lancer la réponse dans un thread séparé pour ne pas bloquer
        def process_message():
            try:
                print(f"📨 Message reçu de l'utilisateur: {message[:50]}...")
                
                # Ajouter le message humain
                orchestrator.speak('human', message)
                print("✅ Message humain ajouté à l'historique")

                # Déclencher des réponses d'agents (max 3 pour éviter la surcharge)
                context = orchestrator._build_context()

                # Faire réagir jusqu'à 3 agents pertinents
                agents_spoken = []
                max_responses = 3

                for i in range(max_responses):
                    print(f"🔄 Tentative {i+1}/{max_responses} de sélection d'agent...")
                    next_speaker = orchestrator._select_next_speaker(context)
                    print(f"👤 Agent sélectionné: {next_speaker}")

                    # Arrêter si aucun agent pertinent
                    if not next_speaker:
                        print("⚠️ Aucun agent pertinent sélectionné")
                        break
                    
                    # Si l'agent a déjà parlé dans cette série, passer au suivant
                    if next_speaker in agents_spoken:
                        print(f"⏭️ {next_speaker} a déjà parlé, on continue...")
                        continue

                    print(f"💬 Génération de la réponse pour {next_speaker}...")
                    response = orchestrator._get_agent_response(next_speaker, context)
                    
                    if response and response.strip():
                        print(f"✅ Réponse générée ({len(response)} caractères)")
                        orchestrator.speak(next_speaker, response)
                        agents_spoken.append(next_speaker)

                        # Reconstruire le contexte pour la prochaine sélection
                        context = orchestrator._build_context()
                    else:
                        print("⚠️ Réponse vide, arrêt")
                        break
                
                print(f"✅ Traitement terminé, {len(agents_spoken)} agents ont répondu")
                        
            except Exception as e:
                print(f"❌ Erreur lors du traitement du message: {e}")
                import traceback
                traceback.print_exc()

        # Lancer dans un thread
        thread = Thread(target=process_message)
        thread.daemon = True
        thread.start()

        return jsonify({'status': 'ok', 'message': 'Message envoyé'})
    else:
        return jsonify({'status': 'error', 'message': 'Réunion non démarrée'}), 400


@app.route('/get_messages', methods=['GET'])
def get_messages():
    """
    Récupère les nouveaux messages.
    Utilisé pour le polling côté client.
    """
    new_messages = []

    # Récupérer tous les messages de la queue
    while not meeting_state['new_messages'].empty():
        new_messages.append(meeting_state['new_messages'].get())

    return jsonify({
        'messages': new_messages,
        'objective': meeting_state['objective'],
        'meeting_active': meeting_state['meeting_active'],
        'status': 'Réunion en cours' if meeting_state['meeting_active'] else 'Réunion terminée'
    })


@app.route('/stop_meeting', methods=['POST'])
def stop_meeting():
    """Arrête la réunion en cours."""
    meeting_state['meeting_active'] = False
    return jsonify({'status': 'ok', 'message': 'Réunion arrêtée'})


if __name__ == '__main__':
    print("🌐 Démarrage du serveur web DebateHub...")
    print("📍 Ouvrez votre navigateur sur : http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001, threaded=True)
